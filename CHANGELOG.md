# Changelog

Alle wesentlichen Projektänderungen werden hier dokumentiert.

## 0.3.0-alpha.1 – 2026-08-04

### Hinzugefügt

- SQLite-Schema 3 mit automatischer Migration von vorhandenen Schema-2-Datenbanken.
- Inkrementeller Re-Scan auf Basis einer abgeschlossenen Index-Sitzung.
- Erkennung neuer, geänderter, verschobener, entfernter und unveränderter Dateien.
- Sichere Verschiebungserkennung über Geräte-/Inode-Identität plus identische Größe und Nanosekunden-Zeit.
- Zusätzliche Hash-Verschiebungserkennung, wenn die Baseline bereits SHA-256-Werte besitzt.
- Wiederverwendung vorhandener SHA-256-Werte für unveränderte Dateien.
- Fortsetzbarer Re-Scan mit persistentem Checkpoint und kompatibilitätsgeprüfter Baseline.
- Prozessübergreifender Linux-Dateilock auf Basis von `fcntl.flock`.
- Persistente Fortschrittsereignisse sowie Ausgabe als verständlicher Text oder JSONL.
- `index sessions` mit Status-, Wurzel- und Mengenfilter.
- `index backup` über die konsistente SQLite-Backup-API.
- `index restore` mit Vorabprüfung und standardmäßiger Sicherheitskopie des Zielindexes.
- Zusätzliche Tests für Migration, Inode-Wiederverwendung, Wiederaufnahme, Backup und Restore.

### Verbessert

- Gleichgroße Dateiersetzungen werden über Geräte-/Inode-Wechsel als Änderung erkannt.
- Inode-Wiederverwendung nach Löschen erzeugt keine falsche Verschiebung mehr.
- Hashing im Re-Scan konzentriert sich auf neue oder geänderte Kandidaten.
- Reparatur, Vollindex, Re-Scan, Backup und Restore verwenden denselben Prozesslock.
- CLI-Status zeigt Scanmodus und Baseline-Sitzung.

### Validiert

- Python-Kompilierung erfolgreich.
- 19 von 19 Unittests erfolgreich mit `PYTHONWARNINGS=error`.
- Schema-2→3-Migration mit historischer Phasen-Check-Constraint erfolgreich.
- End-to-End-Abläufe für Build, Re-Scan, Sitzungen, Backup, Restore und Berichte erfolgreich.

## 0.2.0-alpha.1 – 2026-08-04

- Persistenter SQLite-Index mit Schema-Versionierung, Batch-Import, Wiederaufnahme und Reparaturmodus.
- Gefilterte CSV- und HTML-Berichte.

## 0.1.0-alpha.1 – 2026-08-04

- Rein lesender Scanner, Dateiklassifizierung, Namensprüfung und exakte Duplikaterkennung.
