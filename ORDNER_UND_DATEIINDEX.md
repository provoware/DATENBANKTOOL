# Ordner- und Dateiindex · PROVOWARE DATENBANKTOOL

Diese Übersicht erklärt die Projektstruktur ohne Programmierkenntnisse. Die maschinenlesbare Schwesterdatei ist `TOOL_SCHEMA.json`.

## Wurzel

| Pfad | Zweck |
|---|---|
| `VERSION.json` | zentrale Produkt-, Schema- und Vertragsversionen |
| `MANIFEST.json` | verbindliche Qualitäts-, Datei- und Sicherheitsregeln |
| `TOOL_SCHEMA.json` | maschinenlesbares Schema der Toolstruktur |
| `README.md` | Einstieg und Gesamtüberblick |
| `LAIENHILFE.md` | einfache Bedien- und Fehlerhilfe |
| `AGENTS.md` | verbindliche Entwicklungsregeln |
| `REGRESSIONSPOOL.md` | wiederkehrende Pflichtprüfungen |
| `TODO.md` | offene und erledigte Arbeitspunkte |
| `CHANGELOG.md` | chronologische Änderungen |

## Programmcode

```text
src/
├── core/
│   └── project_meta.py      zentrale Version-/Registry-Lesefunktionen
├── persistence/
│   ├── database.py          SQLite-Verbindungen und Integritätsprüfung
│   ├── migrations.py        unveränderliche Schema-Migrationen
│   └── store.py             wiederverwendbarer Datenspeicher
├── recovery/
│   ├── gate.py              gemeinsamer Gate für kritische Änderungen
│   ├── mutation.py          Mutations-/Rollback-Vertrag
│   └── evidence.py          Recovery-Journal und Evidence
├── backup/
│   ├── engine.py            sichere Backup-Erstellung und Verifikation
│   └── restore.py           Staging-Restore, Swap und Rollback
├── config/
│   ├── defaults.json        eingebaute Standardwerte
│   └── registry.json        zentrale technische Registry
├── web/
│   ├── index.html           Grundstruktur der Oberfläche
│   ├── app.js               UI-Verhalten und Statusabfrage
│   ├── styles.css           Design-Tokens und Komponentenstile
│   └── i18n/de.json         versionierter deutscher Sprachkatalog
├── logging_core.py          Maschinenlog und deutsche Kurzberichte
└── server.py                lokaler HTTP-Server, API und Runtime-Metadaten
```

## Zentrale Metadaten – einfach erklärt

`VERSION.json` ist die einzige fachliche Quelle für Produktversion, Status-ID,
Fortschritt sowie Schema- und Vertragsversionen. Die Browseroberfläche erhält
Produktmetadaten über `GET /api/project/meta`. Dadurch muss keine zweite
Metadatendatei für die Oberfläche gepflegt werden.

Sichtbare deutsche Bezeichnungen liegen nicht in `VERSION.json`, sondern im
versionierten Sprachkatalog `src/web/i18n/de.json`.

## Entwicklung und Prüfung

| Pfad | Zweck |
|---|---|
| `tests/` | automatische Regressionen und Verträge |
| `tools/check_project.py` | prüft Pflichtdateien und harte Dateigrenzen |
| `.github/workflows/ci.yml` | Prüfung jedes Branch-/PR-Stands |
| `.github/workflows/release-gate.yml` | zusätzliche Prüfung auf `main` |
| `docs/ENTWICKLUNGSDISZIPLIN.md` | Voranalyse- und Patch-Regeln |
| `docs/PERSISTENCE.md` | Datenbankvertrag |
| `docs/TRANSAKTIONSVERTRAG.md` | Mutations- und Recovery-Vertrag |
| `docs/BACKUP_VERTRAG.md` | Backup-Vertrag |
| `docs/RESTORE_VERTRAG.md` | Restore-, Swap- und Rollback-Vertrag |

## Lokale Daten – nicht ins Git

- `data/user/` – echte lokale Nutzerdatenbank
- `runtime/` – Recovery-Journal und Laufzeitzustand
- `logs/` – technische Logs und Kurzberichte
- `backups/` – lokale Sicherungen

**Merksatz:** Programm und Regeln sind versioniert. Persönliche Daten, Logs und Backups bleiben lokal.
