# P0-011A · Abnahmekriterien

P0-011A gilt nur dann als abgeschlossen, wenn:

- der SQLite-Snapshot über die SQLite-Backup-API erzeugt wird,
- WAL-Quelldaten im Snapshot enthalten sind,
- Backup-ID, SHA-256, Dateigröße, Schema-Version und UTC-Zeit im Manifest stehen,
- `quick_check` und `foreign_key_check` grün sind,
- ein zweites Verifikations-Gate die Messwerte unabhängig bestätigt,
- `.incomplete_*` niemals als gültiges Backup akzeptiert wird,
- die Veröffentlichung erst nach Verifikation atomar erfolgt,
- manipulierte Snapshot-/Manifestdaten regressiv abgewiesen werden,
- Restore weiterhin deaktiviert bleibt,
- Branch-, PR- und `main`-Gates vollständig grün sind.
