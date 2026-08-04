# Schwachstellen und aktuelle Grenzen

## Ordnerübersicht

1. Die Ampel ist eine Priorisierungshilfe und keine Feststellung, dass Dateien beschädigt sind.
2. Ein kleiner Ordner mit nur einer auffälligen Datei kann wegen des hohen Anteils Rot erhalten. Die Begründung wird deshalb immer angezeigt.
3. Unterordner werden für Gesamtwerte absichtlich mehrfach in ihren Elternordnern mitgerechnet. Summen verschiedener Zeilen dürfen daher nicht einfach addiert werden.
4. Die Ordnerübersicht besitzt derzeit JSON- und HTML-Export, aber noch keinen CSV-Export.
5. Sehr tiefe Ordnerstrukturen können viele Ergebniszeilen erzeugen; `--max-depth` und Seiten begrenzen die Anzeige.

## Farben und Hilfen

6. Farben unterscheiden sich je nach Terminal und Farbprofil.
7. Terminalprogramme bieten keine verlässlichen Maus-Hover-Tooltips. Dort ersetzen Klartexthinweise und `datenbanktool explain` diese Funktion.
8. Farben dürfen nie allein interpretiert werden; deshalb bleiben Farbnamen, Status und Begründung zwingend sichtbar.
9. `--color always` erzeugt bewusst ANSI-Codes und sollte nicht für maschinenlesbare Textweitergabe verwendet werden. JSON-Ausgaben bleiben davon ausgenommen.

## Suchvorlagen

10. Vorlagen gelten derzeit lokal für einen Benutzer und werden noch nicht automatisch zwischen Rechnern übertragen.
11. Die Konfigurationsdatei ist JSON. Manuelle fehlerhafte Änderungen werden erkannt, aber noch nicht automatisch repariert.
12. Vorlagen speichern Filter, nicht die gewählte Datenbank. Dadurch bleiben sie portabel, benötigen beim Start aber weiterhin einen Indexpfad.
13. Gleichzeitiges Schreiben derselben Vorlagendatei durch mehrere Prozesse besitzt noch keinen eigenen Prozesslock; atomarer Dateiaustausch verhindert jedoch halbe Dateien.

## Allgemeine Projektgrenzen

14. Es gibt noch keine grafische Oberfläche mit Schaltflächen und nativen Tooltips.
15. Schreibende Originaldateioperationen sind weiterhin bewusst gesperrt.
16. Medieninhalte werden noch nicht als Vorschau angezeigt.
17. FTS5 durchsucht Metadaten, nicht automatisch den vollständigen Inhalt aller Dateien.
18. Der Entwicklungsstand ist Alpha und benötigt vor einem stabilen Release zusätzliche Last-, Bedien- und reale Datenträgertests.

## Sicherheitsfazit

Keine bekannte Grenze rechtfertigt das Freischalten automatischer Dateiänderungen. Analyse, Suche, Ordnerübersicht, Ampeln und Vorlagen bleiben von Originaldatei-Schreibzugriffen getrennt.
