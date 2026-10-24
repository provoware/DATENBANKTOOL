# Release-Pflichtmatrix · DATENBANKTOOL

Stand: 2026-10-23. Status ist **evidenzbezogen**, keine geschätzte Gesamtprozentzahl.
Basis-HEAD: `main@0fa7749e9ee7591383b8004810b9d5da3cb9b5b1`.
Entwicklungszweig: `agent/dbtool-safe-status-compact-20261023`.
PR: https://github.com/provoware/DATENBANKTOOL/pull/23.
Die jeweils letzten Prüfungen auf dem aktuellen Branch-HEAD sind in GitHub/PR maßgeblich.

Legende: `VORHANDEN` = Quellcode oder Test vorhanden, nicht automatisch releasefertig;
`OFFEN` = noch zu implementieren/prüfen; `BLOCKED` = externe Voraussetzung.

| Pflichtbereich | Soll | Ist / nachprüfbarer Beleg | Status |
|---|---|---|---|
| Fachfunktionen und Grenzfälle | CRUD, Suche, Grenzfälle | `store.py`, `test_persistence.py`; Fach-GUI fehlt | OFFEN |
| Schnittstellen / Integration | Abgesicherte API | `src/server.py`; Fach-GUI fehlt | OFFEN |
| Datensicherheit / Wiederherstellung | Sichern, prüfen, rücktauschen | `test_backup.py`, `test_restore.py` | VORHANDEN |
| Fehlerbehandlung / Sicherheit | Keine HTML-Ausführung aus API-Text | `src/web/app.js`, Browser-Negativtest | PASS Browser |
| Design / UX / Lesbarkeit | Bedienbare Fachoberfläche | `src/web/styles.css`; Fach-GUI fehlt | OFFEN |
| Kleine Fenster / hohe Skalierung | 800×600 und hohe Vergrößerung | 800×600 + Zoom-Näherung geprüft | TEILWEISE |
| Tastatur / Barrierefreiheit | Fokus, Kontrast, Tastatur | `dashboard.spec.js`; Gesamtgate offen | OFFEN |
| Logrotation | ≤2.500 Zeilen/2 MiB je Segment | 6 Tests, CI + Browser grün | PASS PFLICHTPAKET |
| Leistung | Große Datenbestände ohne unzumutbare Verzögerung | `TODO.md` P2-004 | OFFEN |
| Wartbarkeit / Wiederverwendung | Klare Schichten, kein Doppelcode | `AGENTS.md`, `registry.json` | VORHANDEN |
| Paketierung / Installation | Reproduzierbarer Offline-Start | `README.md`; Pakete offen | OFFEN |
| Automatische Funktionstests | Prüfungen auf exaktem HEAD | `tests/test_*.py`, CI | PASS CI |
| Browser / GUI | Browser automatisiert und final real | 20 Playwright-Prüfungen; reale UI offen | TEILWEISE |
| Regression | Sicherheits- und Altfalltests erfolgreich | 41 Python-Tests + 20 Browserprüfungen | PASS CI |
| CI / Qualitätsgates | Alle Pflichtprüfungen grün | CI + Browser grün; Release Gate nur auf main | TEILWEISE |
| Dokumentation | Stand, Grenzen, offene Pflichten nachvollziehbar | `README.md`, `TODO.md`, diese Matrix | VORHANDEN |
| Release-Vorbereitung | Eingefrorener Kandidat, Endabnahme | Noch kein Kandidat | BLOCKED |

## Prüfnachweise (verifizierter Code-HEAD)

- `b7de81bc8a958da33ec03e5bcfbbeb01eb47c32c`:
  [CI](https://github.com/provoware/DATENBANKTOOL/actions/runs/39990541834) PASS,
  [Browser Smoke](https://github.com/provoware/DATENBANKTOOL/actions/runs/39990541764) PASS.
- CI: Ruff, Prettier, 41 Python-Tests und Projektprüfung erfolgreich.
- Browser: 20/20 Playwright-Prüfungen über fünf Viewports bestanden.
- Dokumentations-Nachtrag nach diesem geprüften HEAD erfordert **erneute CI**.
- Release Gate läuft nur auf `main` oder manuell, daher kein PR-Gate-PASS.

## Aktuelles Pflichtarbeitspaket

- **DB-SEC-001:** Serverstatus niemals als HTML einfügen; Browser-Negativtest mit
  eingeschleustem HTML aus dem simulierten Gesundheits-Endpunkt.
- **DB-UX-001:** Automatische Layout-/Tastaturprüfungen auf 800×600 und verkleinertem
  CSS-Viewport (400×300) ausweiten. Letzteres ist **kein** echter 200-%-Zoomtest.
- **Gates:** CI und Browser Smoke nach Dokumentations-Nachtrag erneut prüfen.
  Release Gate ist auf dem PR-Zweig nicht automatisch ausführbar.

## Sicherheitsnachtrag DB-SEC-002 · 2026-10-24

- **Befund reproduziert:** Die bisherige Schwärzung wandelte Listen in Text um.
  Dadurch konnten verschachtelte `Authorization`- und `cookie`-Werte im JSONL stehen.
- **Änderung:** `src/logging_core.py` schwärzt Schlüssel auch innerhalb von Listen;
  Zyklen und Tiefe werden begrenzt. `tests/test_logging.py` prüft beide Fälle.
- **Isolierter Vorabtest:** Ausgangscode 2 PASS / 2 FAIL, Korrektur 4 PASS.
  Dieser Vorabtest ist **kein** vollständiger Repository-Gate-Nachweis.
- **CI auf Code-HEAD `e4d67cfba35110235a34271802bcdbec29409127`:**
  [CI](https://github.com/provoware/DATENBANKTOOL/actions/runs/40060246127) PASS
  (Ruff, Prettier, 43 Python-Tests, Projektprüfung);
  [Browser Smoke](https://github.com/provoware/DATENBANKTOOL/actions/runs/40060246094) PASS.
- **Finaler Dokumentations-HEAD:** erneute CI und Browserprüfung nach diesem Nachtrag erforderlich.
- **Restpflicht:** Logrotation laut Manifest, Fachfunktionen, vollständige Browser-/
  Skalierungsprüfung, Leistung, Paketierung und gebündelte Endabnahme.

## Offene Abhängigkeiten und nächster Schritt

1. CI und Browser Smoke auf dem letzten Entwicklungs-HEAD erneut bestätigen.
2. Danach unabhängige Fachfunktionen und Import/Export sicher entwickeln und testen;
   P1/P2 nicht wegen fehlender persönlicher Abnahme pausieren.
3. Erst nach kompletter Vorrelease-Reife: **eine** gebündelte persönliche Endabnahme
   auf Kubuntu einschließlich sichtbarer Chrome-Prüfung; Veröffentlichung nur mit Freigabe.

Hinweis: Frühere Fortschrittsprozente in älteren Dateien sind **keine**
nachgewiesene Release-Abdeckung. Diese Matrix verwendet ausschließlich überprüfbare Zustände.

## DB-LOG-003 · JSONL-Grenzen (24.10.2026)

- **Soll:** höchstens 2.500 Zeilen und 2.097.152 UTF-8-Bytes pro JSONL-Segment,
  ohne stilles Überschreiben älterer Ereignisse; Manifestwerte sind die Referenz.
- **Ist:** `EventLogger` rotiert unter einer Schreibsperre in fortlaufend nummerierte
  Archivsegmente. Zu große Einzeleinträge werden ausdrücklich abgewiesen.
  Ein Neustart mit gleicher Sitzungs-ID übernimmt den vorhandenen Zähler.
- **Tests:** `tests/test_logging.py` prüft Manifestparität, Zeilen-/Byte-Grenze,
  gleichzeitige Schreiber, Übergröße und Neustart (sechs neue Regressionen).
- **Belegstatus:** PASS für DB-LOG-003 auf Code-/Doku-HEAD
  `c6a8a4bcdd2559f5eee80b4cb41f6ce4e21e790a`:
  [CI](https://github.com/provoware/DATENBANKTOOL/actions/runs/40104407086)
  (49 Python-Tests, Format, Projektprüfung) und
  [Browser](https://github.com/provoware/DATENBANKTOOL/actions/runs/40104407095)
  (20 Playwright-Tests) erfolgreich.
- **Statusnachtrag:** Auf dem neuen Dokumentations-HEAD sind die Gates erneut
  auszuführen; Gesamt-Vorrelease bleibt BLOCKED.
- **Scope:** Logging und Regressionen; Persistenz-, Backup- und Restore-Verträge
  unverändert. Vorrelease und persönliche Endabnahme weiterhin offen.
