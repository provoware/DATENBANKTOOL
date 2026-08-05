# DATENBANKTOOL

**Erledigt:** begrenzte Mehrfachliste unabhängiger Wiederanläufe, getrennte Prüfung und Auswahl je Indexdatei, bewusstes Einzelverwerfen, optionale geprüfte Konfigurationssicherungen vor Vorlagenänderungen, Sicherungsübersicht, Autosave, Crashberichte und SQLite-Härtung.

**Offen:** reale Laienabnahme auf einem Kubuntu-Zielsystem.

**Entwicklungsfortschritt:** **99 %** · **62 Hauptpunkte erledigt** · **1 Hauptpunkt offen**.

**Mögliche Upgrades aus `UPGRADE_POOL.md`:** Wiederanlauf-Diagnoseexport, geführtes Wiederherstellen einer Konfigurationssicherung, Mehrordner-Zeitreihe und später eine barrierefreie grafische Oberfläche.

> Findet, erklärt und vergleicht große Dateisammlungen, ohne persönliche Dateien automatisch zu verändern. Technisch: lokales Linux-Indexwerkzeug mit SQLite.

## Projektstatus

| Bereich | Stand |
|---|---|
| Projektversion | `0.17.0-alpha.1` |
| Paketversion | `0.17.0a1` |
| Python | `>=3.10` |
| SQLite-Schema | `3` |
| Wiederanlauflimit | **12 verschiedene Indexdateien** |
| Originaldateiänderungen | **technisch gesperrt** |
| Externe Laufzeitabhängigkeiten | **0** |
| Automatische Tests | **130 unter Python 3.10 und 3.12** |
| Reale Laienabnahme | **offen** |

## Einfach starten

```bash
datenbanktool start
```

Die Startseite zeigt alle gespeicherten Wiederanläufe verschiedener Indexdateien in einer begrenzten Liste. Jeder Eintrag wird getrennt und nur lesend gegen Ordner, Indexdatei und SQLite-Sitzung geprüft.

Je Eintrag erscheinen:

- Art der Prüfung,
- verständlicher Prüfstatus,
- Ordner,
- Indexdatei,
- gespeicherte Scan-Nummer und Dateizahl,
- vollständiger geprüfter Befehl mit genau einem `--resume`.

Danach kann genau dieser Eintrag:

1. fortgesetzt werden,
2. für später erhalten bleiben,
3. bewusst verworfen werden.

Nicht mehr verfügbare Ordner oder Indexdateien bleiben als nicht startbare Hinweise sichtbar, bis sie ausdrücklich einzeln verworfen werden. Ein erfolgreicher Scan entfernt nur seinen eigenen Eintrag. Die Ausführung erfolgt als Argumentliste ohne Shell-Auswertung.

### Begrenzung und Deduplizierung

- höchstens **12** Wiederanlaufeinträge,
- höchstens ein Eintrag pro normalisierter Indexdatei,
- ein neuerer Lauf derselben Indexdatei aktualisiert den vorhandenen Eintrag,
- das Begrenzen verändert oder löscht keine Index- oder Originaldatei,
- die Statusdatei ist mit Dateimodus `0600` geschützt,
- Zugriffe werden über eine lokale Dateisperre koordiniert.

## Autosave und direkte Wiederaufnahme

Beim Aufbau oder Aktualisieren einer Dateiliste wird spätestens nach **5 Sekunden** oder **500 verarbeiteten Einträgen** gespeichert – je nachdem, was zuerst eintritt.

```bash
datenbanktool index build ~/Daten --database index.sqlite3 --resume
datenbanktool index rescan ~/Daten --database index.sqlite3 --resume
```

Eine gerade einzeln gehashte sehr große Datei kann nach einem Absturz erneut geprüft werden. Bereits bestätigte Batches bleiben erhalten.

## Konfigurationssicherung vor Vorlagenänderungen

Vor dem bewussten Ersetzen oder Löschen einer Such- oder Zeitreihen-Vorlage kann optional eine neue, geprüfte JSON-Sicherung erstellt werden:

```bash
datenbanktool index presets save Audio \
  --replace \
  --backup-before-change

datenbanktool index presets delete Audio \
  --backup-before-change \
  --yes

datenbanktool index timeline-presets save Musik Archiv \
  --replace \
  --backup-before-change
```

Die Startseite fragt bei Ersetzen und Löschen verständlich, ob diese Sicherung erstellt werden soll.

Der Sicherungsvertrag:

- Quelle muss eine normale Datei und darf kein Symlink sein,
- UTF-8-JSON, oberstes Objekt, `schema_version` und `presets`-Liste werden geprüft,
- Sicherung erhält einen UTC-Zeitstempel und Dateimodus `0600`,
- Inhalt und SHA-256 werden nach dem Schreiben erneut geprüft,
- eine fehlerhafte Sicherung wird nicht freigegeben,
- die eigentliche Vorlagenänderung startet erst nach erfolgreicher Sicherung,
- ohne `--backup-before-change` entsteht keine Sicherung,
- vorhandene Sicherungen werden niemals automatisch rotiert oder gelöscht.

## Sicherungsübersicht

```bash
datenbanktool index backups list index.sqlite3
datenbanktool index backups list index.sqlite3 --json
```

Die Übersicht zeigt Typ, Dateiname, Pfad, Größe, UTC-Zeit, Alter, Status und technische Begründung. Neue Vorlagen-Sicherungen erscheinen dort als geprüfte Konfigurationssicherungen.

### Genau eine Sicherung löschen

```bash
datenbanktool index backups delete index.sqlite3 PFAD_ZUR_SICHERUNG \
  --confirm-name EXAKTER_DATEINAME \
  --yes
```

Eine Datei wird nur gelöscht, wenn sie im neu aufgebauten Katalog vorkommt, der Dateiname exakt bestätigt wurde, `--yes` gesetzt ist und das Ziel eine normale Datei ohne Symlink ist. Aktive Dateien, unbekannte Pfade und Sammellöschungen bleiben ausgeschlossen.

## Startklar prüfen

```bash
datenbanktool check
datenbanktool check --database index.sqlite3
```

Die Ausgabe nennt zuerst, was passiert ist, ob persönliche Dateien betroffen sind und was als Nächstes zu tun ist. Fachbegriffe folgen danach.

## Was bei einem Absturz erhalten bleibt

- Konfigurationen und Berichte zeigen entweder den alten oder den vollständig neuen Stand.
- SQLite verwendet `WAL` und `synchronous=FULL`.
- Scan-Zwischenstände besitzen bestätigte Fortsetzungspunkte.
- Mehrere verschiedene Indexdateien verlieren ihre Wiederanlaufhinweise nicht gegenseitig.
- Tastaturabbruch wird als **unterbrochen**, nicht als beschädigt gespeichert.
- Unerwartete Programmfehler erzeugen einen lokalen Crashbericht.
- Typische Passwort-, Token- und Secret-Werte werden ausgeblendet.
- Originaldateien werden nicht automatisch verändert.

Status, Crashberichte und die Wiederanlaufliste liegen unter:

```text
$XDG_STATE_HOME/datenbanktool/
```

Fallback:

```text
~/.local/state/datenbanktool/
```

## Wie weit reicht die Garantie?

Der Softwarevertrag umfasst atomare Dateifreigabe, Datei- und Ordner-`fsync`, bestätigte SQLite-Transaktionen, getrennt validierte Wiederanläufe und geprüfte Sicherungen. Defekte Hardware, volles oder beschädigtes Dateisystem, falsche Controllercache-Zusagen, Kerneldefekte und physischer Verlust bleiben außerhalb des Anwendungsschutzes.

## Entwicklung und Prüfung

```bash
python -m compileall -q src tests
PYTHONWARNINGS=error python -m unittest discover -s tests -v
```

Die maßgebliche Version steht in `registry.json`. Architektur, Grenzen und Nachweise beschreibt die [Entwicklerdokumentation](ENTWICKLERDOKU.md).
