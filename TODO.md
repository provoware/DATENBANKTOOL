# TODO

## In dieser Iteration erledigt

1. [x] Große `cli.py` in klar benannte Fachmodule aufteilen.
2. [x] Einmalige Scans nach `cli_scan.py` verschieben.
3. [x] Suche und Suchvorlagen nach `cli_search.py` verschieben.
4. [x] Ordner-, Änderungs- und Dateiberichte nach `cli_reports.py` verschieben.
5. [x] Indexverwaltung nach `cli_index.py` verschieben.
6. [x] Klassischen Erklärungsbefehl nach `cli_help.py` verschieben.
7. [x] Gemeinsame CLI-Hilfen in `cli_common.py` zentralisieren.
8. [x] `cli.py` auf Zusammensetzung, Dispatch und Fehlergrenze reduzieren.
9. [x] Bestehende Befehlsnamen und Parameter vollständig erhalten.
10. [x] Jeden öffentlichen Befehl mit einer `CommandPolicy` versehen.
11. [x] Originaldatei-Schreibzugriffe im CLI-Vertrag technisch sperren.
12. [x] Globale Regeln als `maintenance_rules.json` versionieren.
13. [x] Globale Regeln in `MAINTENANCE_RULES.md` laienverständlich erklären.
14. [x] Modulgrößen und Importgrenzen automatisch prüfen.
15. [x] Shell-Auswertung, `eval`, `exec` und `os.system` automatisch ausschließen.
16. [x] Handlerzuordnung und Rückgabecodevertrag automatisch prüfen.
17. [x] 54 automatisierte Tests unter Python 3.10 und 3.12 erfolgreich ausführen.

## Noch offen

1. [ ] Ordnerübersicht zusätzlich als CSV exportieren.
2. [ ] Ordnerwachstum zwischen zwei Scan-Sitzungen vergleichen.
3. [ ] Abnahme mit sehr großen realistischen Beständen und Linux-Laien durchführen.

## Direkt folgender einfacher Schritt

Die Ordnerübersicht als CSV speichern. Dateizahl, Gesamtgröße, Ampelgrund und größte
Platzfresser sollen direkt in LibreOffice Calc geöffnet werden können.

## Sichere Zusatzverbesserung

Einen rein lesenden Ordnervergleich ergänzen, der Wachstum und Rückgang zwischen zwei
abgeschlossenen Scan-Sitzungen verständlich anzeigt.
