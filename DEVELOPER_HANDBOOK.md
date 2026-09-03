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
src/recovery/        Mutationsvertrag, Zustandsmaschine und Recovery-Evidence
src/web/             Browseroberfläche
src/config/          eingebaute Defaults
config/              nutzeranpassbare, aber nicht private Beispielkonfiguration
data/                keine echten Nutzerdaten im Git
runtime/             Laufzeitzustand und Recovery-Journal, ignoriert
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

## Mutations- und Recovery-Vertrag

Der ausführbare Vertrag steht in `docs/TRANSAKTIONSVERTRAG.md`.

Produktive Mutationen folgen zentral:

`PRECHECK → MUTATION → POSTCHECK → COMMIT oder ROLLBACK → EVIDENCE`

Pflichtregeln:

- jede Mutation erhält eine Operation-ID
- kritische Mutationen laufen über den zentralen Single-Writer-Gate
- UI/API übergibt bei wiederholbaren Benutzerimpulsen einen Idempotenzschlüssel
- POSTCHECK erfolgt vor dem Commit in derselben SQLite-Transaktion
- Fehler vor dem Commit führen zu Rollback
- Zustandsübergänge werden außerhalb der Business-Transaktion im Recovery-Journal gespeichert
- finale Evidence wird atomar geschrieben
- sensible Evidence-Felder werden geschwärzt
- `COMMITTING` gilt nach Crash als prüfpflichtig und darf nicht automatisch wiederholt werden
- unvollständige Operationen blockieren den normalen Programmstart

Neue produktive Schreibfunktionen dürfen keinen privaten Commit-/Rollback-Vertrag
erfinden. Sie verwenden `MutationCoordinator` oder einen zentral geprüften Adapter.

## Fehlervertrag

Jeder technische Fehler sollte mindestens liefern:

- stabilen Fehlercode
- Schweregrad
- Komponente
- kurze Ursache
- verständlichen nächsten Schritt
- technische Details im Maschinenlog
- Session-ID oder Operation-ID zur Zuordnung

## Tests

Mindestens:

- Syntax / Import
- Formatter / Linter
- Manifest- und Dateigrenzen
- Logging-Schema
- Persistenzschema und Migrationen
- Datenbankintegrität
- Mutation Commit/Rollback
- Single-Writer-Gate und Idempotenz
- Recovery-Evidence und Start-Gate
- keine sensitiven Repo-Daten
- Smoke-Test
- Regressionen

## Technische Schuld

Warnungen werden dokumentiert und nicht still ignoriert.
Grenzwerte werden nicht erhöht, nur um einen Test grün zu machen.
