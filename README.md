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

Die neue Zeitreihe zeigt, wie sich ein relativer Ordner einschließlich seiner
Unterordner über mehrere abgeschlossene Scans entwickelt hat:

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
- rekursive Dateizahl,
- rekursive Gesamtgröße,
- Datei- und Größendifferenz zum vorherigen Scan,
- prozentuale Größenänderung,
- Zustand und verständliche Begründung.

Erkannte Zustände:

- Ausgangswert,
- gewachsen,
- kleiner geworden,
- neu,
- nicht mehr vorhanden,
- Dateizahl geändert,
- unverändert.

### Zeitraum und Begrenzung

```bash
datenbanktool index folder-timeline index.sqlite3 Musik \
  --from-session-id 3 \
  --to-session-id 12 \
  --limit 100
```

- Es werden nur abgeschlossene Sitzungen desselben Stammordners verwendet.
- Der Ordnerpfad muss relativ sein.
- Absolute Pfade und `..` werden abgelehnt.
- Mindestens zwei Scans sind erforderlich.
- `--limit` akzeptiert 2 bis 500 Zeitpunkte.
- Bei mehr Treffern werden transparent die neuesten Zeitpunkte gezeigt.

### Zeitreihe exportieren

```bash
datenbanktool index folder-timeline index.sqlite3 Musik \
  --json musik-verlauf.json \
  --csv musik-verlauf.csv \
  --html musik-verlauf.html
```

Die CSV verwendet UTF-8-BOM und Semikolon für LibreOffice Calc. HTML funktioniert
offline und enthält sichtbare Statuswerte, Tooltips und ARIA-Beschriftungen.
Vorhandene Ziele werden nur mit `--overwrite-report` ersetzt.

## Neu: vollständiger Ordnervergleichsexport

Der vorhandene Vergleich kann jetzt sämtliche gefilterten Zeilen exportieren:

```bash
datenbanktool index folder-compare index.sqlite3 \
  --page-size 25 \
  --csv ordnervergleich.csv \
  --all-pages
```

`--all-pages` gilt gleichzeitig für JSON, CSV und HTML. Die Terminalanzeige bleibt
paginiert und zeigt weiterhin nur die gewählte Seite. Die vollständige gefilterte und
sortierte Ergebnismenge wird genau einmal berechnet und anschließend für Terminal und
Export aufgeteilt.

Ohne Exportziel wird `--all-pages` kontrolliert abgelehnt.

## Weitere zentrale Befehle

```bash
# Index anlegen
datenbanktool index build ~/Daten --database index.sqlite3

# Ordner erneut prüfen
datenbanktool index rescan ~/Daten --database index.sqlite3

# Dateien suchen
datenbanktool index search index.sqlite3 urlaub

# Ordnerübersicht vollständig nach Calc exportieren
datenbanktool index folders index.sqlite3 \
  --csv ordneruebersicht.csv \
  --all-pages

# Zwei Scans vergleichen
datenbanktool index folder-compare index.sqlite3

# Mehrere Scans als Zeitreihe auswerten
datenbanktool index folder-timeline index.sqlite3 Musik

# Index sichern
datenbanktool index backup index.sqlite3 --output backup.sqlite3
```

## Reproduzierbare Großbestandsabnahme

```bash
datenbanktool acceptance --profile quick --workspace ./abnahme-quick
datenbanktool acceptance --profile standard --workspace ./abnahme-standard
```

Profile:

| Profil | Dateien | Ordner | Zeitgrenze | Python-Speichergrenze |
|---|---:|---:|---:|---:|
| `quick` | 600 | 24 | 30 s | 256 MiB |
| `standard` | 10.000 | 250 | 600 s | 1.024 MiB |
| `large` | 100.000 | 1.000 | 3.600 s | 4.096 MiB |

Die Abnahme erzeugt nur synthetische Daten in einem neuen Arbeitsordner, misst
Laufzeit und Speicher, prüft ein Vorher-/Nachher-Manifest und erzeugt JSON-, Markdown-,
CSV- sowie Laien-Checklistenberichte.

## Finale Referenzprüfung auf dem 0.11-Head

GitHub Actions auf Ubuntu 24.04 und Python 3.12:

| Profil | Dateien | Kriterien | Laufzeit | Python-Spitzenspeicher |
|---|---:|---:|---:|---:|
| Quick | 600 | 11/11 | 1,131 s | 1.327.056 Byte |
| Standard | 10.000 | 11/11 | 18,072 s | 13.396.733 Byte |

Die Werte sind reproduzierbare CI-Referenzen und keine Garantie für identische
Laufzeiten auf anderer Hardware. Beide Berichtspakete werden 14 Tage archiviert.

## Sicherheit

- Zeitreihe und Ordnervergleich öffnen SQLite mit `mode=ro`.
- `PRAGMA query_only=ON` sperrt schreibende SQL-Anweisungen.
- Originaldateien werden nicht geöffnet, verschoben, umbenannt oder gelöscht.
- Alle Berichte werden atomar geschrieben.
- Vorhandene Berichte werden nicht still überschrieben.
- Unterschiedliche Stammordner werden nicht vermischt.
- Jeder öffentliche CLI-Befehl besitzt eine `CommandPolicy`.
- Shell-Auswertung, `eval`, `exec` und `os.system` bleiben verboten.
- Externe Laufzeitabhängigkeiten bleiben bei null.

## Modulare Struktur

| Modul | Zuständigkeit |
|---|---|
| `core/folder_timeline.py` | Sitzungsauswahl, rekursive Messwerte und Zustände |
| `core/folder_timeline_exports.py` | atomare JSON-, CSV- und HTML-Ausgabe |
| `cli_folder_timeline.py` | Parser und verständliche Terminaldarstellung |
| `core/folder_compare.py` | Vergleichskern und vollständige Ergebnismenge |
| `cli_folder_compare.py` | Pagination und `--all-pages`-Steuerung |
| `core/folder_csv.py` | LibreOffice-kompatibler Ordner-CSV-Export |
| `core/acceptance.py` | reproduzierbare Abnahmeprofile |
| `cli.py` | Zusammensetzung und zentrale Fehlergrenze |

Globale Regeln stehen in `MAINTENANCE_RULES.md` und `maintenance_rules.json`.

## Prüfungen

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
python -m compileall -q src tests
PYTHONWARNINGS=error python -m unittest discover -s tests -v
```

Die Testmatrix prüft Python 3.10 und 3.12, Architekturgrenzen, Seiteneffektverträge,
Zeitreihenwerte, Datenbank-Unverändertheit, sichere Pfadprüfung, Exportformate,
Vollständigkeit über mehrere Seiten sowie die bisherigen Funktionen.

## Aktuelle Grenzen

- Eine echte Laienabnahme wurde noch nicht durchgeführt.
- Das `large`-Profil wurde noch nicht auf der vorgesehenen Zielhardware ausgeführt.
- Leere Ordner ohne Dateien erscheinen nicht, weil das Schema Dateieinträge speichert.
- Elternordner enthalten bewusst die Summen ihrer Unterordner.
- Die Zeitreihe zeigt Tabellen und Berichte, noch kein eingebettetes Liniendiagramm.
- Der direkte Zeitreihenbefehl ist vorhanden, aber noch nicht als eigener Punkt in der
  geführten Startseite eingebunden.
- Die Oberfläche bleibt terminalbasiert.

## Mögliche weitere Upgrades

- Ordner-Zeitreihe in Startseite und mehrschichtige Laienhilfe integrieren.
- Barrierefreie Liniengrafiken für Größe und Dateizahl im Offline-HTML ergänzen.
- Mehrere Ordner in einer gemeinsamen, rein lesenden Trendansicht vergleichen.
- Reale Laienabnahme auf Kubuntu durchführen.
- `large`-Profil auf Zielhardware vermessen.

## Direkt folgender technischer Entwicklungsschritt

**Geführte Zeitreihenbedienung:** Den neuen Befehl als eigenen Startseitenpunkt mit
Detail-, Schritt-für-Schritt- und Fehlerhilfe integrieren.

## Alternative Verbesserung mit hohem Nutzen und geringem Risiko

**Barrierefreie HTML-Trendgrafik:** Größe und Dateizahl zusätzlich als zwei lokale,
textlich beschriftete SVG-Liniengrafiken darstellen.
