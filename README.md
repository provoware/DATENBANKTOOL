# PROVOWARE DATENBANKTOOL

![Status](https://img.shields.io/badge/Status-RESTOREKERN%20%2F%20AUFBAU-ffd43b?style=flat-square)
![CI](https://img.shields.io/badge/CI-Pflicht-29d3c2?style=flat-square)
![Sprache](https://img.shields.io/badge/Toolsprache-Deutsch-8b5cf6?style=flat-square)

## 🟡 Projektstatus

`[■■■■■■■□□□] 70 % · RESTOREKERN / AUFBAU`

Die Clean Foundation, der SQLite-Datenkern und der zentrale Mutations-/Recovery-Vertrag stehen.
Mit `0.5.0-alpha.1` ist P0-011 vollständig: verifizierte WAL-taugliche Backups plus
Staging-Restore, Rollback-Snapshot, atomarer Austausch, POSTCHECK und Recovery-Evidence.

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
- exklusives Datenbankzugriffsfenster für den kritischen Restore-Swap

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

## Backup-Vertrag · P0-011A

Ein Backup ist erst gültig, wenn es vollständig verifiziert und atomar veröffentlicht wurde.

Ablauf:

`SOURCE CHECK → SQLITE SNAPSHOT → INTEGRITY → HASH/METADATA → MANIFEST → VERIFY → ATOMIC PUBLISH`

Enthalten sind:

- SQLite-Backup-API statt einfacher Dateikopie
- konsistenter Snapshot auch bei WAL-Quelldatenbank
- eindeutige `bkp-...`-Backup-ID
- Backup-Manifest v1
- SHA-256 und Dateigröße
- Schema-Version und UTC-Zeit
- `quick_check` und `foreign_key_check`
- zweites unabhängiges Verifikations-Gate
- `.incomplete_*`-Staging wird niemals als gültiges Backup geführt
- finale Veröffentlichung als `backup_status_verified_*`

Details: `docs/BACKUP_VERTRAG.md`.

## Restore-Vertrag · P0-011B

Ein Restore darf die produktive Datenbank erst nach einem vollständig grünen Staging-Gate austauschen.

Ablauf:

`BACKUP VERIFY → RESTORE STAGING → STAGING VERIFY → ROLLBACK SNAPSHOT → SWAP PREPARED → SWAPPING → SWAPPED → POSTCHECK → COMMITTED oder ROLLED_BACK → EVIDENCE`

Enthalten sind:

- unmittelbare erneute Backup-Verifikation
- separate Staging-Datenbank
- SHA-256-, Schema-, `quick_check`- und Fremdschlüssel-Gate
- gemeinsamer Gate für kritische Mutationen und Restore
- exklusives Prozesszugriffsfenster während des Swap-Bereichs
- verifizierter Rollback-Snapshot des bisherigen Produktivstands
- Abbruch bei aktiven SQLite-Seitendateien statt Vorabmutation
- atomarer Austausch per `os.replace()` erst nach grünem Staging-Gate
- vollständiger POSTCHECK der produktiven Datei
- automatischer Rücktausch bei kontrolliertem Fehler nach `SWAPPED`
- rekonstruierbarer Crash-Zustand `SWAPPING` mit beiden Hashes und Rollback-Pfad
- Start-Gate blockiert unvollständige Restore-Vorgänge
- Restore-API akzeptiert nur aktuell verifizierte Backup-Namen und verlangt die exakte Bestätigung `DATENBANK WIEDERHERSTELLEN`

Status: `GET /api/restore/status`  
Ausführung: `POST /api/restore/execute`

Details: `docs/RESTORE_VERTRAG.md`.

## Sicherheitsgrenze

P0-011 Backup/Restore ist technisch implementiert und regressiv abgesichert. Der nächste P0-Schritt ist **P0-012 reale Browser-Endabnahme unter Kubuntu/KDE + Chrome**.

Direktlöschen, Massenänderungen und überschreibender Import bleiben weiterhin gesperrt,
bis ihre jeweiligen Schutzverträge vollständig implementiert und regressiv geprüft sind.

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
| `docs/BACKUP_VERTRAG.md` | Snapshot-, Manifest- und Backup-Verifikationsvertrag |
| `docs/RESTORE_VERTRAG.md` | Staging-, Swap-, Rollback- und Restore-Recovery-Vertrag |
| `MANIFEST.json` | maschinenlesbare Projektstandards |

## Datenschutz

Das Repository enthält **keine echten Nutzerdaten, Accounts, E-Mails,
Tokens, Passwörter, Browserprofile, Backups oder Betriebslogs**.
Beispielwerte müssen eindeutig als Beispiel gekennzeichnet sein.

## Entwicklungsprinzip

`Besprechen → Implementieren → Formatieren → Prüfen → Regression → Status aktualisieren → Merge`

Vor einer STABLE-Kennzeichnung müssen alle Release-Gates in
`MANIFEST.json` und `REGRESSIONSPOOL.md` grün sein.
