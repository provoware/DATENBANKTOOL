# Entwicklerdokumentation

## Architekturstand 0.5.0-alpha.1

Der Datenkern und die Bedienhilfen sind strikt getrennt:

1. Scanner und Indexaufbau.
2. Inkrementeller Snapshotvergleich.
3. Rein lesende Suche und Berichte.
4. Rein lesende Ordneraggregation.
5. Externe Suchvorlagen-Konfiguration.
6. Zentrale Präsentationsschicht für Farben und Ampeln.
7. Zentrale Hilfetexte für Zweck und Auswirkung.
8. Kommandozeilenoberfläche als dünne Integrationsschicht.

Originaldatei-Schreibfunktionen bleiben außerhalb dieser Architektur.

## Neue Module

### `core/folders.py`

- Öffnet SQLite über URI `mode=ro`.
- Aktiviert `PRAGMA query_only`.
- Wählt ausschließlich abgeschlossene Sitzungen.
- Aggregiert jeden Dateipfad auf seinen direkten Ordner und alle Vorfahren.
- Unterscheidet direkte und rekursive Dateizahlen und Größen.
- Hält je Ordner nur die konfigurierten größten Dateien im Speicher.
- Berechnet Warnungs- und Duplikatanzahlen.
- Liefert stabile Filter-, Sortier- und Seitenergebnisse.
- Exportiert JSON und eigenständiges HTML atomar.

Die Wurzel eines Snapshots wird intern als `.` dargestellt. Ein Dateipfad wird mit `PurePosixPath` verarbeitet, weil Indexpfade unabhängig vom lokalen Betriebssystem als POSIX-Pfade gespeichert sind.

### Ampelvertrag

`TrafficLight` enthält:

- `level`: `green`, `yellow` oder `red`,
- `label`: verständlicher Status,
- `reason`: konkrete Begründung.

Die aktuelle Heuristik berücksichtigt:

- Anzahl und Anteil von Namenshinweisen,
- Anzahl und Anteil von Duplikatmitgliedern,
- größte Einzeldatei,
- Konzentration eines Großteils des Ordnerspeichers auf eine Datei.

Wichtig: Die Ampel ist keine Schadens- oder Löschentscheidung. Diese Bedeutung wird in Terminal, README und HTML ausdrücklich beschrieben.

### `core/presentation.py`

Zentrale Ausgabe für:

- ANSI-Farben,
- Ampeltext,
- Statusfarben,
- Änderungsarten,
- Bedienhinweise.

Farbmodi:

- `auto`: nur bei geeignetem TTY,
- `always`: Farben erzwingen,
- `never`: Farben ausschalten.

`NO_COLOR` besitzt Vorrang vor `auto` und `always`, außer künftige Anforderungen definieren ausdrücklich eine andere Regel. Maschinenlesbare JSON-Ausgaben dürfen nie durch Präsentationsfunktionen laufen.

### `core/presets.py`

Suchvorlagen sind bewusst kein SQLite-Schemaobjekt.

Standardpfad:

```text
$XDG_CONFIG_HOME/datenbanktool/search-presets.json
```

Fallback:

```text
~/.config/datenbanktool/search-presets.json
```

Sicherheitsvertrag:

- Schema-Version in der JSON-Datei.
- Strikte Validierung unbekannter Filterfelder.
- Validierung über `SearchFilter.validate()`.
- Atomisches Schreiben über temporäre Datei und `replace()`.
- Temporäre Datei mit Modus `0600`.
- Ersetzen nur mit `replace=True`.
- Löschen durch separate Funktion; CLI verlangt `--yes`.
- Namen werden Unicode-fähig und ohne Groß-/Kleinschreibung verglichen.

### `core/help_system.py`

Zentrale Hilfetexte verhindern widersprüchliche Beschreibungen zwischen künftiger GUI, CLI und Dokumentation.

Jedes `HelpTopic` enthält:

- Titel,
- Zweck,
- Wirkung,
- geschriebene Daten,
- Risiko,
- geeigneten Anwendungsfall,
- Beispiel.

Terminal-Hover-Tooltips werden nicht simuliert, weil sie nicht portabel sind. Die robuste Alternative ist sichtbarer Hilfetext plus `datenbanktool explain`.

## CLI-Integration

Globale Optionen:

```text
--color auto|always|never
--hints / --no-hints
```

Neue Befehle:

```text
datenbanktool explain
datenbanktool index folders
datenbanktool index presets list
datenbanktool index presets show
datenbanktool index presets save
datenbanktool index presets delete
datenbanktool index search --preset NAME
```

`argparse.RawDescriptionHelpFormatter` erhält mehrzeilige Zweck- und Auswirkungsbeschreibungen. Globale Optionen müssen vor dem Unterbefehl stehen.

## Suchvorlagen-Mergevertrag

Beim Start einer Suche gilt:

1. Ohne Vorlage gelten sichere Standardwerte.
2. Mit Vorlage werden deren Filter geladen.
3. Explizit gesetzte CLI-Werte überschreiben die Vorlage.
4. `page` wird immer pro aktuellem Aufruf bestimmt.
5. Boolesche Werte verwenden `BooleanOptionalAction`, damit ein Vorlagenwert ausdrücklich ausgeschaltet werden kann.
6. Datenbank- und Sitzungs-ID werden nicht in der Vorlage gespeichert.

## HTML-Tooltipvertrag

Der Ordnerbericht verwendet:

- `title` für Maus-Hover,
- `aria-label` für unterstützende Technik,
- sichtbaren Ampeltext,
- HTML-Escaping für sämtliche Dateipfade und Gründe,
- vollständig lokale CSS-Regeln,
- keine CDN- oder JavaScript-Abhängigkeit.

## Qualitätsprüfungen

```bash
python -m compileall -q src tests
PYTHONWARNINGS=error python -m unittest discover -s tests -v
```

Neu abgesicherte Fälle:

- direkte und rekursive Ordnerwerte,
- größte Dateien,
- Ampelstufe mit Begründung,
- HTML-Tooltip und ARIA-Text,
- Vorlagen speichern und laden,
- Überschreibschutz,
- bestätigtes Löschen,
- Suchstart über Vorlage,
- Farbcodes bei erzwungener Farbe,
- farbfreies JSON,
- JSON- und HTML-Ordnerexport.

GitHub Actions prüft Python 3.10 und 3.12 mit `PYTHONWARNINGS=error`.

## Bekannte technische Grenzen

- Ordneraggregation ist derzeit eine Python-Streamingaggregation über die Dateizeilen einer Sitzung. Für Millionen Dateien kann später eine materialisierte Statistik sinnvoll werden.
- Die Top-Dateiliste sortiert je Ordner eine kleine begrenzte Liste; `top_files` ist deshalb auf 10 begrenzt.
- Suchvorlagen besitzen noch keinen Prozesslock für konkurrierende Schreiber.
- Ampelschwellen sind derzeit feste, dokumentierte Standardwerte.
- HTML besitzt Tooltips, die CLI besitzt sichtbare Hilfen statt Mausinteraktion.

## Nächster einfacher Entwicklungsblock

Ein nummeriertes Startmenü entwickeln, das sichere Hauptfunktionen auswählbar macht und vor jedem Start Zweck und Auswirkung zeigt.

## Sichere Zusatzverbesserung

CSV-Export für die Ordnerübersicht ergänzen und mit denselben Filtern wie Terminal, JSON und HTML absichern.

## Unverändert

`AGENTS.md` wird in dieser Iteration nicht verändert.
