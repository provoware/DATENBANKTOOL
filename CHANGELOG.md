# CHANGELOG

Alle wichtigen Projektänderungen werden hier in deutscher Sprache dokumentiert.

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
