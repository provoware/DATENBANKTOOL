# Analyse-Punkte

## Ergebnis dieser Iteration

DATENBANKTOOL führt Nutzer jetzt vollständig durch die rein lesende Ordner-Zeitreihe.
Der neue Startseitenpunkt 11 besitzt Detail-, Schritt-, Feld- und Fehlerhilfe. Der
Offline-HTML-Bericht stellt Größe und Dateizahl zusätzlich in zwei barrierefreien,
skriptfreien SVG-Trendgrafiken dar.

## Vollständig gelöste Bedienungspunkte

1. Eigener Startseitenpunkt `11. Ordner-Zeitreihe`.
2. Vorhandene Indexdatenbank wird schrittweise abgefragt.
3. Relativer Ordnerpfad besitzt verständliche Feldhilfe.
4. `.` wird als gesamter Stammordner erklärt.
5. Optionale älteste Scan-ID wird als positive Ganzzahl validiert.
6. Optionale neueste Scan-ID wird als positive Ganzzahl validiert.
7. Zeitpunkte werden vor dem Start auf 2 bis 500 begrenzt.
8. Berichtsauswahl akzeptiert nur kein, JSON, CSV oder HTML.
9. Berichtspfad besitzt eigene Feldhilfe und sichtbare Wirkungserklärung.
10. Der geplante vollständige Befehl wird vor dem Start angezeigt.
11. Dispatch erfolgt als Argumentliste ohne Shell-Auswertung.
12. Detailhilfe ist über `?11` erreichbar.
13. Schritt-für-Schritt-Hilfe ist über `g11` erreichbar.
14. Jede neue Eingabe kann mit `?` erklärt werden.
15. `datenbanktool help folder-timeline` unterstützt alle drei Hilfestufen.
16. Die Hilfesuche findet Verlauf, Trend und Speicherentwicklung.
17. Fehlerhilfe erklärt fehlende Scans, unpassende Sitzungen, unsichere Pfade,
    leere Ergebnisse und vorhandene Berichte.
18. Die Startseite selbst verändert keine Daten.

## Vollständig gelöste Grafikpunkte

19. Größenverlauf wird als eigenes SVG-Liniendiagramm erzeugt.
20. Dateizahlverlauf wird als eigenes SVG-Liniendiagramm erzeugt.
21. Beide Diagramme sind vollständig lokal eingebettet.
22. HTML enthält kein JavaScript.
23. HTML enthält keine externen HTTP- oder HTTPS-Ressourcen.
24. Jedes Diagramm besitzt `figure` und `figcaption`.
25. Jedes SVG besitzt `role="img"`, `title`, `desc` und `aria-labelledby`.
26. Achsen, Scan-IDs und ausgewählte Werte sind sichtbar beschriftet.
27. Jeder Datenpunkt besitzt Tastaturfokus, `role="img"`, `aria-label` und `title`.
28. Minimum, Maximum und Nettoänderung werden textlich zusammengefasst.
29. Farben werden nie als alleinige Information verwendet.
30. Die vollständige Wertetabelle bleibt unter den Diagrammen erhalten.
31. Lange Zeitreihen reduzieren nur sichtbare Labels, niemals Datenpunkte oder Werte.
32. Darstellung reagiert auf kleinere Bildschirmbreiten.
33. Fokusmarkierung bleibt deutlich sichtbar.

## Architekturentscheidungen

### Hilfethema als getrennte Erweiterung

`core/folder_timeline_help.py` enthält den vollständigen Hilfetextvertrag. Dadurch muss
der bereits große allgemeine Hilfekatalog nicht erneut mit umfangreicher Fachlogik
belastet werden. `guided_home.py` und `help_command.py` binden dieselbe Quelle ein.
Detail-, Schritt- und Fehlerhilfe können dadurch nicht unabhängig auseinanderlaufen.

### Validierung vor dem Dispatch

Der Startseitendialog validiert Integerwerte und erlaubte Berichtstypen bereits vor dem
Aufruf des CLI-Parsers. Der zentrale Parser validiert weiterhin ein zweites Mal. Diese
bewusste doppelte Grenze verbessert die Fehlermeldung für Laien, ohne den eigentlichen
Sicherheitsvertrag vom Dialog abhängig zu machen.

### Argumentliste statt Befehlszeichenkette

Der angezeigte Befehl dient nur der Transparenz. Tatsächlich wird eine Liste einzelner
Argumente an den internen Runner übergeben. Leerzeichen in Pfaden oder Ordnernamen
können dadurch nicht als Shell-Syntax interpretiert werden.

### SVG-Erzeugung in eigenem Modul

`core/folder_timeline_charts.py` erhält ausschließlich das geprüfte Zeitreihenmodell und
liefert statisches SVG-Markup. Dateischreiben, JSON, CSV und HTML-Rahmen bleiben im
Exportmodul. Das hält Berechnung, Visualisierung und Dateifreigabe getrennt testbar.

### Zwei Diagramme statt Doppelachse

Größe und Dateizahl besitzen unterschiedliche Einheiten. Zwei getrennte Diagramme sind
für Laien und Screenreader verständlicher als eine kombinierte Doppelachse. Beide
verwenden dieselbe Scan-Reihenfolge und stehen direkt oberhalb derselben Wertetabelle.

### Vollständigkeit trotz reduzierter Beschriftung

Bis zwölf Punkte werden vollständig sichtbar beschriftet. Bei längeren Reihen werden
sechs repräsentative Achsenpositionen gewählt. Alle Punkte bleiben fokussierbar und
beschrieben; die Tabelle enthält weiterhin jede Zeile. Übersichtlichkeit reduziert
somit keine Information.

### Skriptfreiheit als Sicherheits- und Portabilitätsmerkmal

Die Grafiken benötigen weder JavaScript noch Bibliotheken, Netzwerkzugriff oder
Schriftdateien. Dadurch bleibt der Bericht auch beim ersten netzlosen Start stabil und
enthält keine aktive Ausführungsfläche.

## Automatische Prüfqualität

Die Tests prüfen zusätzlich:

- eindeutigen Startseitenpunkt 11,
- vollständige Argumentliste mit Scan-Grenzen und HTML-Ziel,
- Feldhilfe innerhalb des Dialogs,
- Ablehnung von Zeitpunkten außerhalb 2 bis 500,
- Detail- und Schrittanleitung ohne Aktionsstart,
- zeitreihebezogene Fehlerhilfe,
- eigenständige Hilfe und Alltagswortsuche,
- genau zwei SVG-Elemente,
- zugängliche Rollen, Titel und Beschreibungen,
- Tastaturfokus für Datenpunkte,
- vollständige Wertetabelle,
- Abwesenheit von Skripten und externen URLs.

Gesamtstand der Funktionsreferenz:

- 77 Tests unter Python 3.10,
- 77 Tests unter Python 3.12,
- Warnungen als Fehler,
- Quick-Abnahme 11/11,
- Standard-Abnahme 11/11.

## 0.12-Funktionsreferenz

Commit `b27e678259474ae459f08751ba0b386cccb653a3`:

| Profil | Dateien | Kriterien | Laufzeit | Python-Spitzenspeicher |
|---|---:|---:|---:|---:|
| Quick | 600 | 11/11 | 1,015 s | 1.325.982 Byte |
| Standard | 10.000 | 11/11 | 16,116 s | 13.398.883 Byte |

## Erkannte nächste Analysepunkte

1. Häufig geprüfte relative Ordner als sichere Zeitreihen-Vorlagen speichern.
2. Optionale Trendgrenzen für starkes Größen- oder Dateiwachstum definieren.
3. Diagrammpunkte optional nach realem Zeitabstand positionieren.
4. Mehrere ausgewählte Ordner gemeinsam darstellen.
5. Reale Laienabnahme auf Kubuntu durchführen.
6. `large`-Profil auf Zielhardware vermessen.
7. Später grafische Pfadauswahldialoge ergänzen.

## Fazit

Beide Aufträge sind umgesetzt und automatisch abgesichert. Die Zeitreihe ist ohne
Befehlskenntnis erreichbar, jede Eingabe wird erklärt und vorvalidiert, und Fehler
führen zu konkreten Lösungsschritten. Die HTML-Trends sind lokal, skriptfrei,
tastaturzugänglich und durch eine vollständige Tabelle abgesichert. Offen bleibt
bewusst nur die tatsächlich menschliche Laienabnahme.
