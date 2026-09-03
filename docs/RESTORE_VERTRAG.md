# P0-011B · Restore-Vertrag v1

## Zweck

Ein Restore darf die produktive SQLite-Datenbank erst verändern, nachdem das gewählte Backup und eine separate Staging-Datenbank vollständig geprüft wurden.

## Verbindliche Kette

`BACKUP VERIFY → RESTORE STAGING → STAGING VERIFY → ROLLBACK SNAPSHOT → SWAP PREPARED → SWAPPING → SWAPPED → POSTCHECK → COMMITTED oder ROLLED_BACK → EVIDENCE`

## Vor dem Swap

1. Das veröffentlichte Backup wird unmittelbar erneut über den Backup-Vertrag v1 verifiziert.
2. Die Backup-Datenbank wird ausschließlich nach `runtime/recovery/restore_staging/` kopiert.
3. Die Staging-Datei muss denselben SHA-256 wie das verifizierte Backup besitzen.
4. Schema-Version, `PRAGMA quick_check` und `PRAGMA foreign_key_check` müssen grün sein.
5. Die produktive Datenbank wird während dieser Prüfungen nicht ersetzt oder umgeschaltet.
6. Vor dem Austausch wird ein verifizierter SQLite-Rollback-Snapshot des bisherigen Produktivstands erzeugt.
7. Ein gemeinsamer Datenbank-Gate blockiert parallele kritische Mutationen; ein exklusives Datenbankzugriffsfenster verhindert gleichzeitig neue prozessinterne Verbindungen während des Swap-Fensters.
8. Existieren aktive SQLite-Seitendateien (`-wal`, `-shm`, `-journal`), wird der Restore vor dem Swap abgebrochen.
9. Unmittelbar vor dem Swap wird die Staging-Datei nochmals geprüft.

## Atomarer Austausch

Erst nach allen grünen Vorprüfungen wird `SWAP_PREPARED` protokolliert. Danach wird `SWAPPING` protokolliert und die Staging-Datei mit `os.replace()` atomar an die Stelle der produktiven Datenbank gesetzt. Anschließend wird das Zielverzeichnis mit `fsync` dauerhaft synchronisiert.

## POSTCHECK

Nach dem Swap muss die produktive Datei erneut bestehen:

- erwarteter SHA-256,
- aktuelle Schema-Version,
- `quick_check = ok`,
- keine Fremdschlüsselverletzungen.

Erst danach darf `COMMITTED` als finale Evidence geschrieben werden.

## Rollback

Schlägt ein kontrollierter Schritt nach `SWAPPED` fehl, wird der vorher erzeugte Rollback-Snapshot atomar zurückgetauscht. Danach werden dessen Hash, Schema und Integrität erneut geprüft. Nur bei bestätigtem alten Produktivstand endet der Vorgang als `ROLLED_BACK`.

## Crash-Grenze

Der kritischste Zeitpunkt liegt zwischen `os.replace()` und dem Journalzustand `SWAPPED`. Vor `os.replace()` wurde bereits `SWAPPING` mit folgenden Rekonstruktionsdaten protokolliert:

- Restore-Operation-ID,
- Backup-ID,
- erwarteter Restore-SHA-256,
- SHA-256 des vorherigen Produktivstands,
- Pfad zum Rollback-Snapshot.

Stirbt der Prozess exakt an dieser Grenze, bleibt `SWAPPING` als unvollständige Operation im Recovery-Journal. Der normale Programmstart wird dadurch blockiert. Der Zustand darf nicht automatisch als Erfolg oder Fehler interpretiert werden; Produktivdatei und Rollback-Snapshot müssen anhand der gespeicherten Hashes eindeutig zugeordnet werden.

## API-Schutz

`POST /api/restore/execute` akzeptiert ausschließlich den exakten Namen eines aktuell verifizierten Backup-Ordners. Freie Dateipfade werden nicht akzeptiert. Zusätzlich ist die exakte Bestätigung `DATENBANK WIEDERHERSTELLEN` erforderlich.

`GET /api/restore/status` zeigt unvollständige Restore-Operationen und die erforderliche Bestätigung an.

## Sicherheitsregel

Ein Restore ist niemals `COMMITTED`, nur weil `os.replace()` erfolgreich war. `COMMITTED` ist ausschließlich nach grünem produktivem POSTCHECK und geschriebener finaler Evidence zulässig.
