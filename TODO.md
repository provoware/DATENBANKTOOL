# TODO

## In dieser Iteration erledigt

1. [x] Normale Ordnerübersicht als CSV exportieren.
2. [x] UTF-8-BOM und Semikolon für LibreOffice Calc verwenden.
3. [x] Ampelstufe, Status und Begründung getrennt ausgeben.
4. [x] Direkte und rekursive Dateizahlen ausgeben.
5. [x] Direkte und rekursive Bytegrößen ausgeben.
6. [x] Namenshinweise und Duplikatzahlen ausgeben.
7. [x] Platzfresser als stabile Pfad-/Byte-Spalten ausgeben.
8. [x] CSV atomar schreiben.
9. [x] Vorhandene CSV ohne Freigabe schützen.
10. [x] Vollständigen Export mit `--all-pages` ergänzen.
11. [x] Terminalanzeige trotz vollständigem Export paginiert halten.
12. [x] Vollständigkeitsprüfung über mehr als 25 Ordner testen.
13. [x] Reproduzierbare Abnahmeprofile quick, standard und large anlegen.
14. [x] Synthetische Testdaten strikt in neuem Arbeitsordner erzeugen.
15. [x] Vorhandene Arbeitsordner sicher ablehnen.
16. [x] Laufzeit- und Phasenmessung ergänzen.
17. [x] Python-Spitzenspeicher und Prozess-RSS erfassen.
18. [x] Quelldaten-Manifest vor und nach dem Lauf vergleichen.
19. [x] Elf automatische Abnahmekriterien definieren.
20. [x] JSON- und Markdown-Abnahmebericht erzeugen.
21. [x] Reale Laien-Checkliste mit Aufgaben und Kriterien erzeugen.
22. [x] Laienstatus ehrlich als `pending-real-person` kennzeichnen.
23. [x] Quick-Profil mit 600 Dateien in GitHub Actions ausführen.
24. [x] Standard-Profil mit 10.000 Dateien in GitHub Actions ausführen.
25. [x] Quick- und Standardberichte als Artefakte archivieren.
26. [x] 66 Tests unter Python 3.10 und 3.12 erfolgreich ausführen.

## Noch offen

1. [ ] Reale Laienabnahme auf einem Zielsystem durchführen und die erzeugte
   `NOVICE_ACCEPTANCE_CHECKLIST.md` durch eine unerfahrene Testperson ausfüllen lassen.

## Zusätzliche, nicht blockierende Zielsystemprüfung

- [ ] `large`-Profil mit 100.000 Dateien auf geeigneter Zielhardware ausführen und
  Referenzwerte dokumentieren.

## Direkt folgender technischer Entwicklungsschritt

Eine rein lesende Ordner-Zeitreihe entwickeln, die Größe und Dateizahl eines Ordners
über mehrere abgeschlossene Scans verständlich darstellt.

## Alternative Verbesserung mit hohem Nutzen und geringem Risiko

Den Ordnervergleich um `--all-pages` erweitern, damit JSON, CSV und HTML auf Wunsch
sämtliche gefilterten Vergleichszeilen enthalten.
