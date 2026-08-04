# Analyse-Punkte

## Ergebnis dieser Iteration

Der gespeicherte SQLite-Index ist jetzt direkt nutzbar. Nutzer müssen keine langen JSON-Dateien mehr durchsuchen, sondern können mit einfachen Befehlen suchen, filtern, sortieren und durch Seiten blättern.

## Entscheidungen für Laien

1. Die Standardsuche benötigt nur Datenbank und Suchwort.
2. Ohne Suchwort funktionieren Filter allein.
3. Die Seitengröße ist begrenzt, damit Terminal und Speicher übersichtlich bleiben.
4. Die Ausgabe nennt Trefferzahl, aktuelle Seite und den Befehl für die nächste Seite.
5. Technische FTS5-Beschleunigung ist optional und muss bewusst aufgebaut werden.
6. Fehlt FTS5, bleibt die normale Suche verfügbar.
7. Änderungsarten werden im Terminal deutsch bezeichnet.
8. JSON, CSV und HTML können gleichzeitig erzeugt werden.
9. Vorhandene Berichte werden nicht ungefragt ersetzt.

## Suchmodell

- Suche innerhalb einer unveränderlichen Scan-Sitzung.
- Standardmäßig neueste abgeschlossene Sitzung.
- Stabile Reihenfolge durch Hauptsortierung plus Pfad und Datei-ID.
- SQL-Parameter statt zusammengesetzter Nutzereingaben.
- `mode=ro` und `query_only` für normale Suchabfragen.
- FTS5 nur als ausdrücklich erzeugter Zusatzindex.

## Änderungsmodell

- `added` → Neu
- `modified` → Geändert
- `moved` → Verschoben
- `removed` → Entfernt
- `unchanged` → Unverändert

Der Bericht zeigt alten Pfad, neuen Pfad, Dateityp, Größe, Datum und technische Erkennungsdetails. Er verändert keine Datei.

## Architektur-Fazit

Der nächste sinnvolle Baustein ist keine Dateiänderung, sondern eine verständliche Ordnerübersicht. Nutzer sollen zuerst erkennen können, welche Ordner besonders groß, unübersichtlich oder auffällig sind.
