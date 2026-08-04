# DATENBANKTOOL

> Sicheres Linux-Werkzeug zum Finden, Prüfen und übersichtlichen Strukturieren großer Dateisammlungen.

## Projektstatus

| Bereich | Stand |
|---|---|
| Version | `0.13.0-alpha.1` |
| SQLite-Schema | `3` |
| Entwicklungsfortschritt | **99 %** |
| Erledigte Hauptpunkte | **51** |
| Offene Hauptpunkte | **1** |
| Automatische Originaldateiänderungen | **Gesperrt** |
| Externe Laufzeitabhängigkeiten | **0** |
| Automatisierte Tests | **86/86** unter Python 3.10 und 3.12 |
| Quick-Abnahme | **600 Dateien · 11/11 bestanden** |
| Standard-Abnahme | **10.000 Dateien · 11/11 bestanden** |
| Reale Laienabnahme | **Noch offen** |

## Neu: lokale Zeitreihen-Vorlagen

Häufig geprüfte relative Ordnerpfade können unter einem verständlichen Namen gespeichert
werden. Eine Vorlage enthält bewusst **keinen Datenbankpfad**, keine Scan-Ergebnisse und
keine Originaldateien.

```bash
datenbanktool index timeline-presets save Musik Musik/Archiv \
  --description "Wöchentliche Größenprüfung"
```

Verwalten:

```bash
datenbanktool index timeline-presets list
datenbanktool index timeline-presets show Musik
datenbanktool index timeline-presets delete Musik --yes
```

Sicherheitsvertrag:

- Ordnerpfade sind relativ; absolute Pfade und `..` werden abgelehnt.
- Namen besitzen 1 bis 64 Zeichen, Beschreibungen höchstens 240 Zeichen.
- Gleichnamige Vorlagen werden ohne `--replace` nicht überschrieben.
- Löschen benötigt `--yes`.
- Die JSON-Konfiguration wird atomar mit Dateiberechtigung `0600` geschrieben.
- Standardpfad: `$XDG_CONFIG_HOME/datenbanktool/timeline-presets.json` beziehungsweise
  `~/.config/datenbanktool/timeline-presets.json`.

## Direkte Auswahl auf der Startseite

```bash
datenbanktool start
```

```text
11. Ordner-Zeitreihe
12. Zeitreihen-Vorlage speichern
```

Punkt 11 zeigt vorhandene Vorlagen nummeriert mit Name, Ordner und Beschreibung. Eine
Vorlage kann per Nummer oder exaktem Namen gewählt werden. Der Ordner bleibt vor dem
Start sichtbar und kann bewusst angepasst werden. Punkt 12 schreibt erst nach sichtbarer
Befehlsprüfung und ausdrücklicher Bestätigung eine neue Vorlage.

Hilfen:

```text
?11 / g11   Zeitreihe erklären oder Schritt für Schritt führen
?12 / g12   Vorlagenspeicherung erklären oder Schritt für Schritt führen
?           aktuelles Eingabefeld erklären
```

## Neu: begründete Trendgrenzen

Zeitreihen können optional rein lesende Prozentgrenzen für positives Wachstum erhalten:

```bash
datenbanktool index folder-timeline index.sqlite3 \
  --preset Musik \
  --warn-size-growth-percent 25 \
  --warn-file-growth-percent 50 \
  --html musik-verlauf.html
```

Berechnung:

- Vergleich mit dem unmittelbar vorherigen **sichtbaren** Scan.
- Nur positives Wachstum kann eine Warnschwelle erreichen.
- Bei einem Ausgangswert von null bleibt der Prozentwert leer; es wird nicht durch null
  geteilt und keine künstliche Prozentzahl erzeugt.
- Zulässig sind endliche Werte von 0 bis 1.000.000 Prozent.

Ein Treffer erscheint als:

```text
ROT – Trendgrenze erreicht
```

Daneben stehen immer Messwert, konfigurierte Warnschwelle und Begründung. Zusätzlich
wird ausdrücklich erklärt: Die Warnung ist ein rein lesender Hinweis und **keine
Schadens-, Lösch- oder Aufräumentscheidung**.

## Terminal, JSON, CSV und Offline-HTML

Die neuen Werte erscheinen konsistent in allen Ausgaben:

- Terminal: aktive Grenzen, Trefferzahl, Datei- und Größenänderung in Prozent.
- JSON: konfigurierte Grenzen, Dateiprozent, Trefferstatus und Begründungen.
- CSV: getrennte Spalten für Verlauf, Warnstatus, Rohwerte und Warnschwellen.
- HTML: sichtbare Warnzusammenfassung, vollständige Begründungstabelle und markierte
  SVG-Datenpunkte mit dem Klartext `Warnung`.

Der HTML-Bericht bleibt vollständig lokal:

- kein JavaScript,
- keine externen Bilder, Schriften, Bibliotheken oder Internetadressen,
- zwei getrennte SVG-Diagramme für Größe und Dateizahl,
- `figure`, `figcaption`, SVG-`title`, `desc` und `aria-labelledby`,
- fokussierbare Datenpunkte mit genauer ARIA-Beschreibung,
- vollständige Wertetabelle unter den Diagrammen,
- Farben niemals als alleinige Information.

## Zeitreihe ohne Vorlage

```bash
datenbanktool index folder-timeline index.sqlite3 Musik/Archiv \
  --from-session-id 3 \
  --to-session-id 12 \
  --limit 100 \
  --csv musik-verlauf.csv
```

Ohne Ordner oder Vorlage wird `.` verwendet und damit der gesamte gespeicherte
Stammordner ausgewertet.

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

## 0.13-Funktionsreferenz

GitHub Actions Run `30927676213` auf Ubuntu 24.04, Funktionscommit
`8ded929533f806c739a7139b47d16379a788cfb0`:

| Profil | Dateien | Kriterien | Laufzeit | Python-Spitzenspeicher |
|---|---:|---:|---:|---:|
| Quick | 600 | 11/11 | 1,129 s | 1.324.226 Byte |
| Standard | 10.000 | 11/11 | 18,150 s | 13.398.233 Byte |

Zusätzlich bestanden 86/86 Tests unter Python 3.10 und Python 3.12 mit
`PYTHONWARNINGS=error`. Die Messwerte sind CI-Referenzen und keine Garantie für andere
Hardware.

## Sicherheit

- Zeitreihe und Trendgrenzen öffnen SQLite ausschließlich lesend.
- Vorlagen speichern keine Datenbankpfade und lesen keine Originaldateien.
- Geführte Befehle werden als Argumentlisten und niemals über eine Shell gestartet.
- Vorlagen und Berichte werden atomar geschrieben und nicht still überschrieben.
- Warnungen verändern keine Daten und lösen keine Folgeaktion aus.
- Jeder öffentliche CLI-Befehl besitzt eine geprüfte `CommandPolicy`.
- Automatisches Löschen, Verschieben und Umbenennen von Originaldateien bleibt gesperrt.

## Modulare Struktur

| Modul | Zuständigkeit |
|---|---|
| `core/timeline_presets.py` | Validierung, atomare lokale Vorlagen und Modus 0600 |
| `cli_timeline_presets.py` | list/show/save/delete und Seiteneffektvertrag |
| `core/folder_timeline.py` | Prozentwerte, Trendgrenzen und begründete Ampeln |
| `core/guided_home.py` | Vorlagenauswahl, Speicherung und Schwellenfelder |
| `core/folder_timeline_exports.py` | JSON-, CSV- und HTML-Warninformationen |
| `core/folder_timeline_charts.py` | sichtbare und zugängliche Warnmarken im SVG |

## Aktuelle Grenzen

- Die reale Laienabnahme ist noch nicht durchgeführt.
- Das `large`-Profil wurde noch nicht auf Zielhardware ausgeführt.
- Die Startseite kann Vorlagen speichern und auswählen; geführtes Anzeigen, Ersetzen und
  Löschen ist noch nicht als eigenes Untermenü vorhanden.
- Vorlagen speichern bewusst nur den Ordner, nicht Warnschwellen oder Berichtspfade.
- Prozentwerte sind bei vorherigem Wert null nicht berechenbar.
- Warnschwellen betrachten Übergänge, keine langfristige statistische Anomalie.
- Je Zeitreihe wird weiterhin ein relativer Ordner dargestellt.
- Diagramme positionieren Punkte nach Scan-Reihenfolge, nicht proportional zum
  tatsächlichen Zeitabstand.

## Mögliche weitere Upgrades

- Geführtes Vorlagen-Untermenü für Anzeigen, Ersetzen und Löschen.
- Mehrere ausgewählte Ordner gemeinsam als getrennte Trends darstellen.
- Diagrammpunkte optional nach realem Scan-Zeitabstand positionieren.
- Reale Laienabnahme und 100.000-Dateien-Zieltest durchführen.
- Später eine grafische Oberfläche mit Pfadauswahldialogen ergänzen.

## Direkt folgender technischer Entwicklungsschritt

**Geführte Vorlagenverwaltung:** Zeitreihen-Vorlagen auf der Startseite zusätzlich
anzeigen, bewusst ersetzen und nach Namensprüfung bestätigt löschen können.

## Alternative Verbesserung mit hohem Nutzen und geringem Risiko

**Mehrordner-Zeitreihe:** Mehrere ausgewählte relative Ordner rein lesend in einem
Bericht darstellen – mit getrennten Linien, eindeutiger Legende und ausdrücklichem
Hinweis, dass rekursive Eltern- und Kindwerte nicht addiert werden dürfen.
