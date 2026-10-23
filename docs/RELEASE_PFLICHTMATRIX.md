# Release-Pflichtmatrix · DATENBANKTOOL

Stand: 2026-10-23. Status ist **evidenzbezogen**, keine geschätzte Gesamtprozentzahl.
Basis-HEAD: `main@0fa7749e9ee7591383b8004810b9d5da3cb9b5b1`.
Entwicklungszweig: `agent/dbtool-safe-status-compact-20261023`.
Der jeweils aktuelle Branch-HEAD und die CI-Ergebnisse sind in GitHub/PR maßgeblich.

Legende: `VORHANDEN` = Quellcode oder Test vorhanden, nicht automatisch releasefertig;
`OFFEN` = noch zu implementieren/prüfen; `BLOCKED` = externe Voraussetzung.

| Pflichtbereich | Soll | Ist / nachprüfbarer Beleg | Status |
|---|---|---|---|
| Fachfunktionen und Grenzfälle | Einträge anlegen, finden, bearbeiten; Fehlerfälle | `src/persistence/store.py`, `tests/test_persistence.py`; GUI nur Grundgerüst | OFFEN |
| Schnittstellen / Integration | Einheitliche, abgesicherte API | `src/server.py`, `tests/test_server_cli.py`; GUI-Funktionen fehlen | OFFEN |
| Datensicherheit / Wiederherstellung | Sicherung, Integrität, Rücktausch | `tests/test_backup.py`, `tests/test_restore.py`; neuer HEAD erneut zu prüfen | VORHANDEN |
| Fehlerbehandlung / Sicherheit | Verständliche Fehler, keine HTML-Ausführung aus API-Text | `src/web/app.js`, neuer Test in `tests/browser/dashboard.spec.js` | HEAD-GATE OFFEN |
| Design / UX / Lesbarkeit | Vollständig bedienbare Oberfläche | `src/web/styles.css`, `docs/BROWSER_ABNAHME.md`; Fach-UI fehlt | OFFEN |
| Kleine Fenster / hohe Skalierung | Ab 800×600; bei hoher Vergrößerung bedienbar | `playwright.config.js`: 800×600 + 400×300 als Annäherung; echte Zoomprüfung offen | HEAD-GATE OFFEN |
| Tastatur / Barrierefreiheit | Fokus, Kontrast, vollständige Tastaturbedienung | `tests/browser/dashboard.spec.js` (Hilfe, Skip-Link); Gesamtprüfung offen | OFFEN |
| Leistung | Große Datenbestände ohne unzumutbare Verzögerung | `TODO.md` P2-004 | OFFEN |
| Wartbarkeit / Wiederverwendung | Klare Schichten, keine doppelten Verträge | `AGENTS.md`, `src/config/registry.json`, `tools/check_project.py` | VORHANDEN |
| Paketierung / Installation | Reproduzierbarer Offline-Start, Zielplattformen | `README.md` enthält lokalen Python-Start; Paketprüfung offen | OFFEN |
| Automatische Funktionstests | Reale Testausführung auf exaktem HEAD | `tests/test_*.py`, `.github/workflows/ci.yml` | HEAD-GATE OFFEN |
| Browser / GUI | Chromium automatisiert, Kubuntu/Chrome final | `tests/browser/`, `.github/workflows/browser-smoke.yml` | HEAD-GATE OFFEN |
| Regression | Sicherheits- und Altfalltests erfolgreich | `REGRESSIONSPOOL.md`, `tests/` | HEAD-GATE OFFEN |
| CI / Qualitätsgates | Alle vorgeschriebenen Prüfungen grün | `.github/workflows/ci.yml`, `release-gate.yml`, `browser-smoke.yml` | HEAD-GATE OFFEN |
| Dokumentation | Stand, Grenzen, offene Pflichten nachvollziehbar | `README.md`, `TODO.md`, diese Matrix | VORHANDEN |
| Release-Vorbereitung | Eingefrorener Kandidat, danach einmalige Nutzer-Endabnahme | Noch kein vollständiger Release-Kandidat | BLOCKED |

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
