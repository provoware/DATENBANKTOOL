# DATENBANKTOOL

> Ein sicheres Linux-Werkzeug zum Finden, Prüfen und übersichtlichen Strukturieren großer chaotischer Dateisammlungen.

## Projektstatus

| Bereich | Stand |
|---|---|
| Version | `0.5.0-alpha.1` |
| SQLite-Schema | `3` |
| Entwicklungsfortschritt | **77 %** |
| Erledigte Hauptpunkte | **34** |
| Offene Hauptpunkte | **10** |
| Originaldateien verändern | **Nein** |
| Standardmodus | **Rein lesend** |
| Automatisches Löschen oder Verschieben | **Gesperrt** |

## Neu in dieser Version

1. **Ordnerübersicht:** zeigt pro Ordner Dateizahl, Gesamtgröße und größte Platzfresser.
2. **Ampelsystem:** Grün, Gelb und Rot zeigen den Prüfbedarf. Jede Farbe wird zusätzlich mit Text und Begründung erklärt.
3. **Suchvorlagen:** häufige Suchfilter unter einem Namen speichern und später wieder starten.
4. **Tooltip-Hilfe:** HTML-Berichte erklären Ampeln beim Darüberfahren mit der Maus.
5. **Ausführliche Funktionshilfe:** `datenbanktool explain` beschreibt Zweck, Wirkung, Schreibzugriffe, Risiko und Beispiel.
6. **Farben in der Kommandozeile:** automatisch, immer oder nie; `NO_COLOR` wird unterstützt.

## Ampeln richtig verstehen

| Ampel | Bedeutung |
|---|---|
| **GRÜN – Unauffällig** | Keine erkannten Hinweise in diesem Ergebnis. |
| **GELB – Prüfen** | Es gibt zum Beispiel große Dateien, Namenshinweise oder Duplikate. |
| **ROT – Dringend prüfen** | Mehrere oder besonders deutliche Hinweise wurden erkannt. |

Die Ampel sagt **nicht**, dass eine Datei beschädigt oder gefährlich ist. Sie hilft nur dabei, große Listen sinnvoll zu priorisieren.

Farben sind niemals die einzige Information. Jede Ampel enthält zusätzlich den Farbnamen, eine klare Bezeichnung und eine Begründung.

## Installation für die Entwicklung

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
```

Version prüfen:

```bash
datenbanktool --version
```

## 1. Ordnerübersicht anzeigen

```bash
datenbanktool index folders index.sqlite3
```

Die Ausgabe zeigt je Ordner:

- Dateien direkt im Ordner,
- Dateien einschließlich Unterordnern,
- gesamten Speicherbedarf,
- Dateien mit Namenshinweisen,
- Dateien in Duplikatgruppen,
- größte Platzfresser,
- Ampel mit verständlicher Begründung.

Nur die ersten zwei Ordnerebenen anzeigen:

```bash
datenbanktool index folders index.sqlite3 --max-depth 2
```

Nach Speichergröße sortieren:

```bash
datenbanktool index folders index.sqlite3 --sort size
```

Nur Ordner ab 500 MiB anzeigen:

```bash
datenbanktool index folders index.sqlite3 --min-size-mib 500
```

Lokalen JSON- und HTML-Bericht erzeugen:

```bash
datenbanktool index folders index.sqlite3 \
  --json reports/ordner.json \
  --html reports/ordner.html
```

Der HTML-Bericht funktioniert offline. Beim Darüberfahren mit der Maus erklärt ein Tooltip die jeweilige Ampel.

**Auswirkung:** Die Indexdatenbank und Originaldateien werden nur gelesen. Nur ausdrücklich gewählte Berichtsdateien werden erstellt.

## 2. Suchvorlage speichern

Beispiel: große Audiodateien speichern:

```bash
datenbanktool index presets save grosse-audios \
  --description "Audiodateien ab 100 MiB" \
  --category audio \
  --min-size-mib 100 \
  --sort size \
  --descending
```

Vorlagen auflisten:

```bash
datenbanktool index presets list
```

Vorlage vollständig anzeigen:

```bash
datenbanktool index presets show grosse-audios
```

Gespeicherte Suche starten:

```bash
datenbanktool index search index.sqlite3 --preset grosse-audios
```

Ein einzelner Wert kann beim Start überschrieben werden:

```bash
datenbanktool index search index.sqlite3 \
  --preset grosse-audios \
  --min-size-mib 500
```

Vorlage ersetzen:

```bash
datenbanktool index presets save grosse-audios \
  --category audio \
  --min-size-mib 250 \
  --replace
```

Vorlage löschen:

```bash
datenbanktool index presets delete grosse-audios --yes
```

**Auswirkung:** Suchvorlagen liegen standardmäßig in `~/.config/datenbanktool/search-presets.json`. Sie verändern weder Originaldateien noch den SQLite-Index. Überschreiben benötigt `--replace`, Löschen benötigt `--yes`.

## 3. Funktionen und Auswirkungen erklären lassen

Alle Hilfethemen anzeigen:

```bash
datenbanktool explain
```

Ordnerübersicht erklären:

```bash
datenbanktool explain folders
```

Sichere Wiederherstellung erklären:

```bash
datenbanktool explain restore
```

Die Erklärung enthält:

- Zweck,
- tatsächliche Wirkung,
- geschriebene Daten,
- Risikoeinstufung,
- sinnvollen Anwendungsfall,
- direkt nutzbares Beispiel.

## 4. Farben steuern

Automatisch nur in einem geeigneten Terminal:

```bash
datenbanktool --color auto index folders index.sqlite3
```

Farben immer einschalten:

```bash
datenbanktool --color always index folders index.sqlite3
```

Farben vollständig ausschalten:

```bash
datenbanktool --color never index folders index.sqlite3
```

Alternativ wird die verbreitete Umgebungsvariable `NO_COLOR` respektiert.

Kurze Hinweise ausschalten:

```bash
datenbanktool --no-hints index search index.sqlite3 musik
```

## 5. Bestehende Hauptfunktionen

### Index erstellen

```bash
datenbanktool index build ~/Medien \
  --database index.sqlite3 \
  --progress human
```

### Änderungen neu prüfen

```bash
datenbanktool index rescan ~/Medien \
  --database index.sqlite3 \
  --progress human
```

### Dateien suchen

```bash
datenbanktool index search index.sqlite3 urlaub --category image
```

### Änderungen anzeigen

```bash
datenbanktool index changes index.sqlite3
```

### Index sichern

```bash
datenbanktool index backup index.sqlite3 --output backup.sqlite3
```

### Sicherung wiederherstellen

```bash
datenbanktool index restore index.sqlite3 --backup backup.sqlite3
```

## Sicherheitsgrundsätze

- Originaldateien werden standardmäßig ausschließlich gelesen.
- Symbolischen Verzeichnissen wird standardmäßig nicht gefolgt.
- Berichte und Sicherungen werden nicht still überschrieben.
- Wiederherstellung erzeugt standardmäßig eine zusätzliche Rückfallsicherung.
- Normale Suche und Ordnerauswertung öffnen SQLite rein lesend.
- Der schnelle FTS5-Suchindex wird nur ausdrücklich aufgebaut.
- Keine automatische Löschung, Verschiebung oder Umbenennung.
- Farben dienen nur der Orientierung und ersetzen niemals Klartext.

## Automatische Prüfungen

```bash
python -m compileall -q src tests
PYTHONWARNINGS=error python -m unittest discover -s tests -v
```

GitHub Actions prüft Python 3.10 und Python 3.12.

## Aktuelle Grenzen

- Es gibt noch keine grafische Oberfläche mit echten Schaltflächen.
- Terminalprogramme unterstützen keine verlässlichen Maus-Tooltips; dort übernehmen Klartexthinweise und `explain` diese Aufgabe.
- Die Ordnerampel ist eine Priorisierungshilfe und keine automatische Lösch- oder Aufräumentscheidung.
- Suchvorlagen sind derzeit lokal pro Benutzer gespeichert.
- Ordnerberichte besitzen aktuell JSON und HTML, aber noch keinen CSV-Export.

## Nächster einfacher Schritt

Eine übersichtliche Startseite im Terminal bauen, die die wichtigsten Funktionen als nummeriertes Menü erklärt und startet.

## Sichere Zusatzverbesserung

Die Ordnerübersicht zusätzlich als CSV speichern, damit sie direkt in Tabellenprogrammen geöffnet werden kann.
