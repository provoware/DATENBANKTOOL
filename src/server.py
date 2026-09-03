from __future__ import annotations

import argparse
import json
import os
import sqlite3
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from src.logging_core import EventLogger
from src.persistence import Database, MigrationError

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "src" / "web"
LOGGER: EventLogger | None = None
DATABASE: Database | None = None
APP_VERSION = "0.2.0-alpha.1"


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
            self._json(
                200,
                {
                    "ok": storage.ready,
                    "status": "datenkern",
                    "version": APP_VERSION,
                    "ampel": "gelb" if storage.ready else "rot",
                    "message": (
                        "Datenkern ist bereit. Recovery-Vertrag ist noch im Aufbau."
                        if storage.ready
                        else "Datenkern ist nicht bereit."
                    ),
                    "session_id": logger.session_id,
                    "storage": {
                        "ready": storage.ready,
                        "schema_version": storage.current_version,
                        "target_version": storage.target_version,
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

        super().do_GET()

    def do_POST(self) -> None:
        if urlparse(self.path).path != "/api/log-event":
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


def main() -> int:
    parser = argparse.ArgumentParser(description="PROVOWARE DATENBANKTOOL Clean Foundation")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8765")))
    args = parser.parse_args()

    os.chdir(ROOT)
    logger = get_logger()
    logger.log("PRV-START-001", "Lokaler Server startet.")

    if not _initialize_storage(logger):
        report = logger.write_short_report("absturz")
        print("Datenbankstart fehlgeschlagen. Das Tool wurde sicher angehalten.")
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
