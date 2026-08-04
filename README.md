# DATENBANKTOOL

> Sicheres Linux-Werkzeug zum Finden, Prüfen und übersichtlichen Strukturieren großer Dateisammlungen.

## Projektstatus

| Bereich | Stand |
|---|---|
| Version | `0.11.0-alpha.1` |
| SQLite-Schema | `3` |
| Entwicklungsfortschritt | **99 %** |
| Erledigte Hauptpunkte | **47** |
| Offene Hauptpunkte | **1** |
| Automatische Originaldateiänderungen | **Gesperrt** |
| Externe Laufzeitabhängigkeiten | **0** |
| Automatisierte Tests | **71/71** unter Python 3.10 und 3.12 |
| Quick-Abnahme | **600 Dateien · 11/11 bestanden** |
| Standard-Abnahme | **10.000 Dateien · 11/11 bestanden** |
| Reale Laienabnahme | **Noch offen** |

## Neu: Ordner-Zeitreihe über mehrere Scans

```bash
datenbanktool index folder-timeline index.sqlite3 Musik
```

Ohne Ordnerangabe wird der gesamte Stammordner `.` ausgewertet:

```bash
datenbanktool index folder-timeline index.sqlite3
```

Die Ausgabe enthält pro Scan:

- Scan-ID und UTC-Zeitpunkt,
- Scan-Modus,
- rekursive Dateizahl und Gesamtgröße,
- Datei- und Größendifferenz zum vorherigen Scan,
- prozentuale Größenänderung,
- Zustand und verständliche Begründung.

Erkannte Zustände sind Ausgangswert, gewachsen, kleiner geworden, neu, nicht mehr
vorhanden, Dateizahl geändert und unverändert.

### Zeitraum und Begrenzung

```bash
datenbanktool index folder-timeline index.sqlite3 Musik \
  --from-session-id 3 \
  --to-session-id 12 \
  --limit 100
```

- Nur abgeschlossene Sitzungen desselben Stammordners.
- Relativer Ordnerpfad; absolute Pfade und `..` werden abgelehnt.
- Mindestens zwei Scans.
- `--limit` akzeptiert 2 bis 500 Zeitpunkte.
- Eine Kürzung auf die neuesten Zeitpunkte wird sichtbar gemeldet.

### Zeitreihe exportieren

```bash
datenbanktool index folder-timeline index.sqlite3 Musik \
  --json musik-verlauf.json \
  --csv musik-verlauf.csv \
  --html musik-verlauf.html
```

CSV verwendet UTF-8-BOM und Semikolon für LibreOffice Calc. HTML funktioniert offline
und enthält Statuswerte, Tooltips und ARIA-Beschriftungen. Vorhandene Ziele werden nur
mit `--overwrite-report` ersetzt.

## Neu: vollständiger Ordnervergleichsexport

```bash
datenbanktool index folder-compare index.sqlite3 \
  --page-size 25 \
  --csv ordnervergleich.csv \
  --all-pages
```

`--all-pages` gilt für JSON, CSV und HTML. Das Terminal bleibt paginiert. Die
vollständige gefilterte und sortierte Ergebnismenge wird genau einmal berechnet und
anschließend für Terminal und Export aufgeteilt. Ohne Exportziel wird der Schalter
kontrolliert abgelehnt.

## Zentrale Befehle

```bash
datenbanktool index build ~/Daten --database index.sqlite3
datenbanktool index rescan ~/Daten --database index.sqlite3
datenbanktool index search index.sqlite3 urlaub
datenbanktool index folders index.sqlite3 --csv ordner.csv --all-pages
datenbanktool index folder-compare index.sqlite3
datenbanktool index folder-timeline index.sqlite3 Musik
datenbanktool index backup index.sqlite3 --output backup.sqlite3
```

## Reproduzierbare Großbestandsabnahme

```bash
datenbanktool acceptance --profile quick --workspace ./abnahme-quick
datenbanktool acceptance --profile standard --workspace ./abnahme-standard
```

| Profil | Dateien | Ordner | Zeitgrenze | Python-Speichergrenze |
|---|---:|---:|---:|---:|
| `quick` | 600 | 24 | 30 s | 256 MiB |
| `standard` | 10.000 | 250 | 600 s | 1.024 MiB |
| `large` | 100.000 | 1.000 | 3.600 s | 4.096 MiB |

Die Abnahme erzeugt nur synthetische Daten in einem neuen Arbeitsordner, misst
Laufzeit und Speicher, prüft ein Vorher-/Nachher-Manifest und erzeugt JSON-, Markdown-,
CSV- sowie Laien-Checklistenberichte.

## Finale 0.11-Referenzprüfung

GitHub Actions auf Ubuntu 24.04 und Python 3.12:

| Profil | Dateien | Kriterien | Laufzeit | Python-Spitzenspeicher |
|---|---:|---:|---:|---:|
| Quick | 600 | 11/11 | 1,131 s | 1.327.056 Byte |
| Standard | 10.000 | 11/11 | 18,072 s | 13.396.733 Byte |

Beide Berichtspakete wurden mit SHA-256-Prüfsumme archiviert und 14 Tage aufbewahrt.
Die Werte sind CI-Referenzen und keine Garantie für andere Hardware.

## Sicherheit

- Zeitreihe und Vergleich öffnen SQLite mit `mode=ro` und `query_only`.
- Originaldateien werden nicht geöffnet, verschoben, umbenannt oder gelöscht.
- Berichte werden atomar geschrieben und nicht still überschrieben.
- Unterschiedliche Stammordner werden nicht vermischt.
- Jeder öffentliche CLI-Befehl besitzt eine `CommandPolicy`.
- Shell-Auswertung, `eval`, `exec` und `os.system` bleiben verboten.
- Externe Laufzeitabhängigkeiten bleiben bei null.

## Modulare Struktur

| Modul | Zuständigkeit |
|---|---|
| `core/folder_timeline.py` | Sitzungsauswahl, rekursive Messwerte und Zustände |
| `core/folder_timeline_exports.py` | atomare JSON-, CSV- und HTML-Ausgabe |
| `cli_folder_timeline.py` | Parser und Terminaldarstellung |
| `core/folder_compare.py` | Vergleichskern und vollständige Ergebnismenge |
| `cli_folder_compare.py` | Pagination und `--all-pages` |
| `core/acceptance.py` | reproduzierbare Abnahmeprofile |
| `cli.py` | Zusammensetzung und zentrale Fehlergrenze |

## Prüfungen

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
python -m compileall -q src tests
PYTHONWARNINGS=error python -m unittest discover -s tests -v
```

## Aktuelle Grenzen

- Reale Laienabnahme noch offen.
- `large`-Profil noch nicht auf Zielhardware ausgeführt.
- Leere Ordner ohne Dateien erscheinen nicht.
- Elternordner enthalten rekursive Unterordnerwerte.
- Noch keine eingebettete Liniendiagramm-Darstellung.
- Noch kein eigener Startseitenpunkt für die Zeitreihe.
- Oberfläche bleibt terminalbasiert.

## Mögliche weitere Upgrades

- Zeitreihe in Startseite und mehrschichtige Hilfe integrieren.
- Barrierefreie SVG-Liniengrafiken für Größe und Dateizahl ergänzen.
- Mehrere Ordner gemeinsam als Trend anzeigen.
- Reale Laienabnahme und 100.000-Dateien-Zieltest durchführen.

## Direkt folgender technischer Entwicklungsschritt

**Geführte Zeitreihenbedienung:** Den neuen Befehl als eigenen Startseitenpunkt mit
Detail-, Schritt-für-Schritt-, Feld- und Fehlerhilfe integrieren.

## Alternative Verbesserung mit hohem Nutzen und geringem Risiko

**Barrierefreie HTML-Trendgrafik:** Größe und Dateizahl zusätzlich als zwei lokale,
textlich beschriftete SVG-Liniengrafiken darstellen.
