# TODO

## In dieser Iteration erledigt

1. [x] Ordner-Zeitreihe als eigenen Startseitenpunkt 11 aufnehmen.
2. [x] Indexdatenbank im geführten Dialog auswählen.
3. [x] Relativen Ordner oder `.` verständlich abfragen.
4. [x] Älteste und neueste Scan-ID optional abfragen.
5. [x] Zeitpunkte vor dem Start auf 2 bis 500 validieren.
6. [x] Berichtsauswahl auf kein, JSON, CSV oder HTML begrenzen.
7. [x] Berichtspfad mit eigener Feldhilfe abfragen.
8. [x] Geplanten Zeitreihenbefehl sichtbar anzeigen.
9. [x] Sichere Argumentliste ohne Shell-Auswertung verwenden.
10. [x] Detailhilfe über `?11` verbinden.
11. [x] Schritt-für-Schritt-Hilfe über `g11` verbinden.
12. [x] Feldhilfe über `?` für jede neue Eingabe ergänzen.
13. [x] Zeitreihenspezifische Fehlerhilfe ergänzen.
14. [x] Eigenständiges Hilfethema `folder-timeline` integrieren.
15. [x] Hilfesuche nach Verlauf und Speicherentwicklung ergänzen.
16. [x] Größenverlauf als lokales SVG-Liniendiagramm erzeugen.
17. [x] Dateizahlverlauf als lokales SVG-Liniendiagramm erzeugen.
18. [x] SVG-`title`, `desc` und `aria-labelledby` ergänzen.
19. [x] Datenpunkte mit Tastaturfokus und `aria-label` versehen.
20. [x] Achsen-, Scan- und Wertbeschriftungen sichtbar darstellen.
21. [x] Minimum, Maximum und Nettoänderung textlich zusammenfassen.
22. [x] Vollständige Wertetabelle unter den Diagrammen erhalten.
23. [x] Lange Zeitreihen durch reduzierte sichtbare Beschriftung entzerren.
24. [x] JavaScript und externe HTML-Ressourcen vollständig vermeiden.
25. [x] Responsive Darstellung und sichtbare Fokusmarkierung ergänzen.
26. [x] Menü-, Dialog- und Validierungstests ergänzen.
27. [x] Detail-, Schritt-, Feld- und Fehlerhilfetests ergänzen.
28. [x] SVG-, ARIA-, Offline- und Skriptfreiheitstests ergänzen.
29. [x] 77 Tests unter Python 3.10 und 3.12 erfolgreich ausführen.
30. [x] Quick-Abnahme mit 600 Dateien und 11/11 Kriterien ausführen.
31. [x] Standard-Abnahme mit 10.000 Dateien und 11/11 Kriterien ausführen.
32. [x] Version und Pflichtdokumentation auf 0.12.0-alpha.1 synchronisieren.

## Noch offen

1. [ ] Reale Laienabnahme auf einem Zielsystem durchführen und die erzeugte
   `NOVICE_ACCEPTANCE_CHECKLIST.md` durch eine unerfahrene Testperson ausfüllen lassen.

## Zusätzliche, nicht blockierende Zielsystemprüfung

- [ ] `large`-Profil mit 100.000 Dateien auf geeigneter Zielhardware ausführen und
  Referenzwerte dokumentieren.

## Direkt folgender technischer Entwicklungsschritt

Zeitreihen-Vorlagen entwickeln: häufig geprüfte relative Ordnerpfade lokal, validiert
und überschreibgeschützt speichern und in der geführten Startseite auswählen.

## Alternative Verbesserung mit hohem Nutzen und geringem Risiko

Optionale rein lesende Trendgrenzen für starkes Größen- oder Dateiwachstum ergänzen und
im Terminal sowie HTML immer mit Klartext und Begründung anzeigen.
