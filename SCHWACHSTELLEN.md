# Schwachstellen und aktuelle Grenzen

## Ordner-CSV

1. Ohne `--all-pages` enthält ein Bericht weiterhin nur die gewählte Seite. Das ist
   rückwärtskompatibel, muss aber bewusst beachtet werden.
2. Elternordner enthalten die Summen ihrer Unterordner. Tabellenzeilen dürfen daher
   nicht addiert werden, sonst werden Dateien mehrfach gezählt.
3. Leere Ordner ohne Dateien können nicht erscheinen, weil das aktuelle Schema
   Dateieinträge und keine eigenständige Verzeichnisliste speichert.
4. Die Anzahl der Platzfresser-Spalten richtet sich nach `--top-files`. Unterschiedlich
   konfigurierte Exporte können deshalb unterschiedlich viele Spalten besitzen.
5. Rohgrößen werden in Byte ausgegeben. Für MiB oder GiB muss LibreOffice eine Formel
   oder Zellformatierung verwenden.
6. CSV speichert keine Farben. Ampelstufe, Status und Begründung stehen deshalb als
   getrennte Textspalten bereit.

## Automatische Großbestandsabnahme

7. Die erzeugten Dateien sind synthetisch. Sie decken viele Namen, Endungen und Größen
   ab, aber nicht sämtliche Eigenschaften realer Datenbestände.
8. Sparse-Dateien sparen physischen Speicher und testen Metadaten- und Indexleistung.
   Sie simulieren nicht vollständig die Leselast real gefüllter Mediendateien.
9. `tracemalloc` misst Python-Speicher, nicht jede native SQLite- oder Betriebssystem-
   Allokation. Deshalb wird zusätzlich Prozess-Maximal-RSS protokolliert, aber nur der
   Python-Wert besitzt derzeit eine harte Profilgrenze.
10. Laufzeitwerte hängen von Dateisystem, CPU, Datenträger, Cache und CI-Auslastung ab.
    Die Referenzwerte sind keine Garantie für andere Systeme.
11. Das `large`-Profil mit 100.000 Dateien ist implementiert, aber noch nicht auf der
    vorgesehenen Zielhardware ausgeführt.
12. Die Abnahme erzeugt viele Dateisystemeinträge. Vor `standard` oder `large` müssen
    ausreichend freie Inodes und Speicher vorhanden sein.
13. Ein fehlgeschlagener Lauf löscht seinen Arbeitsordner nicht automatisch. Das ist
    absichtlich sicher, erfordert aber eine spätere manuelle Prüfung und Bereinigung.
14. Die Abnahme nutzt einen neuen Arbeitsordner und lehnt Wiederverwendung vollständig
    ab. Ein Fortsetzen abgebrochener Abnahmen ist noch nicht vorgesehen.
15. Die CI archiviert Berichte 14 Tage; danach können die Artefakte ablaufen.

## Reale Laienabnahme

16. Eine echte Laienabnahme wurde noch nicht durchgeführt.
17. Die generierte Checkliste standardisiert Aufgaben und Kriterien, ersetzt aber weder
    Beobachtung noch Rückfragen einer realen Testperson.
18. Die Checkliste ist deutschsprachig und bislang nicht als interaktiver Assistent
    umgesetzt.
19. Nutzerzeiten und Bewertungen werden manuell eingetragen und noch nicht automatisch
    in ein Ergebnis-JSON übernommen.

## Ordnervergleich und Bedienung

20. Der Ordnervergleich wertet genau zwei Sitzungen aus; eine Zeitreihe fehlt.
21. Vergleichsexporte enthalten die aktuelle Seite und besitzen noch keinen eigenen
    `--all-pages`-Schalter.
22. Die Oberfläche bleibt terminalbasiert und nutzt noch keine grafischen Pfaddialoge.
23. Hilfetexte sind deutschsprachig; die Stichwortsuche ist deterministisch und nicht
    semantisch.
24. Schreibende Originaldateioperationen bleiben gesperrt.

## Sicherheitsfazit

CSV-Export und Abnahme verändern keine gescannten Originaldateien. Testdaten entstehen
nur in einem neuen Arbeitsordner; ein vorhandener Pfad wird abgelehnt. Ein
Vorher-/Nachher-Manifest prüft die erzeugten Quelldaten. Berichte werden atomar und
überschreibgeschützt geschrieben. Keine bekannte Grenze rechtfertigt das Freischalten
automatischer Lösch-, Verschiebe- oder Umbenennungsfunktionen.
