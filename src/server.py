from __future__ import annotations

import argparse
import json
import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from src.logging_core import EventLogger

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "src" / "web"
LOGGER = EventLogger(ROOT)


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
        if urlparse(self.path).path == "/api/health":
            self._json(
                200,
                {
                    "ok": True,
                    "status": "basis",
                    "version": "0.1.0-foundation",
                    "ampel": "gelb",
                    "message": "Clean Foundation läuft. Fachmodule sind noch im Aufbau.",
                    "session_id": LOGGER.session_id,
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
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            record = LOGGER.log(
                str(payload.get("code") or "PRV-UI-900"),
                str(payload.get("summary") or "UI-Ereignis"),
                level=str(payload.get("level") or "INFO"),
                component="browser",
                action=str(payload.get("action") or "Keine Aktion nötig."),
                details=payload.get("details") if isinstance(payload.get("details"), dict) else {},
            )
            self._json(200, {"ok": True, "event_id": record["event_id"]})
        except Exception as exc:
            LOGGER.log(
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


def main() -> int:
    parser = argparse.ArgumentParser(description="PROVOWARE DATENBANKTOOL Clean Foundation")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8765")))
    args = parser.parse_args()
    os.chdir(ROOT)
    LOGGER.log("PRV-START-001", "Lokaler Server startet.")
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"PROVOWARE DATENBANKTOOL: http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer beendet.")
    finally:
        server.server_close()
        LOGGER.log("PRV-STOP-001", "Lokaler Server wurde beendet.")
        report = LOGGER.write_short_report("beendet")
        print(f"Kurzbericht: {report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
