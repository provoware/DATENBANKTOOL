# Entwicklerdokumentation

## Architekturstand 0.12.0-alpha.1

Diese Iteration ergänzt:

1. eine vollständig geführte Bedienung der Ordner-Zeitreihe,
2. mehrschichtige Detail-, Schritt-, Feld- und Fehlerhilfe,
3. zwei lokale barrierefreie SVG-Trendgrafiken im Offline-HTML.

Neue Fachmodule:

- `core/folder_timeline_help.py` – vollständiger Hilfetext- und Fehlerhilfevertrag,
- `core/folder_timeline_charts.py` – skriptfreie SVG-Erzeugung für Größe und Dateizahl.

Gezielt erweiterte Module:

- `core/guided_home.py` – Menüpunkt 11, validierte Eingaben und sicherer Dispatch,
- `help_command.py` – Hilfeliste, Stichwortsuche und alle Hilfestufen,
- `core/folder_timeline_exports.py` – SVG-Einbettung und vollständige HTML-Tabelle.

## Geführter Startseitenpunkt

```text
11. Ordner-Zeitreihe
```

`MenuAction`:

```python
MenuAction("11", "folder-timeline", "folder_timeline")
```

Die Aktion benötigt keine Bestätigung, weil sie nur SQLite liest und optional einen
neuen Bericht schreibt. Vorhandene Berichtszielen werden weiterhin nicht still ersetzt.

## Dialogzustand

`HomeSession` speichert zusätzlich:

```text
last_timeline_folder
```

Standardwert ist `.`. Dadurch kann ein Nutzer mehrere Zeitreihenläufe durchführen,
ohne denselben relativen Ordner jedes Mal erneut einzutragen.

## Geführte Eingaben

`_build_folder_timeline()` erzeugt folgende Argumentstruktur:

```text
index folder-timeline DATENBANK ORDNER
[--from-session-id ID]
[--to-session-id ID]
[--limit 2..500]
[--json|--csv|--html ZIEL]
```

Abgefragt werden:

1. Indexdatenbank,
2. relativer Ordner,
3. optionale Ausgangssitzung,
4. optionale Zielsitzung,
5. Limit mit Standard 100,
6. optionales Exportformat,
7. neuer Berichtspfad.

## Vorvalidierung

### `_optional_integer()`

- akzeptiert leere Eingabe für optionale Werte,
- wandelt ausschließlich ganze Zahlen um,
- prüft Mindestwert,
- prüft optionalen Höchstwert,
- wiederholt das Feld bei Fehlern,
- zeigt Feldhilfe über `?`.

Sitzungs-IDs benötigen mindestens 1. Das Zeitreihenlimit benötigt 2 bis 500.

### `_report_format()`

Akzeptierte Werte:

```text
kein
json
csv
html
```

Zusätzliche verständliche Aliase wie leer, ohne oder none werden intern auf kein
normalisiert. Andere Werte werden vor dem Dispatch abgelehnt.

### Doppelte Validierungsgrenze

Die geführte Oberfläche verbessert die unmittelbare Fehlermeldung. Der öffentliche
CLI-Parser und `FolderTimelineOptions.validate()` bleiben die maßgebliche zweite
Sicherheitsgrenze. Ein direkter CLI-Aufruf ist somit genauso streng wie der Dialog.

## Sicherer Dispatch

Der Dialog baut eine `list[str]`. Der sichtbare Befehl wird nur über `shlex.join()`
formatiert. Der Runner erhält die ursprüngliche Argumentliste; es gibt keine
Shell-Auswertung und keine Interpretation von Sonderzeichen in Pfaden.

## Hilfearchitektur

### `FOLDER_TIMELINE_TOPIC`

Das Hilfethema enthält:

- Kurzerklärung,
- Zweck,
- Schreibwirkung,
- Risiko,
- sinnvolle Einsatzfälle,
- Vorbedingungen,
- sieben geführte Schritte,
- Erfolgskriterien,
- sechs typische Probleme mit Lösungen,
- CLI-Beispiel,
- Suchbegriffe.

### Gemeinsame Quelle

`guided_home.py` und `help_command.py` verwenden dieselbe Instanz. Dadurch stimmen
`?11`, `g11`, eigenständige Hilfe, JSON-Hilfe, Suchergebnisse und Fehlerhilfe fachlich
überein.

### Feldhilfe

Eigene Hilfetexte existieren für:

- relativen Ordner,
- Ausgangssitzung,
- Zielsitzung,
- Zeitreihenlimit,
- Berichtstyp,
- Berichtspfad.

### Fehlerhilfe

`timeline_error_help()` erklärt kontrolliert:

- weniger als zwei Scans,
- unpassende Scan-Sitzungen,
- absolute Pfade oder `..`,
- Ordner ohne gespeicherte Dateien,
- vorhandene Berichtszielen.

Sie bestätigt zusätzlich, dass Startseite, Index und Originaldateien nicht automatisch
verändert wurden.

## SVG-Diagrammmodul

`render_timeline_charts(timeline)` erzeugt genau zwei Diagramme:

1. `Größenverlauf`,
2. `Dateizahlverlauf`.

### Koordinatensystem

Feste logische ViewBox:

```text
960 × 360
```

Die tatsächliche Anzeige skaliert responsiv über CSS. Die Plotfläche reserviert feste
Innenränder für y-Achse, x-Achse und Beschriftungen.

### X-Achse

Zeitpunkte werden nach ihrer chronologischen Scan-Reihenfolge gleichmäßig verteilt.
Bei einem einzelnen Punkt wäre keine Zeitreihe zulässig; das Kernmodell verlangt
mindestens zwei Punkte.

### Y-Achse

`_bounds()` verwendet Minimum und Maximum des sichtbaren Messwerts. Bei identischen
Werten wird ein sicherer positiver Bereich ergänzt, damit keine Division durch null
entsteht. Vier Intervalle erzeugen fünf beschriftete horizontale Rasterlinien.

### Sichtbare Beschriftung

- bis zwölf Punkte: jeder Punkt erhält sichtbare Scan- und Wertbeschriftung,
- darüber: sechs repräsentative Indexpositionen werden sichtbar beschriftet.

Die Datenmenge wird nicht reduziert. Sämtliche Kreise, ARIA-Texte und Tabellenzeilen
bleiben vorhanden.

### Barrierefreiheit

Jedes Diagramm besitzt:

```html
<figure>
<figcaption>…</figcaption>
<svg role="img" aria-labelledby="…">
<title>…</title>
<desc>…</desc>
```

Jeder Punkt besitzt:

```html
<circle tabindex="0" role="img" aria-label="Scan …">
<title>…</title>
```

Zusätzlich stehen Minimum, Maximum und Nettoänderung als normaler Absatz sowie alle
Rohwerte in einer Tabelle mit `caption` und `scope="col"` zur Verfügung.

### Skript- und Netzwerkfreiheit

Der erzeugte Bericht enthält:

- kein `<script>`,
- keine HTTP- oder HTTPS-Adresse,
- keine externen Stylesheets,
- keine externen Schriftdateien,
- keine externen Bilder,
- keine Laufzeitbibliothek.

Das SVG-Markup ist vollständig im HTML-Dokument enthalten.

## HTML-Struktur

```text
main
├── Überschrift und Scan-Metadaten
├── Sicherheits- und Vollständigkeitshinweis
├── section.charts
│   ├── figure Größenverlauf
│   └── figure Dateizahlverlauf
└── vollständige Zeitreihentabelle
```

Die Tabelle bleibt die verbindliche vollständige Datendarstellung. Die Diagramme sind
eine zusätzliche visuelle Form, ersetzen aber keine Werte.

## Tests

### Geführte Bedienung

Geprüft werden:

- eindeutiger Menüpunkt 11,
- richtiges Hilfethema und Builder,
- rein lesende Einstufung ohne Bestätigungsdialog,
- vollständige Argumentliste,
- Scan-Grenzen,
- Limit,
- HTML-Ziel,
- Feldhilfe,
- Korrektur eines ungültigen Limits.

### Hilfesystem

Geprüft werden:

- `?11`,
- `g11`,
- eigenständige geführte Hilfe,
- Stichwortsuche nach Speicherentwicklung,
- spezifische Fehlerhilfe,
- kein unbeabsichtigter Aktionsstart bei reiner Hilfe.

### SVG und Offline-Vertrag

Geprüft werden:

- genau zwei SVGs,
- beide Diagrammtitel,
- `role="img"`,
- `aria-labelledby`,
- SVG-`desc`,
- fokussierbare Datenpunkte,
- vollständige Wertetabelle,
- kein Script,
- keine HTTP-/HTTPS-Ressource.

## Automatische Referenzprüfung

Commit `b27e678259474ae459f08751ba0b386cccb653a3`:

- 77/77 Tests unter Python 3.10,
- 77/77 Tests unter Python 3.12,
- `PYTHONWARNINGS=error`,
- Quick: 600 Dateien, 11/11, 1,015 s, 1.325.982 Byte Python-Peak,
- Standard: 10.000 Dateien, 11/11, 16,116 s, 13.398.883 Byte Python-Peak.

Artefakte:

| Profil | ID | SHA-256 |
|---|---:|---|
| Quick | 8898514789 | `72e26044b5d02b06c771f74c505b3719cc0cbf5219e8965d6dfb80e0e3b7955e` |
| Standard | 8898524811 | `930f15a0d6e0c942a9dffe0f48e45715dd412db5d815b174b94cd37225ab2bab` |

## Bekannte Grenzen

- Diagramme verwenden Scan-Reihenfolge statt proportionalem Zeitabstand.
- 500 Punkte erzeugen 500 fokussierbare Elemente je Diagramm.
- Sichtbare Wertelabels werden bei langen Reihen reduziert.
- Je Lauf wird ein relativer Ordner dargestellt.
- Geführter Dialog besitzt noch keine gespeicherten Zeitreihen-Vorlagen.
- Reale Laienabnahme und Zielhardwaretest bleiben offen.

## Direkt folgender Entwicklungsblock

Validierte lokale Zeitreihen-Vorlagen entwickeln und in Startseite sowie Hilfe
integrieren.

## Sichere Alternative

Rein lesende Trendgrenzen für auffälliges Größen- oder Dateiwachstum ergänzen.

## Unverändert

`AGENTS.md` wird nicht verändert. Externe Laufzeitabhängigkeiten bleiben bei null.
Automatische Schreibzugriffe auf gescannte Originaldateien bleiben gesperrt.
