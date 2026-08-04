# Schwachstellen und aktuelle Grenzen

## Ordner-Zeitreihe

1. Die Zeitreihe benötigt mindestens zwei abgeschlossene Scans desselben
   Stammordners. Ein einzelner Erstscan liefert bewusst keinen Verlauf.
2. Der Ordnerpfad ist relativ zum gespeicherten Stammordner. Absolute Pfade und `..`
   werden aus Sicherheitsgründen abgelehnt.
3. Elternordner enthalten die rekursiven Werte ihrer Unterordner. Mehrere
   Ordnerzeitreihen dürfen daher nicht ungeprüft addiert werden.
4. Leere Ordner ohne Dateien erscheinen nicht, weil das aktuelle Schema Dateien und
   keine eigenständigen Verzeichniszeilen speichert.
5. `--limit` zeigt bei großen Historien nur die neuesten 2 bis 500 Zeitpunkte. Die
   Verkürzung wird sichtbar gemeldet, ältere Punkte müssen mit einer passenden
   Ausgangssitzung gezielt eingegrenzt werden.
6. Bei einem neuen Ordner ohne vorherige Größe ist keine normale prozentuale Änderung
   berechenbar; das Feld bleibt leer beziehungsweise wird mit „–“ dargestellt.
7. Die Zeitstempel stammen aus den gespeicherten Scan-Sitzungen und nicht aus den
   Änderungszeiten einzelner Dateien.
8. Der HTML-Bericht zeigt derzeit eine barrierefreie Tabelle, aber noch keine
   eingebettete Liniengrafik.
9. Der direkte CLI-Befehl ist vorhanden und klassisch erklärt, aber noch nicht als
   eigener Punkt in der geführten Startseite eingebunden.
10. Es wird jeweils ein relativer Ordner ausgewertet. Mehrere parallele Ordnerlinien
    sind noch nicht vorhanden.

## Vollständiger Ordnervergleichsexport

11. Ohne `--all-pages` bleibt das bisherige Verhalten erhalten: Berichte enthalten nur
    die gewählte Seite.
12. `--all-pages` benötigt mindestens ein JSON-, CSV- oder HTML-Ziel und ist damit
    absichtlich sichtbar.
13. Bei sehr vielen gefilterten Ordnern liegt die vollständige sortierte Zeilenmenge
    während des Exports im Arbeitsspeicher. Die Dateidaten werden dennoch nur einmal
    aggregiert.
14. Eltern- und Kindzeilen enthalten überlappende rekursive Werte und dürfen nicht
    addiert werden.
15. CSV speichert Status und Begründung als Text, aber keine sichtbaren Farben.

## Großbestands- und Laienabnahme

16. Synthetische Sparse-Dateien bilden Metadaten- und Indexleistung gut ab, aber nicht
    die vollständige Leselast großer real gefüllter Mediendateien.
17. Das `large`-Profil mit 100.000 Dateien wurde noch nicht auf der vorgesehenen
    Zielhardware ausgeführt.
18. Eine echte Laienabnahme wurde noch nicht durchgeführt. Die Checkliste ersetzt
    keine reale Beobachtung und Rückfragen.
19. `tracemalloc` misst Python-Speicher; nativer SQLite- und Betriebssystemspeicher
    wird zusätzlich protokolliert, besitzt aber noch keine harte Plattformgrenze.
20. GitHub-Actions-Artefakte laufen nach der festgelegten Aufbewahrungsdauer ab.

## Bedienung und Plattform

21. Die Oberfläche bleibt terminalbasiert und besitzt keine grafischen Pfaddialoge.
22. Hilfetexte sind deutschsprachig; die Stichwortsuche ist deterministisch.
23. Automatische Lösch-, Verschiebe- und Umbenennungsfunktionen bleiben gesperrt.

## Sicherheitsfazit

Zeitreihe und Ordnervergleich öffnen SQLite ausschließlich lesend. Originaldateien
werden nicht erneut geöffnet oder verändert. Unterschiedliche Stammordner werden nicht
vermischt, relative Ordnerpfade werden strikt validiert, und Berichte werden atomar
sowie überschreibgeschützt geschrieben. Keine bekannte Grenze rechtfertigt das
Freischalten automatischer Originaldateioperationen.
