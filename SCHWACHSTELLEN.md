# Schwachstellen und aktuelle Grenzen

## Aktuelle Grenzen der Suche

1. FTS5 durchsucht derzeit Dateinamen, Pfade, Endungen, Typen und Warncodes – nicht den Inhalt aller Dateien.
2. Die normale SQLite-`LIKE`-Suche ist bei sehr großen Beständen langsamer als FTS5.
3. FTS5 ist von der verwendeten Python-/SQLite-Buildoption abhängig.
4. Ein FTS5-Index gehört immer zu einer konkreten Scan-Sitzung und muss für neue Sitzungen neu aufgebaut werden.
5. Pro Seite sind absichtlich höchstens 200 Treffer erlaubt.
6. Unicode-Groß-/Kleinschreibung der normalen SQLite-Suche ist nicht in allen Sprachen vollständig.
7. Suchergebnisse besitzen noch keine grafischen Vorschauen.
8. Ordnergrößen werden noch nicht zusammengefasst.

## Aktuelle Grenzen der Änderungsberichte

1. Ein Änderungsbericht benötigt einen abgeschlossenen Re-Scan mit Baseline.
2. HTML-Berichte mit sehr vielen Änderungen können groß werden.
3. Details werden technisch als JSON gespeichert und teilweise noch nicht in Alltagssprache übersetzt.
4. Berichte zeigen erkannte Änderungen, führen aber keine Dateiaktion aus.

## Weiterhin kritisch vor Dateiänderungen

- keine vollständige Planungsengine,
- keine Kollisionsprüfung,
- kein Undo-Manifest für Dateioperationen,
- keine Quarantäne,
- keine getestete Wiederherstellung halbfertiger Dateioperationen.

Deshalb bleiben Verschieben, Umbenennen und Löschen weiterhin gesperrt.
