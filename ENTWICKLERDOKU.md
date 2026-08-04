# Entwicklerdokumentation

## Architekturstand 0.8.0-alpha.1

Die Kommandozeilenoberfläche ist vollständig in klar begrenzte Fachmodule aufgeteilt.
Die sichtbaren Befehle und Parameter bleiben unverändert.

```text
entrypoint.py
    entscheidet zwischen direktem Befehl, Startseite und mehrschichtiger Hilfe

cli.py
    globale Parseroptionen, Zusammensetzung der Fachparser,
    zentraler Dispatch und kontrollierte Fehlergrenze

cli_contract.py
    CommandPolicy, Handlerbindung und Rückgabecodeprüfung

cli_common.py
    gemeinsame Eingabevalidierung, Parserbausteine,
    Größenformatierung, Fortschritt und atomare JSON-Ausgabe

cli_scan.py
    einmaliger rein lesender Scan

cli_search.py
    Suche, optionaler FTS5-Aufbau und Suchvorlagen

cli_reports.py
    Ordnerübersicht, Änderungsberichte und allgemeine Dateiberichte

cli_index.py
    Indexaufbau, Re-Scan, Status, Sitzungen,
    Backup, Restore und Reparatur

cli_help.py
    kompatibler Befehl datenbanktool explain

help_command.py
    eigenständige mehrschichtige Hilfe datenbanktool help
```

`cli.py` wurde von 1.409 auf rund 100 Zeilen reduziert. Fachlogik darf nicht wieder
in den zentralen Einstieg verschoben werden.

## Registrierungsvertrag

Jeder Fachparser wird im zuständigen Modul angelegt und dort unmittelbar mit seinem
Handler verbunden:

```python
bind_handler(parser, handler, CommandPolicy(...))
```

Dadurch liegen zusammen:

- sichtbare Befehlsbeschreibung,
- Argumentdefinitionen,
- Ausführungsfunktion,
- Lese- und Schreibwirkung,
- Rückgabecodevertrag.

Der zentrale Einstieg kennt nur die Reihenfolge, in der Fachmodule ihre Parser
registrieren. Er enthält keine Such-, Scan-, Berichts- oder Datenbanklogik.

## `CommandPolicy`

`CommandPolicy` beschreibt maschinenlesbar:

- Befehlsname,
- Lesen gescannter Originaldateien,
- Schreiben gescannter Originaldateien,
- Schreiben des SQLite-Indexes,
- Schreiben von Berichten,
- Schreiben von Sicherungen,
- Schreiben von Benutzerkonfigurationen.

### Sicherheitsprüfung

`CommandPolicy.validate()` weist jede Richtlinie mit
`writes_original_files=True` sofort ab. Damit kann kein neuer CLI-Befehl still als
Originaldatei-Schreiber registriert werden.

Optionale Schreibmöglichkeiten werden konservativ deklariert. Die Suche besitzt zum
Beispiel einen möglichen Indexschreibzugriff, weil `--build-fulltext-index` den
optionalen FTS5-Metadatenindex aufbauen kann. Ein normaler Suchaufruf bleibt dennoch
rein lesend.

## Zentraler Dispatch

`dispatch(arguments)` prüft vor der Ausführung:

1. Ein aufrufbarer Handler ist registriert.
2. Eine gültige `CommandPolicy` ist vorhanden.
3. Die Sicherheitsrichtlinie erlaubt keinen Originaldatei-Schreibzugriff.
4. Der Handler liefert einen echten ganzzahligen Rückgabecode.
5. Der Rückgabecode liegt zwischen 0 und 255.

Vereinbarte Rückgabecodes:

- `0`: erfolgreich,
- `1`: fachlich abgeschlossen, aber unvollständig oder mit erkannten Problemen,
- `2`: kontrollierter Eingabe-, Datei-, SQLite- oder Sicherheitsfehler.

Die zentrale Fehlergrenze in `cli.py` behandelt weiterhin:

- fehlende Dateien oder Ordner,
- vorhandene geschützte Zieldateien,
- SQLite-Fehler,
- gesperrte Indexprozesse,
- Fach- und Validierungsfehler.

## Modulzuständigkeiten

### `cli_scan.py`

Enthält ausschließlich:

- Parserregistrierung für `datenbanktool scan`,
- Aufbau von `ScanOptions`,
- Terminalausgabe des Ergebnisses,
- optionalen atomaren JSON-Bericht.

### `cli_search.py`

Enthält:

- `index search`,
- Zusammenführung direkter Suchwerte mit Suchvorlagen,
- optionalen FTS5-Aufbau,
- Darstellung gefundener Dateien,
- `index presets list|show|save|delete`.

Das Modul liegt nahe am globalen Höchstwert von 500 Zeilen. Bei der nächsten größeren
Such- oder Vorlagenfunktion wird es in getrennte Module geteilt.

### `cli_reports.py`

Enthält:

- `index folders`,
- `index changes`,
- `report`,
- Parser und Ausführung der zugehörigen JSON-, CSV- und HTML-Ausgaben.

Die zugrunde liegende Fachlogik bleibt weiterhin in den Core-Modulen. Das CLI-Modul
übersetzt ausschließlich Argumente und präsentiert Ergebnisse.

### `cli_index.py`

Enthält:

- `index build`,
- `index rescan`,
- `index status`,
- `index sessions`,
- `index backup`,
- `index restore`,
- `index repair`.

Zusätzliche größere Verwaltungsfunktionen lösen künftig eine weitere Teilung in
Scanverwaltung und Indexadministration aus.

### `cli_common.py`

Gemeinsam genutzt werden ausschließlich stabile Querschnittsfunktionen:

- positive und nichtnegative Zahlenvalidierung,
- Dateikategorien und Änderungsbezeichnungen,
- gemeinsame Scan- und Fortschrittsoptionen,
- Farbmodus und Bedienhinweise,
- Fortschrittsereignisse,
- menschenlesbare Dateigrößen,
- atomare JSON-Ausgabe.

Fachentscheidungen gehören nicht in dieses Modul.

## Globale Wartungsregeln

Die verständliche Fassung liegt in:

```text
MAINTENANCE_RULES.md
```

Die maschinenlesbare Fassung liegt in:

```text
maintenance_rules.json
```

Das JSON-Manifest ist versioniert und enthält:

- eindeutige Regelkennungen,
- Anforderungen,
- vorgesehene Prüfmechanismen,
- Modulgrößenlimits,
- verbotene CLI-Aufrufsmuster,
- Zielwert für externe Laufzeitabhängigkeiten.

### Erzwungene Kernregeln

1. Öffentliche Befehle bleiben kompatibel.
2. Parser und Handler liegen im selben Fachmodul.
3. CLI-Fachmodule importieren nicht zurück aus `cli.py`.
4. Jeder öffentliche Befehl besitzt eine Seiteneffektrichtlinie.
5. Originaldatei-Schreibzugriffe bleiben gesperrt.
6. Ersetzbare Dateien werden atomar geschrieben.
7. Vorhandene Ziele werden nicht still überschrieben.
8. Shell-Auswertung, `eval`, `exec` und `os.system` sind verboten.
9. Maschinenformate bleiben frei von ANSI-Codes und Bedienhinweisen.
10. `cli.py` bleibt unter 150 Zeilen.
11. CLI-Fachmodule bleiben unter 500 Zeilen.
12. Änderungen erhalten vollständige Regressionstests.
13. Pflichtdokumente und Registry werden gemeinsam aktualisiert.
14. Neue Laufzeitabhängigkeiten benötigen eine dokumentierte Begründung.

Nicht jede textliche Regel lässt sich vollständig automatisieren. Deshalb ergänzen
sich maschinenlesbare Prüfungen und dokumentierte Reviewpflichten.

## Architekturtests

`tests/test_cli_architecture.py` prüft:

1. Regelmanifest, Version und eindeutige Regelkennungen.
2. Zeilenlimits für zentralen Einstieg und Fachmodule.
3. Verbotene Importe und Shell-Ausführungsfunktionen über den Python-AST.
4. Handler- und `CommandPolicy`-Registrierung aller öffentlichen Befehle.
5. Technische Ablehnung einer Originaldatei-Schreibrichtlinie.
6. Zuständigkeit ausgewählter Befehle für das vorgesehene Fachmodul.

Diese Prüfungen laufen bei jedem GitHub-Actions-Durchlauf unter Python 3.10 und 3.12.

## Rückwärtskompatibilität

Unverändert bleiben unter anderem:

```text
datenbanktool scan
datenbanktool report
datenbanktool explain
datenbanktool index build
datenbanktool index rescan
datenbanktool index status
datenbanktool index sessions
datenbanktool index search
datenbanktool index folders
datenbanktool index changes
datenbanktool index presets
datenbanktool index backup
datenbanktool index restore
datenbanktool index repair
```

Auch globale Optionen wie `--color` und `--hints` bleiben an derselben Position und
mit derselben Wirkung erhalten. Die Startseite ruft weiterhin `cli.main()` mit einer
strukturierten Argumentliste auf.

## Schreib- und Ausgabegrundsätze

- Scan und Suche lesen Originaldateien beziehungsweise Indexdaten nur im vorgesehenen
  Modus.
- Berichte und Konfigurationen werden atomar freigegeben.
- Überschreiben benötigt eine ausdrückliche Option.
- JSON-Ausgaben enthalten keine Farben oder Bedienhinweise.
- Fortschritts-JSONL wird auf `stderr` ausgegeben.
- Startseite und direkte CLI führen keine Shell-Zeichenkette aus.
- Automatisches Löschen, Verschieben und Umbenennen bleibt nicht verfügbar.

## Automatische Prüfungen

```bash
python -m compileall -q src tests
PYTHONWARNINGS=error python -m unittest discover -s tests -v
```

Aktueller Gesamtstand:

- Python 3.10: 54 von 54 Tests erfolgreich,
- Python 3.12: 54 von 54 Tests erfolgreich,
- Warnungen werden als Fehler behandelt,
- sechs zusätzliche Architekturprüfungen,
- keine externe Laufzeitabhängigkeit.

## Bekannte technische Grenzen

- `cli_search.py` und `cli_index.py` liegen nahe am Fachmodullimit und müssen bei
  größeren Erweiterungen weiter aufgeteilt werden.
- `argparse.Namespace` ist dynamisch; streng typisierte Befehlsmodelle könnten später
  zusätzliche statische Sicherheit bieten.
- Statische AST-Prüfungen ersetzen keine manuelle fachliche Sicherheitsprüfung.
- Das Regelmanifest kann Dokumentationssynchronität nicht vollständig automatisch
  garantieren.
- Ordnerübersichten besitzen noch keinen CSV-Export.
- Ordnerwachstum zwischen zwei Sitzungen wird noch nicht direkt berechnet.
- Vor einem stabilen Release fehlen reale Großbestands- und Laienabnahmen.

## Nächster einfacher Entwicklungsblock

Die Ordnerübersicht zusätzlich als CSV exportieren. Die Tabelle soll Dateizahl,
Gesamtgröße, Ampelstufe, Ampelgrund und größte Platzfresser enthalten und denselben
Filter-, Sortier- und Überschreibschutz wie Terminal, JSON und HTML verwenden.

## Sichere Zusatzverbesserung

Einen rein lesenden Ordnervergleich zwischen zwei abgeschlossenen Scan-Sitzungen
entwickeln. Er zeigt Wachstum und Rückgang, ohne Originaldateien oder bestehende
Snapshots zu verändern.

## Unverändert

`AGENTS.md` wird nicht verändert. Originaldatei-Schreibfunktionen bleiben bis zu
einem separaten versionierten Sicherheitsvertrag gesperrt.
