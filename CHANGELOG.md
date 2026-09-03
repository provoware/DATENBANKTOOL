# CHANGELOG

Alle wichtigen Projektänderungen werden hier in deutscher Sprache dokumentiert.

## [0.5.0-alpha.1] – 2026-09-03

### Hinzugefügt

- 🟢 `RestoreManager` mit eigenständigem Staging-Restore-Vertrag.
- 🟢 unmittelbare erneute Backup-Verifikation vor jedem Restore.
- 🟢 SHA-256-, Schema-, `quick_check`- und Fremdschlüsselprüfung im Staging.
- 🟢 verifizierter Rollback-Snapshot des bisherigen Produktivstands.
- 🟢 gemeinsamer kritischer Datenbank-Gate für Mutation und Restore.
- 🟢 exklusives Datenbankzugriffsfenster während des Swap-Bereichs.
- 🟢 atomarer Datenbanktausch per `os.replace()` erst nach grünem Staging-Gate.
- 🟢 produktiver POSTCHECK als Pflicht vor `COMMITTED`.
- 🟢 automatischer Rücktausch bei kontrolliertem Fehler nach `SWAPPED`.
- 🟢 rekonstruierbarer Crash-Zustand `SWAPPING` mit Restore-Hash,
  vorherigem Hash und Rollback-Pfad.
- 🟢 `GET /api/restore/status` und bestätigungspflichtiger
  `POST /api/restore/execute`.
- 🟢 Regressionstests für Staging, Manipulation, Pre-Swap-Abbruch,
  POSTCHECK-Rollback und Crash an der Swap-Grenze.
- 🟢 Entwicklerdokument `docs/RESTORE_VERTRAG.md`.

### Geändert

- 🟣 Projektstatus auf `RESTOREKERN / AUFBAU` und Fortschritt auf 70 % gesetzt.
- 🟣 `P0-011` Backup/Restore vollständig abgeschlossen.
- 🟣 `P0-012` reale Browser-Endabnahme ist der nächste P0-Schritt.

### Sicherheitsgrenze

- 🟡 Ein Restore gilt erst nach grünem produktivem POSTCHECK und finaler Evidence
  als `COMMITTED`.
- 🟡 Ein unvollständiger Restore im Zustand `SWAPPING` blockiert den normalen Start
  und muss anhand der gespeicherten Hashes rekonstruiert werden.

## [0.4.0-alpha.1] – 2026-09-03

### Hinzugefügt

- 🟢 `BackupManager` für konsistente SQLite-Snapshots über die SQLite-Backup-API.
- 🟢 Backup-Manifest v1 mit Backup-ID, SHA-256, Dateigröße, Schema-Version und UTC-Zeit.
- 🟢 `quick_check` und `foreign_key_check` für jeden Snapshot.
- 🟢 unabhängiges Verifikations-Gate vor Veröffentlichung eines Backups.
- 🟢 `.incomplete_*`-Staging für noch nicht gültige Sicherungen.
- 🟢 atomare Veröffentlichung als `backup_status_verified_*` erst nach erfolgreicher Prüfung.
- 🟢 Regressionstests für WAL-Quelle, manipulierte Datenbank, manipuliertes Manifest und Abbruch.
- 🟢 Entwicklerdokument `docs/BACKUP_VERTRAG.md`.

### Geändert

- 🟣 Projektstatus auf `BACKUPKERN / AUFBAU` und Fortschritt auf 60 % gesetzt.
- 🟣 `P0-011A` abgeschlossen; `P0-011B` Staging-Restore ist der nächste P0-Schritt.

### Sicherheitsgrenze

- 🟡 Restore bleibt deaktiviert. Kein verifiziertes Backup darf die produktive Datenbank ersetzen,
  bevor P0-011B Staging-Restore, Integritätsprüfung, atomaren Austausch und Evidence vollständig prüft.

## [0.3.0-alpha.1] – 2026-09-03

### Hinzugefügt

- 🟢 zentraler `MutationCoordinator` für produktive Datenänderungen.
- 🟢 Zustandsmaschine `PRECHECK → MUTATION → POSTCHECK → COMMIT/ROLLBACK → EVIDENCE`.
- 🟢 eindeutige Operation-ID für jede Mutation.
- 🟢 Single-Writer-Gate gegen parallele kritische Mutationen.
- 🟢 Idempotenzschlüssel gegen Doppel-Submit und Doppelklick-Mutationen.
- 🟢 maschinenlesbares JSONL-Recovery-Journal außerhalb der Business-Transaktion.
- 🟢 atomare finale Recovery-Evidence mit Status im Dateinamen.
- 🟢 Start-Gate für unvollständige Operationen aus vorherigen Sitzungen.
- 🟢 `/api/recovery/status` für lesbaren Recovery-Zustand.
- 🟢 Regressionstests für Commit, Rollback, Gate, Idempotenz und Evidence.
- 🟢 Entwicklerdokument `docs/TRANSAKTIONSVERTRAG.md`.

### Geändert

- 🟣 `EntryStore.create()` läuft jetzt über den zentralen Mutationsvertrag.
- 🟣 Projektstatus auf `TRANSAKTIONSKERN / AUFBAU` und Fortschritt auf 50 % gesetzt.
- 🟣 `P0-010` abgeschlossen; `P0-011` Backup/Restore ist jetzt der nächste P0-Schritt.

### Sicherheitsgrenze

- 🟡 Direktlöschen, Massenänderungen, überschreibender Import und Restore bleiben bewusst gesperrt,
  bis die jeweiligen Fachverträge und P0-011 abgeschlossen sind.

## [0.2.0-alpha.1] – 2026-09-03

### Hinzugefügt

- 🟢 SQLite-Persistenzkern mit lokalem Standardpfad `data/user/provoware.sqlite3`.
- 🟢 Schema-Version `1` für Einträge, Hierarchie, Tags und App-Einstellungen.
- 🟢 vorwärts gerichtete Migrationen mit SHA-256-Prüfsummen.
- 🟢 Schema-Metadaten über `schema_migrations` und `PRAGMA user_version`.
- 🟢 WAL, Fremdschlüssel, Busy-Timeout und Integritätsprüfung.
- 🟢 generischer `EntryStore` als Basis für Archiv-, Memo- und Dashboardmodule.
- 🟢 `/api/storage/status` und erweiterter `/api/health`-Status.
- 🟢 automatische Persistenztests für Migration, Idempotenz, Hierarchie und Integrität.
- 🟢 Entwicklerdokument `docs/PERSISTENCE.md`.

### Geändert

- 🟣 Projektstatus von `BASIS / AUFBAU` auf `DATENKERN / AUFBAU`.
- 🟣 Entwicklungsfortschritt von 30 % auf 40 %.
- 🟣 `P0-009` abgeschlossen; `P0-010` ist jetzt der nächste releasekritische Schritt.

### Bewusst noch offen

- 🟡 vollständiger PRE-/POST-/Rollback-Vertrag für Mutationen.
- 🟡 Recovery-Journal und Wiederaufnahme nach Prozessabbruch.
- 🟡 Backup-/Restore-Vertrag.

## [0.1.0-foundation] – 2026-09-03

### Hinzugefügt

- 🟢 Clean-Foundation-Rebuild des Repository-Baums.
- 🟢 Sicherheits-Branch `backup/pre-clean-rebuild-20260903` für den alten Stand.
- 🟢 klare Trennung von Basistool, Konfiguration, Nutzerdaten und Laufzeitdaten.
- 🟢 zentrale Projektdokumentation für Laien und Entwickler.
- 🟢 `MANIFEST.json` mit Datei- und Zeilenlimits.
- 🟢 GitHub-Actions-Workflows für CI und Release-Gate.
- 🟢 automatische Format- und Projektprüfungen.
- 🟢 JSONL-Maschinenlogging und deutsche TXT-Kurzberichte als Basis.
- 🟢 sensible-Feld-Schwärzung in Logs.
- 🟢 dunkle kontrastreiche Basisoberfläche mit Ampeln, Tooltips und Fortschrittsanzeige.

### Entfernt

- 🔴 alter Projektbaum aus `main`.
- 🔴 alte Laufzeit-/Nutzerdatenstrukturen aus dem versionierten Bestand.

### Hinweis

Die Git-Historie wurde nicht gelöscht. Der Rebuild ist daher nachvollziehbar und rücksetzbar.
