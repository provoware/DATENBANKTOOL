# DATENBANKTOOL

**Erledigt:** absturzsicheres Laufjournal, Crashberichte, zeit- und mengenbegrenztes Autosave, sichere Wiederaufnahme, SQLite-Härtung, dauerhaft atomare Konfigurationen/Exporte/Sicherungen, Startklar-Prüfung und stark vereinfachte Nutzeransprache.

**Offen:** reale Laienabnahme auf einem Zielsystem.

**Entwicklungsfortschritt:** **99 %** · **58 Hauptpunkte erledigt** · **1 Hauptpunkt offen**.

**Mögliche Upgrades aus `UPGRADE_POOL.md`:** geführter Wiederherstellungsassistent, Mehrordner-Zeitreihe, Abnahmehistorie und später eine barrierefreie grafische Oberfläche.

> Findet, erklärt und vergleicht große Dateisammlungen, ohne persönliche Dateien automatisch zu verändern. Technisch: lokales Linux-Indexwerkzeug mit SQLite.

## Projektstatus

| Bereich | Stand |
|---|---|
| Projektversion | `0.15.0-alpha.1` |
| Paketversion | `0.15.0a1` |
| Python | `>=3.10` |
| SQLite-Schema | `3` |
| Originaldateiänderungen | **technisch gesperrt** |
| Externe Laufzeitabhängigkeiten | **0** |
| Reale Laienabnahme | **offen** |

## Einfach starten

```bash
datenbanktool start
```

Prüfen, ob alles startklar ist:

```bash
datenbanktool check
```

Zusätzlich eine vorhandene Indexdatei prüfen:

```bash
datenbanktool check --database index.sqlite3
```

Die Ausgabe nennt zuerst verständlich, was los ist. Der Fachbegriff steht erst danach als technische Einzelheit.

## Autosave und Wiederaufnahme

Beim Aufbau oder Aktualisieren einer Dateiliste wird spätestens nach **5 Sekunden** oder **500 verarbeiteten Einträgen** gespeichert – je nachdem, was zuerst eintritt.

```bash
datenbanktool index build ~/Daten \
  --database index.sqlite3 \
  --autosave-seconds 5
```

Nach Abbruch oder Programmfehler denselben Schritt mit `--resume` fortsetzen:

```bash
datenbanktool index build ~/Daten \
  --database index.sqlite3 \
  --resume
```

Für eine Änderungsprüfung gilt dasselbe:

```bash
datenbanktool index rescan ~/Daten \
  --database index.sqlite3 \
  --resume
```

Eine gerade einzeln gelesene oder gehashte sehr große Datei kann nach einem Absturz erneut geprüft werden. Bereits bestätigte Dateien werden nicht erneut vollständig aufgebaut.

## Was bei einem Absturz erhalten bleibt

- Konfigurationen und Berichte zeigen entweder den alten oder den vollständig neuen Stand, niemals eine absichtlich freigegebene Halbdatei.
- SQLite verwendet `WAL` und `synchronous=FULL`.
- Scan-Zwischenstände werden fest bestätigt und besitzen einen Fortsetzungspunkt.
- Ein normaler Tastaturabbruch wird als **unterbrochen**, nicht als beschädigt gespeichert.
- Unerwartete Programmfehler erzeugen einen lokalen Crashbericht.
- Werte hinter typischen Passwort-, Token- und Secret-Schaltern werden im Crashbericht ausgeblendet.
- Originaldateien werden durch diese Fehlergrenze nicht automatisch verändert.

Laufjournal und Crashberichte liegen standardmäßig hier:

```text
$XDG_STATE_HOME/datenbanktool/
```

Ohne gesetztes `XDG_STATE_HOME`:

```text
~/.local/state/datenbanktool/
```

## Wie weit reicht die Garantie?

Der geprüfte **Softwarevertrag** garantiert:

1. Schreiben in eine neue Datei, vollständiges Leeren des Dateipuffers und atomare Umschaltung.
2. Bestätigung des Ordnerzustands nach der Umschaltung.
3. Dauerhafte SQLite-Transaktionen mit fortsetzbaren Checkpoints.
4. Kontrollierte Rückgabecodes: `2` für verständliche Bedienfehler, `70` für unerwartete Programmfehler und `130` für Tastaturabbruch.
5. Startdiagnose, Integritätsprüfung, Sicherheitskopie und Wiederaufnahme.

Keine Software kann absolute Lauffähigkeit bei defekter Hardware, vollem Datenträger, fehlerhaftem Dateisystem oder Controller, Kernelabsturz, physischem Verlust oder einer Stromunterbrechung mit nicht wahrheitsgemäßem Gerätepuffer garantieren. Deshalb bleiben geprüfte Sicherungen notwendig:

```bash
datenbanktool index backup index.sqlite3
```

## Sichere Wiederherstellung

```bash
datenbanktool check --database index.sqlite3
datenbanktool index status index.sqlite3
datenbanktool index backup index.sqlite3
datenbanktool index repair index.sqlite3
```

`repair` erstellt standardmäßig zuerst eine Sicherheitskopie. `restore` erzeugt standardmäßig zusätzlich eine Rückfallsicherung des aktuellen Index.

## Nutzeransprache

Öffentliche Einstiege und neue Fehlermeldungen folgen diesem Aufbau:

1. **Alltagssprache:** Was ist passiert?
2. **Auswirkung:** Wurden persönliche Dateien verändert?
3. **Nächster Schritt:** Was ist jetzt zu tun?
4. **Fachbegriff:** Technische Einzelheit in Klammern oder einer eigenen Zeile.

Beispiel:

```text
Der letzte bestätigte Zwischenstand bleibt erhalten.
Starte denselben Scan mit --resume erneut.
Technische Einzelheit: Wiederaufnahme am Checkpoint.
```

## Entwicklung und Prüfung

```bash
python -m compileall -q src tests
PYTHONWARNINGS=error python -m unittest discover -s tests -v
```

Die maßgebliche Version steht in `registry.json`. Architektur, Grenzen und Nachweise beschreibt die [Entwicklerdokumentation](ENTWICKLERDOKU.md).
