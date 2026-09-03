# PROVOWARE DATENBANKTOOL

![Status](https://img.shields.io/badge/Status-TRANSAKTIONSKERN%20%2F%20AUFBAU-ffd43b?style=flat-square)
![CI](https://img.shields.io/badge/CI-Pflicht-29d3c2?style=flat-square)
![Sprache](https://img.shields.io/badge/Toolsprache-Deutsch-8b5cf6?style=flat-square)

## 🟡 Projektstatus

`[■■■■■□□□□□] 50 % · TRANSAKTIONSKERN / AUFBAU`

Die Clean Foundation und der SQLite-Datenkern stehen. Mit `0.3.0-alpha.1` ist
zusätzlich der zentrale Mutations-/Recovery-Vertrag aktiv: Operation-ID,
PRE-/POST-Prüfung, Commit/Rollback, Single-Writer-Gate, Idempotenz und Evidence.

Der Stand vor dem Clean Rebuild bleibt auf
`backup/pre-clean-rebuild-20260903` gesichert.

## Ziel

PROVOWARE DATENBANKTOOL soll ein lokal betreibbares, laienfreundliches
und robustes Datenbank-/Wissenswerkzeug werden.

Die Architektur trennt konsequent:

- **Basistool** – Programmcode und feste UI-Grundlage
- **Konfiguration** – versionierbare Standardwerte, keine privaten Einstellungen
- **Nutzerdaten** – lokal, nicht im Repository
- **Laufzeitdaten** – Logs, Recovery-Evidence, Caches und Sessions; nicht im Repository
- **Backups** – lokal und getrennt vom Basistool
- **Dokumentation** – Laien- und Entwicklerwissen getrennt
- **Tests & Werkzeuge** – reproduzierbare Qualitätskontrolle

## Schnellstart

```bash
python3 -m src.server
```

Danach im Browser öffnen:

`http://127.0.0.1:8765`

Die lokale Datenbank wird beim ersten Start automatisch unter
`data/user/provoware.sqlite3` angelegt und auf die aktuelle Schema-Version migriert.

Optional kann der Datenbankpfad gesetzt werden:

```bash
PROVOWARE_DB_PATH=/anderer/pfad/provoware.sqlite3 python3 -m src.server
```

## Datenkern

Der Persistenzkern verwendet die Python-Standardbibliothek `sqlite3`.

Enthalten sind:

- Schema-Version `1`
- Migrationen mit SHA-256-Prüfsumme
- SQLite-Fremdschlüssel und WAL
- `PRAGMA quick_check` und Fremdschlüsselprüfung
- hierarchische Einträge über `parent_id`
- Tags und App-Einstellungen
- generischer `EntryStore`

Details: `docs/PERSISTENCE.md`.

## Transaktions- und Recovery-Vertrag

Produktive Mutationen folgen zentral:

`PRECHECK → MUTATION → POSTCHECK → COMMIT oder ROLLBACK → EVIDENCE`

Zusätzlich aktiv:

- eindeutige `operation_id`
- Single-Writer-Gate gegen parallele kritische Änderungen
- optionaler Idempotenzschlüssel gegen Doppel-Submit/Doppelklick
- JSONL-Recovery-Journal unter `runtime/recovery/`
- atomare finale JSON-Evidence mit Status im Dateinamen
- sensible Evidence-Details werden geschwärzt
- unvollständige frühere Operation blockiert den normalen Start
- Status-Endpunkt: `GET /api/recovery/status`

Details: `docs/TRANSAKTIONSVERTRAG.md`.

## Sicherheitsgrenze

Direktlöschen, Massenänderungen, überschreibender Import und Restore werden nicht
vorschnell freigegeben. Der nächste P0-Schritt ist **P0-011 Backup/Restore mit
Integritätsprüfung und sicherem Austauschvertrag**.

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
| `docs/PERSISTENCE.md` | Datenbank-, Schema- und Migrationsvertrag |
| `docs/TRANSAKTIONSVERTRAG.md` | Mutations-, Rollback- und Recovery-Vertrag |
| `MANIFEST.json` | maschinenlesbare Projektstandards |

## Datenschutz

Das Repository enthält **keine echten Nutzerdaten, Accounts, E-Mails,
Tokens, Passwörter, Browserprofile, Backups oder Betriebslogs**.
Beispielwerte müssen eindeutig als Beispiel gekennzeichnet sein.

## Entwicklungsprinzip

`Besprechen → Implementieren → Formatieren → Prüfen → Regression → Status aktualisieren → Merge`

Vor einer STABLE-Kennzeichnung müssen alle Release-Gates in
`MANIFEST.json` und `REGRESSIONSPOOL.md` grün sein.
