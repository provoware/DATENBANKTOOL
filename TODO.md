# TODO

## In dieser Iteration erledigt

1. [x] Ordner-Zeitreihe über mehrere abgeschlossene Scans entwickeln.
2. [x] Relativen Ordner einschließlich Unterordnern auswerten.
3. [x] Dateizahl und Gesamtgröße je Scan darstellen.
4. [x] Datei- und Größendifferenz zum vorherigen Scan berechnen.
5. [x] Prozentuale Größenänderung mit Null-Ausgangswert sicher behandeln.
6. [x] Wachstum, Rückgang, Neu, Entfernt, Dateizahländerung und Unverändert erkennen.
7. [x] Scan-ID, UTC-Zeitpunkt und Scan-Modus ausgeben.
8. [x] Zeitraum über Ausgangs- und Zielsitzung begrenzen.
9. [x] Maximal 2 bis 500 Zeitpunkte über `--limit` zulassen.
10. [x] Unterschiedliche Stammordner kontrolliert ablehnen.
11. [x] Absolute Pfade und `..` im relativen Ordnerpfad ablehnen.
12. [x] Mindestens zwei abgeschlossene Scans verlangen.
13. [x] SQLite ausschließlich mit `mode=ro` und `query_only` öffnen.
14. [x] JSON-Bericht der Zeitreihe atomar erzeugen.
15. [x] Calc-kompatible CSV mit UTF-8-BOM und Semikolon erzeugen.
16. [x] Eigenständigen Offline-HTML-Bericht mit Tooltips und ARIA erzeugen.
17. [x] Vorhandene Berichte vor stillem Überschreiben schützen.
18. [x] Ordnervergleich um `--all-pages` erweitern.
19. [x] Alle gefilterten JSON-, CSV- und HTML-Zeilen vollständig exportieren.
20. [x] Terminalanzeige trotz vollständigem Vergleichsexport paginiert halten.
21. [x] Vergleichsergebnis nur einmal aggregieren und anschließend paginieren.
22. [x] `--all-pages` ohne Exportziel kontrolliert ablehnen.
23. [x] Handler, `CommandPolicy` und Modulzuständigkeit automatisch prüfen.
24. [x] Zeitreihen-, Sicherheits- und Vollständigkeitstests ergänzen.
25. [x] 71 Tests unter Python 3.10 und 3.12 erfolgreich ausführen.
26. [x] Quick-Abnahme mit 600 Dateien und 11/11 Kriterien erneut ausführen.
27. [x] Standard-Abnahme mit 10.000 Dateien und 11/11 Kriterien erneut ausführen.
28. [x] Finale Abnahmeberichte und Prüfsummen im Projektregister dokumentieren.

## Noch offen

1. [ ] Reale Laienabnahme auf einem Zielsystem durchführen und die erzeugte
   `NOVICE_ACCEPTANCE_CHECKLIST.md` durch eine unerfahrene Testperson ausfüllen lassen.

## Zusätzliche, nicht blockierende Zielsystemprüfung

- [ ] `large`-Profil mit 100.000 Dateien auf geeigneter Zielhardware ausführen und
  Referenzwerte dokumentieren.

## Direkt folgender technischer Entwicklungsschritt

Den Zeitreihenbefehl als eigenen Punkt in die geführte Startseite aufnehmen und mit
Detail-, Schritt-für-Schritt-, Feld- und Fehlerhilfe verbinden.

## Alternative Verbesserung mit hohem Nutzen und geringem Risiko

Den Offline-HTML-Bericht der Zeitreihe um zwei barrierefreie, lokal erzeugte
SVG-Liniengrafiken für Größe und Dateizahl ergänzen.
