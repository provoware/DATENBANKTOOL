# DATENBANKTOOL

**Erledigt:** vollständig lesende Wiederanlauf-Diagnose für alle gespeicherten Einträge sowie optionales inhaltsfreies Wiederherstellungsprotokoll nach erfolgreichem Konfigurations-Restore. Weiterhin vorhanden: geführte Konfigurations-Wiederherstellung, automatischer geprüfter Rückfall, Mehrfach-Wiederanlauf, Konfigurationsvorsicherungen, Sicherungskatalog, Autosave, Crashberichte und SQLite-Härtung.

**Offen:** reale Laienabnahme auf einem Kubuntu-Zielsystem.

**Entwicklungsfortschritt:** **99 %** · **65 Hauptpunkte erledigt** · **1 Hauptpunkt offen**.

**Mögliche Upgrades aus `UPGRADE_POOL.md`:** Prüfbefehl für Wiederherstellungsprotokolle, geführte Protokollauswahl auf der Startseite, Mehrordner-Zeitreihe und später eine barrierefreie grafische Oberfläche.

> Lokales Linux-Indexwerkzeug für große Dateisammlungen. Persönliche Originaldateien werden nicht automatisch verändert.

## Projektstatus

| Bereich | Stand |
|---|---|
| Projektversion | `0.19.0-alpha.1` |
| Paketversion | `0.19.0a1` |
| Python | `>=3.10` |
| SQLite-Schema | `3` |
| Wiederanlauflimit | **12 verschiedene Indexdateien** |
| Originaldateiänderungen | **technisch gesperrt** |
| Externe Laufzeitabhängigkeiten | **0** |
| Automatische Tests | **145 unter Python 3.10 und 3.12** |
| Reale Laienabnahme | **offen** |

## Einfach starten

```bash
datenbanktool start
```

## Alle Wiederanläufe nur prüfen

Terminalübersicht:

```bash
datenbanktool index recovery
```

JSON-Ausgabe:

```bash
datenbanktool index recovery --json
```

Die Diagnose zeigt für jeden gespeicherten Eintrag:

- Prüfstatus,
- Quellordner,
- Indexdatei,
- SQLite-Sitzungsnummer,
- Zustand und Phase,
- bestätigte Dateizahl,
- Aktualisierungszeit in UTC,
- Startbarkeit und technische Begründung.

Der Befehl startet keinen Scan, verwirft keinen Eintrag und verändert weder `resume-run.json` noch die geprüften Indexdateien. Die JSON-Ausgabe enthält zusätzlich Gesamtzahl, startbare und nicht startbare Einträge sowie die vollständigen geprüften Datensätze ohne ANSI-Farbcodes.

## Konfigurationssicherung zuerst nur vergleichen

```bash
datenbanktool index backups compare index.sqlite3 SICHERUNG
```

Maschinenlesbar:

```bash
datenbanktool index backups compare index.sqlite3 SICHERUNG --json
```

Der Vergleich ist vollständig lesend. Er zeigt aktive Datei, Vorlagenzahlen, Hinzufügungen, Entfernungen, Ersetzungen, unveränderte Vorlagen und die SHA-256-Werte beider Dateien.

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
6. Vor dem Überschreiben entsteht eine neue geprüfte Rückfallsicherung.
7. Aktive Datei und ausgewählte Sicherung werden unmittelbar vorher erneut per SHA-256 geprüft.
8. Die Veröffentlichung erfolgt atomar mit Dateimodus `0600`.
9. Inhalt, Schema, Vorlagen und SHA-256 werden nachgeprüft.
10. Scheitert die Nachprüfung, wird automatisch aus der Rückfallsicherung zurückgesetzt und erneut geprüft.

## Optionales Wiederherstellungsprotokoll

Nur bei ausdrücklich angegebenem Ziel:

```bash
datenbanktool index backups restore index.sqlite3 SICHERUNG \
  --confirm-name EXAKTER_DATEINAME \
  --yes \
  --restore-log /pfad/restore-nachweis.json
```

Das Protokoll wird erst nach einer erfolgreich bestätigten Wiederherstellung geschrieben. Es enthält ausschließlich:

- UTC-Zeit des Protokolls,
- UTC-Zeit der abgeschlossenen Wiederherstellung,
- aktive Konfigurationsdatei,
- ausgewählte Sicherung,
- automatische Rückfallsicherung,
- SHA-256 der aktiven Datei nach Restore,
- SHA-256 der ausgewählten Sicherung,
- SHA-256 der Rückfallsicherung.

Es enthält keine Vorlagen, Antwortwerte, Konfigurationsinhalte, Kommandozeilenargumente oder Geheimnisse. Das Ziel wird atomar mit Modus `0600` angelegt. Eine vorhandene Datei wird nicht überschrieben. Es gibt keine automatische Benennung, Auswahl, Rotation oder Löschung.

Kann das ausdrücklich gewünschte Protokoll nicht geschrieben werden, bleibt die zuvor erfolgreich bestätigte Wiederherstellung bestehen. Der Befehl meldet diesen Teilfehler mit Rückgabecode `1` und nennt die technische Ursache.

## Optionale Sicherung vor Vorlagenänderungen

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
- Konfigurationen, Statusdateien und Protokolle werden atomar veröffentlicht.
- SQLite verwendet `WAL` und `synchronous=FULL`.
- Wiederanlauf-Diagnose verändert keine Wiederanlauf- oder Indexdaten.
- Protokollfehler rollen eine bereits erfolgreiche Konfigurations-Wiederherstellung nicht zurück.
- Hardwaredefekte, volles oder beschädigtes Dateisystem, Kerneldefekte und physischer Verlust bleiben außerhalb des Anwendungsschutzes.

## Entwicklung und Prüfung

```bash
python -m compileall -q src tests
PYTHONWARNINGS=error python -m unittest discover -s tests -v
```

Die maßgebliche Version steht in `registry.json`. Architektur, Grenzen und Nachweise beschreibt die [Entwicklerdokumentation](ENTWICKLERDOKU.md).
