# DATENBANKTOOL

**Erledigt:** geführter Wiederanlauf unterbrochener Scans, dauerhaftes Autosave, geprüfte Sicherungsübersicht, sichere Einzellöschung, Crashberichte, SQLite-Härtung und laienverständliche Nutzerführung.

**Offen:** reale Laienabnahme auf einem Kubuntu-Zielsystem.

**Entwicklungsfortschritt:** **99 %** · **60 Hauptpunkte erledigt** · **1 Hauptpunkt offen**.

**Mögliche Upgrades aus `UPGRADE_POOL.md`:** mehrere unabhängige Wiederanläufe, automatische Konfigurations-Sicherungen vor Änderungen, Mehrordner-Zeitreihe und später eine barrierefreie grafische Oberfläche.

> Findet, erklärt und vergleicht große Dateisammlungen, ohne persönliche Dateien automatisch zu verändern. Technisch: lokales Linux-Indexwerkzeug mit SQLite.

## Projektstatus

| Bereich | Stand |
|---|---|
| Projektversion | `0.16.0-alpha.1` |
| Paketversion | `0.16.0a1` |
| Python | `>=3.10` |
| SQLite-Schema | `3` |
| Originaldateiänderungen | **technisch gesperrt** |
| Externe Laufzeitabhängigkeiten | **0** |
| Automatische Tests | **119 unter Python 3.10 und 3.12** |
| Reale Laienabnahme | **offen** |

## Einfach starten

```bash
datenbanktool start
```

Beim Start prüft das Tool, ob eine frühere Ordnerprüfung sicher fortgesetzt werden kann. Gefunden werden nur tatsächlich unterbrochene Vollscans oder Änderungsprüfungen, deren Ordner, Indexdatei und SQLite-Sitzung zusammenpassen.

Die Startseite zeigt zuerst verständlich:

- Art der Prüfung,
- Ordner,
- Indexdatei,
- gespeicherte Scan-Nummer und Dateizahl,
- den vollständigen geprüften Befehl mit `--resume`.

Erst danach wird gefragt, ob die Fortsetzung gestartet werden soll. **Nein** lässt den Wiederanlauf gespeichert. **Ja** führt exakt die angezeigte Argumentliste ohne Shell-Auswertung aus.

## Autosave und Wiederaufnahme

Beim Aufbau oder Aktualisieren einer Dateiliste wird spätestens nach **5 Sekunden** oder **500 verarbeiteten Einträgen** gespeichert – je nachdem, was zuerst eintritt.

Direkte Wiederaufnahme bleibt möglich:

```bash
datenbanktool index build ~/Daten --database index.sqlite3 --resume
datenbanktool index rescan ~/Daten --database index.sqlite3 --resume
```

Eine gerade einzeln gelesene oder gehashte sehr große Datei kann nach einem Absturz erneut geprüft werden. Bereits bestätigte Batches bleiben erhalten.

## Sicherungsübersicht

Index- und erkannte Konfigurationssicherungen anzeigen:

```bash
datenbanktool index backups list index.sqlite3
```

Maschinenlesbar:

```bash
datenbanktool index backups list index.sqlite3 --json
```

Die Übersicht zeigt:

- Index- oder Konfigurationssicherung,
- Dateiname und vollständigen Pfad,
- Größe,
- Änderungszeit und verständliches Alter,
- Prüfergebnis,
- technische Einzelheit.

Index-Sicherungen werden nur lesend mit SQLite `quick_check` und Schemaversion geprüft. Konfigurationssicherungen werden als JSON mit `schema_version` und `presets`-Liste geprüft.

### Genau eine Sicherung löschen

```bash
datenbanktool index backups delete index.sqlite3 PFAD_ZUR_SICHERUNG \
  --confirm-name EXAKTER_DATEINAME \
  --yes
```

Schutzregeln:

1. Die Datei muss in derselben geprüften Übersicht vorkommen.
2. Der Dateiname muss exakt wiederholt werden.
3. `--yes` ist zwingend.
4. Aktive Index- und Konfigurationsdateien sind ausgeschlossen.
5. Symbolische Verknüpfungen werden weder überschrieben noch gelöscht.
6. Es gibt keine automatische Sicherungsrotation oder Sammellöschung.

Auf der Startseite bündelt Menüpunkt **7 – Sicherungen verwalten** das Erstellen, Anzeigen und einzelne Löschen mit zusätzlicher sichtbarer Befehlsbestätigung.

## Startklar prüfen

```bash
datenbanktool check
datenbanktool check --database index.sqlite3
```

Die Ausgabe nennt zuerst, was passiert ist, ob persönliche Dateien betroffen sind und was als Nächstes zu tun ist. Fachbegriffe folgen erst danach.

## Was bei einem Absturz erhalten bleibt

- Konfigurationen und Berichte zeigen entweder den alten oder den vollständig neuen Stand.
- SQLite verwendet `WAL` und `synchronous=FULL`.
- Scan-Zwischenstände besitzen bestätigte Fortsetzungspunkte.
- Tastaturabbruch wird als **unterbrochen**, nicht als beschädigt gespeichert.
- Unerwartete Programmfehler erzeugen einen lokalen Crashbericht.
- Typische Passwort-, Token- und Secret-Werte werden im Crashbericht ausgeblendet.
- Originaldateien werden nicht automatisch verändert.

Status, Crashberichte und Wiederanlaufdatensatz liegen standardmäßig unter:

```text
$XDG_STATE_HOME/datenbanktool/
```

Fallback:

```text
~/.local/state/datenbanktool/
```

## Wie weit reicht die Garantie?

Der geprüfte Softwarevertrag umfasst atomare Dateifreigabe, Datei- und Ordner-`fsync`, bestätigte SQLite-Transaktionen, validierte Wiederaufnahme und geprüfte Sicherungen. Keine Software kann defekte Hardware, volles oder beschädigtes Dateisystem, falsche Controllercache-Zusagen, Kerneldefekte oder physischen Verlust ausschließen.

Vor wichtigen Arbeiten:

```bash
datenbanktool check --database index.sqlite3
datenbanktool index backup index.sqlite3
datenbanktool index backups list index.sqlite3
```

## Entwicklung und Prüfung

```bash
python -m compileall -q src tests
PYTHONWARNINGS=error python -m unittest discover -s tests -v
```

Die maßgebliche Version steht in `registry.json`. Architektur, Grenzen und Nachweise beschreibt die [Entwicklerdokumentation](ENTWICKLERDOKU.md).
