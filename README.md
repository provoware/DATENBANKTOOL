# PROVOWARE DATENBANKTOOL

![Status](https://img.shields.io/badge/Status-BASIS%20%2F%20AUFBAU-ffd43b?style=flat-square)
![CI](https://img.shields.io/badge/CI-Pflicht-29d3c2?style=flat-square)
![Sprache](https://img.shields.io/badge/Toolsprache-Deutsch-8b5cf6?style=flat-square)

## 🟡 Projektstatus

`[■■■□□□□□□□] 30 % · CLEAN FOUNDATION`

Das Repository wurde bewusst auf eine saubere Basis zurückgesetzt.
Die alte Projektgeschichte bleibt über Git erhalten.
Der unmittelbare Vorgängerstand ist zusätzlich auf
`backup/pre-clean-rebuild-20260903` gesichert.

## Ziel

PROVOWARE DATENBANKTOOL soll ein lokal betreibbares, laienfreundliches
und robustes Datenbank-/Wissenswerkzeug werden.
Die neue Basis trennt konsequent:

- **Basistool** – Programmcode und feste UI-Grundlage
- **Konfiguration** – versionierbare Standardwerte, keine privaten Einstellungen
- **Nutzerdaten** – lokal, nicht im Repository
- **Laufzeitdaten** – Logs, Caches, Backups, Sessions; nicht im Repository
- **Dokumentation** – Laien- und Entwicklerwissen getrennt
- **Tests & Werkzeuge** – reproduzierbare Qualitätskontrolle

## Schnellstart

```bash
python3 src/server.py
```

Danach im Browser öffnen:

`http://127.0.0.1:8765`

## Ampeln

- 🟢 **GRÜN** – Prüfung bestanden / normaler Betrieb
- 🟡 **GELB** – Hinweis / noch nicht releasefertig
- 🔴 **ROT** – Fehler / Gate blockiert
- 🟣 **INFO** – Erklärung, Tipp oder Entwicklungsdetail

## Wichtige Dokumente

| Datei | Zweck |
|---|---|
| `TODO.md` | aktuelle Abhakliste |
| `FORTSCHRITTSINFO.md` | kompakter Status |
| `ENTWICKLUNGSPLAN.md` | Roadmap |
| `REGRESSIONSPOOL.md` | wiederkehrende Fehlerprüfungen |
| `AGENTS.md` | verbindliche Entwicklungsregeln |
| `DEVELOPER_HANDBOOK.md` | Architektur & Entwicklerwissen |
| `LAIENHILFE.md` | einfache Hilfe & Tipps |
| `DEBUGGING_LOGGING.md` | Logging-/Fehlerstandard |
| `MANIFEST.json` | maschinenlesbare Projektstandards |

## Datenschutz

Das Repository enthält **keine echten Nutzerdaten, Accounts, E-Mails,
Tokens, Passwörter, Browserprofile, Backups oder Betriebslogs**.
Beispielwerte müssen eindeutig als Beispiel gekennzeichnet sein.

## Entwicklungsprinzip

`Besprechen → Implementieren → Formatieren → Prüfen → Regression → Status aktualisieren → Merge`

Vor einer STABLE-Kennzeichnung müssen alle Release-Gates in
`MANIFEST.json` und `REGRESSIONSPOOL.md` grün sein.
