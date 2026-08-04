# Entwicklerdokumentation

## Architektur

1. Rein lesender Scanner.
2. Versionierter SQLite-Snapshot-Index.
3. Inkrementeller Vergleich zwischen abgeschlossenen Sitzungen.
4. Lesende Berichts- und künftig Suchschicht.
5. Spätere Planungsengine für Dateiänderungen.
6. Spätere Transaktions- und Wiederherstellungsengine.
7. Oberfläche ohne direkten Dateisystem-Schreibzugriff.

## SQLite-Schema 3

### Neue Strukturen

- `scan_sessions.parent_session_id`: Baseline eines Re-Scans.
- `scan_sessions.scan_mode`: `full` oder `incremental`.
- `scan_sessions.incremental_stage`: interner, fortsetzbarer Re-Scan-Schritt.
- `files.source_file_id`: Verbindung zur Baseline-Datei.
- `file_identity`: Geräte-ID, Inode und Änderungszeit in Nanosekunden.
- `file_changes`: normalisierte Änderungsereignisse.
- `progress_events`: persistente Fortschritts- und Diagnoseereignisse.

Die historische `phase`-Check-Constraint wird nicht erweitert. Neue Re-Scan-Unterphasen liegen deshalb bewusst in `incremental_stage`. Dadurch bleibt die Migration vorhandener Schema-2-Datenbanken kompatibel.

## Re-Scan-Ablauf

1. Prozesslock erwerben.
2. Schema migrieren.
3. abgeschlossene Baseline bestimmen.
4. kompatiblen Fingerabdruck erzeugen.
5. neue oder unterbrochene Re-Scan-Sitzung öffnen.
6. Dateibaum deterministisch durchlaufen.
7. gleiche Pfade vergleichen und Hashwerte unveränderter Dateien übernehmen.
8. eindeutige Inode-Verschiebungen erkennen.
9. optional eindeutige Hash-Verschiebungen erkennen.
10. nicht zugeordnete Baseline-Dateien als entfernt markieren.
11. nur fehlende Hash-Kandidaten verarbeiten.
12. Duplikatgruppen neu aufbauen.
13. Sitzung vollständig abschließen.

## Lockvertrag

`IndexProcessLock` verwendet `<datenbank>.lock` und `fcntl.flock`.

- Der Lock muss vor jeder schreibenden Indexaktion erworben werden.
- Das bloße Vorhandensein der Lockdatei bedeutet keine Sperre; entscheidend ist der Kernel-Lock.
- Metadaten in der Datei dienen nur der Diagnose.
- Callbacks oder Fortschrittsausgabe dürfen einen Indexlauf nicht beschädigen.

## Backupvertrag

- Sicherungsziel vorab prüfen.
- niemals still überschreiben.
- SQLite-Backup-API statt Dateikopie verwenden.
- temporäre Sicherung mit `quick_check` prüfen.
- erst danach atomar sichtbar machen.

## Restorevertrag

- Sicherung vorab vollständig prüfen.
- neuere unbekannte Schemaversion ablehnen.
- standardmäßig Rückfallsicherung erzeugen.
- Wiederherstellung zuerst in temporärer Datenbank aufbauen.
- Ziel atomar ersetzen und erneut prüfen.
- bei Fehler Rückfallsicherung einspielen.

## Fortschrittsereignisse

`ProgressEvent` enthält:

- Phase
- Ereignisart
- verständliche Nachricht
- aktuellen und optional gesamten Wert
- Sitzung
- strukturierte Zusatzdaten

Ereignisse werden in SQLite gespeichert und optional als Text oder JSONL ausgegeben.

## Prüfungen

```bash
python -m compileall -q src tests
PYTHONPATH=src PYTHONWARNINGS=error python -m unittest discover -s tests -v
```

Aktueller Stand: 19 Tests.

## Nächster technischer Schritt

Eine lesende SQLite-Suchschicht mit Pagination, stabiler Sortierung, kombinierten Filtern und FTS5 entwickeln. Danach können GUI und mobile Bedienung auf eine belastbare API aufsetzen.
