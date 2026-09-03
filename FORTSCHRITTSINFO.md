# FORTSCHRITTSINFO

## Aktueller Stand

**Version:** `0.5.1-alpha.1`  
**Status:** 🟡 `RESTOREKERN / AUFBAU`  
**Fortschritt:** `[■■■■■■■□□□] 70 %`

| Bereich | Status | Kurzdetail |
|---|---|---|
| Repository-Basis | 🟢 | Clean Foundation steht |
| Entwicklungsdisziplin | 🟢 | Voranalyse, Minimal-Patch und Diff-Audit verbindlich |
| Versionierung | 🟢 | `VERSION.json` ist die einzige fachliche Produktversionsquelle |
| Registry | 🟢 | Module, Endpunkte und stabile Fehlercodes zentral indexiert |
| Runtime-Metadaten | 🟢 | Oberfläche liest Produktstand über `/api/project/meta` |
| Sprache / UI-Basis | 🟢 | deutscher Sprachkatalog + Design-Tokens zentralisiert |
| Dokumentation | 🟢 | Tool-Schema und laienfreundlicher Dateiindex vorhanden |
| CI / Tests | 🟢 | Pflicht-Gates und Architektur-Driftprüfungen aktiv |
| Persistenz | 🟢 | SQLite-Schema v1 + exklusives Restore-Zugriffsfenster |
| Transaktionsvertrag | 🟢 | PRE/POST, Commit/Rollback, Operation-ID und Evidence aktiv |
| Recovery-Journal | 🟢 | JSONL-Zustandsjournal + Start-Gate aktiv |
| Backup Engine | 🟢 | WAL-Snapshot + Manifest v1 + unabhängige Verifikation |
| Restore Engine | 🟢 | Staging-Gate + Rollback-Snapshot + atomarer Swap + POSTCHECK |
| reale UI-Abnahme | 🔴 | P0-012 noch nicht durchgeführt |

## Nachweis P0-011B

Der P0-011B-Merge wurde auch nach dem Merge auf exakt demselben `main`-Head geprüft.
CI und Release Gate sind dort grün. Backup/Restore ist damit vollständig
post-merge nachgewiesen; offen bleibt die reale Plattform-/Browser-Endabnahme P0-012.

## Wartbarkeitsverbesserungen

- `VERSION.json` trennt Produkt-, Schema- und Vertragsversionen.
- `src/core/project_meta.py` stellt dieselben Metadaten wiederverwendbar für Python bereit.
- `GET /api/project/meta` liefert den Produktstand an die Browseroberfläche.
- eine zweite statische UI-Metadatendatei ist nicht mehr nötig und wurde entfernt.
- sichtbare Statusbezeichnungen liegen ausschließlich im versionierten Sprachkatalog.
- `src/config/registry.json` macht vorhandene Module, Endpunkte und Fehlercodes auffindbar.
- `TOOL_SCHEMA.json` beschreibt die Toolstruktur maschinenlesbar.
- `ORDNER_UND_DATEIINDEX.md` erklärt dieselbe Struktur für Menschen.
- `tools/check_project.py` übernimmt kritische Pflichtdateien aus `TOOL_SCHEMA.json`.
- `docs/ENTWICKLUNGSDISZIPLIN.md` verlangt Code-Ort- und Wiederverwendungsanalyse vor Patches.
- wiederkehrende Abstände, Radien, Schatten und Farben sind als Design-Tokens vereinheitlicht.
- Regressionen verhindern Versions-, Registry-, Sprach- und Tool-Schema-Drift.
- Persistenz-, Recovery-, Backup- und Restore-Sicherheitslogik wurde fachlich nicht verändert.

## Nächster sinnvoller Schritt

**P0-012 – reale Browser-Endabnahme unter Kubuntu/KDE + Chrome.**

Ziel: Start, Status, Layout, Fokus, Zoom, Fehlersichtbarkeit und kritische Bedienpfade
im echten Zielsystem prüfen, ohne die bereits grünen Datenverträge neu zu erfinden.

## Release-Regel

`STABLE` erst nach grünem Persistenz-, Recovery-, Backup/Restore-, UI-, A11y-
und Regression-Gate.
