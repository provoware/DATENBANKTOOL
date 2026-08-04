# DATENBANKTOOL

> Sicheres Linux-Werkzeug zum Finden, Prüfen und übersichtlichen Strukturieren großer Dateisammlungen.

## Projektstatus

| Bereich | Stand |
|---|---|
| Version | `0.7.0-alpha.1` |
| SQLite-Schema | `3` |
| Entwicklungsfortschritt | **91 %** |
| Erledigte Hauptpunkte | **40** |
| Offene Hauptpunkte | **4** |
| Automatische Originaldateiänderungen | **Gesperrt** |
| Externe Laufzeitabhängigkeiten | **0** |
| Automatisierte Tests | **48/48** unter Python 3.10 und 3.12 |

## Neu: mehrschichtige Laienhilfe

DATENBANKTOOL erklärt Funktionen jetzt in mehreren Tiefen. Der Nutzer entscheidet selbst, wie viele Informationen benötigt werden.

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

Die Detailhilfe nennt Zweck, tatsächliche Schreibwirkung, Risiko, Voraussetzungen, Erfolgskontrolle und Beispielbefehl.

### Ebene 3: Schritt-für-Schritt-Hilfe

In der Startseite `g` vor die Nummer setzen:

```text
g1   Dateisuche Schritt für Schritt
g5   Indexaufbau Schritt für Schritt
g7   Sicherung Schritt für Schritt
```

### Ebene 4: Hilfe im Eingabefeld

Bei jeder geführten Pfad-, Such- oder Bestätigungsfrage kann `?` eingegeben werden. Das Tool erklärt dann genau dieses Feld und fragt anschließend erneut.

### Ebene 5: Fehlerhilfe

Beendet ein Fachbefehl sich mit einem Fehlercode, zeigt die Startseite:

- dass keine automatische Originaldateiänderung erfolgt ist,
- die wahrscheinlichsten Prüfstellen,
- den passenden ausführlichen Hilfebefehl.

## Eigenständiger Hilfebefehl

Alle Themen auflisten:

```bash
datenbanktool help
```

Kurze Erklärung:

```bash
datenbanktool help search --level quick
```

Ausführliche Erklärung:

```bash
datenbanktool help build --level detail
```

Vollständige Anleitung:

```bash
datenbanktool help build --level guided
```

Mit einem Alltagsbegriff suchen:

```bash
datenbanktool help --find "große Ordner"
datenbanktool help --find Platzfresser
```

Maschinenlesbar:

```bash
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

Farben stehen nie allein. Farbnamen, Statuswort und Begründung bleiben immer sichtbar.

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
- Die Startseite führt keine Shell-Zeichenkette aus.
- Pfade und Suchtexte werden als einzelne Argumente übergeben.
- Indexaufbau, Re-Scan und Sicherung benötigen in der Startseite eine Bestätigung.
- Berichte und Sicherungen werden nicht still überschrieben.
- Restore erstellt standardmäßig eine Rückfallsicherung.
- Automatisches Löschen, Verschieben und Umbenennen bleibt gesperrt.
- Der Hilfebefehl und sämtliche Hilfestufen verändern keine Daten.

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

GitHub Actions prüft Python 3.10 und 3.12.

## Aktuelle Grenzen

- Die Oberfläche bleibt vorerst terminalbasiert.
- Pfade werden noch als Text eingegeben oder eingefügt.
- Alltagssuche arbeitet über gepflegte Stichwörter und noch nicht über semantische KI.
- Fehlerhilfe gibt sichere nächste Prüfungen, repariert aber nicht automatisch.
- Die zentrale `cli.py` ist weiterhin groß und soll als Nächstes zerlegt werden.

## Nächster einfacher Entwicklungsschritt

Den großen Befehlsblock in kleinere Funktionsmodule aufteilen, damit Änderungen leichter geprüft und Fehler schneller gefunden werden können.

## Sichere Zusatzverbesserung

Die Ordnerübersicht zusätzlich als CSV speichern, damit sie direkt in LibreOffice Calc geöffnet werden kann.

## Weitere sinnvolle Upgrades

- Ordnerwachstum zwischen zwei Scans vergleichen.
- Suchvorlagen exportieren und importieren.
- Grafische Oberfläche mit Schaltflächen und Dateiauswahlfenstern entwickeln.
- Sehr große reale Dateibestände mit festen Laufzeit- und Speichergrenzen prüfen.
