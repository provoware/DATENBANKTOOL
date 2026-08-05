# DATENBANKTOOL

**Erledigt:** geführte optionale Auswahl eines neuen Wiederherstellungsprotokollpfads, geführte rein lesende Protokollprüfung und optionaler SHA-256-Pin vor jeder Schemaauswertung. Weiterhin vorhanden: geprüfter Konfigurations-Restore mit automatischer Rückfallsicherung, Wiederanlauf-Diagnose, Sicherungskatalog, Autosave, Crashberichte und SQLite-Härtung.

**Offen:** reale Laienabnahme auf einem Kubuntu-Zielsystem.

**Entwicklungsfortschritt:** **99 %** · **69 Hauptpunkte erledigt** · **1 Hauptpunkt offen**.

**Mögliche Upgrades aus `UPGRADE_POOL.md`:** geführte synthetische Kubuntu-Abnahmesitzung, optionaler Prüfberichtsexport und später eine barrierefreie grafische Oberfläche.

> Lokales Linux-Indexwerkzeug für große Dateisammlungen. Persönliche Originaldateien werden nicht automatisch verändert.

## Projektstatus

| Bereich | Stand |
|---|---|
| Projektversion | `0.21.0-alpha.1` |
| Paketversion | `0.21.0a1` |
| Python | `>=3.10` |
| SQLite-Schema | `3` |
| Wiederanlauflimit | **12 verschiedene Indexdateien** |
| Originaldateiänderungen | **technisch gesperrt** |
| Externe Laufzeitabhängigkeiten | **0** |
| Automatische Tests | **158 unter Python 3.10 und 3.12** |
| Reale Laienabnahme | **offen** |

## Einfach starten

```bash
datenbanktool start
```

Unter **7 – Sicherungen verwalten** stehen nun zusätzlich zwei geführte Verträge bereit.

### Optionales Protokoll nach geführtem Restore

Nach dem Nur-Lese-Vergleich und der exakten Wiederholung des Sicherungsnamens fragt die Startseite optional nach einem neuen Protokollpfad.

- Leere Eingabe: kein `--restore-log`.
- Ausdrücklicher neuer absoluter Pfad: `--restore-log PFAD` wird an die sichere Argumentliste angehängt.
- Existierende Datei oder Symlink: wird abgelehnt und nicht überschrieben.
- Es wird kein Pfad vorgeschlagen, gesucht oder automatisch gespeichert.
- Der vollständige Befehl bleibt vor dem Start sichtbar und bestätigungspflichtig.

### Geführte Protokollprüfung

Aktion **Protokoll prüfen**:

1. genau einen vollständigen Protokollpfad eingeben,
2. vollständigen normalisierten Pfad prüfen,
3. optional einen ausdrücklich bekannten SHA-256-Pin eingeben,
4. vollständigen Nur-Lese-Befehl bestätigen,
5. dieselbe Grün-/Gelb-/Rot-Auswertung wie im Terminal erhalten.

Es gibt keine automatische Suche, Auswahl, Wiederherstellung, Änderung oder Löschung.

## Wiederherstellungsprotokoll im Terminal prüfen

```bash
datenbanktool index backups verify-log /pfad/restore-nachweis.json
```

Maschinenlesbar:

```bash
datenbanktool index backups verify-log /pfad/restore-nachweis.json --json
```

Optional kann vor jeder JSON-Schemaauswertung exakt die erwartete Protokolldatei bestätigt werden:

```bash
datenbanktool index backups verify-log /pfad/restore-nachweis.json \
  --expected-protocol-sha256 64_KLEINGESCHRIEBENE_HEXZEICHEN
```

Der Pin:

- wird nur bei ausdrücklicher Eingabe verwendet,
- wird nicht automatisch ermittelt oder gespeichert,
- muss exakt 64 kleingeschriebene Hexzeichen besitzen,
- wird über eine sichere, nicht symlink-folgende Leseöffnung geprüft,
- stoppt bei Abweichung vor der Schemaauswertung mit Rückgabecode `2`.

Bei erfolgreichem Pin enthält JSON zusätzlich `protocol_identity` mit erwartetem und tatsächlichem SHA-256-Wert.

## Protokollprüfung ohne Pin

Der feste Prüfvertrag kontrolliert:

- UTF-8-JSON und exaktes Schema `1`,
- Ereignis `configuration_restore`,
- zwei UTC-Zeiten und ihre Reihenfolge,
- drei unterschiedliche absolute Pfade,
- drei fest benannte SHA-256-Werte,
- vorhandene Dateien über `O_RDONLY`, `O_NOFOLLOW`, `fstat()` und Streaming-Hashing.

Zustände:

| Zustand | Bedeutung |
|---|---|
| Grün | alle drei Dateien stimmen überein |
| Gelb | Protokoll gültig, mindestens eine Datei fehlt |
| Rot | Datei weicht ab, ist ein Symlink oder nicht sicher lesbar |

Rückgabecodes: `0` vollständig bestätigt, `1` Dateinachweis unvollständig/abweichend, `2` Eingabe oder Protokoll ungültig.

## Genau eine Konfigurationssicherung wiederherstellen

```bash
datenbanktool index backups restore index.sqlite3 SICHERUNG \
  --confirm-name EXAKTER_DATEINAME \
  --yes
```

Optionales neues Protokollziel:

```bash
datenbanktool index backups restore index.sqlite3 SICHERUNG \
  --confirm-name EXAKTER_DATEINAME \
  --yes \
  --restore-log /neuer/pfad/restore-nachweis.json
```

Vor dem Überschreiben entsteht eine geprüfte Rückfallsicherung. Aktive Datei, Sicherung und Rückfallsicherung werden nachgeprüft. Scheitert die Restore-Nachprüfung, erfolgt automatischer Rückfall. Protokolle werden nicht automatisch benannt, rotiert oder gelöscht.

## Wiederanläufe nur prüfen

```bash
datenbanktool index recovery
datenbanktool index recovery --json
```

Die Diagnose startet keinen Scan, verwirft keinen Eintrag und verändert weder Wiederanlaufdatei noch Index.

## Startklar prüfen

```bash
datenbanktool check
datenbanktool check --database index.sqlite3
```

## Sicherheitsgrenzen

- Originaldateien bleiben schreibgeschützt.
- CLI-Fachmodule verwenden keine Shell-Auswertung.
- Schreibziele werden atomar veröffentlicht; bestehende Protokollziele werden nicht überschrieben.
- Protokollprüfung folgt keinen Symlinks und verändert keine Prüfobjekte.
- SHA-Pins werden weder automatisch berechnet noch gespeichert.
- Der zentrale Prozessrahmen aktualisiert weiterhin ausschließlich sein internes Absturzjournal.
- Hardwaredefekte, volles oder beschädigtes Dateisystem, Kerneldefekte und physischer Verlust bleiben außerhalb des Anwendungsschutzes.

## Entwicklung und Prüfung

```bash
python -m compileall -q src tests
PYTHONWARNINGS=error python -m unittest discover -s tests -v
```

Die maßgebliche Version steht in `registry.json`. Architektur, Grenzen und Nachweise beschreibt die [Entwicklerdokumentation](ENTWICKLERDOKU.md).
