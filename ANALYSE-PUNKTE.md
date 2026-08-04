# Analyse-Punkte

## Ergebnis dieser Iteration

Der bisherige CLI-Monolith wurde ohne sichtbare Befehlsänderung vollständig aufgeteilt. Parser und Ausführung liegen jetzt im jeweiligen Fachmodul. Gemeinsame Regeln, Sicherheitswirkungen und Größenlimits sind zentral definiert und werden automatisch geprüft.

## Vollständig gelöste Punkte

1. `cli.py` wurde von 1.409 auf rund 100 Zeilen reduziert.
2. Einmalige Scans besitzen ein eigenes CLI-Modul.
3. Suche und Suchvorlagen besitzen ein eigenes CLI-Modul.
4. Ordner-, Änderungs- und Dateiberichte besitzen ein eigenes CLI-Modul.
5. Indexaufbau, Re-Scan, Status, Sitzungen, Backup, Restore und Reparatur besitzen ein eigenes CLI-Modul.
6. Der klassische Erklärungsbefehl besitzt ein eigenes CLI-Modul.
7. Gemeinsame Validierer und Ausgabefunktionen liegen nur noch in `cli_common.py`.
8. Parser und Handler liegen jeweils im selben Fachmodul.
9. Ein zentraler Dispatch ersetzt die frühere große Befehlstabelle.
10. Jeder öffentliche Befehl besitzt eine maschinenlesbare `CommandPolicy`.
11. Originaldatei-Schreibzugriffe werden durch `CommandPolicy.validate()` technisch abgewiesen.
12. Handler müssen einen ganzzahligen Rückgabecode liefern.
13. Ungültige oder fehlende Handler werden kontrolliert abgefangen.
14. Bestehende Befehlsnamen und Parameter bleiben unverändert.
15. Globale Regeln sind als verständliches Dokument und JSON-Manifest vorhanden.
16. `cli.py` darf automatisch höchstens 150 Zeilen besitzen.
17. CLI-Fachmodule dürfen automatisch höchstens 500 Zeilen besitzen.
18. Zyklische Importe zurück zu `cli.py` werden geprüft.
19. `subprocess`, `os.system`, `eval`, `exec` und `shell=True` werden in CLI-Fachmodulen geprüft.
20. Die fachliche Modulzuständigkeit ausgewählter Befehle wird getestet.
21. Alle öffentlichen Parser werden auf Handler und Richtlinie geprüft.
22. Sämtliche bisherigen Regressionstests bleiben grün.
23. 54 Tests laufen unter Python 3.10 und 3.12 erfolgreich.
24. Externe Laufzeitabhängigkeiten bleiben bei null.

## Zentrale Architekturentscheidungen

### Parser und Handler zusammenhalten

Ein Parser ohne nahegelegene Ausführungsfunktion erschwert Änderungen und führt schnell zu widersprüchlichen Parametern. Jedes Fachmodul registriert deshalb seine Parser und bindet dort unmittelbar den passenden Handler.

### Dünner zentraler Einstieg

`cli.py` kennt nur die Reihenfolge der Fachbereiche, globale Anzeigeoptionen, den Dispatch und die zentrale Fehlergrenze. Fachliche Datenbank-, Such- oder Berichtsfunktionen dürfen nicht wieder dorthin zurückwandern.

### Seiteneffekte als Datenmodell

Die Wirkung eines Befehls ist nicht mehr nur Dokumentation. `CommandPolicy` beschreibt Lese- und Schreibwirkungen maschinenlesbar. Dadurch können spätere Startseiten, Hilfetexte und Sicherheitsprüfungen dieselbe Quelle verwenden.

### Konservative Sicherheitsangaben

Ein Befehl mit optionalem Schreibmodus wird in der Richtlinie als potenziell schreibend eingestuft. Das verhindert eine irreführende grüne Einstufung, auch wenn der konkrete Aufruf rein lesend bleibt.

### Regeln automatisch absichern

Nur dokumentierte Regeln werden mit der Zeit leicht übergangen. Deshalb enthält `maintenance_rules.json` maschinenlesbare Limits, während `test_cli_architecture.py` die wichtigsten davon bei jedem CI-Lauf erzwingt.

## Erkannte nächste Analysepunkte

1. CSV-Export für die Ordnerübersicht ergänzen.
2. Ordnerwachstum zwischen zwei abgeschlossenen Sitzungen berechnen.
3. `cli_search.py` bei der nächsten größeren Funktion in Suche und Vorlagen trennen.
4. `cli_index.py` bei zusätzlichen Verwaltungsbefehlen in Scanverwaltung und Administration trennen.
5. `CommandPolicy` später direkt für automatische Hilfetexte und Startseitenampeln verwenden.
6. Stärker typisierte Befehlsargumente als mögliche spätere Qualitätsstufe prüfen.
7. Reale Großbestände und Bedienwege mit Linux-Laien abnehmen.
8. Regeln für Core-Modulgrößen und Komplexität ergänzen, sobald belastbare Grenzwerte vorliegen.

## Fazit

Die größte bekannte Wartbarkeitsschwäche der Kommandozeilenoberfläche ist behoben. Änderungen können jetzt fachlich begrenzt vorgenommen werden, während automatische Prüfungen verhindern, dass erneut ein unkontrollierter Monolith, Shell-Auswertung oder Originaldatei-Schreibzugriff entsteht.
