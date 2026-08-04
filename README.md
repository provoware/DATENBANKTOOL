# DATENBANKTOOL

> Sicheres Linux-Werkzeug zum Finden, Prüfen und übersichtlichen Strukturieren großer Dateisammlungen.

## Projektstatus

| Bereich | Stand |
|---|---|
| Version | `0.10.0-alpha.1` |
| SQLite-Schema | `3` |
| Entwicklungsfortschritt | **99 %** |
| Erledigte Hauptpunkte | **45** |
| Offene Hauptpunkte | **1** |
| Automatische Originaldateiänderungen | **Gesperrt** |
| Externe Laufzeitabhängigkeiten | **0** |
| Automatisierte Tests | **66/66** unter Python 3.10 und 3.12 |
| Quick-Abnahme | **600 Dateien · 11/11 bestanden** |
| Standard-Abnahme | **10.000 Dateien · 11/11 bestanden** |
| Reale Laienabnahme | **Noch offen** |

## Neu: Ordnerübersicht als CSV für LibreOffice Calc

Die normale Ordnerübersicht kann jetzt direkt als Tabelle gespeichert werden:

```bash
datenbanktool index folders index.sqlite3 \
  --csv ordneruebersicht.csv
```

Für **alle** passenden Ordner statt nur der sichtbaren Terminalseite:

```bash
datenbanktool index folders index.sqlite3 \
  --csv ordneruebersicht.csv \
  --all-pages
```

Die Terminalanzeige bleibt dabei paginiert. Das Tool nennt ausdrücklich, wie viele
Ordner vollständig exportiert wurden.

### CSV-Spalten

Die CSV enthält:

- Ampelstufe,
- Ampelstatus,
- Ampelbegründung,
- Ordnerpfad und Ordnertiefe,
- Dateizahl direkt im Ordner,
- Dateizahl einschließlich Unterordnern,
- direkte Größe in Byte,
- Gesamtgröße in Byte,
- Anzahl der Namenshinweise,
- Dateien in Duplikatgruppen,
- Pfad und Größe der gewählten größten Platzfresser.

Technische Eigenschaften:

- UTF-8 mit BOM,
- Semikolon als Trennzeichen,
- stabile Spalten,
- Rohgrößen in Byte für Formeln und Sortierung,
- atomare Dateifreigabe,
- kein stilles Überschreiben,
- vollständig offline.

Vorhandene Berichte werden nur ausdrücklich ersetzt:

```bash
datenbanktool index folders index.sqlite3 \
  --csv ordneruebersicht.csv \
  --all-pages \
  --overwrite-report
```

`--all-pages` ist nur zusammen mit JSON, CSV oder HTML zulässig. Dadurch kann keine
unbeabsichtigte, wirkungslose Vollauswertung gestartet werden.

## Neu: reproduzierbare Großbestandsabnahme

Der neue Befehl erzeugt ausschließlich synthetische Testdaten in einem neuen
Arbeitsordner:

```bash
datenbanktool acceptance \
  --profile quick \
  --workspace ./abnahme-quick
```

Verfügbare Profile:

| Profil | Dateien | Ordner | Standard-Zeitgrenze | Python-Speichergrenze |
|---|---:|---:|---:|---:|
| `quick` | 600 | 24 | 30 Sekunden | 256 MiB |
| `standard` | 10.000 | 250 | 600 Sekunden | 1.024 MiB |
| `large` | 100.000 | 1.000 | 3.600 Sekunden | 4.096 MiB |

Realistischer Standardlauf:

```bash
datenbanktool acceptance \
  --profile standard \
  --workspace ./abnahme-standard
```

Das `large`-Profil ist für ein geeignetes Zielsystem vorgesehen und wird nicht bei
jedem normalen Testlauf ausgeführt.

### Elf feste automatische Kriterien

1. Testbestand vollständig erzeugt.
2. Indexstatus `complete`.
3. Alle Testdateien importiert.
4. Keine Indexfehler.
5. Ordnerauswertung vorhanden.
6. CSV enthält alle Ordnerzeilen.
7. CSV besitzt UTF-8-BOM.
8. Quelldateien nach der Auswertung unverändert.
9. CSV- und `--all-pages`-Hilfe vorhanden.
10. Laufzeit innerhalb der Profilgrenze.
11. Python-Spitzenspeicher innerhalb der Profilgrenze.

Vor und nach der Auswertung wird jede Testdatei über Pfad, Größe und
Nanosekunden-Änderungszeit verglichen.

### Erzeugte Abnahmedateien

Im neuen Arbeitsordner entstehen:

```text
acceptance-result.json
acceptance-report.md
NOVICE_ACCEPTANCE_CHECKLIST.md
ordneruebersicht.csv
index.sqlite3
dataset/
```

Ein vorhandener Arbeitsordner wird vollständig abgelehnt. Es wird nichts gelöscht,
bereinigt oder wiederverwendet.

## Nachgewiesene Referenzläufe

GitHub Actions auf Ubuntu 24.04 und Python 3.12:

| Profil | Dateien | Kriterien | Laufzeit | Python-Spitzenspeicher |
|---|---:|---:|---:|---:|
| Quick | 600 | 11/11 | 1,086 s | 1.326.097 Byte |
| Standard | 10.000 | 11/11 | 17,781 s | 13.394.783 Byte |

Die Ergebnisse sind reproduzierbare Referenzwerte der CI-Umgebung und keine Garantie
für identische Laufzeiten auf anderer Hardware.

Die Berichte beider Profile werden als GitHub-Actions-Artefakte 14 Tage archiviert.

## Reale Laienabnahme

Automatische Prüfungen können keine unerfahrene Testperson ersetzen. Deshalb erzeugt
jedes Profil eine `NOVICE_ACCEPTANCE_CHECKLIST.md` mit Aufgaben zu:

- Startseite und Orientierung,
- Ordnerübersicht,
- vollständigem CSV-Export,
- mehrschichtiger Hilfe,
- Sicherheitsverständnis,
- kontrolliertem Überschreibfehler,
- Zeitmessung und Verständlichkeitsbewertung.

Die reale Laienabnahme bleibt ausdrücklich **offen**, bis eine reale Person die
Checkliste auf einem Zielsystem ausgefüllt hat.

## Ordnervergleich

Der vorhandene rein lesende Vergleich bleibt verfügbar:

```bash
datenbanktool index folder-compare index.sqlite3
```

Er zeigt gewachsene, kleiner gewordene, neue, entfernte und unveränderte Ordner zwischen
zwei abgeschlossenen Scans desselben Stammordners.

## Hilfe

```bash
# CSV und vollständiger Export
datenbanktool help folders --level guided

# Abnahmeprofile
datenbanktool help acceptance --level guided

# Ordnervergleich
datenbanktool help folder-compare --level guided
```

In der Startseite:

```text
?2   ausführliche Ordnerhilfe
g2   Ordnerübersicht Schritt für Schritt
?10  ausführliche Vergleichshilfe
g10  Ordnervergleich Schritt für Schritt
```

## Sicherheitsgrundsätze

- Normale Scans und Auswertungen verändern keine Originaldateien.
- CSV-, JSON- und HTML-Berichte werden atomar geschrieben.
- Vorhandene Berichte werden nicht still überschrieben.
- Vollständige Exporte benötigen den sichtbaren Schalter `--all-pages`.
- Abnahmetests schreiben nur in einen neuen Arbeitsordner.
- Vorhandene Arbeitsordner werden nicht wiederverwendet.
- Persönliche Dateien werden nicht als Abnahmedaten verwendet.
- Jede CLI-Funktion besitzt eine maschinenlesbare `CommandPolicy`.
- Shell-Auswertung, `eval`, `exec` und `os.system` bleiben verboten.
- Automatisches Löschen, Verschieben und Umbenennen bleibt gesperrt.

## Modulare Struktur

| Modul | Zuständigkeit |
|---|---|
| `core/folder_csv.py` | LibreOffice-kompatibler Ordner-CSV-Export |
| `core/acceptance.py` | Profile, Datensatz, Messung und Berichte |
| `cli_acceptance.py` | sicherer öffentlicher Abnahmebefehl |
| `cli_reports.py` | Ordner-, Änderungs- und Dateiberichte |
| `cli_folder_compare.py` | Ordnervergleich |
| `cli.py` | Zusammensetzung und zentrale Fehlergrenze |

Globale Regeln stehen in `MAINTENANCE_RULES.md` und `maintenance_rules.json`.

## Entwicklung und Prüfungen

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
python -m compileall -q src tests
PYTHONWARNINGS=error python -m unittest discover -s tests -v
```

GitHub Actions prüft:

- Python 3.10 und 3.12,
- 66 Tests mit Warnungen als Fehler,
- Quick-Profil mit 600 Dateien,
- Standard-Profil mit 10.000 Dateien,
- Archivierung der Abnahmeberichte.

## Aktuelle Grenzen

- Die reale Laienabnahme ist noch nicht durchgeführt.
- Das `large`-Profil mit 100.000 Dateien ist implementiert, aber noch nicht auf der
  vorgesehenen Zielhardware ausgeführt.
- Leere Ordner ohne Dateien erscheinen weiterhin nicht im Index.
- Elternordner enthalten bewusst die Werte ihrer Unterordner.
- Der Ordnervergleich zeigt genau zwei Sitzungen, noch keine Zeitreihe.
- Vergleichsexporte enthalten derzeit die gewählte Seite und besitzen noch keinen
  eigenen `--all-pages`-Schalter.
- Die Oberfläche bleibt terminalbasiert.

## Mögliche weitere Upgrades

- Größenentwicklung eines Ordners über mehr als zwei Scans als Zeitreihe anzeigen.
- Vollständigen `--all-pages`-Export auch für den Ordnervergleich ergänzen.
- Reale Laienabnahme auf Kubuntu durchführen und Befunde dokumentieren.
- `large`-Profil mit 100.000 Dateien auf der Zielhardware vermessen.
- Grafische Oberfläche mit Dateiauswahldialogen entwickeln.

## Direkt folgender technischer Entwicklungsschritt

**Ordner-Zeitreihe:** Die Größenentwicklung eines Ordners über mehrere abgeschlossene
Scans rein lesend anzeigen.

## Alternative Verbesserung mit hohem Nutzen und geringem Risiko

**Vollständiger Vergleichsexport:** JSON, CSV und HTML des Ordnervergleichs mit einem
sichtbaren `--all-pages`-Schalter über alle Filtertreffer exportieren.
