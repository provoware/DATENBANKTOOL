# DATENBANKTOOL

> Sicheres Linux-Werkzeug zum Finden, Prüfen und übersichtlichen Strukturieren großer Dateisammlungen.

## Projektstatus

| Bereich | Stand |
|---|---|
| Version | `0.12.0-alpha.1` |
| SQLite-Schema | `3` |
| Entwicklungsfortschritt | **99 %** |
| Erledigte Hauptpunkte | **49** |
| Offene Hauptpunkte | **1** |
| Automatische Originaldateiänderungen | **Gesperrt** |
| Externe Laufzeitabhängigkeiten | **0** |
| Automatisierte Tests | **77/77** unter Python 3.10 und 3.12 |
| Quick-Abnahme | **600 Dateien · 11/11 bestanden** |
| Standard-Abnahme | **10.000 Dateien · 11/11 bestanden** |
| Reale Laienabnahme | **Noch offen** |

## Neu: geführte Ordner-Zeitreihe

Die Ordner-Zeitreihe ist jetzt als eigener Punkt in der geführten Startseite verfügbar:

```bash
datenbanktool start
```

```text
11. Ordner-Zeitreihe
```

Der Assistent fragt nacheinander ab:

1. Indexdatenbank,
2. relativen Ordnerpfad oder `.`,
3. optionale älteste und neueste Scan-ID,
4. höchstens 2 bis 500 Zeitpunkte,
5. optional JSON, CSV oder HTML,
6. neuen Zielpfad für den Bericht.

Jede Eingabe besitzt eine Feldhilfe über `?`. Zahlenbereiche werden vor dem Start
geprüft. Der geplante Befehl wird sichtbar angezeigt und ausschließlich als sichere
Argumentliste gestartet – ohne Shell-Auswertung.

### Mehrschichtige Hilfe

```text
?11   ausführliche Erklärung
g11   Schritt-für-Schritt-Anleitung
```

Direkt aufrufbar:

```bash
datenbanktool help folder-timeline --level detail
datenbanktool help folder-timeline --level guided
datenbanktool help --find Speicherentwicklung
```

Bei einem Fehler nennt die Startseite konkrete Ursachen und Lösungen, etwa fehlende
zweite Scans, unpassende Sitzungen, unsichere Ordnerpfade oder vorhandene Berichte.

## Neu: barrierefreie Offline-Trendgrafiken

Der HTML-Zeitreihenbericht enthält jetzt zwei vollständig lokale SVG-Liniendiagramme:

- **Größenverlauf** des Ordners einschließlich Unterordnern,
- **Dateizahlverlauf** einschließlich Unterordnern.

```bash
datenbanktool index folder-timeline index.sqlite3 Musik \
  --html musik-verlauf.html
```

Eigenschaften:

- kein JavaScript,
- keine externen Bilder, Schriften, Bibliotheken oder Internetadressen,
- `figure`, `figcaption`, SVG-`title` und SVG-`desc`,
- sichtbare Achsen-, Scan- und Wertbeschriftungen,
- jeder Datenpunkt mit Tastaturfokus und genauer `aria-label`-Beschreibung,
- textliche Zusammenfassung von Minimum, Maximum und Nettoänderung,
- vollständige Wertetabelle direkt unter den Diagrammen,
- Farben niemals als alleinige Information.

Bei langen Zeitreihen werden sichtbare Achsenbeschriftungen reduziert, während jeder
Datenpunkt und jede Tabellenzeile vollständig erhalten bleibt.

## Direkter Zeitreihenbefehl

```bash
datenbanktool index folder-timeline index.sqlite3 Musik
```

Ohne Ordnerangabe wird der gesamte Stammordner `.` ausgewertet:

```bash
datenbanktool index folder-timeline index.sqlite3
```

Die Ausgabe enthält pro Scan Scan-ID, UTC-Zeitpunkt, Scan-Modus, rekursive Dateizahl,
Gesamtgröße, Differenzen, Prozentwert, Zustand und verständliche Begründung.

```bash
datenbanktool index folder-timeline index.sqlite3 Musik \
  --from-session-id 3 \
  --to-session-id 12 \
  --limit 100 \
  --json musik-verlauf.json \
  --csv musik-verlauf.csv \
  --html musik-verlauf.html
```

CSV verwendet UTF-8-BOM und Semikolon für LibreOffice Calc. Vorhandene Ziele werden
nur mit `--overwrite-report` ersetzt.

## Vollständiger Ordnervergleichsexport

```bash
datenbanktool index folder-compare index.sqlite3 \
  --page-size 25 \
  --csv ordnervergleich.csv \
  --all-pages
```

`--all-pages` exportiert sämtliche gefilterten und sortierten JSON-, CSV- oder
HTML-Zeilen. Das Terminal bleibt paginiert, und die vollständige Ergebnismenge wird
nur einmal berechnet.

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

## 0.12-Funktionsreferenz

GitHub Actions auf Ubuntu 24.04 und Python 3.12, Commit
`b27e678259474ae459f08751ba0b386cccb653a3`:

| Profil | Dateien | Kriterien | Laufzeit | Python-Spitzenspeicher |
|---|---:|---:|---:|---:|
| Quick | 600 | 11/11 | 1,015 s | 1.325.982 Byte |
| Standard | 10.000 | 11/11 | 16,116 s | 13.398.883 Byte |

Die automatisierten Tests liefen mit `PYTHONWARNINGS=error`. Die Werte sind eine
reproduzierbare CI-Referenz und keine Garantie für andere Hardware.

## Sicherheit

- Zeitreihe, Diagramme und Hilfen verändern weder SQLite noch Originaldateien.
- Zeitreihen-SQLite wird mit `mode=ro` und `PRAGMA query_only=ON` geöffnet.
- Absolute Ordnerpfade und `..` werden abgelehnt.
- Geführte Befehle werden als Argumentlisten und niemals über eine Shell gestartet.
- HTML enthält kein JavaScript und keine externen Ressourcen.
- Berichte werden atomar geschrieben und nicht still überschrieben.
- Jeder öffentliche CLI-Befehl besitzt eine geprüfte `CommandPolicy`.
- Automatisches Löschen, Verschieben und Umbenennen bleibt gesperrt.

## Modulare Struktur

| Modul | Zuständigkeit |
|---|---|
| `core/folder_timeline.py` | Sitzungsauswahl, rekursive Messwerte und Zustände |
| `core/folder_timeline_help.py` | Detail-, Schritt-, Feld- und Fehlerhilfe |
| `core/folder_timeline_charts.py` | lokale, barrierefreie SVG-Trendgrafiken |
| `core/folder_timeline_exports.py` | atomare JSON-, CSV- und HTML-Ausgabe |
| `core/guided_home.py` | Startseitenpunkt 11 und validierter Dialog |
| `cli_folder_timeline.py` | direkter Parser und Terminaldarstellung |

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

- Die reale Laienabnahme ist noch nicht durchgeführt.
- Das `large`-Profil wurde noch nicht auf Zielhardware ausgeführt.
- Leere Ordner ohne Dateien erscheinen nicht im aktuellen Dateisnapshot-Schema.
- Elternordner enthalten rekursive Unterordnerwerte.
- Diagrammpunkte sind nach Scan-Reihenfolge gleichmäßig verteilt, nicht nach realem
  Zeitabstand.
- Bei 500 Punkten entstehen entsprechend viele fokussierbare SVG-Punkte; die Tabelle
  bleibt die kompakteste vollständige Alternative.
- Zeitreihen zeigen derzeit jeweils einen relativen Ordner.
- Die Oberfläche bleibt terminalbasiert.

## Mögliche weitere Upgrades

- Häufig verwendete Zeitreihenordner als validierte lokale Vorlagen speichern.
- Optionale textlich erklärte Warnschwellen für starkes Wachstum ergänzen.
- Mehrere ausgewählte Ordner gemeinsam als Trends darstellen.
- Reale Laienabnahme und 100.000-Dateien-Zieltest durchführen.
- Später eine grafische Oberfläche mit Pfadauswahldialogen ergänzen.

## Direkt folgender technischer Entwicklungsschritt

**Zeitreihen-Vorlagen:** Häufig geprüfte relative Ordnerpfade lokal, validiert und
überschreibgeschützt speichern und direkt in der geführten Startseite auswählbar machen.

## Alternative Verbesserung mit hohem Nutzen und geringem Risiko

**Trendgrenzen:** Optionale rein lesende Warnschwellen für starkes Größen- oder
Dateiwachstum in Terminal und HTML ergänzen – immer mit Klartext und Begründung.
