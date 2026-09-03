from __future__ import annotations

import argparse
import json
import os
import sqlite3
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from src.backup import BackupCreationError, BackupManager, BackupVerificationError
from src.logging_core import EventLogger
from src.persistence import Database, MigrationError
from src.recovery import EvidenceJournal

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "src" / "web"
LOGGER: EventLogger | None = None
DATABASE: Database | None = None
BACKUP_MANAGER: BackupManager | None = None
APP_VERSION = "0.4.0-alpha.1"


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

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/health":
            logger = get_logger()
            storage = get_database().schema_status()
            incomplete = get_recovery_journal().incomplete_operations()
            verified_backups = get_backup_manager().list_verified_backups()
            healthy = storage.ready and not incomplete
            ready_message = "Daten-, Transaktions- und Backupkern sind bereit."
            message = (
                f"{ready_message} Restore ist noch gesperrt."
                if healthy
                else "Datenkern oder Recovery-Zustand benötigt Prüfung."
            )
            self._json(
                200 if healthy else 503,
                {
                    "ok": healthy,
                    "status": "backupkern",
                    "version": APP_VERSION,
                    "ampel": "gelb" if healthy else "rot",
                    "message": message,
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
                        "restore_enabled": False,
                    },
                },
            )
            return

        if path == "/api/storage/status":
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
            return

        if path == "/api/recovery/status":
            incomplete = get_recovery_journal().incomplete_operations()
            self._json(
                200 if not incomplete else 503,
                {
                    "ok": not incomplete,
                    "contract_ready": True,
                    "incomplete_operations": len(incomplete),
                    "operations": list(incomplete.values())[:20],
                    "message": (
                        "Keine unvollständigen Datenänderungen erkannt."
                        if not incomplete
                        else "Unvollständige Datenänderung erkannt. Vor neuen Änderungen prüfen."
                    ),
                },
            )
            return

        if path == "/api/backup/status":
            backups = get_backup_manager().list_verified_backups()
            backup_message = "Backup-Verifikation ist aktiv."
            self._json(
                200,
                {
                    "ok": True,
                    "contract_ready": True,
                    "manifest_version": 1,
                    "verified_backups": len(backups),
                    "backups": [backup.name for backup in backups[:20]],
                    "restore_enabled": False,
                    "message": f"{backup_message} Restore bleibt bis P0-011B gesperrt.",
                },
            )
            return

        super().do_GET()

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/backup/create":
            self._create_backup()
            return
        if path != "/api/log-event":
            self._json(404, {"ok": False, "error": "Unbekannter Endpunkt."})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = 0
        if length <= 0 or length > 65536:
            self._json(400, {"ok": False, "error": "Ungültige Ereignisgröße."})
            return
        logger = get_logger()
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
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
                "restore_enabled": False,
            },
        )

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
            "Recovery-Journal enthält keine unvollständige Datenänderung.",
            component="recovery",
        )
        return True
    logger.log(
        "PRV-REC-001",
        "Unvollständige Datenänderung aus einer vorherigen Sitzung erkannt.",
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
