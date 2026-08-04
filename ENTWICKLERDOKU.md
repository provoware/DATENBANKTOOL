# Entwicklerdokumentation

Stand: Version 0.13.0-alpha.1

## Aufbau

- `project_registry.json`: fachlicher Projektstand, Module, Sicherheitsvertrag und Prüfungsreferenzen.
- `registry.json`: Paketname und aktuelle Paketversion.
- `src/datenbanktool/`: modulare CLI-, Kernlogik-, Hilfe-, Export- und Testdatenlogik.
- `tests/`: fokussierte Unit-, Integrations-, Architektur- und Abnahmetests.

## Schnittstellenvertrag

- Erfolgreiche Befehle liefern Exitcode `0`.
- Validierungs- und Datenbankfehler liefern Exitcode `2`.
- Schreibende Originaldateioperationen bleiben gesperrt.
- Konfigurationsschreibzugriffe müssen ausdrücklich deklariert und bestätigt sein.
- JSON-Ausgaben bleiben maschinenlesbar und enthalten Fehler als klare Felder.

## Versionierung und Prüfung

Semantische Versionierung wird verwendet: inkompatible Änderung = Hauptversion, neue kompatible Funktion = Nebenversion, Fehlerkorrektur = Patchversion. `project_registry.json` beschreibt den fachlichen Projektstand; `registry.json` enthält den Paketnamen und dieselbe aktuelle Version.

Vor einem Commit mit Codeänderung:

```bash
python -m json.tool registry.json >/dev/null
python -m json.tool project_registry.json >/dev/null
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python -m datenbanktool --help
```

## Historischer MVP-Status

Die frühe reine SQLite-Strukturprüfung ist abgeschlossen. Ihre Dateien und Befehle
sind nicht mehr die vollständige Architekturübersicht des aktuellen Alpha-Stands.

## Architekturstand 0.13.0-alpha.1

Diese Iteration ergänzt zwei getrennte Fachverträge:

1. lokale, validierte und überschreibgeschützte Zeitreihen-Vorlagen,
2. optionale, rein lesende Trendgrenzen für Größen- und Dateizahlwachstum.

Neue Fachmodule:

- `core/timeline_presets.py` – Schema, Normalisierung, atomare Speicherung und Rechte,
- `cli_timeline_presets.py` – Parser, Ausgabe und `CommandPolicy` für list/show/save/delete.

Gezielt erweiterte Module:

- `core/folder_timeline.py` – Datei- und Größenprozente sowie Schwellenklassifikation,
- `cli_folder_timeline.py` – `--preset` und Warnschwellenoptionen,
- `core/guided_home.py` – Vorlagenauswahl, Punkt 12 und Schwellenfelder,
- `core/folder_timeline_exports.py` – Warnfelder in JSON, CSV und HTML,
- `core/folder_timeline_charts.py` – sichtbare und zugängliche SVG-Warnmarken,
- `core/folder_timeline_help.py` – gemeinsame Vorlagen- und Schwellenhilfe.

## Vorlagenschema

```json
{
  "schema_version": 1,
  "presets": [
    {
      "name": "Musik",
      "folder": "Musik/Archiv",
      "description": "Wöchentliche Prüfung",
      "created_utc": "...",
      "updated_utc": "..."
    }
  ]
}
```

Nicht gespeichert werden:

- SQLite-Datenbankpfad,
- Stammordner des Scans,
- Sitzungsnummern,
- Warnschwellen,
- Berichtspfade,
- Dateilisten oder Messwerte.

Damit bleibt eine Vorlage unabhängig von einem konkreten Index und enthält nur den
wiederverwendbaren relativen Ordner.

## Validierung und Schreibvertrag

`save_timeline_preset()`:

1. normalisiert den Namen auf einzelne Leerzeichen,
2. erlaubt 1 bis 64 Zeichen,
3. begrenzt die Beschreibung auf 240 Zeichen,
4. validiert den Ordner über `normalise_folder()`,
5. liest vorhandene Einträge erneut validierend,
6. verweigert gleiche Namen ohne `replace=True`,
7. schreibt formatiertes UTF-8-JSON in eine prozessbezogene temporäre Datei,
8. setzt Modus `0600`,
9. gibt die Datei atomar per `replace()` frei,
10. entfernt die temporäre Datei bei Fehlern.

Namen werden für Vergleich und Auflösung mit `casefold()` behandelt. Die gespeicherte
Schreibweise bleibt erhalten.

## Öffentliche Vorlagenbefehle

```text
index timeline-presets list
index timeline-presets show NAME
index timeline-presets save NAME ORDNER [--description TEXT] [--replace]
index timeline-presets delete NAME --yes
```

`list` und `show` sind rein lesend. `save` und `delete` deklarieren
`writes_configuration=True`. Originaldatei-, Index-, Backup-, Bericht- und
Testdatenschreibzugriffe bleiben falsch.

## Zeitreihenauflösung

```text
index folder-timeline DATENBANK [ORDNER]
  [--preset NAME]
  [--preset-file PFAD]
```

`_timeline_folder()` erzwingt:

- entweder positionaler Ordner,
- oder gespeicherte Vorlage,
- niemals beides gleichzeitig,
- ohne beide Angaben den Standard `.`.

## Geführte Startseite

Punkt 11:

1. lädt und validiert die lokale Vorlagendatei,
2. zeigt Name, Ordner und Beschreibung nummeriert,
3. akzeptiert Nummer oder exakten Namen,
4. erlaubt leere Auswahl für manuelle Eingabe,
5. zeigt den gewählten Ordner erneut,
6. übergibt bei unverändertem Ordner `--preset`,
7. wechselt bei bewusster Änderung auf den direkten Ordnerpfad.

Eine fehlerhafte Vorlagendatei wird gemeldet, blockiert aber nicht die manuelle
Zeitreihe.

Punkt 12 erzeugt einen `timeline-presets save`-Befehl und besitzt
`confirmation_required=True`. Die Startseite bietet absichtlich kein stilles Ersetzen.

## Trendgrenzenmodell

`FolderTimelineOptions` enthält:

```python
warn_size_growth_percent: float | None
warn_file_growth_percent: float | None
```

Validiert werden endliche Werte von 0 bis 1.000.000. Ein leerer Wert deaktiviert die
jeweilige Grenze.

`FolderTimelinePoint` enthält zusätzlich:

```python
file_delta_percent: float | None
threshold_triggered: bool
threshold_reasons: tuple[str, ...]
```

`FolderTimeline` enthält die konfigurierten Grenzen und `threshold_trigger_count`.

## Prozentberechnung

```text
(current - previous) / previous × 100
```

- Ergebnis auf zwei Dezimalstellen gerundet.
- Vorheriger Wert `<= 0` liefert `None`.
- Der erste sichtbare Punkt ist immer Ausgangswert.
- Vergleichsbasis ist der unmittelbar vorherige sichtbare Scan.

## Auslösungslogik

Eine Grenze löst nur aus, wenn:

1. die Grenze konfiguriert ist,
2. der absolute Unterschied positiv ist,
3. ein Prozentwert berechenbar ist,
4. der Prozentwert größer oder gleich der Grenze ist.

Bei Auslösung:

```text
traffic_level = red
traffic_label = Trendgrenze erreicht
```

`status` und `status_label` bleiben unverändert und beschreiben weiterhin den
fachlichen Verlauf. Dadurch bleibt `grown` von der optionalen Warnwirkung getrennt.

## Ausgaben

### Terminal

Zeigt aktive Grenzen, Trefferzahl, Datei- und Größenprozente sowie die vollständige
Ampelbegründung. Der Hinweis „keine Schadensbewertung“ ist Bestandteil jedes Treffers.

### JSON

`FolderTimeline.to_dict()` enthält Konfiguration, Trefferzahl und sämtliche neuen
Punktfelder ohne ANSI-Ausgaben.

### CSV

Enthält getrennte Spalten für Verlaufsstatus, Warnstatus, Begründung, Trefferflag,
Dateiprozent, Größenprozent und konfigurierte Warnschwellen. UTF-8-BOM und Semikolon
bleiben erhalten.

### HTML und SVG

HTML zeigt eine Warnzusammenfassung und die vollständige Begründung in der Tabelle.
SVG-Punkte verwenden bei einem passenden metrischen Treffer:

```html
<circle class="data-point warning-point" ...>
<text class="warning-label">Warnung</text>
```

Titel, ARIA-Beschreibung und sichtbarer Text enthalten dieselbe fachliche Begründung.
JavaScript und externe Ressourcen bleiben ausgeschlossen.

## Sicherheitsinvarianten

- Vorlagen lesen oder schreiben keine Originaldateien.
- Zeitreihe und Trendgrenzen öffnen SQLite nur lesend.
- Warnungen lösen keine Folgeaktion aus.
- Konfigurations- und Berichtsdateien werden atomar freigegeben.
- Vorhandene Inhalte werden nicht still überschrieben.
- Geführte Befehle bleiben Argumentlisten ohne Shell-Auswertung.
- Automatische Originaldateioperationen bleiben gesperrt.

## Automatische Tests

Geprüft werden unter anderem:

- Vorlagen-Roundtrip, Modus 0600 und Überschreibschutz,
- bewusstes Ersetzen und bestätigtes Löschen,
- unsichere Ordnerpfade und beschädigte Strukturen,
- CLI-Parser, Handler, Policies und Modulzuständigkeit,
- Startseiten-Auswahl per Nummer und bestätigtes Speichern,
- Komma- und Punktdezimalwerte,
- Größen- und Dateizahlgrenze einzeln und gemeinsam,
- Null-, NaN-, Unendlich- und Bereichsfälle,
- getrennte Verlauf- und Warnfelder,
- Terminal-, JSON-, CSV-, HTML- und SVG-Begründungen,
- Skript- und Netzwerkfreiheit.

## 0.13-Funktionsreferenz

Run `30927676213`, Commit `8ded929533f806c739a7139b47d16379a788cfb0`:

- 86/86 Tests unter Python 3.10,
- 86/86 Tests unter Python 3.12,
- `PYTHONWARNINGS=error`,
- Quick: 600 Dateien, 11/11, 1,129 s, 1.324.226 Byte Python-Peak,
- Standard: 10.000 Dateien, 11/11, 18,150 s, 13.398.233 Byte Python-Peak.

Artefakte:

| Profil | ID | SHA-256 |
|---|---:|---|
| Quick | 8899780387 | `c3678cdd50d235b9819475d6f1f6660e0367833c3a80f7faa5dff7ce990b0c1b` |
| Standard | 8899791444 | `846ebbd02d213bc336800d330a8a2612e2a069e17e13362f0a27f5aa4ed7571d` |

## Bekannte Grenzen

- Geführtes Ersetzen und Löschen von Vorlagen fehlt noch.
- Vorlagen enthalten bewusst keine Warnschwellen oder Exportziele.
- Trendgrenzen sind Übergangsregeln, keine statistische Anomalieerkennung.
- Je Bericht wird ein relativer Ordner dargestellt.
- Reale Laienabnahme und Zielhardwaretest bleiben offen.

## Direkt folgender Entwicklungsblock

Geführtes Vorlagen-Untermenü für Anzeigen, bewusstes Ersetzen und bestätigtes Löschen.

## Sichere Alternative

Mehrere relative Ordner in einem rein lesenden Bericht mit getrennten Linien und
klarer Nicht-Addierbarkeitswarnung darstellen.

## Unverändert

`AGENTS.md` wird nicht verändert. Externe Laufzeitabhängigkeiten bleiben bei null.
Automatische Schreibzugriffe auf gescannte Originaldateien bleiben gesperrt.
