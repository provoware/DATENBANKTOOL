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
Recovery / Backup / Logging / Storage
```

Querschnittsfunktionen wie Logging, Validierung und Konfiguration dürfen
Fachmodule nicht duplizieren.

## Verzeichnisvertrag

```text
src/                 Basistool
src/persistence/     SQLite, Migrationen und generischer Datenspeicher
src/recovery/        Mutationsvertrag, Zustandsmaschine und Recovery-Evidence
src/backup/          Snapshot, Backup-Manifest und Verifikations-Gate
src/web/             Browseroberfläche
src/config/          eingebaute Defaults
config/              nutzeranpassbare, aber nicht private Beispielkonfiguration
data/                keine echten Nutzerdaten im Git
runtime/             Laufzeitzustand und Recovery-Journal, ignoriert
logs/                Laufzeitlogs, ignoriert
backups/             lokale Backup-Artefakte, ignoriert
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

## Backup-Vertrag

Der ausführbare Vertrag steht in `docs/BACKUP_VERTRAG.md`.

P0-011A verwendet die SQLite-Backup-API für konsistente Snapshots. Eine einfache
Dateikopie der produktiven SQLite-Datei ist als Backup-Verfahren nicht zulässig.

Pflichtregeln:

- Quelldatenbank muss Schema- und Integritätsprüfung bestehen.
- Snapshot entsteht ausschließlich in `.incomplete_<backup-id>`.
- Backup-ID beginnt mit `bkp-`.
- Manifest v1 enthält Hash, Größe, Schema, UTC-Zeit und Integritätsdaten.
- SHA-256, Größe, Schema, `quick_check` und Fremdschlüssel werden unabhängig nachgemessen.
- nur erfolgreich verifiziertes Staging wird atomar als `backup_status_verified_*` veröffentlicht.
- `.incomplete_*` darf niemals als gültiges Backup gelistet oder als Restore-Quelle akzeptiert werden.
- beschädigte oder manipulierte Backups werden von `list_verified_backups()` ausgeschlossen.
- Restore bleibt bis P0-011B deaktiviert.

Neue Backup-Funktionen verwenden `BackupManager`. Fachmodule dürfen keine eigene
SQLite-Dateikopie oder eigene Manifestlogik implementieren.

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
- Backup unter WAL-Betrieb
- Backup-Hash, Dateigröße und Manifest
- manipulierte Backup-Datei und manipuliertes Manifest
- unvollständiges Staging wird nicht veröffentlicht
- keine sensitiven Repo-Daten
- Smoke-Test
- Regressionen

## Technische Schuld

Warnungen werden dokumentiert und nicht still ignoriert.
Grenzwerte werden nicht erhöht, nur um einen Test grün zu machen.
