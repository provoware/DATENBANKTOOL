# Schwachstellen und Grenzen

Stand: Version `0.16.0-alpha.1`

## Behobene Schwachstellen

1. Die Startseite kannte nur den äußeren Prozess, nicht den konkret gestarteten Scan. Bestätigte Vollscan- und Re-Scan-Befehle erhalten jetzt einen eigenen dauerhaften Wiederanlaufdatensatz.
2. Ein gespeicherter Befehl allein wäre nicht vertrauenswürdig genug. Ordner, Indexdatei, Scanart und fortsetzbare SQLite-Sitzung werden vor jeder Anzeige nur lesend gegengeprüft.
3. Manuelle `--resume`-Kenntnis war erforderlich. Die Startseite zeigt nun den vollständigen geprüften Befehl und startet erst nach Bestätigung.
4. Sicherungen konnten nur erstellt oder manuell im Dateisystem gesucht werden. Eine geprüfte Übersicht zeigt jetzt Art, Größe, Alter und Zustand.
5. Eine Löschfunktion ohne strikte Begrenzung wäre zu riskant. Gelöscht wird nur eine katalogisierte Sicherung nach exaktem Pfad, Dateinamen und `--yes`.
6. Der zentrale Einzellöschhelfer normalisierte zunächst mit `resolve()` und hätte bei direkter Nutzung einen Symlink verfolgen können. Schreiben und Löschen verweigern jetzt Symlink-Ziele selbstständig.
7. Eine schwer lesbare Sortierformel erschwerte die Wartung. Sicherungen werden eindeutig nach kleinstem Alter und damit neueste zuerst sortiert.

## Verbleibende Grenzen

1. **Ein Wiederanlaufdatensatz:** Aktuell wird genau der zuletzt bestätigte Scan vorgemerkt. Mehrere gleichzeitig oder nacheinander unterbrochene Scans verschiedener Indexdateien benötigen künftig eine begrenzte Liste.
2. **Vorübergehend fehlender Ordner:** Ist ein Datenträger nicht eingehängt, wird kein Wiederanlauf angeboten. Der Hinweis bleibt erhalten und kann nach erneutem Einhängen wieder geprüft werden.
3. **Einzeldatei-Grenze:** Während des Hashens einer sehr großen Datei kann nicht innerhalb dieser Datei fortgesetzt werden; höchstens dieser Einzelhash wird wiederholt.
4. **Erkannte Sicherungsnamen:** Die Übersicht nimmt nur vom Tool verwendete oder ausdrücklich unterstützte Dateinamensmuster auf. Beliebig benannte manuelle Kopien werden aus Sicherheitsgründen nicht automatisch als löschbar eingestuft.
5. **Konfigurationssicherungen werden noch nicht automatisch erzeugt:** Die Übersicht kann vorhandene unterstützte Kopien prüfen; Vorlagenänderungen erzeugen derzeit nicht standardmäßig vorher eine Sicherung.
6. **Keine automatische Löschung:** Anzahl und Alter werden gezeigt, führen aber bewusst zu keiner Rotation oder Sammellöschung.
7. **Keine absolute Hardwaregarantie:** Defekter Datenträger, volles oder beschädigtes Dateisystem, falsche Controllercache-Zusagen, Kerneldefekt und physischer Verlust bleiben außerhalb des Anwendungsschutzes.
8. **Reale Laienabnahme offen:** Automatisierte Dialogtests ersetzen keine Beobachtung einer unerfahrenen Person.

## Schutzverträge

- Wiederanlauf nur für `index build` und `index rescan`.
- SQLite-Prüfung über URI `mode=ro` und `query_only`.
- Kein Shell-Aufruf; ausschließlich geprüfte Argumentlisten.
- Nein, Abbruch oder geschlossene Eingabe startet nichts und löscht keinen Hinweis.
- Aktive Dateien und unbekannte Pfade sind nicht löschbar.
- Symlinks werden weder überschrieben noch gelöscht.
- Einzellöschung bestätigt anschließend den Ordnerzustand mit `fsync`.
- Originaldateien bleiben schreibgeschützt.

## Praktische Folge

```bash
datenbanktool start
datenbanktool check --database index.sqlite3
datenbanktool index backups list index.sqlite3
```

Die Anwendung stellt ihren eigenen Softwarezustand kontrolliert wieder her, behauptet aber keine Lauffähigkeit unabhängig von Hardware und Betriebssystem.
