# Schwachstellen und aktuelle Grenzen

## Geführte Startseite

1. Die Startseite ist eine Terminaloberfläche und ersetzt noch keine grafische Anwendung mit Dateiauswahlfenstern und Schaltflächen.
2. Ordner- und Datenbankpfade müssen weiterhin als Text eingegeben oder eingefügt werden.
3. Der zuletzt verwendete Pfad wird nur während der laufenden Startseiten-Sitzung gemerkt und noch nicht dauerhaft gespeichert.
4. Restore und Reparatur stehen absichtlich nicht im einfachen Hauptmenü, weil sie stärkere Auswirkungen auf die Indexdatenbank haben. Sie bleiben über direkte Befehle und `explain` erreichbar.
5. Ein durch die bestehende CLI abgelehnter Befehl führt zurück ins Menü, nimmt aber noch keine automatische Fehlerkorrektur vor.
6. In nicht-interaktiven Umgebungen öffnet sich das Menü absichtlich nicht automatisch, damit Skripte und Weiterleitungen nicht hängen bleiben.

## Codequalität

7. Die zentrale `cli.py` ist mit vielen Unterbefehlen weiterhin groß. Die neue Startseite wurde deshalb außerhalb dieser Datei umgesetzt, aber die vorhandenen Handler sollten schrittweise in kleinere Module ausgelagert werden.
8. Menüaktionen und bestehende CLI-Unterbefehle sind über Argumentlisten gekoppelt. Änderungen an Befehlsnamen oder Pflichtargumenten benötigen passende Menütests.
9. Ruff und MyPy sind konfiguriert, werden in der aktuellen GitHub-Actions-Datei aber noch nicht als Pflichtprüfung ausgeführt.
10. Die Tests decken die geführten Dialoge mit simulierten Ein- und Ausgaben ab; eine zusätzliche manuelle Abnahme in mehreren realen Terminals bleibt sinnvoll.

## Ordnerübersicht

11. Die Ampel ist eine Priorisierungshilfe und keine Feststellung, dass Dateien beschädigt sind.
12. Ein kleiner Ordner mit nur einer auffälligen Datei kann wegen des hohen Anteils Rot erhalten. Die Begründung wird deshalb immer angezeigt.
13. Unterordner werden für Gesamtwerte absichtlich mehrfach in ihren Elternordnern mitgerechnet. Summen verschiedener Zeilen dürfen daher nicht einfach addiert werden.
14. Die Ordnerübersicht besitzt derzeit JSON- und HTML-Export, aber noch keinen CSV-Export.
15. Sehr tiefe Ordnerstrukturen können viele Ergebniszeilen erzeugen; `--max-depth` und Seiten begrenzen die Anzeige.

## Farben und Hilfen

16. Farben unterscheiden sich je nach Terminal und Farbprofil.
17. Terminalprogramme bieten keine verlässlichen Maus-Hover-Tooltips. Dort ersetzen Klartexthinweise und `datenbanktool explain` diese Funktion.
18. Farben dürfen nie allein interpretiert werden; deshalb bleiben Farbnamen, Status und Begründung zwingend sichtbar.
19. `--color always` erzeugt bewusst ANSI-Codes und sollte nicht für maschinenlesbare Textweitergabe verwendet werden. JSON-Ausgaben bleiben davon ausgenommen.

## Suchvorlagen

20. Vorlagen gelten derzeit lokal für einen Benutzer und werden noch nicht automatisch zwischen Rechnern übertragen.
21. Die Konfigurationsdatei ist JSON. Manuelle fehlerhafte Änderungen werden erkannt, aber noch nicht automatisch repariert.
22. Vorlagen speichern Filter, nicht die gewählte Datenbank. Dadurch bleiben sie portabel, benötigen beim Start aber weiterhin einen Indexpfad.
23. Gleichzeitiges Schreiben derselben Vorlagendatei durch mehrere Prozesse besitzt noch keinen eigenen Prozesslock; atomarer Dateiaustausch verhindert jedoch halbe Dateien.

## Allgemeine Projektgrenzen

24. Schreibende Originaldateioperationen sind weiterhin bewusst gesperrt.
25. Medieninhalte werden noch nicht als Vorschau angezeigt.
26. FTS5 durchsucht Metadaten, nicht automatisch den vollständigen Inhalt aller Dateien.
27. Der Entwicklungsstand ist Alpha und benötigt vor einem stabilen Release zusätzliche Last-, Bedien- und reale Datenträgertests.

## Sicherheitsfazit

Die Startseite senkt die Fehlbedienungsgefahr, erweitert aber keine Berechtigung. Originaldateien bleiben lesend, schreibende Indexaktionen werden klar angekündigt, und automatische Dateiänderungen bleiben gesperrt.
