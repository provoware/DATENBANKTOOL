# Entwicklerdokumentation

## Architekturstand 0.7.0-alpha.1

Die Bedien- und Hilfeschichten sind jetzt klar getrennt:

1. `entrypoint.py` entscheidet zwischen direktem Befehl, Startseite und Hilfebefehl.
2. `help_command.py` verarbeitet die eigenständige mehrschichtige Hilfe.
3. `core/layered_help.py` enthält den zentralen Hilfekatalog und reine Renderfunktionen.
4. `core/guided_home.py` enthält die interaktive Startseitenlogik.
5. `core/terminal_home.py` ist nur noch ein Kompatibilitätsimport.
6. `core/presentation.py` liefert Farben, Ampeln und Statusdarstellung.
7. `cli.py` enthält weiterhin die bestehenden Fachbefehle.

## `core/layered_help.py`

### Datenmodell

`HelpTopic` ist unveränderlich und enthält:

- technischen Namen,
- sichtbaren Titel,
- Kurzbeschreibung,
- Zweck,
- Schreibwirkung,
- Risiko,
- geeigneten Einsatzfall,
- Voraussetzungen,
- Schrittfolge,
- Erfolgskontrolle,
- typische Probleme,
- Beispiel,
- Suchstichwörter.

### Hilfestufen

`render_topic()` unterstützt:

- `quick`: Titel, Kurzbeschreibung, Schreibwirkung und Risiko,
- `detail`: zusätzlich Zweck, Einsatzfall, Voraussetzungen, Erfolg und Beispiel,
- `guided`: zusätzlich nummerierte Schritte und typische Probleme.

Die Funktion ist rein und führt keine Ein-/Ausgabe oder Dateioperation aus.

### Alltagssuche

`find_topics()` vergleicht den Suchtext ohne Groß-/Kleinschreibung mit:

- Themenname,
- Titel,
- Kurzbeschreibung,
- Einsatzbeschreibung,
- gepflegten Stichwörtern.

Die Suche funktioniert vollständig offline. Leerer Suchtext liefert alle Themen.

### Fehlerhilfe

`error_help()` erzeugt aus Themenname und Rückgabecode:

- verständliche Fehlerzusammenfassung,
- Sicherheitsinformation zu Originaldateien,
- bis zu drei passende Prüfhinweise,
- direkten Befehl zur geführten Hilfe.

Es wird bewusst keine automatische Korrektur ausgeführt.

## `core/guided_home.py`

### Menüvertrag

`MenuAction` enthält nur:

- eindeutige Taste,
- Hilfethema,
- Buildername,
- Bestätigungspflicht.

Titel, Beschreibung und Wirkung stammen zentral aus `layered_help.py`. Dadurch werden widersprüchliche doppelte Texte vermieden.

### Hilfenavigation

- `h`, `hilfe`, `help` oder `?`: Hilfezentrum,
- `?NUMMER`: Detailhilfe,
- `gNUMMER`: geführte Hilfe,
- `?` in einem Eingabefeld: Feldhilfe,
- `q`: aktueller Schritt wird abgebrochen,
- `0`: Startseite wird beendet.

Hilfenavigation startet keinen Fachbefehl.

### Feldhilfe

`_read()` erkennt `?`, `hilfe` und `help`, wenn für das Feld ein Hilfetext hinterlegt ist. Danach wird dieselbe Frage erneut gestellt. Der Hilfetext wird nicht als Nutzereingabe übernommen.

Abgesicherte Felder:

- Indexdatenbank,
- Quellordner,
- Suchtext,
- Suchvorlage,
- Prüfsummenentscheidung,
- Sicherungsziel,
- Abschlussbestätigung.

### Befehlsausführung

Die Startseite baut weiterhin ausschließlich `list[str]`-Argumente. Es gibt:

- keine Shell-Auswertung,
- keinen Subprozess,
- kein `eval`,
- keine Interpretation von Metazeichen.

Pfade und Suchtexte mit Leerzeichen bleiben einzelne Argumente.

### Fehlerpfad

Ein Fachbefehl mit Rückgabecode ungleich null:

1. beendet nicht die Startseite,
2. zeigt den Rückgabecode,
3. zeigt kontextbezogene Fehlerhilfe,
4. kehrt anschließend ins Hauptmenü zurück.

## `help_command.py`

Befehlsformen:

```text
datenbanktool help
datenbanktool help THEMA --level quick
datenbanktool help THEMA --level detail
datenbanktool help THEMA --level guided
datenbanktool help --find TEXT
datenbanktool help THEMA --json
```

Unbekannte Themen werden kontrolliert behandelt und liefern Rückgabecode 2. JSON-Ausgaben enthalten Rohdaten und gerenderte Zeilen der gewählten Stufe.

## Kompatibilität

Bestehende Importe aus `datenbanktool.core.terminal_home` bleiben gültig. Das Modul exportiert die Klassen und Funktionen aus `guided_home.py`, enthält aber keine zweite Startseitenimplementierung.

Der bestehende Befehl `datenbanktool explain` bleibt unverändert. Die neue mehrschichtige Oberfläche wird zusätzlich über `datenbanktool help` angeboten.

## Automatische Prüfungen

```bash
python -m compileall -q src tests
PYTHONWARNINGS=error python -m unittest discover -s tests -v
```

Neu geprüft werden:

- zunehmender Informationsumfang der drei Hilfestufen,
- Alltagssuche nach „Platzfresser“ und „große Ordner“,
- Detailhilfe ohne Fachbefehlsstart,
- geführte Hilfe mit Schrittfolge,
- Feldhilfe mit Wiederholung derselben Eingabe,
- kontextbezogene Fehlerhilfe,
- eigenständiger Hilfebefehl,
- unbekanntes Thema mit kontrolliertem Fehlercode.

Gesamtstand: 48 Tests unter Python 3.10 und 3.12, jeweils mit Warnungen als Fehler.

## Bekannte technische Grenzen

- `cli.py` ist weiterhin zu groß und muss in kleinere Befehlsmodule zerlegt werden.
- Hilfetexte sind derzeit deutschsprachig.
- Stichwortsuche ist deterministisch und nicht semantisch.
- Fehlerhilfe schlägt Prüfungen vor, repariert aber nicht automatisch.
- Persistente Favoriten und grafische Dateiauswahl fehlen noch.

## Nächster Entwicklungsblock

`cli.py` ohne sichtbare Befehlsänderung in getrennte Module für Parser, Scans, Suche, Berichte und Indexverwaltung aufteilen. Jede Verschiebung wird durch bestehende Regressionstests abgesichert.

## Sichere Zusatzverbesserung

CSV-Export der Ordnerübersicht mit denselben Filtern, stabiler Sortierung und Überschreibschutz ergänzen.

## Unverändert

`AGENTS.md` wird nicht verändert. Automatische Originaldateioperationen bleiben gesperrt.
