# Analyse-Punkte

## Ergebnis dieser Iteration

DATENBANKTOOL kann jetzt zwei abgeschlossene Scans desselben Stammordners rein lesend
auf Ordnerebene vergleichen. Nutzer sehen sofort, welche Ordner gewachsen, kleiner,
neu oder nicht mehr vorhanden sind. Größe, Dateizahl, Differenz, Prozentwert, Ampel und
Begründung werden gemeinsam angezeigt.

## Vollständig gelöste Punkte

1. Zwei abgeschlossene Sitzungen können direkt miteinander verglichen werden.
2. Ohne manuelle Scan-Nummern wird ein passendes aktuelles Vergleichspaar gewählt.
3. Der direkte Vorgänger eines Re-Scans wird bevorzugt.
4. Ohne direkten Vorgänger wird der vorherige abgeschlossene Scan desselben Ordners
   verwendet.
5. Nicht abgeschlossene Sitzungen werden abgelehnt.
6. Die Ausgangssitzung muss älter als die Zielsitzung sein.
7. Unterschiedliche Stammordner werden sicher abgelehnt.
8. SQLite wird mit `mode=ro` und `PRAGMA query_only=ON` geöffnet.
9. Die Datenbank bleibt bei der reinen Auswertung unverändert.
10. Originaldateien werden nicht erneut geöffnet oder verändert.
11. Dateizahl und Größe werden für jeden Ordner einschließlich Unterordnern berechnet.
12. Gewachsene Ordner werden erkannt.
13. Kleiner gewordene Ordner werden erkannt.
14. Neue Ordner werden erkannt.
15. Nicht mehr vorhandene belegte Ordner werden erkannt.
16. Gleiche Größe bei geänderter Dateizahl wird getrennt ausgewiesen.
17. Unveränderte Ordner können gezielt eingeblendet werden.
18. Absolute und prozentuale Größenänderung werden berechnet.
19. Neue Ordner erhalten keinen irreführenden unendlichen Prozentwert.
20. Filter nach Zustand, Pfad, Mindeständerung und Tiefe sind kombinierbar.
21. Sortierung und Pagination sind stabil und begrenzt.
22. Starkes Wachstum besitzt eine konfigurierbare Warnschwelle.
23. Ampeln werden immer mit Klartext und Begründung ausgegeben.
24. JSON-, CSV- und HTML-Berichte werden atomar geschrieben.
25. CSV ist für LibreOffice Calc vorbereitet.
26. HTML funktioniert offline und maskiert Nutzerdaten sicher.
27. Vorhandene Berichte werden nicht still überschrieben.
28. Startseitenpunkt 10 startet den Vergleich ohne Pflichtbestätigung, da er rein lesend ist.
29. `?10` und `g10` bieten unterschiedliche Hilfetiefen.
30. Direkte und klassische Hilfe enthalten dasselbe Thema.
31. Der öffentliche Befehl besitzt eine geprüfte Seiteneffektrichtlinie.
32. Die modulare CLI-Größen- und Importregeln bleiben erfüllt.
33. 59 Tests laufen unter Python 3.10 und 3.12 erfolgreich.

## Zentrale Architekturentscheidungen

### Ganze Snapshots statt nur Dateiänderungsprotokoll

Der Vergleich aggregiert die gespeicherten Dateien beider Sitzungen. Dadurch können
beliebige abgeschlossene Sitzungen desselben Stammordners verglichen werden, nicht nur
ein einzelner inkrementeller Re-Scan mit seinem direkten Vorgänger.

### Rekursive Ordnerwerte

Jede Datei zählt für ihren direkten Elternordner und alle übergeordneten Ordner bis zur
Wurzel. Das entspricht der Frage „Wie viel Speicher belegt dieser Ordner insgesamt?“.
Die Dokumentation warnt deshalb ausdrücklich davor, Eltern- und Kindzeilen zu addieren.

### Strenger Stammordnervertrag

Ähnliche relative Pfade aus unterschiedlichen Stammordnern könnten falsche Vergleiche
erzeugen. Deshalb müssen die gespeicherten Wurzelpfade übereinstimmen. Das Tool rät
nicht und mischt keine Bestände.

### Sichere automatische Sitzungswahl

Die automatische Auswahl ist nur eine Komfortfunktion. Die tatsächlich verwendeten
Sitzungsnummern werden immer im Ausgabekopf angezeigt und können über explizite
Optionen ersetzt werden.

### Zustände statt bloßer Vorzeichen

Positive und negative Bytewerte allein sind für Laien zu abstrakt. Der Vergleich
übersetzt sie in verständliche Zustände und zeigt trotzdem die exakten Zahlen daneben.

### Kein automatisches Aufräumen

Wachstum oder Rückgang beweist nicht, dass Dateien unnötig oder korrekt entfernt sind.
Der Vergleich bleibt deshalb reine Diagnose und löst keine Dateisystemaktion aus.

### Getrennter Exportbaustein

Vergleichsberechnung und Dateiexporte sind getrennt. Dadurch bleibt der Kern rein
lesend und kann unabhängig von JSON-, CSV- und HTML-Ausgabe getestet werden.

## Erkannte nächste Analysepunkte

1. CSV-Export der normalen Ordnerübersicht ergänzen.
2. Wahlweise alle gefilterten Vergleichszeilen statt nur der aktuellen Seite exportieren.
3. Entwicklung eines Ordners über mehr als zwei Scans als Zeitreihe darstellen.
4. Leere Ordner nur nach einer späteren, bewusst versionierten Schemaerweiterung erfassen.
5. Sehr große Bestände unter festen Laufzeit- und Speichergrenzen vermessen.
6. Automatische Sitzungswahl und Begriffe mit Linux-Laien praktisch abnehmen.
7. HTML- und CSV-Ausgaben mit realistischen Sonderzeichen und langen Pfaden prüfen.

## Fazit

Der Ordnervergleich ergänzt die bisherige Dateiansicht um eine verständliche
Speicherentwicklung auf Ordnerebene. Die Funktion bleibt nachvollziehbar, offline,
rein lesend und vollständig in Startseite, Hilfe, Sicherheitsvertrag und Tests
eingebunden.
