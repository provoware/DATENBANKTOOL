# Analyse-Punkte

## In dieser Iteration vollständig gelöst

1. Persistenz großer Scanergebnisse in SQLite.
2. Nachvollziehbare Schema-Versionierung.
3. Automatische V1→V2-Migration.
4. Batchweise Transaktionen statt Einzelcommit pro Datei.
5. Eindeutige Dateiimporte je Sitzung.
6. Persistenter Scan-Checkpoint.
7. Getrennte Phasen für Scan, Hashing und Finalisierung.
8. Wiederaufnahme kompatibler Sitzungen.
9. Reproduzierbarer Neuaufbau von Duplikatgruppen.
10. Reparatur mit Sicherung vor verändernden Maßnahmen.
11. Vorher-/Nachher-Integritätsprüfung.
12. CSV-Bericht mit Datenfiltern.
13. HTML-Bericht mit Daten- und Browserfiltern.
14. Schutz vor stiller Berichtsüberschreibung.
15. Schutz vor halber CSV-/HTML-Mehrfachausgabe durch Vorprüfung.

## Fachliche Entscheidungen

### SQLite statt flüchtigem Arbeitsspeicher

Der Index ist die verbindliche Datenquelle für spätere Suche und Oberfläche. Große Sammlungen müssen nicht vollständig im RAM gehalten werden. Sitzungen, Fehler und Checkpoints bleiben nach Neustart erhalten.

### Sitzungen statt global überschriebenem Bestand

Jeder Scan besitzt eine eigene Sitzung. Dadurch bleiben ältere Ergebnisse nachvollziehbar und ein abgebrochener Lauf beschädigt keinen abgeschlossenen Bestand.

### Fingerabdruck für Wiederaufnahme

Wurzelpfad und sicherheitsrelevante Optionen werden zu einem SHA-256-Fingerabdruck zusammengefasst. Nur passende Sitzungen werden fortgesetzt. Batchgröße und Testgrenze gehören bewusst nicht zum Fingerabdruck.

### Atomarer Batchvertrag

Dateien, Warnungen, Fehler, Zähler und Checkpoint werden innerhalb derselben SQLite-Transaktion gespeichert. Ein Absturz vor `COMMIT` bestätigt nichts; ein Absturz danach besitzt einen konsistenten Wiederaufnahmepunkt.

### Reparatur ist kein falsches Heilversprechen

Der Reparaturmodus kann lesbare Datenbanken prüfen, migrieren, liegengebliebene Sitzungen korrigieren, Duplikatgruppen neu aufbauen und Indizes regenerieren. Beliebig zerstörte SQLite-Dateien können nicht garantiert wiederhergestellt werden.

## Noch offene Analysepunkte

1. Stabiler Wiederanlauf, wenn die Checkpointdatei zwischenzeitlich entfernt wurde.
2. Inkrementeller Vergleich abgeschlossener Sitzungen.
3. Identifikation von Dateien über Gerät, Inode, Größe, Zeit und optional Hash.
4. Behandlung von Umbenennungen ohne erneutes Vollhashing.
5. Schutz vor zwei gleichzeitig laufenden Indexprozessen.
6. Wechselnde Mountpunkte externer Datenträger.
7. Dateisysteme mit anderer Groß-/Kleinschreibung.
8. Hashing-Pause und kontrollierter Abbruch mitten im Kandidatenlauf.
9. Aufteilung sehr großer HTML-Berichte.
10. Datenschutzregeln für spätere Inhaltsindizierung.
11. Lebenszyklus und Bereinigung alter Indexsitzungen.
12. Export- und Importvertrag für portable Indexarchive.

## Architektur-Fazit

Die belastbare Reihenfolge bleibt:

1. Inventarisieren.
2. Persistieren.
3. Prüfen und suchen.
4. Verständlich gruppieren.
5. Änderungsplan erzeugen.
6. Plan vollständig validieren.
7. Transaktion mit Journal ausführen.
8. Ergebnis prüfen.
9. Undo und Wiederherstellung bereitstellen.

Die ersten drei Stufen besitzen jetzt einen validierten Alpha-Kern. Schreibende Dateifunktionen bleiben korrekt blockiert.
