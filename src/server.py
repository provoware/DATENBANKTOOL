from __future__ import annotations

import argparse
import json
import os
import sqlite3
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from src.backup import (
    BackupCreationError,
    BackupManager,
    BackupVerificationError,
    RestoreBusyError,
    RestoreError,
    RestoreManager,
)
from src.logging_core import EventLogger
from src.persistence import Database, MigrationError
from src.recovery import EvidenceJournal

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "src" / "web"
LOGGER: EventLogger | None = None
DATABASE: Database | None = None
BACKUP_MANAGER: BackupManager | None = None
RESTORE_MANAGER: RestoreManager | None = None
APP_VERSION = "0.5.0-alpha.1"
RESTORE_CONFIRMATION = "DATENBANK WIEDERHERSTELLEN"


def get_logger() -> EventLogger:
    global LOGGER
    if LOGGER is None:
        LOGGER = EventLogger(ROOT)
    return LOGGER


def get_database() -> Database:
    global DATABASE
    if DATABASE is None:
        configured = os.environ.get("PROVOWARE_DB_PATH")
        path = Path(configured) if configured else ROOT / "data" / "user" / "provoware.sqlite3"
        DATABASE = Database(path)
    return DATABASE


def get_recovery_journal() -> EvidenceJournal:
    return EvidenceJournal(ROOT / "runtime")


def get_backup_manager() -> BackupManager:
    global BACKUP_MANAGER
    if BACKUP_MANAGER is None:
        BACKUP_MANAGER = BackupManager(get_database(), ROOT / "backups")
    return BACKUP_MANAGER


def get_restore_manager() -> RestoreManager:
    global RESTORE_MANAGER
    if RESTORE_MANAGER is None:
        RESTORE_MANAGER = RestoreManager(
            get_database(),
            get_backup_manager(),
            ROOT / "runtime",
        )
    return RESTORE_MANAGER


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB), **kwargs)

    def _json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _read_json_body(self) -> dict | None:
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            return None
        if length <= 0 or length > 65536:
            return None
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return None
        return payload if isinstance(payload, dict) else None

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/health":
            self._health()
            return
        if path == "/api/storage/status":
            self._storage_status()
            return
        if path == "/api/recovery/status":
            self._recovery_status()
            return
        if path == "/api/backup/status":
            self._backup_status()
            return
        if path == "/api/restore/status":
            self._restore_status()
            return
        super().do_GET()

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/backup/create":
            self._create_backup()
            return
        if path == "/api/restore/execute":
            self._execute_restore()
            return
        if path == "/api/log-event":
            self._log_event()
            return
        self._json(404, {"ok": False, "error": "Unbekannter Endpunkt."})

    def _health(self) -> None:
        logger = get_logger()
        storage = get_database().schema_status()
        incomplete = get_recovery_journal().incomplete_operations()
        verified_backups = get_backup_manager().list_verified_backups()
        healthy = storage.ready and not incomplete
        ready_message = "Daten-, Transaktions-, Backup- und Restorekern sind bereit."
        self._json(
            200 if healthy else 503,
            {
                "ok": healthy,
                "status": "restorekern",
                "version": APP_VERSION,
                "ampel": "gelb" if healthy else "rot",
                "message": (
                    ready_message
                    if healthy
                    else "Datenkern oder Recovery-Zustand benötigt Prüfung."
                ),
                "session_id": logger.session_id,
                "storage": {
                    "ready": storage.ready,
                    "schema_version": storage.current_version,
                    "target_version": storage.target_version,
                },
                "recovery": {
                    "contract_ready": True,
                    "incomplete_operations": len(incomplete),
                },
                "backup": {
                    "contract_ready": True,
                    "manifest_version": 1,
                    "verified_backups": len(verified_backups),
                    "restore_enabled": True,
                },
            },
        )

    def _storage_status(self) -> None:
        storage = get_database().schema_status()
        integrity = get_database().integrity_check() if storage.ready else None
        self._json(
            200 if storage.ready else 503,
            {
                "ok": storage.ready and bool(integrity and integrity.ok),
                "schema_version": storage.current_version,
                "target_version": storage.target_version,
                "journal_mode": storage.journal_mode,
                "integrity": {
                    "ok": integrity.ok,
                    "foreign_key_violations": integrity.foreign_key_violations,
                }
                if integrity
                else None,
            },
        )

    def _recovery_status(self) -> None:
        incomplete = get_recovery_journal().incomplete_operations()
        self._json(
            200 if not incomplete else 503,
            {
                "ok": not incomplete,
                "contract_ready": True,
                "incomplete_operations": len(incomplete),
                "operations": list(incomplete.values())[:20],
                "message": (
                    "Keine unvollständigen Datenoperationen erkannt."
                    if not incomplete
                    else "Unvollständige Datenoperation erkannt. Vor neuen Änderungen prüfen."
                ),
            },
        )

    def _backup_status(self) -> None:
        backups = get_backup_manager().list_verified_backups()
        self._json(
            200,
            {
                "ok": True,
                "contract_ready": True,
                "manifest_version": 1,
                "verified_backups": len(backups),
                "backups": [backup.name for backup in backups[:20]],
                "restore_enabled": True,
                "message": "Backup-Verifikation und Staging-Restore sind aktiv.",
            },
        )

    def _restore_status(self) -> None:
        incomplete = get_recovery_journal().incomplete_operations()
        restore_operations = [
            item for item in incomplete.values() if item.get("operation_kind") == "database.restore"
        ]
        self._json(
            200 if not restore_operations else 503,
            {
                "ok": not restore_operations,
                "restore_enabled": True,
                "confirmation_required": RESTORE_CONFIRMATION,
                "incomplete_restore_operations": len(restore_operations),
                "operations": restore_operations[:20],
            },
        )

    def _create_backup(self) -> None:
        logger = get_logger()
        try:
            report = get_backup_manager().create_backup()
        except (BackupCreationError, BackupVerificationError, sqlite3.Error, OSError) as exc:
            logger.log(
                "PRV-BKP-001",
                "Backup konnte nicht sicher erstellt oder verifiziert werden.",
                level="ERROR",
                component="backup",
                action="Quelldatenbank und unvollständige Backup-Ordner prüfen.",
                details={"error": type(exc).__name__},
            )
            self._json(503, {"ok": False, "error": "Backup-Verifikation ist fehlgeschlagen."})
            return
        logger.log(
            "PRV-BKP-100",
            "Backup wurde erstellt und unabhängig verifiziert.",
            component="backup",
            details={
                "backup_id": report.backup_id,
                "size_bytes": report.measured_size_bytes,
                "schema_version": report.measured_schema_version,
            },
        )
        self._json(
            201,
            {
                "ok": True,
                "backup_id": report.backup_id,
                "status": "verified",
                "directory": report.backup_path.name,
                "sha256": report.measured_sha256,
                "size_bytes": report.measured_size_bytes,
                "schema_version": report.measured_schema_version,
                "restore_enabled": True,
            },
        )

    def _execute_restore(self) -> None:
        payload = self._read_json_body()
        if payload is None:
            self._json(400, {"ok": False, "error": "Ungültige Restore-Anfrage."})
            return
        if payload.get("confirm") != RESTORE_CONFIRMATION:
            self._json(409, {"ok": False, "error": "Restore-Bestätigung fehlt."})
            return
        requested = str(payload.get("backup") or "").strip()
        candidates = {path.name: path for path in get_backup_manager().list_verified_backups()}
        backup_path = candidates.get(requested)
        if backup_path is None:
            self._json(404, {"ok": False, "error": "Verifiziertes Backup nicht gefunden."})
            return
        logger = get_logger()
        try:
            report = get_restore_manager().restore_backup(backup_path)
        except RestoreBusyError as exc:
            self._json(409, {"ok": False, "error": str(exc)})
            return
        except (BackupVerificationError, RestoreError, sqlite3.Error, OSError) as exc:
            logger.log(
                "PRV-RST-001",
                "Restore wurde durch ein Sicherheits-Gate abgebrochen.",
                level="ERROR",
                component="restore",
                action="Recovery-Status und Restore-Evidence prüfen.",
                details={"error": type(exc).__name__, "backup": requested},
            )
            self._json(503, {"ok": False, "error": "Restore-Sicherheitsprüfung fehlgeschlagen."})
            return
        logger.log(
            "PRV-RST-100",
            "Restore wurde nach POSTCHECK als COMMITTED abgeschlossen.",
            component="restore",
            details={
                "operation_id": report.operation_id,
                "backup_id": report.backup_id,
                "schema_version": report.schema_version,
            },
        )
        self._json(
            200,
            {
                "ok": True,
                "state": "COMMITTED",
                "operation_id": report.operation_id,
                "backup_id": report.backup_id,
                "sha256": report.restored_sha256,
                "schema_version": report.schema_version,
            },
        )

    def _log_event(self) -> None:
        payload = self._read_json_body()
        if payload is None:
            self._json(400, {"ok": False, "error": "Ungültige Ereignisgröße."})
            return
        logger = get_logger()
        try:
            details = payload.get("details")
            if not isinstance(details, dict):
                details = {}
            record = logger.log(
                str(payload.get("code") or "PRV-UI-900"),
                str(payload.get("summary") or "UI-Ereignis"),
                level=str(payload.get("level") or "INFO"),
                component="browser",
                action=str(payload.get("action") or "Keine Aktion nötig."),
                details=details,
            )
            self._json(200, {"ok": True, "event_id": record["event_id"]})
        except Exception as exc:
            logger.log(
                "PRV-ERR-001",
                "Browser-Ereignis konnte nicht verarbeitet werden.",
                level="ERROR",
                component="server",
                action="Kurzbericht prüfen und Anfrage erneut versuchen.",
                details={"error": type(exc).__name__},
            )
            self._json(400, {"ok": False, "error": "Ereignis konnte nicht gespeichert werden."})

    def log_message(self, fmt: str, *args) -> None:
        print("[PROVOWARE] " + (fmt % args))


def _initialize_storage(logger: EventLogger) -> bool:
    database = get_database()
    try:
        report = database.initialize()
    except (MigrationError, sqlite3.Error, OSError) as exc:
        logger.log(
            "PRV-DATA-001",
            "Datenbank konnte nicht sicher vorbereitet werden.",
            level="CRITICAL",
            component="persistence",
            action="Kurzbericht prüfen. Datenbank nicht manuell überschreiben.",
            details={"error": type(exc).__name__},
        )
        return False

    logger.log(
        "PRV-DATA-100",
        "Datenbank und Schema sind bereit.",
        component="persistence",
        details={
            "schema_version": report.to_version,
            "migrations": list(report.applied_versions),
        },
    )
    return True


def _check_recovery_state(logger: EventLogger) -> bool:
    incomplete = get_recovery_journal().incomplete_operations()
    if not incomplete:
        logger.log(
            "PRV-REC-100",
            "Recovery-Journal enthält keine unvollständige Datenoperation.",
            component="recovery",
        )
        return True
    logger.log(
        "PRV-REC-001",
        "Unvollständige Datenoperation aus einer vorherigen Sitzung erkannt.",
        level="CRITICAL",
        component="recovery",
        action="Keine neue Änderung starten. Recovery-Evidence prüfen.",
        details={"incomplete_operations": len(incomplete)},
    )
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description="PROVOWARE DATENBANKTOOL Clean Foundation")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8765")))
    args = parser.parse_args()

    os.chdir(ROOT)
    logger = get_logger()
    logger.log("PRV-START-001", "Lokaler Server startet.")

    if not _initialize_storage(logger) or not _check_recovery_state(logger):
        report = logger.write_short_report("absturz")
        print("Sicherheitsprüfung fehlgeschlagen. Das Tool wurde angehalten.")
        print(f"Kurzbericht: {report}")
        return 2

    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"PROVOWARE DATENBANKTOOL: http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer beendet.")
    finally:
        server.server_close()
        logger.log("PRV-STOP-001", "Lokaler Server wurde beendet.")
        report = logger.write_short_report("beendet")
        print(f"Kurzbericht: {report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
