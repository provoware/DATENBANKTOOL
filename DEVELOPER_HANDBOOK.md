# Entwicklerhandbuch

## Architektur

```text
Browser/UI
   ↓
HTTP/API-Schicht
   ↓
Anwendungsdienste
   ↓
Daten-/Persistenzschicht
   ↓
Recovery / Logging / Storage
```

Querschnittsfunktionen wie Logging, Validierung und Konfiguration dürfen Fachmodule nicht duplizieren.

## Verzeichnisvertrag

```text
src/                 Basistool
src/web/             Browseroberfläche
src/config/          eingebaute Defaults
config/              nutzeranpassbare, aber nicht private Beispielkonfiguration
data/                keine echten Nutzerdaten im Git
runtime/             Laufzeitzustand, ignoriert
logs/                 Laufzeitlogs, ignoriert
backups/              Backups, ignoriert
docs/                 vertiefende Dokumentation
tests/                automatisierte Tests
tools/                Entwicklungs-/Prüfwerkzeuge
.github/workflows/    CI und Release-Gates
```

## Fehlervertrag

Jeder technische Fehler sollte mindestens liefern:

- stabilen Fehlercode
- Schweregrad
- Komponente
- kurze Ursache
- verständlichen nächsten Schritt
- technische Details im Maschinenlog
- Session-ID zur Zuordnung

## Datenänderungen

Spätere produktive Mutationen müssen den Vertrag erfüllen:

`PRECHECK → MUTATION → POSTCHECK → COMMIT oder ROLLBACK → EVIDENCE`

## Tests

Mindestens:

- Syntax / Import
- Formatter / Linter
- Manifest- und Dateigrenzen
- Logging-Schema
- keine sensitiven Repo-Daten
- Smoke-Test
- Regressionen

## Technische Schuld

Warnungen werden dokumentiert und nicht still ignoriert. Grenzwerte werden nicht erhöht, nur um einen Test grün zu machen.
