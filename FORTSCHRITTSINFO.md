# FORTSCHRITTSINFO

## Aktueller Stand

**Version:** `0.5.2-alpha.1`  
**Status:** 🟡 `BROWSER-ABNAHME VORBEREITET`  
**Fortschritt:** `[■■■■■■■■□□] 75 %`

| Bereich | Status | Kurzdetail |
|---|---|---|
| Repository-Basis | 🟢 | Clean Foundation steht |
| Entwicklungsdisziplin | 🟢 | Voranalyse, Minimal-Patch und Diff-Audit verbindlich |
| Versionierung | 🟢 | Produkt-, Schema- und Vertragsstände zentral getrennt |
| Registry | 🟢 | Module, Endpunkte, Qualitäts-Gates und Fehlercodes zentral indexiert |
| Sprache / UI-Basis | 🟢 | deutscher Sprachkatalog + Design-Tokens zentralisiert |
| Dokumentation | 🟢 | Tool-Schema und laienfreundlicher Dateiindex vorhanden |
| CI / Tests | 🟢 | Pflicht-Gates und Architektur-Driftprüfungen aktiv |
| Persistenz | 🟢 | SQLite-Schema v1 + exklusives Restore-Zugriffsfenster |
| Transaktionsvertrag | 🟢 | PRE/POST, Commit/Rollback, Operation-ID und Evidence aktiv |
| Recovery-Journal | 🟢 | JSONL-Zustandsjournal + Start-Gate aktiv |
| Backup Engine | 🟢 | WAL-Snapshot + Manifest v1 + unabhängige Verifikation |
| Restore Engine | 🟢 | Staging-Gate + Rollback-Snapshot + atomarer Swap + POSTCHECK |
| automatischer Browser-Smoke | 🟡 | P0-012A implementiert, Branch-/PR-Gates laufen noch |
| reale UI-Abnahme | 🔴 | P0-012B/C auf Kubuntu/KDE + Chrome noch offen |

## P0-012A · reproduzierbare Browser-Abnahme

Neu vorhanden:

- Playwright-Smoke für 1366×768, 1600×900 und 1920×1080.
- Prüfung von Runtime-Metadaten, Health-Status, Fortschritt und Footer.
- Prüfung auf horizontalen Seitenüberlauf und JavaScript-Fehler.
- Tastaturtest für Kurzhilfe und Skip-Link.
- eigener GitHub-Workflow `Browser Smoke` mit Evidence-Artefakten.
- lokaler Starter `bash tools/run_browser_acceptance.sh` für echtes Google Chrome.
- manuelle KDE-/Chrome-Abnahmematrix in `docs/BROWSER_ABNAHME.md`.

Der CI-Chromium-Lauf ist ausdrücklich **kein Ersatz** für die reale KDE-/Chrome-Endabnahme.

## Nächster sinnvoller Schritt

**P0-012B/C – Browser-Smoke und sichtbare Matrix auf dem realen Kubuntu/KDE-/Chrome-System ausführen.**

Die reale Abnahme prüft zusätzlich Browser-Zoom 100/125/150/200 %, KDE-Fensterverhalten,
Kontrast, Fokus, Fehlersichtbarkeit und Offline-Verhalten.

## Release-Regel

`STABLE` erst nach grünem Persistenz-, Recovery-, Backup/Restore-, automatischem Browser-,
realem UI-/A11y- und Regression-Gate.
