# Analyse-Punkte

## Ergebnis dieser Iteration

DATENBANKTOOL besitzt jetzt eine rein lesende Ordner-Zeitreihe über mehrere
abgeschlossene Scans. Zusätzlich kann der bestehende Ordnervergleich sämtliche
gefilterten JSON-, CSV- und HTML-Zeilen exportieren, ohne die Dateidaten für jede
Terminalseite erneut zu aggregieren.

## Vollständig gelöste Zeitreihenpunkte

1. Neuer öffentlicher Befehl `index folder-timeline`.
2. Standardordner `.` bildet den gesamten Stammordner ab.
3. Relative Unterordner werden einschließlich ihrer Unterordner ausgewertet.
4. Dateizahl und Gesamtgröße werden pro abgeschlossenem Scan berechnet.
5. Scan-ID, UTC-Zeitpunkt und Scan-Modus werden dokumentiert.
6. Datei- und Größendifferenz zum vorherigen Zeitpunkt werden berechnet.
7. Prozentwerte werden nur bei vorhandenem positiven Ausgangswert berechnet.
8. Ausgangswert, Wachstum, Rückgang, Neu, Entfernt, Dateizahländerung und
   Unverändert werden getrennt klassifiziert.
9. Ampel, Status und konkrete Begründung erscheinen gemeinsam.
10. Ausgangs- und Zielsitzung können ausdrücklich begrenzt werden.
11. Ohne Zielangabe wird der neueste abgeschlossene Scan gewählt.
12. `--limit` begrenzt transparent auf 2 bis 500 neueste Zeitpunkte.
13. Mindestens zwei passende Scans werden verlangt.
14. Unterschiedliche Stammordner werden nicht vermischt.
15. Absolute Pfade und `..` werden abgelehnt.
16. SQLite wird mit `mode=ro` und `PRAGMA query_only=ON` geöffnet.
17. JSON wird atomar und ohne ANSI-Ausgaben geschrieben.
18. CSV besitzt UTF-8-BOM, Semikolon und numerische Rohwerte.
19. HTML funktioniert vollständig offline, maskiert Nutzerdaten und besitzt ARIA.
20. Vorhandene Ziele werden nicht still überschrieben.

## Vollständig gelöste Vergleichsexportpunkte

21. `folder-compare` akzeptiert jetzt `--all-pages`.
22. JSON, CSV und HTML enthalten damit alle gefilterten und sortierten Treffer.
23. Das Terminal bleibt auf der gewählten Seite paginiert.
24. `compare_folders(..., all_rows=True)` erzeugt die vollständige Menge einmal.
25. `paginate_folder_comparison()` schneidet daraus die Terminalseite.
26. Ohne `--all-pages` bleibt das bisherige Seitenverhalten unverändert.
27. `--all-pages` ohne Exportziel wird kontrolliert abgelehnt.
28. Vollständigkeit über mehrere Seiten wird für alle drei Formate geprüft.
29. Die SQLite-Datenbank bleibt bei beiden Funktionen bytegenau unverändert.
30. Handler, `CommandPolicy`, Modulzuständigkeit und Zeilengrenzen werden geprüft.

## Zentrale Architekturentscheidungen

### Zeitreihe aus gespeicherten Snapshots

Die Zeitreihe liest ausschließlich abgeschlossene Sitzungen und deren Dateizeilen.
Sie führt keinen neuen Dateisystemscan aus. Dadurch bleibt das Ergebnis reproduzierbar
und verändert weder Index noch Originaldateien.

### Rekursive Präfixauswertung

Für einen relativen Ordner `Musik` werden alle Pfade mit dem sicheren Präfix
`Musik/` gezählt. Dadurch werden Unterordner erfasst, ohne ähnliche Pfade wie
`Musik-Alt/` versehentlich einzubeziehen.

### Strenger Pfad- und Stammordnervertrag

Ordnerangaben bleiben relativ. Absolute Pfade und Elternnavigation werden verworfen.
Ausgangs- und Zielsitzungen müssen abgeschlossen sein und denselben normalisierten
Stammordner besitzen.

### Zustand pro Übergang

Der erste sichtbare Punkt ist ein Ausgangswert. Jeder weitere Punkt wird gegenüber
dem direkten vorherigen sichtbaren Scan klassifiziert. Das liefert eine verständliche
Chronologie statt nur einer Gesamtdifferenz.

### Berechnung und Export getrennt

`core/folder_timeline.py` enthält Auswahl und Messwerte.
`core/folder_timeline_exports.py` enthält ausschließlich die atomaren Formate.
`cli_folder_timeline.py` übernimmt Parser und menschenlesbare Ausgabe.

### Vollständiger Vergleich ohne doppelte Aggregation

Bei `--all-pages` entsteht eine vollständige sortierte `FolderComparisonPage`.
Die Terminalseite wird daraus nachträglich ausgeschnitten. Export und Bildschirm
verwenden damit dieselbe geprüfte Ergebnismenge.

## Automatische Prüfqualität

Die neue Testdatei prüft:

- drei chronologische Scans mit Wachstum und Rückgang,
- rekursive Dateizahl und Größe,
- Datenbank-Unverändertheit,
- JSON-, Calc-CSV- und Offline-HTML-Ausgabe,
- CLI-Ausgabe,
- Ablehnung von `..`,
- Mindestanzahl von zwei Scans,
- vollständige Vergleichsexporte über mehrere Seiten,
- kontrollierten Fehler ohne Exportziel.

Der Architekturtest bindet den neuen Befehl zusätzlich an sein CLI-Modul und seine
`CommandPolicy`. Gesamtstand: 71 Tests unter Python 3.10 und 3.12.

## Erkannte nächste Analysepunkte

1. Zeitreihe als eigenen Punkt in die geführte Startseite aufnehmen.
2. Mehrschichtige Detail-, Schritt-, Feld- und Fehlerhilfe ergänzen.
3. Barrierefreie SVG-Liniengrafiken im Offline-HTML erzeugen.
4. Mehrere ausgewählte Ordner gemeinsam darstellen.
5. Warnschwellen für starkes Wachstum optional ergänzen.
6. Reale Laienabnahme auf Kubuntu durchführen.
7. `large`-Profil auf Zielhardware vermessen.

## Fazit

Beide technischen Aufträge sind umgesetzt und automatisch abgesichert. Nutzer können
einen Ordner über mehrere Scans nachvollziehen und Vergleichsberichte ohne Seitenverlust
exportieren. Alle neuen Wege bleiben offline, nachvollziehbar und rein lesend; der
einzige offene Hauptpunkt bleibt die tatsächlich menschliche Laienabnahme.
