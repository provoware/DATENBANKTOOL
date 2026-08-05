# DATENBANKTOOL

**Erledigt:** geführte Konfigurations-Wiederherstellung mit Nur-Lese-Vergleich, exakter Einzelauswahl, automatischer geprüfter Rückfallsicherung und automatischem Rückfall bei fehlgeschlagener Nachprüfung; außerdem Mehrfach-Wiederanlauf, Konfigurationsvorsicherungen, Sicherungskatalog, Autosave, Crashberichte und SQLite-Härtung.

**Offen:** reale Laienabnahme auf einem Kubuntu-Zielsystem.

**Entwicklungsfortschritt:** **99 %** · **63 Hauptpunkte erledigt** · **1 Hauptpunkt offen**.

**Mögliche Upgrades aus `UPGRADE_POOL.md`:** Wiederanlauf-Diagnosebefehl, Wiederherstellungsprotokoll, Mehrordner-Zeitreihe und später eine barrierefreie grafische Oberfläche.

> Lokales Linux-Indexwerkzeug für große Dateisammlungen. Persönliche Originaldateien werden nicht automatisch verändert.

## Projektstatus

| Bereich | Stand |
|---|---|
| Projektversion | `0.18.0-alpha.1` |
| Paketversion | `0.18.0a1` |
| Python | `>=3.10` |
| SQLite-Schema | `3` |
| Wiederanlauflimit | **12 verschiedene Indexdateien** |
| Originaldateiänderungen | **technisch gesperrt** |
| Externe Laufzeitabhängigkeiten | **0** |
| Automatische Tests | **139 unter Python 3.10 und 3.12** |
| Reale Laienabnahme | **offen** |

## Einfach starten

```bash
datenbanktool start
```

Menüpunkt **7 – Sicherungen verwalten** bietet:

- Sicherungen anzeigen und prüfen,
- neue Indexsicherung erstellen,
- eine Konfigurationssicherung vergleichen und kontrolliert wiederherstellen,
- genau eine erkannte Sicherung nach Bestätigung löschen.

## Konfigurationssicherung zuerst nur vergleichen

```bash
datenbanktool index backups compare index.sqlite3 \
  /pfad/search-presets.json.backup-ZEIT.json
```

Maschinenlesbar:

```bash
datenbanktool index backups compare index.sqlite3 SICHERUNG --json
```

Der Vergleich ist vollständig lesend. Er zeigt:

- zugehörige aktive Such- oder Zeitreihen-Konfiguration,
- Anzahl der Vorlagen in Sicherung und aktiver Datei,
- Vorlagen, die hinzukämen,
- Vorlagen, die entfernt würden,
- Vorlagen, die ersetzt würden,
- unveränderte Vorlagen,
- SHA-256 beider Dateien.

Es wird dabei nichts gesichert, überschrieben, wiederhergestellt oder gelöscht.

## Genau eine Konfigurationssicherung wiederherstellen

```bash
datenbanktool index backups restore index.sqlite3 SICHERUNG \
  --confirm-name EXAKTER_DATEINAME \
  --yes
```

Der Sicherheitsablauf ist fest:

1. Die Sicherung muss im frisch aufgebauten Sicherungskatalog vorkommen.
2. Sie muss eine grün geprüfte Such- oder Zeitreihen-Konfigurationssicherung sein.
3. Sicherung und aktive Datei werden erneut vollständig verglichen.
4. Der Sicherungsdateiname muss exakt wiederholt werden.
5. `--yes` ist zwingend.
6. Unmittelbar vor dem Überschreiben wird eine neue geprüfte Rückfallsicherung der aktiven Datei erstellt.
7. Aktive Datei und ausgewählte Sicherung werden nochmals per SHA-256 gegen den Vergleich geprüft.
8. Die Wiederherstellung erfolgt atomar mit Dateimodus `0600`.
9. Inhalt, Schema, Vorlagen und SHA-256 werden danach erneut geprüft.
10. Scheitert diese Nachprüfung, wird die aktive Datei automatisch aus der neuen Rückfallsicherung zurückgesetzt und erneut geprüft.

Die ausgewählte Sicherung und die Rückfallsicherung bleiben erhalten. Es gibt keine automatische Auswahl, Rotation, Alterslöschung oder Sammellöschung.

### Bewusste Ablehnungen

Nicht wiederherstellbar sind:

- Indexsicherungen über diesen Konfigurationsassistenten,
- beschädigte oder gelb/rot bewertete JSON-Dateien,
- unbekannte oder manuell beliebig benannte Pfade,
- symbolische Verknüpfungen,
- Sicherungen ohne zugehörige aktive Konfigurationsdatei,
- bytegenau bereits identische Sicherungen.

## Optionale Sicherung vor Vorlagenänderungen

Vor dem Ersetzen oder Löschen einer Such- oder Zeitreihen-Vorlage kann weiterhin eine neue geprüfte JSON-Sicherung erzeugt werden:

```bash
datenbanktool index presets save Audio --replace --backup-before-change
datenbanktool index presets delete Audio --backup-before-change --yes
datenbanktool index timeline-presets save Musik Archiv \
  --replace --backup-before-change
```

Ohne `--backup-before-change` entsteht keine Sicherung. Vorhandene Sicherungen werden niemals automatisch rotiert oder gelöscht.

## Mehrere unabhängige Wiederanläufe

Die Startseite führt höchstens zwölf unterbrochene Scans verschiedener Indexdateien. Jeder Eintrag wird getrennt gegen Ordner, Indexdatei und SQLite-Sitzung geprüft und kann einzeln fortgesetzt, erhalten oder bewusst verworfen werden.

Nicht verfügbare Ordner oder Indexdateien bleiben sichtbar, sind aber nicht startbar. Erfolg oder Verwerfen entfernt ausschließlich den ausgewählten internen Hinweis.

## Sicherungsübersicht und Einzellöschung

```bash
datenbanktool index backups list index.sqlite3
datenbanktool index backups list index.sqlite3 --json
```

Genau eine Sicherung löschen:

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
- Konfigurationen werden atomar veröffentlicht und mit Datei- sowie Ordner-`fsync` abgesichert.
- SQLite verwendet `WAL` und `synchronous=FULL`.
- Hardwaredefekte, ein beschädigtes oder volles Dateisystem, Kerneldefekte und physischer Verlust bleiben außerhalb des Anwendungsschutzes.

## Entwicklung und Prüfung

```bash
python -m compileall -q src tests
PYTHONWARNINGS=error python -m unittest discover -s tests -v
```

Die maßgebliche Version steht in `registry.json`. Architektur, Grenzen und Nachweise beschreibt die [Entwicklerdokumentation](ENTWICKLERDOKU.md).
