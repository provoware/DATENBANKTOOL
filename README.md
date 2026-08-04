# DATENBANKTOOL

> Sicheres Linux-Werkzeug zum Finden, Prüfen und übersichtlichen Strukturieren großer Dateisammlungen.

## Projektstatus

| Bereich | Stand |
|---|---|
| Version | `0.8.0-alpha.1` |
| SQLite-Schema | `3` |
| Entwicklungsfortschritt | **93 %** |
| Erledigte Hauptpunkte | **42** |
| Offene Hauptpunkte | **3** |
| Automatische Originaldateiänderungen | **Gesperrt** |
| Externe Laufzeitabhängigkeiten | **0** |
| Automatisierte Tests | **54/54** unter Python 3.10 und 3.12 |

## Neu: modularer und dauerhaft abgesicherter CLI-Aufbau

Der frühere zentrale Befehlsblock mit 1.409 Zeilen wurde ohne sichtbare
Befehlsänderungen in klar abgegrenzte Fachmodule aufgeteilt.

| Modul | Zuständigkeit |
|---|---|
| `cli.py` | nur Zusammensetzung, Dispatch und zentrale Fehlergrenze |
| `cli_scan.py` | einmalige Scans |
| `cli_search.py` | Suche und Suchvorlagen |
| `cli_reports.py` | Ordner-, Änderungs- und Dateiberichte |
| `cli_index.py` | Indexaufbau, Re-Scan, Status, Sitzungen, Backup, Restore und Reparatur |
| `cli_help.py` | klassischer Erklärungsbefehl |
| `cli_common.py` | gemeinsame Eingabeprüfung, Ausgabe und Formatierung |
| `cli_contract.py` | Handlervertrag und deklarierte Seiteneffekte |

`cli.py` besitzt jetzt nur noch rund 100 Zeilen. Alle bisherigen Befehle und
Parameter bleiben unverändert.

## Globale Wartungsregeln

Die projektweiten Regeln stehen verständlich in:

```text
MAINTENANCE_RULES.md
```

Die maschinenlesbare und versionierte Fassung steht in:

```text
maintenance_rules.json
```

Automatische Architekturtests erzwingen unter anderem:

- `cli.py` höchstens 150 Zeilen,
- jedes CLI-Fachmodul höchstens 500 Zeilen,
- keine zyklischen Importe zurück zu `cli.py`,
- keine Shell-Auswertung, `eval`, `exec` oder `os.system`,
- jeder öffentliche Befehl besitzt Handler und `CommandPolicy`,
- Originaldatei-Schreibzugriffe bleiben global gesperrt,
- Parser und Handler gehören zum selben Fachmodul,
- Rückgabecodes bleiben ganzzahlig und kontrolliert.

## Mehrschichtige Laienhilfe

DATENBANKTOOL erklärt Funktionen in mehreren Tiefen. Der Nutzer entscheidet selbst,
wie viele Informationen benötigt werden.

### Ebene 1: Soforthilfe

Direkt in der Startseite stehen Kurzbeschreibung, Ampel und Schreibwirkung.

```bash
datenbanktool start
```

### Ebene 2: Detailhilfe

In der Startseite `?` vor die Funktionsnummer setzen:

```text
?1   Details zur Dateisuche
?5   Details zum Indexaufbau
?7   Details zur Sicherung
```

### Ebene 3: Schritt-für-Schritt-Hilfe

In der Startseite `g` vor die Nummer setzen:

```text
g1   Dateisuche Schritt für Schritt
g5   Indexaufbau Schritt für Schritt
g7   Sicherung Schritt für Schritt
```

### Ebene 4: Hilfe im Eingabefeld

Bei jeder geführten Pfad-, Such- oder Bestätigungsfrage kann `?` eingegeben werden.
Das Tool erklärt dieses Feld und stellt danach dieselbe Frage erneut.

### Ebene 5: Fehlerhilfe

Beendet ein Fachbefehl sich mit einem Fehlercode, zeigt die Startseite sichere
Prüfstellen und den passenden ausführlichen Hilfebefehl. Es erfolgt keine versteckte
Reparatur.

## Eigenständiger Hilfebefehl

```bash
# Alle Themen
datenbanktool help

# Kurze Erklärung
datenbanktool help search --level quick

# Ausführliche Erklärung
datenbanktool help build --level detail

# Vollständige Anleitung
datenbanktool help build --level guided

# Suche mit Alltagsbegriff
datenbanktool help --find Platzfresser

# Maschinenlesbar
datenbanktool help folders --level guided --json
```

## Bedienung der Startseite

```text
1  Dateien suchen
2  Ordnerübersicht
3  Änderungen anzeigen
4  Indexstatus prüfen
5  Neuen Index anlegen
6  Ordner erneut prüfen
7  Index sichern
8  Suchvorlagen anzeigen
9  Funktionen erklären
h  Hilfezentrum
0  Beenden
```

| Eingabe | Wirkung |
|---|---|
| `?NUMMER` | ausführliche Hilfe zur Funktion |
| `gNUMMER` | vollständige Schrittanleitung |
| `?` im Feld | Hilfe zur aktuellen Eingabe |
| `q` | aktuellen Schritt abbrechen |
| `0` | Startseite beenden |

## Ampeln

| Ampel | Bedeutung |
|---|---|
| **GRÜN** | rein lesend oder ohne erkannte Auffälligkeit |
| **GELB** | kontrollierter Schreibzugriff oder Prüfbedarf |
| **ROT** | dringender Prüfbedarf |

Farben stehen nie allein. Farbnamen, Statuswort und Begründung bleiben sichtbar.

## Wichtige Direktbefehle

```bash
# Index aufbauen
datenbanktool index build ~/Daten --database index.sqlite3

# Erneut prüfen
datenbanktool index rescan ~/Daten --database index.sqlite3

# Dateien suchen
datenbanktool index search index.sqlite3 urlaub

# Ordnerübersicht
datenbanktool index folders index.sqlite3

# Änderungen anzeigen
datenbanktool index changes index.sqlite3

# Index sichern
datenbanktool index backup index.sqlite3 --output backup.sqlite3
```

## Sicherheitsgrundsätze

- Originaldateien werden standardmäßig nur gelesen.
- Jeder CLI-Befehl deklariert seine Seiteneffekte über `CommandPolicy`.
- Eine Richtlinie mit Originaldatei-Schreibzugriff wird technisch abgewiesen.
- Die Startseite und direkte CLI führen keine Shell-Zeichenketten aus.
- Pfade und Suchtexte werden als einzelne Argumente übergeben.
- Berichte und Sicherungen werden nicht still überschrieben.
- Restore erstellt standardmäßig eine Rückfallsicherung.
- Automatisches Löschen, Verschieben und Umbenennen bleibt gesperrt.
- Maschinenlesbare Ausgaben bleiben frei von Farbcodes und Bedienhinweisen.

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

GitHub Actions prüft Python 3.10 und 3.12. Zusätzlich werden Modulgrößen,
Importgrenzen, Handlerzuordnung, Seiteneffekte und verbotene Shell-Funktionen geprüft.

## Aktuelle Grenzen

- Die Oberfläche bleibt vorerst terminalbasiert.
- Pfade werden noch als Text eingegeben oder eingefügt.
- Die Ordnerübersicht besitzt JSON und HTML, aber noch keinen CSV-Export.
- Ordnerwachstum zwischen zwei Scan-Sitzungen wird noch nicht direkt verglichen.
- Vor einem stabilen Release fehlt eine Abnahme mit sehr großen realistischen Beständen
  und Linux-Laien.

## Nächster einfacher Entwicklungsschritt

**Ordnerübersicht als CSV speichern:** Ordnergrößen, Dateizahlen, Ampelgründe und
größte Platzfresser sollen direkt in LibreOffice Calc geöffnet werden können.

## Sichere Zusatzverbesserung

**Ordnervergleich:** Anzeigen, welche Ordner seit dem vorherigen Scan gewachsen oder
kleiner geworden sind, ohne Originaldateien zu verändern.

## Weitere sinnvolle Upgrades

- Grafische Oberfläche mit Schaltflächen und Dateiauswahlfenstern entwickeln.
- Suchvorlagen exportieren und importieren.
- Sehr große reale Dateibestände mit festen Laufzeit- und Speichergrenzen prüfen.
- Hilfetexte später für weitere Sprachen vorbereiten.
