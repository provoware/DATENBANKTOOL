# Backup-Vertrag · P0-011A

## Ziel

P0-011A erzeugt verifizierte SQLite-Sicherungen, ohne Restore bereits freizugeben.
Ein Backup gilt erst dann als gültig, wenn Snapshot, Manifest und unabhängige
Verifikation erfolgreich abgeschlossen wurden.

## Ablauf

`SOURCE CHECK → SQLITE SNAPSHOT → INTEGRITY → HASH/METADATA → MANIFEST → VERIFY → ATOMIC PUBLISH`

## Gültigkeitsregel

Während der Erstellung liegt das Backup ausschließlich in einem Ordner mit Präfix:

`.incomplete_<backup-id>`

Dieser Ordner gilt niemals als gültiges Backup und wird von der öffentlichen
Backup-Auflistung ignoriert. Erst nach erfolgreicher Verifikation wird der komplette
Ordner atomar veröffentlicht als:

`backup_status_verified_<UTC-Zeit>_<backup-id>`

## SQLite/WAL

Der Snapshot wird über die SQLite-Backup-API erzeugt. Dadurch wird ein konsistentes
Abbild der Datenbank erstellt, auch wenn die Quelldatenbank im WAL-Modus arbeitet.
Die produktive Datenbankdatei wird nicht mit einer einfachen Dateikopie gesichert.

## Backup-Manifest v1

Pflichtfelder:

- `manifest_version`
- `backup_id`
- `status`
- `created_at_utc`
- `database_file`
- `sha256`
- `size_bytes`
- `schema_version`
- `integrity_ok`
- `quick_check`
- `foreign_key_violations`

`status` muss für ein gültiges Backup exakt `verified` sein.

## Unabhängiges Verifikations-Gate

`BackupManager.verify_backup()` misst erneut:

- SHA-256 der Snapshot-Datei
- Dateigröße
- SQLite-Schema-Version
- `PRAGMA quick_check`
- `PRAGMA foreign_key_check`

Nur wenn Manifest und reale Messwerte übereinstimmen, wird das Backup akzeptiert.
Manipulierte oder beschädigte Backups werden nicht in `list_verified_backups()`
aufgenommen.

## Abbruchregel

Scheitert ein Lauf vor der atomaren Veröffentlichung, bleibt der Staging-Ordner
`.incomplete_...` bestehen und erhält nach Möglichkeit:

`STATUS_UNVOLLSTAENDIG.txt`

Ein solcher Bestand darf nicht als Restore-Quelle dienen.

## Sicherheitsgrenze

Restore ist in P0-011A ausdrücklich nicht freigegeben.

P0-011B muss zuerst einen Staging-Restore implementieren:

`BACKUP VERIFY → RESTORE STAGING → HASH/SCHEMA/INTEGRITY → ATOMIC SWAP → POSTCHECK → EVIDENCE`

Erst nach grünen Regressionstests darf die produktive Datenbank ersetzt werden.
