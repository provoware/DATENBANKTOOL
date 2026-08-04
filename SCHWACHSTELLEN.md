# Schwachstellen und aktuelle Grenzen

## Geführte Ordner-Zeitreihe

1. Die Zeitreihe benötigt mindestens zwei abgeschlossene Scans desselben
   Stammordners. Ein einzelner Erstscan liefert bewusst keinen Verlauf.
2. Der Ordnerpfad ist relativ zum gespeicherten Stammordner. Absolute Pfade und `..`
   werden aus Sicherheitsgründen abgelehnt.
3. Die geführte Startseite kann Pfade erklären und Argumente validieren, aber keine
   grafische Dateiauswahl bereitstellen.
4. Scan-IDs sind optional. Wer sie ausdrücklich eingibt, muss weiterhin passende
   abgeschlossene Sitzungen desselben Stammordners wählen.
5. Der Dialog bietet pro Lauf ein Exportformat. Mehrere Formate gleichzeitig bleiben
   über den direkten CLI-Befehl möglich.
6. Vorhandene Berichte werden nicht still überschrieben. Die geführte Oberfläche bietet
   absichtlich keinen schnellen Überschreibschalter; ein neuer Dateiname ist sicherer.
7. Die Hilfe ist deutschsprachig und nutzt eine deterministische Stichwortsuche statt
   einer semantischen Suchmaschine.

## SVG-Trendgrafiken

8. Diagrammpunkte werden gleichmäßig nach Scan-Reihenfolge verteilt. Unterschiedlich
   lange reale Zeitabstände zwischen Scans sind deshalb nicht proportional sichtbar.
9. Bei mehr als zwölf Punkten werden nur ausgewählte sichtbare Scan- und Wertelabels
   gezeigt. Jeder Punkt bleibt per Tastatur und ARIA beschrieben; alle Werte stehen
   zusätzlich vollständig in der Tabelle.
10. Bei der Höchstgrenze von 500 Zeitpunkten enthält jedes Diagramm 500 fokussierbare
    Datenpunkte. Das ist vollständig, kann für reine Tastaturnutzung aber umfangreich
    sein.
11. Die Diagramme verwenden eine automatisch aus den sichtbaren Werten gebildete
    y-Achse. Verschiedene Berichte besitzen daher nicht zwingend dieselbe Skala.
12. Größe und Dateizahl werden bewusst in getrennten Diagrammen dargestellt. Eine
    gemeinsame Doppelachse wäre kompakter, aber deutlich schwerer verständlich.
13. SVG wird von aktuellen Browsern direkt unterstützt. Sehr alte HTML-Programme
    können die Grafik ignorieren; die vollständige Tabelle bleibt dennoch lesbar.
14. Die Diagramme zeigen derzeit jeweils einen relativen Ordner. Mehrere parallele
    Ordnerlinien sind noch nicht vorhanden.

## Ordner-Zeitreihe allgemein

15. Elternordner enthalten die rekursiven Werte ihrer Unterordner. Mehrere
    Ordnerzeitreihen dürfen daher nicht ungeprüft addiert werden.
16. Leere Ordner ohne Dateien erscheinen nicht, weil das aktuelle Schema Dateien und
    keine eigenständigen Verzeichniszeilen speichert.
17. `--limit` zeigt bei großen Historien nur die neuesten 2 bis 500 Zeitpunkte. Die
    Verkürzung wird sichtbar gemeldet.
18. Bei einem neuen Ordner ohne vorherige Größe ist kein normaler Prozentwert
    berechenbar; das Feld bleibt leer beziehungsweise wird mit „–“ dargestellt.
19. Zeitstempel stammen aus den Scan-Sitzungen und nicht aus Änderungszeiten einzelner
    Dateien.

## Großbestands- und Laienabnahme

20. Synthetische Sparse-Dateien bilden Metadaten- und Indexleistung gut ab, aber nicht
    die vollständige Leselast großer real gefüllter Mediendateien.
21. Das `large`-Profil mit 100.000 Dateien wurde noch nicht auf der vorgesehenen
    Zielhardware ausgeführt.
22. Eine echte Laienabnahme wurde noch nicht durchgeführt. Die Checkliste ersetzt
    keine reale Beobachtung und Rückfragen.
23. `tracemalloc` misst Python-Speicher; nativer SQLite- und Betriebssystemspeicher
    besitzt noch keine harte plattformübergreifende Grenze.
24. GitHub-Actions-Artefakte laufen nach der festgelegten Aufbewahrungsdauer ab.

## 0.12-Funktionsreferenz

- 77/77 Tests unter Python 3.10 und Python 3.12.
- Quick: 600 Dateien, 11/11 Kriterien, 1,015 Sekunden.
- Standard: 10.000 Dateien, 11/11 Kriterien, 16,116 Sekunden.
- Diese CI-Werte sind Referenzen und keine Zusage für andere Hardware.

## Sicherheitsfazit

Geführte Zeitreihe, Hilfe und SVG-Berichte verändern weder SQLite noch Originaldateien.
Der Dialog erzeugt ausschließlich sichere Argumentlisten. HTML bleibt skriptfrei und
vollständig lokal. Pfade, Zahlenbereiche und Berichtsauswahl werden vor dem Start
validiert; Berichte werden atomar und überschreibgeschützt geschrieben. Keine bekannte
Grenze rechtfertigt das Freischalten automatischer Originaldateioperationen.
