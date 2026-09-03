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

Querschnittsfunktionen wie Logging, Validierung und Konfiguration dürfen
Fachmodule nicht duplizieren.

## Verzeichnisvertrag

```text
src/                 Basistool
src/persistence/     SQLite, Migrationen und generischer Datenspeicher
src/web/             Browseroberfläche
src/config/          eingebaute Defaults
config/              nutzeranpassbare, aber nicht private Beispielkonfiguration
data/                keine echten Nutzerdaten im Git
runtime/             Laufzeitzustand, ignoriert
logs/                Laufzeitlogs, ignoriert
backups/             Backups, ignoriert
docs/                vertiefende Dokumentation
tests/               automatisierte Tests
tools/               Entwicklungs-/Prüfwerkzeuge
.github/workflows/   CI und Release-Gates
```

## Persistenz

Der Datenkern ist in `docs/PERSISTENCE.md` spezifiziert.

Wichtige Regeln:

- Fachmodule greifen nicht direkt mit eigenem SQL auf die Datenbank zu.
- Schemaänderungen erfolgen ausschließlich über neue Migrationen.
- Bereits angewendete Migrationen werden nicht nachträglich verändert.
- Nutzerdaten bleiben außerhalb des versionierten Repository-Baums.
- schreibende Hochrisiko-Aktionen warten auf den vollständigen P0-010-Vertrag.

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

Produktive Mutationen müssen künftig den Vertrag erfüllen:

`PRECHECK → MUTATION → POSTCHECK → COMMIT oder ROLLBACK → EVIDENCE`

SQLite-Transaktionen allein gelten noch nicht als vollständiger Recovery-Vertrag.

## Tests

Mindestens:

- Syntax / Import
- Formatter / Linter
- Manifest- und Dateigrenzen
- Logging-Schema
- Persistenzschema und Migrationen
- Datenbankintegrität
- keine sensitiven Repo-Daten
- Smoke-Test
- Regressionen

## Technische Schuld

Warnungen werden dokumentiert und nicht still ignoriert.
Grenzwerte werden nicht erhöht, nur um einen Test grün zu machen.
