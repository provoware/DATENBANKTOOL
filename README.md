# DATENBANKTOOL

> Sicheres, portables Linux-Werkzeug zum Suchen, Prüfen, Bearbeiten und Strukturieren großer chaotischer Datensammlungen – mit Schwerpunkt auf Medien, Audio, Texten, Archiven und Codeprojekten.

## Projektstatus

| Bereich | Stand |
|---|---|
| Version | `0.1.0-alpha.1` |
| Entwicklungsphase | Fundament / sicherer Analyse-Kern |
| Entwicklungsfortschritt | **18 %** |
| Erledigte Hauptpunkte | **7** |
| Offene Hauptpunkte | **32** |
| Schreibende Dateioperationen | **Noch gesperrt** |
| Standardmodus | **Rein lesend** |

### In dieser Iteration erledigt

1. Python-Projektstruktur und Versionsregister angelegt.
2. Rein lesenden Verzeichnisscanner implementiert.
3. Dateiklassifizierung für Audio, Video, Bilder, Texte, Archive, Code und Dokumente implementiert.
4. Prüfung problematischer und schlecht portierbarer Dateinamen implementiert.
5. Erkennung großer Dateien mit frei einstellbarer Grenze implementiert.
6. Optionale Erkennung exakter Duplikate per Größen-Vorfilter und SHA-256 implementiert.
7. Tests, Risikoanalyse, Roadmap und Entwicklerdokumentation angelegt.

### Wichtigste offene Punkte

1. Persistenter Index für Millionen Dateien.
2. Grafische, touchfähige Oberfläche für Linux-Desktop und kleine Displays.
3. Vorschaumodule für Bild, Audio, Video, Text, PDF und Archive.
4. Sichere Sortier-, Verschiebe- und Umbenennungspläne mit Voransicht.
5. Transaktionales Undo, Papierkorb, Quarantäne und Wiederherstellung.
6. Ähnlichkeitsanalyse für Bilder, Audio und Texte.
7. Ressourcensteuerung, Pausieren, Fortsetzen und Wiederaufnahme nach Absturz.
8. Paketierung als portables Linux-Programm mit Doppelklick-Start.

### Mögliche nächste Upgrades

- SQLite-Index mit inkrementeller Aktualisierung.
- PySide6-Oberfläche mit Modus **Einfach**, **Geführt** und **Experte**.
- FFmpeg/ffprobe- und MediaInfo-Anbindung für echte Medienprüfung.
- Sichere Stapelumbenennung mit Vorschau, Konflikterkennung und Undo-Manifest.
- Audio-Fingerprints und Bild-Ähnlichkeit statt bloßer Hash-Gleichheit.

Weitere Ideen stehen in [`UPGRADE_POOL.md`](UPGRADE_POOL.md).

---

## Ziel

DATENBANKTOOL soll sehr große, unübersichtliche Datensammlungen durchschaubar machen, ohne den Nutzer mit Fachbegriffen oder riskanten Direktaktionen zu überfordern. Das Tool soll:

- Dateien und Ordner schnell auffindbar machen,
- technische und organisatorische Probleme sichtbar machen,
- sichere Ordnungsvorschläge erzeugen,
- Änderungen erst nach verständlicher Vorschau ausführen,
- jede Änderung protokollieren und rückgängig machen,
- vollständig lokal und datensparsam arbeiten.

## Zielgruppen

- Nutzer ohne Linux- oder Dateisystemkenntnisse,
- Musiker, Fotografen, Videoproduzenten und Autoren,
- Besitzer großer gewachsener Festplattenarchive,
- Nutzer mit vielen Dubletten, kryptischen Namen und unsortierten Ordnern,
- Entwickler mit vielen alten oder mehrfach kopierten Codeprojekten,
- fortgeschrittene Nutzer, die transparente Stapelverarbeitung benötigen.

## Sicherheitsgrundsatz

**Analyse zuerst. Änderung später.**

Die aktuelle Version verändert keine gescannten Dateien. Sie liest Metadaten, klassifiziert Dateien und kann auf ausdrücklichen Wunsch Datei-Hashes berechnen. Geplante spätere Dateioperationen müssen folgende Sperren erfüllen:

1. Vorher-Nachher-Vorschau.
2. Konflikt- und Speicherplatzprüfung.
3. Verständliche Zusammenfassung der Wirkung.
4. Explizite Bestätigung.
5. Transaktionsprotokoll.
6. Undo-Manifest und Wiederherstellungstest.
7. Papierkorb oder Quarantäne statt Direktlöschung.
8. Abbruch ohne halbfertigen Zustand.

## Aktuell funktionsfähig

### Rein lesender Scan

Der Scanner erfasst:

- relativen Pfad,
- Dateigröße,
- Änderungsdatum in UTC,
- Dateiendung,
- Dateikategorie,
- symbolische Verknüpfungen,
- große Dateien,
- problematische Dateinamen,
- optionale SHA-256-Prüfsummen für mögliche Duplikate,
- Zugriffs- und Lesefehler ohne Gesamtabsturz.

### Dateikategorien

- Audio
- Video
- Bilder
- Texte
- Archive
- Code
- Dokumente
- Sonstige Dateien

### Dateinamenprüfung

Linux verbietet innerhalb eines einzelnen Dateinamens nur NUL und `/`. Trotzdem können viele Namen in Shells, Archiven, Netzlaufwerken oder anderen Betriebssystemen Probleme verursachen. Deshalb meldet das Tool unter anderem:

- führende oder abschließende Leerzeichen,
- führende Bindestriche,
- Steuerzeichen und Zeilenumbrüche,
- schlecht portable Sonderzeichen,
- uneinheitliche Unicode-Normalisierung,
- überlange Dateinamen,
- mehrfach aufeinanderfolgende Leerzeichen.

Es wird **nichts automatisch umbenannt**.

## Installation für die Entwicklung

Voraussetzung: Python 3.10 oder neuer.

```bash
git clone https://github.com/provoware/DATENBANKTOOL.git
cd DATENBANKTOOL
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
```

## Verwendung

### Einfacher Scan

```bash
datenbanktool scan ~/Musik
```

### Bericht als JSON speichern

```bash
datenbanktool scan ~/Musik --json reports/musik-scan.json
```

Ein vorhandener Bericht wird nicht still überschrieben. Dafür ist eine ausdrückliche Freigabe erforderlich:

```bash
datenbanktool scan ~/Musik \
  --json reports/musik-scan.json \
  --overwrite-report
```

### Exakte Duplikate prüfen

```bash
datenbanktool scan ~/Medien \
  --hash-duplicates \
  --json reports/medien-mit-duplikaten.json
```

Die Hash-Prüfung liest den vollständigen Inhalt möglicher Kandidaten und kann bei großen Sammlungen lange dauern. Sie wird deshalb nur ausdrücklich aktiviert.

### Grenze für große Dateien ändern

```bash
datenbanktool scan ~/Daten --large-file-mib 500
```

### Testscan begrenzen

```bash
datenbanktool scan ~/Daten --max-files 1000
```

## Geplantes Bedienkonzept für Laien

### Modus „Einfach“

- Ein großer Knopf: **Ordner auswählen und prüfen**.
- Keine technischen Parameter im Hauptbild.
- Ergebnisse als Ampel und verständliche Gruppen.
- Keine direkte Löschfunktion.
- Empfohlene sichere nächste Aktion pro Fund.

### Modus „Geführt“

- Schrittweise Assistenten für Duplikate, Dateinamen, große Dateien und Sortierung.
- Jede Regel wird anhand echter Beispiele erklärt.
- Wirkung und Risiko werden vor der Ausführung angezeigt.
- Kritische Entscheidungen lassen sich zurücknehmen.

### Modus „Experte“

- Filterkombinationen, reguläre Ausdrücke, Metadatenregeln und Stapelpläne.
- Exportierbare Profile.
- Vollständige Protokolle und technische Diagnose.
- Gleicher Sicherheitskern wie in den einfachen Modi.

## Geplante Kernmodule

| Modul | Aufgabe | Sicherheitsanforderung |
|---|---|---|
| Scanner | Dateien und Ordner inventarisieren | rein lesend, fehlertolerant |
| Index | Millionen Einträge schnell durchsuchen | inkrementell, reparierbar |
| Suche | Namen, Typen, Inhalte und Metadaten finden | klare Filteranzeige |
| Vorschau | Medien, Texte, Archive und Code prüfen | kein automatisches Ausführen |
| Duplikate | exakte und ähnliche Dateien gruppieren | Original nie automatisch wählen |
| Benennung | sichere Linux- und portable Namen planen | Vorschau und Konflikttest |
| Sortierung | Regeln und Zielstrukturen vorschlagen | nur als Plan starten |
| Dateioperationen | kopieren, verschieben, umbenennen | Transaktion, Undo, Quarantäne |
| Wiederherstellung | Abbruch und Fehler reparieren | journalbasiert |
| Berichte | Ergebnisse dokumentieren | JSON, CSV, HTML, später PDF |

## Technische Leitlinien

- Linux zuerst, vollständig lokal und offline nutzbar.
- Python-Kern ohne zwingende externe Laufzeitabhängigkeiten.
- Grafische Oberfläche später getrennt vom Analyse-Kern.
- Keine direkte Kopplung von UI und Dateioperationen.
- Klare Datenmodelle und maschinenlesbare Berichte.
- Symbolischen Links standardmäßig nicht folgen.
- Hashing und Inhaltsprüfung nur gezielt aktivieren.
- Große Aufgaben pausierbar und fortsetzbar ausführen.
- Minimaler Schreibzugriff und atomare Berichtsdateien.

## Projektstruktur

```text
DATENBANKTOOL/
├── src/datenbanktool/
│   ├── cli.py
│   └── core/
│       ├── classification.py
│       ├── models.py
│       ├── naming.py
│       └── scanner.py
├── tests/
├── project_registry.json
├── ANALYSE-PUNKTE.md
├── SCHWACHSTELLEN.md
├── TODO.md
├── UPGRADE_POOL.md
├── ENTWICKLERDOKU.md
└── CHANGELOG.md
```

## Prüfungen

```bash
python -m compileall -q src tests
PYTHONPATH=src python -m unittest discover -s tests -v
```

Spätere Qualitätsstufen sollen zusätzlich Ruff, MyPy, Bandit, pip-audit, Coverage und reale Dateisystemtests enthalten.

## Dokumentation

- [`ANALYSE-PUNKTE.md`](ANALYSE-PUNKTE.md): vollständige Funktions- und Bedarfsanalyse
- [`SCHWACHSTELLEN.md`](SCHWACHSTELLEN.md): aktuelle Risiken und technische Grenzen
- [`TODO.md`](TODO.md): priorisierte Umsetzungsschritte
- [`UPGRADE_POOL.md`](UPGRADE_POOL.md): spätere Erweiterungen
- [`ENTWICKLERDOKU.md`](ENTWICKLERDOKU.md): Architektur und Entwicklungsregeln
- [`CHANGELOG.md`](CHANGELOG.md): Versionshistorie

## Aktuelle Grenze

Diese Alpha-Basis ist noch kein fertiger Dateimanager. Sie dient als überprüfbares Fundament. Verschieben, Umbenennen, Editieren, Sortieren und Löschen sind bewusst noch nicht freigeschaltet, weil dafür zuerst Transaktions-, Konflikt- und Wiederherstellungslogik fertig sein muss.
