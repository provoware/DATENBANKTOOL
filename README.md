# DATENBANKTOOL

**Erledigt:** vollständig lesender Prüfungsbefehl für ausdrücklich ausgewählte Wiederherstellungsprotokolle. Er validiert das feste Schema, beide UTC-Zeiten, drei unterschiedliche absolute Pfade und drei SHA-256-Werte und vergleicht vorhandene Dateien ohne Wiederherstellung, Änderung oder Löschung. Weiterhin vorhanden: Wiederanlauf-Diagnose, optionales Restore-Protokoll, geprüfter Konfigurations-Restore, automatischer Rückfall, Sicherungskatalog, Autosave, Crashberichte und SQLite-Härtung.

**Offen:** reale Laienabnahme auf einem Kubuntu-Zielsystem.

**Entwicklungsfortschritt:** **99 %** · **66 Hauptpunkte erledigt** · **1 Hauptpunkt offen**.

**Mögliche Upgrades aus `UPGRADE_POOL.md`:** geführte Protokollprüfung auf der Startseite, optionaler SHA-256-Pin für die Protokolldatei, Mehrordner-Zeitreihe und später eine barrierefreie grafische Oberfläche.

> Lokales Linux-Indexwerkzeug für große Dateisammlungen. Persönliche Originaldateien werden nicht automatisch verändert.

## Projektstatus

| Bereich | Stand |
|---|---|
| Projektversion | `0.20.0-alpha.1` |
| Paketversion | `0.20.0a1` |
| Python | `>=3.10` |
| SQLite-Schema | `3` |
| Wiederanlauflimit | **12 verschiedene Indexdateien** |
| Originaldateiänderungen | **technisch gesperrt** |
| Externe Laufzeitabhängigkeiten | **0** |
| Automatische Tests | **151 unter Python 3.10 und 3.12** |
| Reale Laienabnahme | **offen** |

## Einfach starten

```bash
datenbanktool start
```

## Wiederherstellungsprotokoll vollständig lesend prüfen

Terminalausgabe:

```bash
datenbanktool index backups verify-log /pfad/restore-nachweis.json
```

Maschinenlesbar:

```bash
datenbanktool index backups verify-log /pfad/restore-nachweis.json --json
```

Der Befehl prüft zuerst die ausdrücklich ausgewählte Protokolldatei:

1. normales UTF-8-JSON und keine symbolische Verknüpfung,
2. exakt das unterstützte Protokollschema `1`,
3. Ereignis `configuration_restore`,
4. Konfigurationsart `search` oder `timeline`,
5. zwei gültige UTC-Zeiten in richtiger Reihenfolge,
6. genau drei unterschiedliche absolute Dateipfade,
7. genau drei kleingeschriebene SHA-256-Werte mit jeweils 64 Hexzeichen,
8. keine fehlenden oder unerwarteten Schemafelder.

Anschließend werden die drei referenzierten Dateien ausschließlich lesend geöffnet und gehasht:

- aktive Datei nach der Wiederherstellung,
- ausgewählte Sicherung,
- automatische Rückfallsicherung.

Symlinks werden nicht verfolgt. Fehlende Dateien werden als unvollständiger Nachweis, abweichende Hashes als Integritätsfehler und vollständig übereinstimmende Dateien als bestätigt ausgegeben.

| Rückgabecode | Bedeutung |
|---:|---|
| `0` | Protokoll gültig und alle drei Dateien stimmen überein |
| `1` | Protokoll gültig, aber Datei fehlt, ist nicht sicher lesbar oder weicht ab |
| `2` | Protokolldatei oder festes Schema ist ungültig |

Es wird keine Wiederherstellung gestartet. Das Protokoll und seine referenzierten Dateien werden nicht verändert oder gelöscht.

## Alle Wiederanläufe nur prüfen

```bash
datenbanktool index recovery
datenbanktool index recovery --json
```

Die Diagnose zeigt Prüfstatus, Quellordner, Indexdatei, SQLite-Sitzung, Zustand, Phase, bestätigte Dateizahl, UTC-Zeit und Startbarkeit. Sie startet keinen Scan und verwirft keinen Eintrag.

## Konfigurationssicherung zuerst nur vergleichen

```bash
datenbanktool index backups compare index.sqlite3 SICHERUNG
datenbanktool index backups compare index.sqlite3 SICHERUNG --json
```

Der Vergleich zeigt aktive Datei, Vorlagenzahlen, Hinzufügungen, Entfernungen, Ersetzungen, unveränderte Vorlagen und die SHA-256-Werte beider Dateien, ohne etwas zu verändern.

## Genau eine Konfigurationssicherung wiederherstellen

```bash
datenbanktool index backups restore index.sqlite3 SICHERUNG \
  --confirm-name EXAKTER_DATEINAME \
  --yes
```

Vor dem Überschreiben entsteht eine neue geprüfte Rückfallsicherung. Aktive Datei und ausgewählte Sicherung werden erneut per SHA-256 geprüft. Die Veröffentlichung erfolgt atomar mit Modus `0600`; eine fehlgeschlagene Nachprüfung löst den automatisch bestätigten Rückfall aus.

## Optionales Wiederherstellungsprotokoll erzeugen

```bash
datenbanktool index backups restore index.sqlite3 SICHERUNG \
  --confirm-name EXAKTER_DATEINAME \
  --yes \
  --restore-log /neuer/pfad/restore-nachweis.json
```

Das Protokoll entsteht erst nach einer erfolgreich bestätigten Wiederherstellung und enthält ausschließlich UTC-Zeiten, drei Pfade und drei SHA-256-Werte. Vorlagen, Konfigurationsinhalte, Argumente und Geheimnisse sind ausgeschlossen. Das Ziel wird atomar mit Modus `0600` angelegt und niemals überschrieben, automatisch benannt, rotiert oder gelöscht.

## Optionale Sicherung vor Vorlagenänderungen

```bash
datenbanktool index presets save Audio --replace --backup-before-change
datenbanktool index presets delete Audio --backup-before-change --yes
datenbanktool index timeline-presets save Musik Archiv \
  --replace --backup-before-change
```

Ohne `--backup-before-change` entsteht keine Sicherung. Vorhandene Sicherungen werden niemals automatisch rotiert oder gelöscht.

## Sicherungsübersicht und Einzellöschung

```bash
datenbanktool index backups list index.sqlite3
datenbanktool index backups list index.sqlite3 --json
```

```bash
datenbanktool index backups delete index.sqlite3 SICHERUNG \
  --confirm-name EXAKTER_DATEINAME \
  --yes
```

Aktive Dateien, unbekannte Pfade, Verzeichnisse und Symlinks sind ausgeschlossen.

## Startklar prüfen

```bash
datenbanktool check
datenbanktool check --database index.sqlite3
```

## Sicherheitsgrenzen

- Originaldateien bleiben schreibgeschützt.
- CLI-Fachmodule verwenden keine Shell-Auswertung.
- Protokollprüfung besitzt eine `CommandPolicy` ohne Schreibwirkung.
- Protokoll und referenzierte Dateien werden mit `O_NOFOLLOW` ausschließlich lesend geöffnet.
- Fehlende Dateien werden nicht neu angelegt oder rekonstruiert.
- Abweichende Dateien werden nur gemeldet und niemals automatisch ersetzt.
- Hardwaredefekte, volles oder beschädigtes Dateisystem, Kerneldefekte und physischer Verlust bleiben außerhalb des Anwendungsschutzes.

## Entwicklung und Prüfung

```bash
python -m compileall -q src tests
PYTHONWARNINGS=error python -m unittest discover -s tests -v
```

Die maßgebliche Version steht in `registry.json`. Architektur, Grenzen und Nachweise beschreibt die [Entwicklerdokumentation](ENTWICKLERDOKU.md).
