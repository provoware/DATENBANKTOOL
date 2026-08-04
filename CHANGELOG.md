# Changelog

## 0.2.0-alpha.1 – 2026-08-04

### Hinzugefügt

- SQLite-Index mit Schema-Version 2.
- Migrationstabelle und automatische V1→V2-Migration.
- Transaktionaler Batch-Import.
- Persistente Scan- und Hashing-Checkpoints.
- Wiederaufnahme unterbrochener oder fehlgeschlagener Sitzungen.
- Reparaturmodus mit konsistenter SQLite-Sicherheitskopie.
- Integritäts-, Fremdschlüssel-, Index- und Statistikprüfung.
- Reproduzierbarer Neuaufbau exakter Duplikatgruppen.
- CSV-Berichte in UTF-8 mit BOM.
- Eigenständige HTML-Berichte mit interaktiver lokaler Filterung.
- Berichtfilter nach Dateikategorie, Größe, Namensproblem und Duplikatstatus.
- CLI-Kommandos `index build`, `index status`, `index repair` und `report`.
- 10 neue Index-, Berichts- und CLI-Tests.
- GitHub-Actions-Prüfung unter Python 3.10 und 3.12.

### Geändert

- Scanner läuft deterministisch sortiert.
- SHA-256-Dateifunktion ist für Index und Direkt-Scan gemeinsam nutzbar.
- Versionsstand auf `0.2.0-alpha.1` angehoben.
- Dokumentation und Projektregister vollständig aktualisiert.

### Validiert

- 14/14 automatisierte Tests erfolgreich.
- Kompilierung mit `compileall` erfolgreich.
- Tests mit `PYTHONWARNINGS=error` ohne Warnungen.
- End-to-End-Probelauf einschließlich Reparatursicherung erfolgreich.

### Unverändert

- `AGENTS.md` wurde nicht verändert.
- Schreibende Operationen an Nutzerdaten bleiben gesperrt.

## 0.1.0-alpha.1 – 2026-08-04

- Rein lesender Scanner, Klassifizierung, Dateinamenprüfung, große Dateien, optionale SHA-256-Duplikaterkennung und JSON-Berichte eingeführt.
