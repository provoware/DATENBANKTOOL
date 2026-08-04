# Analyse-Punkte

## Ergebnis dieser Iteration

Der Index arbeitet jetzt als Snapshot-Folge statt als überschreibbarer Einzelbestand. Ein Re-Scan erzeugt eine neue Sitzung, verknüpft sie mit einer abgeschlossenen Baseline und speichert jede erkannte Änderung separat.

## Änderungsmodell

- `added`: Pfad existiert nur im neuen Snapshot.
- `modified`: Pfad existiert in beiden Snapshots, Identität oder Metadaten unterscheiden sich.
- `moved`: eine alte und neue Datei konnten eindeutig über stabile Linux-Identität oder vorhandenen SHA-256-Wert verbunden werden.
- `removed`: Baseline-Datei besitzt keine Zuordnung im neuen Snapshot.
- `unchanged`: Pfad, Größe, Identität und Änderungszeit stimmen überein.

## Sicherheitsregeln der Verschiebungserkennung

1. Geräte-ID und Inode allein reichen nicht, weil Inodes wiederverwendet werden können.
2. Eine Inode-Verschiebung wird nur bei identischer Größe und identischer Nanosekunden-Zeit bestätigt.
3. Hardlinks oder Mehrdeutigkeiten werden nicht automatisch zugeordnet.
4. Hash-Zuordnung wird nur bei eindeutiger alter und neuer Datei verwendet.
5. Unsichere Fälle bleiben als `added` und `removed` sichtbar.

## Wiederaufnahme

- Jeder Batch bestätigt Dateien, Fehler und Checkpoint gemeinsam.
- Baseline, Wurzel und Scanoptionen fließen in den Fingerabdruck ein.
- Eine Fortsetzung mit anderer Baseline oder anderen Sicherheitsoptionen wird abgelehnt.
- Vergleich und Finalisierung sind idempotent wiederholbar.

## Prozesslock

- Vollindex, Re-Scan, Reparatur, Backup und Restore verwenden einen gemeinsamen Dateilock.
- Der Lock enthält PID, Host, Zeitpunkt und Operation als verständliche Diagnose.
- Absturz oder Prozessende gibt den Betriebssystemlock automatisch frei.
- Ein Timeout kann ausdrücklich gesetzt werden; Standard ist sofortiges, klares Scheitern.

## Backup und Restore

- Sicherungen werden über die SQLite-Backup-API erzeugt.
- Eine temporäre Datei wird geprüft, bevor sie zum sichtbaren Sicherungsziel wird.
- Restore prüft Schema und `quick_check`, bevor die aktive Datenbank ersetzt wird.
- Vor Restore entsteht standardmäßig eine zusätzliche Rückfallsicherung.
- Bei Übernahmefehlern wird die Rückfallsicherung verwendet.

## Architektur-Fazit

Der Datenkern ist nun ausreichend belastbar für eine echte Suchschicht. Die grafische Oberfläche sollte weiterhin erst nach Pagination, FTS5-Suche, Ordneraggregaten und Sitzungsaufbewahrung aufgebaut werden.
