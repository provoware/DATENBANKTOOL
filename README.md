# DATENBANKTOOL

> Ein sicheres Linux-Werkzeug zum Finden, Prüfen und übersichtlichen Strukturieren großer chaotischer Dateisammlungen.

## Projektstatus

| Bereich | Stand |
|---|---|
| Version | `0.6.0-alpha.1` |
| SQLite-Schema | `3` |
| Entwicklungsfortschritt | **84 %** |
| Erledigte Hauptpunkte | **37** |
| Offene Hauptpunkte | **7** |
| Originaldateien verändern | **Nein** |
| Standardmodus | **Rein lesend** |
| Automatisches Löschen oder Verschieben | **Gesperrt** |

## Neu in dieser Version

1. **Geführte Startseite:** Die wichtigsten Funktionen stehen als nummerierte Auswahl bereit.
2. **Wirkung vor dem Start:** Jede Auswahl erklärt, ob nur gelesen oder eine Index-/Sicherungsdatei geschrieben wird.
3. **Sichere Ausführung:** Eingaben werden als feste Argumentliste übergeben und nicht durch eine Shell ausgewertet.
4. **Bestätigungsschutz:** Indexaufbau, Re-Scan und Sicherung starten erst nach einer zusätzlichen Bestätigung.
5. **Robuster Programmstart:** Ohne Befehl öffnet sich das Menü nur in einem echten Terminal; Skripte und Umleitungen blockieren nicht.
6. **Bessere Codequalität:** Startlogik, Menümodell und bestehende Befehlslogik sind klar getrennt und unabhängig testbar.

## Geführte Startseite verwenden

```bash
datenbanktool start
```

In einem echten Terminal kann auch nur folgender Befehl verwendet werden:

```bash
datenbanktool
```

Die Startseite zeigt diese Bereiche:

1. Dateien suchen
2. Ordnerübersicht
3. Änderungen anzeigen
4. Indexstatus prüfen
5. Neuen Index anlegen
6. Ordner erneut prüfen
7. Index sichern
8. Suchvorlagen anzeigen
9. Funktionen erklären
0. Beenden

### Bedienregeln

- Eine angezeigte Nummer startet den geführten Dialog.
- `q` bricht nur den aktuellen Schritt ab und führt zum Hauptmenü zurück.
- `0` beendet die Startseite.
- Der zuletzt verwendete Datenbank- und Ordnerpfad wird innerhalb derselben Sitzung vorgeschlagen.
- Vor der Ausführung wird der vollständige geplante Befehl angezeigt.
- Schreibende Index- und Sicherungsaktionen benötigen eine ausdrückliche Bestätigung.

### Farben der Startseite steuern

```bash
datenbanktool start --color auto
datenbanktool start --color always
datenbanktool start --color never
```

Farbe ist nie das einzige Signal. Neben jeder Ampel stehen Farbnamen, Wirkung und Begründung im Klartext.

### Sicherheitswirkung

Die Startseite selbst verändert keine Datei. Sie führt ausschließlich vorhandene, getestete DATENBANKTOOL-Befehle aus. Nutzereingaben werden nicht als Shell-Befehl interpretiert. Pfade mit Leerzeichen bleiben deshalb sichere einzelne Argumente.

## Ampeln richtig verstehen

| Ampel | Bedeutung |
|---|---|
| **GRÜN – Nur lesen** | Index und Originaldateien bleiben unverändert. |
| **GELB – Schreibt Index/Sicherung** | Nur die angekündigte SQLite- oder Sicherungsdatei wird geschrieben. |
| **ROT – Dringend prüfen** | Wird in Auswertungen für besonders auffällige Ergebnisse verwendet. |

Die Ampel sagt **nicht**, dass eine Datei beschädigt oder gefährlich ist. Sie hilft nur dabei, Wirkung und Prüfbedarf schnell zu erkennen.

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

## Ordnerübersicht anzeigen

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

## Suchvorlage speichern

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

## Funktionen und Auswirkungen erklären lassen

Alle Hilfethemen anzeigen:

```bash
datenbanktool explain
```

Startseite erklären:

```bash
datenbanktool explain start
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

## Farben bestehender Befehle steuern

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

## Bestehende Hauptfunktionen

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
- Geführte Schreibaktionen benötigen eine zusätzliche Bestätigung.
- Die Startseite verwendet keine Shell-Auswertung.
- Keine automatische Löschung, Verschiebung oder Umbenennung.
- Farben dienen nur der Orientierung und ersetzen niemals Klartext.

## Codequalität

Die Startseite wurde bewusst außerhalb der bereits großen `cli.py` umgesetzt:

- `entrypoint.py` entscheidet nur zwischen Startseite und bestehender CLI.
- `terminal_home.py` enthält Menümodell, Eingabeprüfung und geführte Dialoge.
- Ein austauschbarer `command_runner` macht den Ablauf ohne echte Dateioperationen testbar.
- Ein-/Ausgabeströme werden injiziert und können in Tests vollständig simuliert werden.
- Menüeinträge liegen in einer unveränderlichen, zentralen Definition.
- Doppelte Auswahlnummern werden beim Start erkannt.
- Nicht-interaktive Aufrufe ohne Befehl blockieren nicht.
- Alle neuen Quelldateien halten die konfigurierte maximale Zeilenlänge ein.

## Automatische Prüfungen

```bash
python -m compileall -q src tests
PYTHONWARNINGS=error python -m unittest discover -s tests -v
```

GitHub Actions prüft Python 3.10 und Python 3.12. Aktuell bestehen **39 von 39 Tests** in beiden Umgebungen.

## Aktuelle Grenzen

- Es gibt noch keine grafische Oberfläche mit echten Schaltflächen.
- Die zentrale `cli.py` ist weiterhin groß und sollte schrittweise in kleinere Befehlsmodule zerlegt werden.
- Terminalprogramme unterstützen keine verlässlichen Maus-Tooltips; dort übernehmen Klartexthinweise und `explain` diese Aufgabe.
- Die Ordnerampel ist eine Priorisierungshilfe und keine automatische Lösch- oder Aufräumentscheidung.
- Suchvorlagen sind derzeit lokal pro Benutzer gespeichert.
- Ordnerberichte besitzen aktuell JSON und HTML, aber noch keinen CSV-Export.

## Nächster einfacher Schritt

Den großen Befehlsblock in kleinere Bausteine teilen, damit einzelne Funktionen leichter geprüft und geändert werden können.

## Sichere Zusatzverbesserung

Die Ordnerübersicht zusätzlich als CSV speichern, damit sie direkt in Tabellenprogrammen geöffnet werden kann.
