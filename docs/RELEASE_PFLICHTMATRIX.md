# Release-Pflichtmatrix · DATENBANKTOOL

Stand: 2026-10-23. Status ist **evidenzbezogen**, keine geschätzte Gesamtprozentzahl.
Basis-HEAD: `main@0fa7749e9ee7591383b8004810b9d5da3cb9b5b1`.
Entwicklungszweig: `agent/dbtool-safe-status-compact-20261023`.
Der jeweils aktuelle Branch-HEAD und die CI-Ergebnisse sind in GitHub/PR maßgeblich.

Legende: `VORHANDEN` = Quellcode oder Test vorhanden, nicht automatisch releasefertig;
`OFFEN` = noch zu implementieren/prüfen; `BLOCKED` = externe Voraussetzung.

| Pflichtbereich | Soll | Ist / nachprüfbarer Beleg | Status |
|---|---|---|---|
| Fachfunktionen und Grenzfälle | CRUD, Suche, Grenzfälle | `store.py`, `test_persistence.py`; Fach-GUI fehlt | OFFEN |
| Schnittstellen / Integration | Abgesicherte API | `src/server.py`; Fach-GUI fehlt | OFFEN |
| Datensicherheit / Wiederherstellung | Sichern, prüfen, rücktauschen | `test_backup.py`, `test_restore.py` | VORHANDEN |
| Fehlerbehandlung / Sicherheit | Keine HTML-Ausführung aus API-Text | `src/web/app.js`, Browser-Negativtest | HEAD-GATE OFFEN |
| Design / UX / Lesbarkeit | Bedienbare Fachoberfläche | `src/web/styles.css`; Fach-GUI fehlt | OFFEN |
| Kleine Fenster / hohe Skalierung | 800×600 und hohe Vergrößerung | `playwright.config.js`; echter Zoom offen | HEAD-GATE OFFEN |
| Tastatur / Barrierefreiheit | Fokus, Kontrast, Tastatur | `dashboard.spec.js`; Gesamtgate offen | OFFEN |
| Leistung | Große Datenbestände ohne unzumutbare Verzögerung | `TODO.md` P2-004 | OFFEN |
| Wartbarkeit / Wiederverwendung | Klare Schichten, kein Doppelcode | `AGENTS.md`, `registry.json` | VORHANDEN |
| Paketierung / Installation | Reproduzierbarer Offline-Start | `README.md`; Pakete offen | OFFEN |
| Automatische Funktionstests | Prüfungen auf exaktem HEAD | `tests/test_*.py`, CI | HEAD-GATE OFFEN |
| Browser / GUI | Browser automatisiert und final real | `tests/browser/`, Browser Smoke | HEAD-GATE OFFEN |
| Regression | Sicherheits- und Altfalltests erfolgreich | `REGRESSIONSPOOL.md`, `tests/` | HEAD-GATE OFFEN |
| CI / Qualitätsgates | Alle Pflichtprüfungen grün | CI, Browser Smoke, Release Gate | HEAD-GATE OFFEN |
| Dokumentation | Stand, Grenzen, offene Pflichten nachvollziehbar | `README.md`, `TODO.md`, diese Matrix | VORHANDEN |
| Release-Vorbereitung | Eingefrorener Kandidat, Endabnahme | Noch kein Kandidat | BLOCKED |

## Aktuelles Pflichtarbeitspaket

- **DB-SEC-001:** Serverstatus niemals als HTML einfügen; Browser-Negativtest mit
  eingeschleustem HTML aus dem simulierten Gesundheits-Endpunkt.
- **DB-UX-001:** Automatische Layout-/Tastaturprüfungen auf 800×600 und verkleinertem
  CSS-Viewport (400×300) ausweiten. Letzteres ist **kein** echter 200-%-Zoomtest.
- **Gates:** CI, Browser Smoke und Release Gate auf dem PR-HEAD abwarten und
  Fehlprüfungen korrigieren. Kein PASS vor Abschluss.

## Offene Abhängigkeiten und nächster Schritt

1. Pflichtprüfungen auf dem exakten Entwicklungs-HEAD erfolgreich abschließen.
2. Danach unabhängige Fachfunktionen und Import/Export sicher entwickeln und testen;
   P1/P2 nicht wegen fehlender persönlicher Abnahme pausieren.
3. Erst nach kompletter Vorrelease-Reife: **eine** gebündelte persönliche Endabnahme
   auf Kubuntu einschließlich sichtbarer Chrome-Prüfung; Veröffentlichung nur mit Freigabe.

Hinweis: Frühere Fortschrittsprozente in älteren Dateien sind **keine**
nachgewiesene Release-Abdeckung. Diese Matrix verwendet ausschließlich überprüfbare Zustände.
