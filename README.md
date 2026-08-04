# DATENBANKTOOL

> Sicheres Linux-Werkzeug zum Finden, Prüfen und übersichtlichen Strukturieren großer Dateisammlungen.

## Projektstatus

| Bereich | Stand |
|---|---|
| Version | `0.9.0-alpha.1` |
| SQLite-Schema | `3` |
| Entwicklungsfortschritt | **96 %** |
| Erledigte Hauptpunkte | **43** |
| Offene Hauptpunkte | **2** |
| Automatische Originaldateiänderungen | **Gesperrt** |
| Externe Laufzeitabhängigkeiten | **0** |
| Automatisierte Tests | **59/59** unter Python 3.10 und 3.12 |

## Neu: Ordner zwischen zwei Scans vergleichen

Der Ordnervergleich zeigt verständlich, wo Speicher hinzugekommen oder weggefallen ist.
Er arbeitet ausschließlich mit zwei bereits gespeicherten, abgeschlossenen Scans.

```bash
datenbanktool index folder-compare index.sqlite3
```

Ohne weitere Angaben wählt das Tool automatisch:

1. den neuesten abgeschlossenen Scan mit einer passenden Vergleichsbasis,
2. dessen direkten Vorgänger oder den vorherigen abgeschlossenen Scan desselben Stammordners.

Explizite Auswahl:

```bash
datenbanktool index folder-compare index.sqlite3 \
  --from-session-id 3 \
  --to-session-id 7
```

Beide Sitzungen müssen abgeschlossen sein, dieselbe Ordnerwurzel besitzen und in der
richtigen zeitlichen Reihenfolge liegen.

### Verständliche Zustände

| Zustand | Bedeutung |
|---|---|
| **Gewachsen** | Gesamtgröße des Ordners ist gestiegen |
| **Kleiner geworden** | Gesamtgröße ist gesunken |
| **Neu** | Ordner enthält erstmals Dateien |
| **Nicht mehr vorhanden** | Im neueren Scan liegen dort keine Dateien mehr |
| **Dateizahl geändert** | Größe gleich, aber Anzahl der Dateien anders |
| **Unverändert** | Größe und Dateizahl sind gleich |

Unveränderte Ordner werden standardmäßig ausgeblendet. Sie können gezielt angezeigt
werden:

```bash
datenbanktool index folder-compare index.sqlite3 --type unchanged
```

### Filter und Sortierung

```bash
# Nur gewachsene Ordner
datenbanktool index folder-compare index.sqlite3 --type grown

# Nur Änderungen ab 100 MiB
datenbanktool index folder-compare index.sqlite3 --min-change-mib 100

# Nur zwei Ordnerebenen
datenbanktool index folder-compare index.sqlite3 --max-depth 2

# Nach Pfad sortieren
datenbanktool index folder-compare index.sqlite3 --sort path --no-descending
```

Weitere Sortierungen:

- `change` – größte absolute Speicheränderung,
- `percent` – größte prozentuale Änderung,
- `files` – größte Änderung der Dateizahl,
- `current-size` – aktuelle Ordnergröße,
- `path` – Ordnername.

### Sichere Exporte

```bash
datenbanktool index folder-compare index.sqlite3 \
  --json ordnervergleich.json \
  --csv ordnervergleich.csv \
  --html ordnervergleich.html
```

- CSV verwendet UTF-8 mit BOM und Semikolon und ist für LibreOffice Calc geeignet.
- HTML funktioniert vollständig offline und besitzt Klartext, Ampeln und Tooltips.
- JSON ist maschinenlesbar und enthält keine Farbcodes.
- Vorhandene Berichte werden nur mit `--overwrite-report` ersetzt.
- Exportiert wird die aktuell gefilterte und ausgewählte Seite.

## Startseite und Hilfe

Der Vergleich ist als Punkt **10** in der geführten Startseite erreichbar:

```bash
datenbanktool start
```

```text
1   Dateien suchen
2   Ordnerübersicht
3   Änderungen anzeigen
4   Indexstatus prüfen
5   Neuen Index anlegen
6   Ordner erneut prüfen
7   Index sichern
8   Suchvorlagen anzeigen
9   Funktionen erklären
10  Ordner vergleichen
h   Hilfezentrum
0   Beenden
```

Mehrschichtige Hilfe:

```text
?10   ausführliche Erklärung
g10   vollständige Schritt-für-Schritt-Anleitung
```

Direkter Hilfebefehl:

```bash
datenbanktool help folder-compare --level guided
datenbanktool explain folder-compare
```

## Ampeln beim Ordnervergleich

| Ampel | Bedeutung |
|---|---|
| **ROT – Stark gewachsen** | Zunahme überschreitet die gewählte Warnschwelle |
| **GELB – Gewachsen/Neu** | Veränderung verdient Aufmerksamkeit |
| **GRÜN – Kleiner/Entfernt/Unverändert** | kein Speicherwachstum erkannt |

Die Ampel bewertet nur die Größenentwicklung. Sie sagt nicht, dass Dateien beschädigt,
gefährlich oder überflüssig sind. Farbe, Status und Begründung werden immer gemeinsam
angezeigt.

## Modulare CLI-Struktur

| Modul | Zuständigkeit |
|---|---|
| `cli.py` | Zusammensetzung, Dispatch und zentrale Fehlergrenze |
| `cli_scan.py` | einmalige Scans |
| `cli_search.py` | Suche und Suchvorlagen |
| `cli_reports.py` | Ordner-, Änderungs- und Dateiberichte |
| `cli_folder_compare.py` | Ordnervergleich |
| `cli_index.py` | Indexaufbau, Re-Scan, Status, Backup, Restore und Reparatur |
| `cli_help.py` | klassischer Erklärungsbefehl |
| `cli_common.py` | gemeinsame Eingabeprüfung und Ausgabe |
| `cli_contract.py` | Handler- und Seiteneffektvertrag |

Globale Regeln stehen in `MAINTENANCE_RULES.md` und `maintenance_rules.json`.
Automatische Tests erzwingen unter anderem Größenlimits, Importgrenzen, Handler- und
Sicherheitsrichtlinien sowie das Verbot von Shell-Auswertung.

## Wichtige Direktbefehle

```bash
# Index aufbauen
datenbanktool index build ~/Daten --database index.sqlite3

# Ordner erneut prüfen
datenbanktool index rescan ~/Daten --database index.sqlite3

# Ordner vergleichen
datenbanktool index folder-compare index.sqlite3

# Dateien suchen
datenbanktool index search index.sqlite3 urlaub

# Ordnerübersicht
datenbanktool index folders index.sqlite3

# Dateiänderungen anzeigen
datenbanktool index changes index.sqlite3

# Index sichern
datenbanktool index backup index.sqlite3 --output backup.sqlite3
```

## Sicherheitsgrundsätze

- Der Ordnervergleich öffnet SQLite mit `mode=ro` und `PRAGMA query_only=ON`.
- Er liest nicht erneut den aktuellen Dateisystemstand.
- Originaldateien werden nicht geöffnet, gelöscht, verschoben oder verändert.
- Die SQLite-Indexdatenbank bleibt während des Vergleichs unverändert.
- Berichte werden atomar geschrieben und nicht still überschrieben.
- Unterschiedliche Stammordner werden nicht miteinander vermischt.
- Jeder CLI-Befehl deklariert seine Seiteneffekte über `CommandPolicy`.
- Shell-Auswertung, `eval`, `exec` und `os.system` bleiben verboten.
- Externe Laufzeitabhängigkeiten bleiben bei null.

## Installation für die Entwicklung

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
```

## Prüfungen

```bash
python -m compileall -q src tests
PYTHONWARNINGS=error python -m unittest discover -s tests -v
```

GitHub Actions prüft Python 3.10 und 3.12 sowie Architekturgrenzen,
Seiteneffektverträge und verbotene Shell-Funktionen.

## Aktuelle Grenzen

- Es werden immer genau zwei Scan-Sitzungen verglichen, noch keine längere Zeitreihe.
- Leere Ordner ohne Dateien können nicht erscheinen, weil der Index Dateien speichert.
- Elternordner enthalten bewusst die Werte ihrer Unterordner; Zeilen dürfen deshalb
  nicht addiert werden.
- Der Vergleich zeigt gespeicherte Scanstände und nicht automatisch den heutigen
  Dateisystemzustand.
- Exporte enthalten die aktuelle gefilterte Seite, nicht automatisch alle Treffer.
- Die normale Ordnerübersicht besitzt weiterhin JSON und HTML, aber noch keinen CSV-Export.
- Vor einem stabilen Release fehlt eine Abnahme mit sehr großen realistischen Beständen
  und Linux-Laien.

## Nächster einfacher Entwicklungsschritt

**Ordnerübersicht als CSV speichern:** Dateizahl, Gesamtgröße, Ampelgrund und größte
Platzfresser sollen direkt in LibreOffice Calc geöffnet werden können.

## Sichere Zusatzverbesserung

**Großbestands- und Laienabnahme:** Einen realistischen Testbestand mit festen Laufzeit-,
Speicher- und Bedienkriterien prüfen, ohne Originaldateioperationen freizuschalten.
