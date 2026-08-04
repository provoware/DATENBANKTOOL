# TODO

## In dieser Iteration erledigt

1. [x] Geführte Startseite als nummeriertes Terminalmenü entwickeln.
2. [x] Such-, Ordner-, Änderungs- und Statusfunktionen direkt aus dem Menü starten.
3. [x] Indexaufbau, Re-Scan und Sicherung geführt vorbereiten.
4. [x] Wirkung jeder Auswahl mit Ampel und Klartext erklären.
5. [x] Schreibende Menüaktionen durch zusätzliche Bestätigung schützen.
6. [x] Geplanten vollständigen Befehl vor der Ausführung anzeigen.
7. [x] Pfade und Suchtexte ohne Shell-Auswertung als sichere Argumentliste übergeben.
8. [x] `datenbanktool start` als neuen Programmeinstieg ergänzen.
9. [x] Interaktiven Leerstart ermöglichen und nicht-interaktive Aufrufe vor Blockierung schützen.
10. [x] Startlogik aus der großen `cli.py` in eigene Module auslagern.
11. [x] Ein-/Ausgabe und Befehlsausführung für automatisierte Tests austauschbar machen.
12. [x] Acht neue Tests für Auswahl, Abbruch, Bestätigung und sicheren Start ergänzen.
13. [x] 39 automatisierte Tests unter Python 3.10 und 3.12 erfolgreich ausführen.

## Noch offen

1. [ ] Die große `cli.py` schrittweise in kleinere Befehlsmodule aufteilen.
2. [ ] Ordnerübersicht zusätzlich als CSV exportieren.
3. [ ] Speicherentwicklung eines Ordners zwischen zwei Scans vergleichen.
4. [ ] Gespeicherte Suchvorlagen exportieren und importieren.
5. [ ] Alte Scan-Sitzungen nach Vorschau sicher archivieren.
6. [ ] Barrierearme grafische Oberfläche mit Schaltflächen entwickeln.
7. [ ] Sichere Dateiänderungspläne mit Journal, Rückgängig-Funktion und Quarantäne entwickeln.

## Direkt folgender einfacher Schritt

Den großen Befehlsblock in kleinere Bausteine teilen, damit einzelne Funktionen leichter geprüft und geändert werden können.

## Sichere Zusatzverbesserung

Die Ordnerübersicht als CSV speichern, damit sie direkt in LibreOffice Calc oder ähnlichen Tabellenprogrammen geöffnet werden kann.
