# PROVOWARE DATENBANKTOOL

![Status](https://img.shields.io/badge/Status-RESTOREKERN%20%2F%20AUFBAU-ffd43b?style=flat-square)
![CI](https://img.shields.io/badge/CI-Pflicht-29d3c2?style=flat-square)
![Sprache](https://img.shields.io/badge/Toolsprache-Deutsch-8b5cf6?style=flat-square)

## 🟡 Projektstatus

`[■■■■■■■□□□] 70 % · RESTOREKERN / AUFBAU`

Version `0.5.0-alpha.1` besitzt einen abgesicherten SQLite-Datenkern,
einen zentralen Mutations-/Recovery-Vertrag sowie verifizierte Backups und Restore.
Die reale Browser-Endabnahme unter Kubuntu/KDE + Chrome ist der nächste P0-Schritt.

## Was ist das Tool?

PROVOWARE DATENBANKTOOL ist die lokale technische Grundlage für ein späteres
Datenbank- und Wissenswerkzeug. Informationen sollen übersichtlich gespeichert,
wiedergefunden, gesichert und nach Fehlern kontrolliert wiederhergestellt werden.

**Offline-first** bedeutet: echte Nutzerdaten, Logs und Backups bleiben standardmäßig
auf dem eigenen Rechner und werden nicht als Projektcode versioniert.

## Sicherheitskern

### Datenänderungen

`PRECHECK → MUTATION → POSTCHECK → COMMIT oder ROLLBACK → EVIDENCE`

Jede kritische Änderung erhält eine Operation-ID. Parallele kritische Änderungen
werden zentral koordiniert. Unvollständige Vorgänge bleiben im Recovery-Journal sichtbar.

### Backup

`SOURCE CHECK → SQLITE SNAPSHOT → INTEGRITY → HASH/METADATA → MANIFEST → VERIFY → ATOMIC PUBLISH`

Ein Backup gilt erst nach erneuter unabhängiger Verifikation als gültig.

### Restore

`BACKUP VERIFY → RESTORE STAGING → STAGING VERIFY → ROLLBACK SNAPSHOT → SWAPPING → POSTCHECK → EVIDENCE`

Die produktive Datenbank wird erst nach vollständig grünem Staging-Gate ausgetauscht.
Nach dem Austausch ist ein produktiver POSTCHECK Pflicht vor `COMMITTED`.

## Wartbarkeitsgrundlage

Damit spätere Entwicklung gezielter und codesparsamer bleibt, gibt es nun zentrale
Quellen und Indizes:

- `VERSION.json` – Produkt-, Schema- und Vertragsversionen
- `src/config/registry.json` – stabile Module, API-Endpunkte und Fehlercodes
- `TOOL_SCHEMA.json` – maschinenlesbare Struktur des Tools
- `ORDNER_UND_DATEIINDEX.md` – dieselbe Struktur in einfacher Sprache
- `src/web/i18n/de.json` – versionierter deutscher UI-Sprachkatalog
- `src/web/styles.css` – zentrale Design-Tokens für Abstände, Radien, Schatten und Farben
- `docs/ENTWICKLUNGSDISZIPLIN.md` – Voranalyse- und Minimal-Patch-Vertrag

## Schnellstart

```bash
python3 -m src.server
```

Danach im Browser öffnen:

`http://127.0.0.1:8765`

Optional kann der Datenbankpfad gesetzt werden:

```bash
PROVOWARE_DB_PATH=/anderer/pfad/provoware.sqlite3 python3 -m src.server
```

## Ordner in einfacher Sprache

```text
src/                 Programmcode
src/core/            gemeinsame Metadaten-Helfer
src/persistence/     SQLite, Schema und Migrationen
src/recovery/        Mutationsschutz, Journal und Evidence
src/backup/          Backup, Restore und Verifikation
src/config/          eingebaute Registry und Standardwerte
src/web/             Browseroberfläche, Sprachkatalog und Design-Tokens
data/user/           echte lokale Nutzerdaten – nicht im Git
runtime/             Recovery-Laufzeitdaten – nicht im Git
logs/                Logs und Kurzberichte – nicht im Git
backups/             lokale Sicherungen – nicht im Git
tests/               automatische Regressionen
tools/               Entwicklungs- und Prüfwerkzeuge
docs/                technische Verträge und Erklärungen
```

Mehr Details: `ORDNER_UND_DATEIINDEX.md`.

## Entwicklungsregel

Vor jedem Patch:

`Gate prüfen → Ursache eingrenzen → Code-Ort bestimmen → Wiederverwendung suchen → kleinsten Patch festlegen`

Danach:

`Ändern → Formatieren → Tests → Regression → Diff-Audit → PR-CI → Merge → Main-Gates`

Bestehende Sicherheitskerne werden bei Wartbarkeitsarbeiten nicht nebenbei umgebaut.
Details: `docs/ENTWICKLUNGSDISZIPLIN.md`.

## Wichtige Dokumente

| Datei | Zweck |
|---|---|
| `VERSION.json` | zentrale Versionierungsübersicht |
| `MANIFEST.json` | verbindliche Qualitäts- und Sicherheitsregeln |
| `TOOL_SCHEMA.json` | maschinenlesbare Toolstruktur |
| `ORDNER_UND_DATEIINDEX.md` | laienfreundlicher Datei-/Ordnerindex |
| `AGENTS.md` | verbindliche Entwicklungsregeln |
| `LAIENHILFE.md` | einfache Hilfe und Fachbegriffserklärungen |
| `TODO.md` | aktuelle Abhakliste |
| `REGRESSIONSPOOL.md` | wiederkehrende Pflichtprüfungen |
| `FORTSCHRITTSINFO.md` | kompakter Projektstatus |
| `docs/PERSISTENCE.md` | Datenbank- und Migrationsvertrag |
| `docs/TRANSAKTIONSVERTRAG.md` | Mutations-/Recovery-Vertrag |
| `docs/BACKUP_VERTRAG.md` | Backup-Vertrag |
| `docs/RESTORE_VERTRAG.md` | Restore-, Swap- und Rollback-Vertrag |
| `docs/ENTWICKLUNGSDISZIPLIN.md` | Voranalyse- und Minimal-Patch-Regeln |

## Ampeln

- 🟢 **GRÜN** – Prüfung bestanden / normaler Betrieb
- 🟡 **GELB** – Hinweis / noch nicht releasefertig
- 🔴 **ROT** – Fehler / Gate blockiert
- 🟣 **INFO** – Erklärung oder Entwicklungsdetail

## Datenschutz

Das Repository enthält keine echten Nutzerdaten, Accounts, Passwörter, Tokens,
Backups oder Betriebslogs. Beispielwerte müssen eindeutig als Beispiel erkennbar sein.

## Release-Grenze

Kein `STABLE`, bevor Persistenz-, Recovery-, Backup/Restore-, UI-, A11y- und
Regression-Gates vollständig grün sind. Automatische Tests ersetzen keine reale
Browser-/Plattform-Endabnahme.
