# Schwachstellen und aktuelle Grenzen

## Mehrschichtige Laienhilfe

1. Die Hilfe arbeitet mit gepflegten Themen und Stichwörtern, nicht mit einer semantischen KI-Suche.
2. Alltagssuche findet Begriffe wie „Platzfresser“, kennt aber nicht jede denkbare Umschreibung.
3. Feldhilfe erklärt Eingaben, kann einen unbekannten Pfad aber nicht automatisch erraten.
4. Fehlerhilfe nennt sichere Prüfstellen, führt jedoch absichtlich keine automatische Reparatur aus.
5. Die Hilfetexte müssen bei neuen Funktionen zentral ergänzt und durch Tests abgesichert werden.
6. Der ältere Befehl `datenbanktool explain` bleibt aus Kompatibilitätsgründen bestehen; die vollständig mehrschichtige Hilfe liegt unter `datenbanktool help`.

## Terminalbedienung

7. Die Oberfläche besitzt noch keine grafischen Dateiauswahlfenster.
8. Ordner- und Datenbankpfade werden als Text eingegeben oder eingefügt.
9. Zuletzt verwendete Pfade gelten nur innerhalb der aktuellen Startseiten-Sitzung.
10. `q` bricht den aktuellen Schritt ab; versehentliche Eingaben werden nicht als Pfad übernommen.
11. In Skripten öffnet sich die Startseite absichtlich nicht automatisch.

## Codequalität

12. `cli.py` enthält weiterhin viele Parser- und Ausführungsfunktionen in einer großen Datei.
13. Die neue Hilfe wurde bewusst außerhalb von `cli.py` umgesetzt, die restliche Befehlslogik muss aber noch modularisiert werden.
14. `terminal_home.py` ist jetzt nur noch eine Kompatibilitätsschicht; neue Entwicklung findet in `guided_home.py` statt.
15. Der Hilfekatalog ist zentral, aber derzeit deutschsprachig und noch nicht für Übersetzungen strukturiert.

## Fachliche Grenzen

16. Die Ordnerübersicht besitzt JSON und HTML, aber noch keinen CSV-Export.
17. Ordnerwachstum zwischen zwei Scans wird noch nicht direkt zusammengefasst.
18. FTS5 durchsucht Metadaten, nicht automatisch den Inhalt aller Dateien.
19. Schreibende Originaldateioperationen bleiben gesperrt.
20. Vor einem stabilen Release fehlen Last- und Bedienabnahmen mit sehr großen realen Beständen.

## Sicherheitsfazit

Keine bekannte Grenze rechtfertigt automatische Originaldateiänderungen. Die Hilfe erklärt Wirkungen, bestätigt schreibende Indexaktionen und bleibt selbst vollständig datenänderungsfrei.
