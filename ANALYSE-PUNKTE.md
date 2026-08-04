# Analyse-Punkte

## Ergebnis dieser Iteration

DATENBANKTOOL kann jetzt ohne Kenntnis einzelner Befehle bedient werden. Eine nummerierte Startseite erklärt jede Funktion, fragt nur die benötigten Werte ab, zeigt den geplanten Befehl und schützt schreibende Indexaktionen durch eine zusätzliche Bestätigung.

## Vollständig gelöste Punkte

1. Die wichtigsten Funktionen sind über eine einheitliche Startseite erreichbar.
2. Jede Auswahl besitzt eine kurze Funktionsbeschreibung.
3. Jede Auswahl nennt ihre tatsächliche Wirkung auf Index, Sicherung und Originaldateien.
4. Lesende Funktionen werden grün und schreibende Index-/Sicherungsfunktionen gelb markiert.
5. Farbe bleibt Zusatzinformation; Wirkung und Begründung stehen immer im Klartext.
6. Ungültige Auswahlnummern führen nicht zum Programmabbruch.
7. `q` bricht nur den aktuellen Dialog ab und kehrt sicher zum Menü zurück.
8. Ein geschlossenes Eingabemedium beendet die Startseite ohne Endlosschleife.
9. Tastaturabbruch wird kontrolliert mit eigenem Rückgabecode behandelt.
10. Der zuletzt verwendete Datenbank- und Ordnerpfad wird innerhalb der Sitzung vorgeschlagen.
11. Schreibende Indexaktionen benötigen eine ausdrückliche Ja/Nein-Bestätigung.
12. Der geplante Befehl wird vor der Ausführung lesbar angezeigt.
13. Pfade und Suchtexte werden als Argumentliste und nicht über eine Shell übergeben.
14. Leerzeichen und Sonderzeichen in Pfaden können dadurch keine zusätzlichen Befehle erzeugen.
15. Interaktive Leerstarts öffnen die Startseite.
16. Nicht-interaktive Leerstarts blockieren keine Skripte oder Umleitungen.
17. Bestehende direkte CLI-Befehle werden unverändert an die bisherige Befehlslogik weitergereicht.
18. Startlogik und Menülogik wurden außerhalb der bereits großen `cli.py` umgesetzt.
19. Ein-/Ausgabeströme und Befehlsausführung sind austauschbar und vollständig testbar.
20. Acht neue Tests decken Auswahl, Abbruch, Bestätigung, sichere Argumente und Nicht-Blockierung ab.
21. Der vollständige Stand besteht 39 Tests unter Python 3.10 und Python 3.12.

## Fachliche Entscheidungen

### Keine Shell-Auswertung

Die Startseite baut keine Befehlskette als ausführbaren Text. Sie übergibt eine feste Liste von Argumenten direkt an die vorhandene Python-CLI. Das reduziert Befehlseinschleusung, schützt Pfade mit Leerzeichen und vermeidet unnötige Unterprozesse.

### Startseite als eigener Programmeinstieg

Die bestehende `cli.py` enthält bereits viele Parser und Handler. Eine weitere interaktive Schicht direkt dort hätte Komplexität und Kopplung erhöht. `entrypoint.py` übernimmt deshalb nur die Startentscheidung; `terminal_home.py` enthält ausschließlich Menü und Dialoge.

### Schreibbestätigung nur dort, wo sie nötig ist

Lesende Funktionen starten nach der Eingabe direkt. Indexaufbau, Re-Scan und Sicherung zeigen zuerst den geplanten Befehl und benötigen dann eine zusätzliche Bestätigung. Dadurch bleibt die Bedienung schnell, ohne schreibende Wirkungen zu verstecken.

### Kein automatisches Menü in Skripten

Ein Aufruf ohne Argumente öffnet das Menü nur, wenn Eingabe und Ausgabe echte Terminals sind. In Pipelines, Tests oder Umleitungen erscheint stattdessen ein kurzer Hinweis. Das verhindert unbemerkte Warteschleifen in Automation.

### Restore und Reparatur nicht im einfachen Hauptmenü

Wiederherstellung und Reparatur wirken stärker auf die Indexdatenbank. Sie bleiben bewusst außerhalb des einfachen Hauptmenüs und werden weiterhin über direkte Befehle sowie ausführliche Wirkungsbeschreibungen angeboten.

## Codequalitätsbewertung

### Verbessert

- Verantwortung zwischen Einstieg, Menü und Fachbefehlen getrennt.
- Keine Erweiterung der bereits großen `cli.py`.
- Unveränderlicher Menükatalog als zentrale Quelle.
- Doppelte Auswahlnummern werden beim Start erkannt.
- Keine Shell- oder Subprozessabhängigkeit.
- Neue Dateien halten die konfigurierte Zeilenlänge ein.
- Testbare Ein-/Ausgabe ohne echte Dateioperationen.
- Bestehende Regressionstests bleiben vollständig grün.

### Weiter offen

- Die vorhandene `cli.py` sollte schrittweise nach Befehlsgruppen aufgeteilt werden.
- Ruff und MyPy sollten als verpflichtende CI-Schritte aktiviert werden.
- Eine zentrale Spezifikation könnte Menüeinträge, Hilfetexte und CLI-Unterbefehle künftig noch enger synchronisieren.
- Reale Bedienabnahmen in verschiedenen Linux-Terminals bleiben notwendig.

## Erkannte nächste Analysepunkte

1. Handler für Suche, Berichte, Verwaltung und Scans aus `cli.py` in getrennte Module verschieben.
2. Gemeinsame Rückgabecodes und Fehlermeldungen zentralisieren.
3. Ruff und MyPy in GitHub Actions aufnehmen.
4. CSV-Export der Ordnerübersicht ergänzen.
5. Favoriten für häufige Index- und Ordnerpfade sicher speichern.
6. Menütests gegen alle registrierten Aktionen automatisch erzeugen.
7. Startseite später als Grundlage einer grafischen Oberfläche verwenden.
8. Bedienabnahme mit vollständigen Linux-Laien durchführen.
9. Sehr große Bestände mit Millionen Dateien messen.
10. Restore und Reparatur in einem getrennten, besonders deutlich gewarnten Expertenbereich führen.

## Architektur-Fazit

Die Startseite verbessert die Laienbedienung, ohne den Sicherheitsvertrag zu erweitern. Sie ist nur eine geführte Schicht über den vorhandenen Befehlen. Originaldateien bleiben geschützt, und die neue Architektur verhindert, dass interaktive Bedienlogik die fachliche Indexlogik vermischt.
