# TODO

Stand: Version 0.13.0-alpha.1

## Offen

1. [ ] reale Laienabnahme,
2. [ ] `large`-Profil auf Zielhardware,
3. [ ] geführte Vorlagenverwaltung,
4. [ ] Mehrordner-Zeitreihe.

## Historisch erledigter MVP-Status

Der frühe SQLite-MVP ist abgeschlossen. Seine Punkte werden nicht mehr als aktuelle
Offenliste geführt, damit der Status nicht doppelt erscheint.

## In dieser Iteration erledigt

1. [x] Eigenständige Zeitreihen-Vorlagendomäne entwickeln.
2. [x] Nur Name, relativen Ordner, Beschreibung und Zeitstempel speichern.
3. [x] Datenbankpfade und Scan-Inhalte aus Vorlagen ausschließen.
4. [x] Relative Ordner über dieselbe Kernvalidierung wie Zeitreihen prüfen.
5. [x] Absolute Pfade und `..` ablehnen.
6. [x] Namen und Beschreibungen begrenzen und normalisieren.
7. [x] Vorlagendatei atomar mit Modus `0600` schreiben.
8. [x] Gleichnamige Vorlagen ohne `--replace` schützen.
9. [x] Löschen nur mit `--yes` zulassen.
10. [x] CLI-Befehle `list`, `show`, `save` und `delete` ergänzen.
11. [x] `folder-timeline --preset` und `--preset-file` ergänzen.
12. [x] Ordner und Vorlage als gegenseitig ausschließend validieren.
13. [x] Gespeicherte Vorlagen auf Startseitenpunkt 11 nummeriert anzeigen.
14. [x] Auswahl per Nummer oder exaktem Namen ermöglichen.
15. [x] Manuelle Eingabe bei leerer oder beschädigter Vorlagenliste erhalten.
16. [x] Startseitenpunkt 12 zum bestätigten Speichern ergänzen.
17. [x] Detail-, Schritt-, Feld- und Fehlerhilfe für Vorlagen ergänzen.
18. [x] Größenwachstum als optionale Prozent-Warnschwelle ergänzen.
19. [x] Dateizahlwachstum als optionale Prozent-Warnschwelle ergänzen.
20. [x] Nur positives Wachstum zum vorherigen sichtbaren Scan prüfen.
21. [x] Nicht endliche und unzulässige Schwellen ablehnen.
22. [x] Prozentwert bei vorherigem Wert null sicher leer lassen.
23. [x] Warnstatus von der normalen Verlaufsklassifikation trennen.
24. [x] Messwert, Schwelle und Klartextbegründung gemeinsam ausgeben.
25. [x] Rein lesenden Charakter und fehlende Schadensbewertung ausdrücklich nennen.
26. [x] Terminal um aktive Grenzen, Trefferzahl und Datei-Prozentwerte erweitern.
27. [x] JSON, CSV und HTML um Grenzen und Begründungen erweitern.
28. [x] SVG-Grenztreffer sichtbar mit `Warnung` und ARIA markieren.
29. [x] CLI-Architektur- und Seiteneffektverträge erweitern.
30. [x] Vorlagen-, Startseiten-, Schwellen-, Export- und Hilfetests ergänzen.
31. [x] 86/86 Tests unter Python 3.10 und 3.12 erfolgreich ausführen.
32. [x] Quick- und Standard-Abnahme mit jeweils 11/11 Kriterien ausführen.
33. [x] Version und Pflichtdokumentation auf 0.13.0-alpha.1 synchronisieren.

## Noch offen

1. [ ] reale Laienabnahme,
2. [ ] `large`-Profil auf Zielhardware,
3. [ ] geführte Vorlagenverwaltung,
4. [ ] Mehrordner-Zeitreihe.
