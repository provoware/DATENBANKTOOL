from pathlib import Path
from tempfile import TemporaryDirectory
import sqlite3
import unittest

from datenbanktool.core.incremental import IncrementalScanOptions, incremental_rescan
from datenbanktool.core.index_database import IndexBuildOptions, IndexDatabase, SCHEMA_VERSION, build_index
from datenbanktool.core.index_lock import IndexLockedError, IndexProcessLock
from datenbanktool.core.progress import ProgressEvent


class IncrementalTests(unittest.TestCase):
    def test_schema_three_is_created(self) -> None:
        with TemporaryDirectory() as directory:
            db = Path(directory) / "index.sqlite3"
            with IndexDatabase(db) as index:
                self.assertEqual(index.migrate(), SCHEMA_VERSION)
                tables = {
                    row[0]
                    for row in index.connection.execute(
                        "SELECT name FROM sqlite_master WHERE type='table'"
                    )
                }
                self.assertIn("file_changes", tables)
                self.assertIn("progress_events", tables)
                self.assertIn("file_identity", tables)

    def test_incremental_detects_new_changed_moved_removed_and_unchanged(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory) / "data"
            root.mkdir()
            db = Path(directory) / "index.sqlite3"
            (root / "move.txt").write_text("move", encoding="utf-8")
            (root / "change.txt").write_text("before", encoding="utf-8")
            (root / "remove.txt").write_text("remove", encoding="utf-8")
            (root / "keep.txt").write_text("keep", encoding="utf-8")
            baseline = build_index(IndexBuildOptions(root=root, database=db, hash_duplicates=True, batch_size=2))
            (root / "move.txt").rename(root / "moved.txt")
            (root / "change.txt").write_text("after-with-different-size", encoding="utf-8")
            (root / "remove.txt").unlink()
            (root / "new.txt").write_text("new", encoding="utf-8")
            result = incremental_rescan(
                IncrementalScanOptions(root=root, database=db, batch_size=2)
            )
            self.assertEqual(result.baseline_session_id, baseline.session_id)
            self.assertEqual(result.added_count, 1)
            self.assertEqual(result.modified_count, 1)
            self.assertEqual(result.moved_count, 1)
            self.assertEqual(result.removed_count, 1)
            self.assertEqual(result.unchanged_count, 1)
            self.assertEqual(result.status, "complete")
            with IndexDatabase(db) as index:
                moved = index.connection.execute(
                    "SELECT old_path,new_path,details_json FROM file_changes WHERE session_id=? AND change_type='moved'",
                    (result.session_id,),
                ).fetchone()
                self.assertEqual((moved["old_path"], moved["new_path"]), ("move.txt", "moved.txt"))

    def test_incremental_can_resume(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory) / "data"
            root.mkdir()
            db = Path(directory) / "index.sqlite3"
            for index in range(5):
                (root / f"{index}.txt").write_text(str(index), encoding="utf-8")
            build_index(IndexBuildOptions(root=root, database=db))
            (root / "new.txt").write_text("new", encoding="utf-8")
            interrupted = incremental_rescan(
                IncrementalScanOptions(root=root, database=db, max_files=2, batch_size=1)
            )
            self.assertEqual(interrupted.status, "interrupted")
            complete = incremental_rescan(
                IncrementalScanOptions(root=root, database=db, resume=True, batch_size=1)
            )
            self.assertTrue(complete.resumed)
            self.assertEqual(complete.status, "complete")
            self.assertEqual(complete.imported_count, 6)

    def test_unchanged_hashes_are_reused(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory) / "data"
            root.mkdir()
            db = Path(directory) / "index.sqlite3"
            (root / "a.txt").write_text("same", encoding="utf-8")
            (root / "b.txt").write_text("same", encoding="utf-8")
            baseline = build_index(IndexBuildOptions(root=root, database=db, hash_duplicates=True))
            result = incremental_rescan(IncrementalScanOptions(root=root, database=db))
            with IndexDatabase(db) as index:
                old = {
                    row["relative_path"]: row["sha256"]
                    for row in index.connection.execute(
                        "SELECT relative_path,sha256 FROM files WHERE session_id=?", (baseline.session_id,)
                    )
                }
                new = {
                    row["relative_path"]: row["sha256"]
                    for row in index.connection.execute(
                        "SELECT relative_path,sha256 FROM files WHERE session_id=?", (result.session_id,)
                    )
                }
            self.assertEqual(old, new)
            self.assertTrue(all(new.values()))

    def test_process_lock_blocks_second_writer(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory) / "data"
            root.mkdir()
            (root / "a.txt").write_text("a", encoding="utf-8")
            db = Path(directory) / "index.sqlite3"
            with IndexProcessLock(db, "test"):
                with self.assertRaises(IndexLockedError):
                    build_index(IndexBuildOptions(root=root, database=db))

    def test_progress_events_are_callbacked_and_persisted(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory) / "data"
            root.mkdir()
            (root / "a.txt").write_text("a", encoding="utf-8")
            db = Path(directory) / "index.sqlite3"
            events: list[ProgressEvent] = []
            result = build_index(
                IndexBuildOptions(root=root, database=db, batch_size=1),
                progress_callback=events.append,
            )
            self.assertTrue(events)
            self.assertEqual(events[-1].kind, "complete")
            with IndexDatabase(db) as index:
                amount = index.connection.execute(
                    "SELECT COUNT(*) FROM progress_events WHERE session_id=?", (result.session_id,)
                ).fetchone()[0]
            self.assertGreaterEqual(amount, 2)


if __name__ == "__main__":
    unittest.main()

class MigrationAndEdgeCaseTests(unittest.TestCase):
    def test_existing_schema_two_with_phase_check_migrates_and_rescans(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory) / "data"
            root.mkdir()
            (root / "a.txt").write_text("a", encoding="utf-8")
            db = Path(directory) / "legacy.sqlite3"
            connection = sqlite3.connect(db)
            connection.executescript(
                """
                PRAGMA user_version=2;
                CREATE TABLE schema_migrations(version INTEGER PRIMARY KEY, applied_utc TEXT NOT NULL, description TEXT NOT NULL);
                CREATE TABLE metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL);
                CREATE TABLE scan_sessions(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    root TEXT NOT NULL,
                    options_json TEXT NOT NULL,
                    status TEXT NOT NULL CHECK(status IN ('running','interrupted','complete','failed')),
                    phase TEXT NOT NULL CHECK(phase IN ('scanning','hashing','finalizing','complete')),
                    started_utc TEXT NOT NULL, updated_utc TEXT NOT NULL, finished_utc TEXT,
                    last_relative_path TEXT, last_hash_path TEXT,
                    imported_count INTEGER NOT NULL DEFAULT 0,
                    error_count INTEGER NOT NULL DEFAULT 0,
                    truncated INTEGER NOT NULL DEFAULT 0 CHECK(truncated IN (0,1)),
                    source_fingerprint TEXT
                );
                CREATE TABLE files(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL REFERENCES scan_sessions(id) ON DELETE CASCADE,
                    relative_path TEXT NOT NULL,
                    size_bytes INTEGER NOT NULL,
                    modified_utc TEXT NOT NULL,
                    suffix TEXT NOT NULL,
                    category TEXT NOT NULL,
                    is_symlink INTEGER NOT NULL,
                    is_large INTEGER NOT NULL,
                    sha256 TEXT,
                    UNIQUE(session_id,relative_path)
                );
                CREATE TABLE filename_warnings(file_id INTEGER NOT NULL REFERENCES files(id) ON DELETE CASCADE, code TEXT NOT NULL, PRIMARY KEY(file_id,code));
                CREATE TABLE scan_errors(id INTEGER PRIMARY KEY AUTOINCREMENT, session_id INTEGER NOT NULL REFERENCES scan_sessions(id) ON DELETE CASCADE, path TEXT NOT NULL, operation TEXT NOT NULL, message TEXT NOT NULL);
                CREATE TABLE duplicate_groups(id INTEGER PRIMARY KEY AUTOINCREMENT, session_id INTEGER NOT NULL REFERENCES scan_sessions(id) ON DELETE CASCADE, sha256 TEXT NOT NULL, size_bytes INTEGER NOT NULL, UNIQUE(session_id,sha256,size_bytes));
                CREATE TABLE duplicate_members(group_id INTEGER NOT NULL REFERENCES duplicate_groups(id) ON DELETE CASCADE, file_id INTEGER NOT NULL REFERENCES files(id) ON DELETE CASCADE, PRIMARY KEY(group_id,file_id));
                """
            )
            connection.commit()
            connection.close()
            with IndexDatabase(db) as index:
                self.assertEqual(index.migrate(), SCHEMA_VERSION)
                columns = {row[1] for row in index.connection.execute("PRAGMA table_info(scan_sessions)")}
                self.assertIn("incremental_stage", columns)
            baseline = build_index(IndexBuildOptions(root=root, database=db))
            (root / "b.txt").write_text("b", encoding="utf-8")
            result = incremental_rescan(IncrementalScanOptions(root=root, database=db))
            self.assertEqual(result.status, "complete")
            self.assertEqual(result.baseline_session_id, baseline.session_id)

    def test_same_size_replacement_is_modified_not_unchanged(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory) / "data"
            root.mkdir()
            db = Path(directory) / "index.sqlite3"
            target = root / "a.txt"
            target.write_text("AAAA", encoding="utf-8")
            build_index(IndexBuildOptions(root=root, database=db))
            replacement = root / "replacement.tmp"
            replacement.write_text("BBBB", encoding="utf-8")
            replacement.replace(target)
            result = incremental_rescan(IncrementalScanOptions(root=root, database=db))
            self.assertEqual(result.modified_count, 1)
            self.assertEqual(result.unchanged_count, 0)

    def test_hash_move_detection_works_when_inode_changes(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory) / "data"
            root.mkdir()
            db = Path(directory) / "index.sqlite3"
            old = root / "old.txt"
            old.write_text("hash-move", encoding="utf-8")
            (root / "anchor.txt").write_text("hash-move", encoding="utf-8")
            build_index(IndexBuildOptions(root=root, database=db, hash_duplicates=True))
            payload = old.read_bytes()
            old.unlink()
            (root / "new.txt").write_bytes(payload)
            result = incremental_rescan(
                IncrementalScanOptions(root=root, database=db, detect_moves_by_hash=True)
            )
            self.assertEqual(result.moved_count, 1)
            self.assertEqual(result.added_count, 0)
            self.assertEqual(result.removed_count, 0)
