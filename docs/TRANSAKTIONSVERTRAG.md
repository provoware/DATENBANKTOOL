# Transaktions- und Recovery-Vertrag · P0-010

## Ziel

Jede produktive Datenänderung folgt demselben zentralen Ablauf:

`PRECHECK → MUTATION → POSTCHECK → COMMIT oder ROLLBACK → EVIDENCE`

Damit gelten Validierung, Sperrung, Rollback und Nachweis nicht mehr nur als
Entwicklerkonvention, sondern als ausführbarer Vertrag.

## Zustandsmaschine

```text
RECEIVED
   ↓
PRECHECK
   ↓
MUTATION
   ↓
POSTCHECK
   ↓
COMMITTING
   ↓
COMMITTED
```

Fehler vor erfolgreichem Commit laufen über:

```text
ROLLING_BACK → ROLLED_BACK
```

Nicht gestartete Änderungen können als `REJECTED` enden. Technisch nicht sauber
abschließbare Zustände werden als `FAILED` behandelt.

## Operation-ID

Jede Mutation erhält eine eindeutige Kennung:

`op-<uuid>`

Diese ID verbindet Journal, Abschluss-Evidence und spätere Diagnose.

## Schutz gegen Parallel- und Doppelklick-Mutationen

### Single-Writer-Gate

Pro Datenbankpfad darf innerhalb des Prozesses nur eine kritische Mutation
zur selben Zeit laufen. Ein paralleler Versuch wird nicht wartend versteckt,
sondern mit `MutationBusyError` und eigener Evidence abgewiesen.

### Idempotenzschlüssel

UI/API kann für einen Benutzerimpuls einen stabilen `operation_key` mitsenden.
Im Journal wird davon nur SHA-256 gespeichert. Wurde derselbe Schlüssel bereits
erfolgreich committed, wird ein Wiederholungsversuch als `REJECTED` beendet.

Damit kann ein Doppelklick oder erneutes HTTP-Senden denselben Fachvorgang nicht
unbemerkt zweimal erzeugen.

## Recovery-Evidence

Evidence liegt bewusst außerhalb der Geschäftsdatenbank unter:

```text
runtime/recovery/
├── recovery_journal_status_laufend.jsonl
└── evidence/
    └── recovery_evidence_status_<zustand>_<operation-id>.json
```

Das JSONL-Journal schreibt jeden Zustandsübergang sofort und führt `fsync` aus.
Die finale Evidence wird erst in eine temporäre Datei geschrieben und anschließend
atomar umbenannt.

## Warum Evidence nicht in derselben SQLite-Transaktion liegt

Ein Rollback darf nicht gleichzeitig den Beweis des Fehlers löschen. Deshalb
bleiben Business-Transaktion und Recovery-Evidence getrennt.

## Crash-Grenze `COMMITTING`

Zwischen erfolgreichem SQLite-Commit und finaler Evidence besteht technisch ein
kleines nicht vollständig atomarisierbares Fenster. Deshalb wird vor dem Commit
`COMMITTING` geschrieben.

Findet der nächste Start einen Vorgang, dessen letzter Zustand nicht final ist,
stoppt das Tool sicher und meldet die Recovery-Prüfung. Besonders `COMMITTING`
darf niemals automatisch wiederholt werden, weil die Business-Daten bereits
committed sein könnten.

## PRECHECK

Der PRECHECK prüft vor der Änderung alle Voraussetzungen, die innerhalb derselben
Datenbanktransaktion sicher entscheidbar sind, z. B.:

- Ziel existiert oder darf neu angelegt werden
- Eltern-/Referenzobjekt existiert
- Status erlaubt die gewünschte Mutation
- erwartete Version stimmt
- Fachvalidierung ist erfüllt

## POSTCHECK

Der POSTCHECK läuft vor dem Commit in derselben SQLite-Transaktion und beweist
mindestens die kritischen Nachbedingungen. Schlägt er fehl, wird zurückgerollt.

## Evidence-Datenschutz

Recovery-Evidence darf keine vollständigen Nutzdaten duplizieren. Gespeichert
werden technische Metadaten wie Objekt-ID, Art, Größen oder boolesche Zustände.
Sensible Schlüssel wie Token, Passwort oder API-Key werden wie im Maschinenlog
mit `[GESCHWÄRZT]` ersetzt.

## Bereits angebunden

`EntryStore.create()` läuft seit P0-010 vollständig über den zentralen
`MutationCoordinator`.

## Bewusst noch nicht freigegeben

Bis P0-011 und den darauf aufbauenden Fachverträgen bleiben folgende Funktionen
bewusst nicht als produktive Mutationen implementiert:

- Direktlöschen
- Massenänderungen
- Import mit Überschreiben
- Restore
- automatische Konfliktauflösung

## Start-Gate

Beim Programmstart wird das Recovery-Journal geprüft. Gibt es eine unvollständige
Operation, wird der normale Start blockiert und ein kritischer Logeintrag erzeugt.

Status kann zusätzlich gelesen werden über:

`GET /api/recovery/status`

## Pflichtregel für neue Schreibfunktionen

Neue Fachmodule dürfen `connection.execute(...)` für produktive Änderungen nicht
eigenständig mit einem privaten Commit-/Rollback-Vertrag kapseln. Kritische
Mutationen müssen über `MutationCoordinator.execute()` laufen oder einen fachlich
gleichwertigen, zentral geprüften Adapter verwenden.
