# Entwicklerdokumentation

## Architekturstand 0.6.0-alpha.1

Der Datenkern, die Präsentation und der Programmeinstieg sind getrennt:

1. Scanner und Indexaufbau.
2. Inkrementeller Snapshotvergleich.
3. Rein lesende Suche und Berichte.
4. Rein lesende Ordneraggregation.
5. Externe Suchvorlagen-Konfiguration.
6. Zentrale Präsentationsschicht für Farben und Ampeln.
7. Zentrale Hilfetexte für Zweck und Auswirkung.
8. Bestehende argparse-CLI mit Fachhandlern.
9. Neuer schmaler Programmeinstieg.
10. Neue geführte Terminal-Startseite.

Originaldatei-Schreibfunktionen bleiben außerhalb dieser Architektur.

## Neuer Programmeinstieg

### `entrypoint.py`

Der installierte Konsolenbefehl verweist jetzt auf:

```text
datenbanktool.entrypoint:main
```

Der Einstieg besitzt nur drei Aufgaben:

1. `datenbanktool start` an die geführte Startseite weiterleiten.
2. Einen leeren interaktiven Aufruf ebenfalls an die Startseite weiterleiten.
3. Alle anderen Argumente unverändert an `datenbanktool.cli.main()` übergeben.

Nicht-interaktive Aufrufe ohne Argumente öffnen kein Menü. Sie geben einen kurzen Nutzungshinweis aus und kehren zurück. Damit entstehen in Pipelines, Tests und umgeleiteten Ein-/Ausgaben keine unbeabsichtigten Warteschleifen.

Auch `python -m datenbanktool` verwendet den neuen Einstiegspunkt.

## Geführte Startseite

### `core/terminal_home.py`

Das Modul enthält keine Scanner-, SQLite- oder Berichtslogik. Es baut ausschließlich sichere Argumentlisten für bereits vorhandene CLI-Befehle.

Zentrale Typen:

- `MenuAction`: unveränderliche Beschreibung einer auswählbaren Funktion.
- `HomeSession`: merkt Datenbank- und Ordnerpfad innerhalb einer laufenden Menüsitzung.
- `TerminalHome`: rendert Menü, validiert Eingaben und ruft den injizierten `command_runner` auf.
- `InputClosed`: kontrolliertes Ende bei geschlossenem Eingabestrom.
- `UserCancelled`: Rückkehr zum Hauptmenü bei `q` oder `abbrechen`.

### Menükatalog

Der Katalog ist ein unveränderliches Tupel. Jeder Eintrag besitzt:

- eindeutige Nummer,
- Titel,
- kurze Beschreibung,
- Ampelstufe,
- Wirkungsbezeichnung,
- konkrete Wirkungsbegründung,
- internen Buildernamen,
- Kennzeichen für zusätzliche Bestätigung.

Beim Erzeugen einer `TerminalHome`-Instanz werden doppelte Auswahlnummern erkannt.

### Aktuelle Aktionen

```text
1 Suche
2 Ordnerübersicht
3 Änderungen
4 Indexstatus
5 Indexaufbau
6 Re-Scan
7 Sicherung
8 Suchvorlagen
9 Hilfe
0 Beenden
```

Restore und Reparatur sind absichtlich nicht Teil des einfachen Hauptmenüs. Sie besitzen stärkere Auswirkungen auf die Indexdatenbank und bleiben über direkte Befehle sowie `datenbanktool explain` verfügbar.

## Sicherheitsvertrag der Startseite

### Keine Shell-Auswertung

Die Startseite verwendet weder `subprocess` noch `shell=True`. Sie erzeugt zum Beispiel:

```python
["index", "search", "/pfad/mit leerzeichen/index.sqlite3", "urlaub bilder"]
```

Diese Liste wird direkt an `cli.main()` übergeben. Der angezeigte Text wird nur mit `shlex.join()` formatiert und niemals ausgeführt.

Folgen:

- Leerzeichen bleiben Teil eines Arguments.
- Shell-Metazeichen erzeugen keinen zweiten Befehl.
- Kein unnötiger Unterprozess.
- Bestehende Parser- und Validierungsregeln bleiben verbindlich.

### Bestätigungsschutz

Folgende Aktionen benötigen nach der Befehlsvorschau eine zusätzliche Ja/Nein-Bestätigung:

- Index neu aufbauen,
- Re-Scan starten,
- Sicherung erstellen.

Lesende Funktionen starten ohne zweite Bestätigung. Dadurch bleibt die Bedienung schnell und die Wirkung trotzdem transparent.

### Abbruchverhalten

- `q`, `quit`, `abbrechen`, `zurück` und `zurueck` brechen den aktuellen Dialog ab.
- Ungültige Menünummern zeigen einen Fehler und wiederholen das Menü.
- Ein geschlossener Eingabestrom beendet die Startseite mit Rückgabecode 0.
- `KeyboardInterrupt` beendet sie kontrolliert mit Rückgabecode 130.
- Ein Fachbefehl mit Rückgabecode ungleich 0 führt nicht zum Absturz der Startseite.

## Testbarkeit

`TerminalHome` erhält vier Abhängigkeiten von außen:

- `command_runner`,
- `input_stream`,
- `output_stream`,
- `error_stream`.

Dadurch können Menüabläufe vollständig mit `StringIO` und einem aufzeichnenden Stub getestet werden. Die Tests erzeugen keine echte Indexdatenbank und führen keine Dateioperationen aus.

Neu geprüfte Fälle:

1. eindeutige Menünummern,
2. ungültige Auswahl,
3. sichere Suche mit Leerzeichen in Pfad und Suchtext,
4. Abbruch einer schreibenden Aktion,
5. bestätigter Indexaufbau,
6. geschlossener Eingabestrom,
7. nicht-interaktiver Leerstart ohne Blockierung,
8. ausdrücklicher Start und sofortiges Beenden.

Der vollständige Stand besteht 39 Tests unter Python 3.10 und Python 3.12 mit `PYTHONWARNINGS=error`.

## Bestehende Module

### `core/folders.py`

- Öffnet SQLite über URI `mode=ro`.
- Aktiviert `PRAGMA query_only`.
- Aggregiert direkte und rekursive Ordnerwerte.
- Liefert größte Dateien, Ampelwerte, Seiten und JSON-/HTML-Export.

### `core/presentation.py`

Zentrale Ausgabe für:

- ANSI-Farben,
- Ampeltext,
- Statusfarben,
- Änderungsarten,
- Bedienhinweise.

Farbmodi:

- `auto`,
- `always`,
- `never`.

Farben sind nie das einzige Signal.

### `core/presets.py`

- versionierte JSON-Struktur,
- strikte Filtervalidierung,
- atomisches Schreiben,
- Ersetzen nur mit ausdrücklicher Freigabe,
- bestätigtes Löschen in der CLI.

### `core/help_system.py`

Jedes `HelpTopic` enthält:

- Titel,
- Zweck,
- Wirkung,
- geschriebene Daten,
- Risiko,
- geeigneten Anwendungsfall,
- Beispiel.

Neu hinzugekommen ist das Thema `start`.

## Codequalitätsentscheidung

Die Startseite wurde nicht in die bereits große `cli.py` integriert. Dadurch:

- wächst die zentrale Parserdatei nicht weiter,
- kann interaktive Logik unabhängig getestet werden,
- bleiben bestehende Handler unverändert,
- bleibt der Programmeinstieg klein,
- können künftige GUI- oder TUI-Oberflächen denselben Fachkern verwenden.

Offen bleibt die schrittweise Zerlegung von `cli.py` nach Befehlsgruppen. Vorgeschlagene Zielmodule:

```text
commands/scan_commands.py
commands/search_commands.py
commands/report_commands.py
commands/admin_commands.py
commands/preset_commands.py
```

Eine zentrale Handlerregistrierung sollte anschließend Unterbefehle, Hilfetexte und Rückgabecodes zusammenführen.

## Qualitätsprüfungen

```bash
python -m compileall -q src tests
PYTHONWARNINGS=error python -m unittest discover -s tests -v
```

GitHub Actions prüft:

- Python 3.10,
- Python 3.12,
- installierbares Editable-Paket,
- vollständige Kompilierung,
- 39 automatisierte Tests.

Ruff und MyPy sind konfiguriert, aber noch nicht Teil des verpflichtenden Workflows. Dies bleibt ein nächster Codequalitätsblock.

## Bekannte technische Grenzen

- `cli.py` ist weiterhin groß.
- Menü und CLI sind über stabile Argumentnamen gekoppelt; Änderungen benötigen Regressionstests.
- Pfadfavoriten werden noch nicht dauerhaft gespeichert.
- Die Startseite bietet keine nativen Dateiauswahldialoge.
- Ordnerexport besitzt noch kein CSV-Format.
- Reale Bedienabnahmen in verschiedenen Terminalgrößen und Themes stehen noch aus.

## Nächster einfacher Entwicklungsblock

Die große `cli.py` schrittweise in kleinere Befehlsmodule aufteilen und dabei Rückgabecodes, Fehlermeldungen und Handlerregistrierung vereinheitlichen.

## Sichere Zusatzverbesserung

CSV-Export für die Ordnerübersicht ergänzen und mit denselben Filtern wie Terminal, JSON und HTML absichern.

## Unverändert

`AGENTS.md` wird in dieser Iteration nicht verändert.
