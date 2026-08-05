# Schwachstellen und Grenzen

Stand: Version `0.17.0-alpha.1`

## Behobene Schwachstellen

1. **Nur ein Wiederanlaufhinweis:** Unterschiedliche unterbrochene Indexdateien konnten sich gegenseitig verdrängen. Schema 2 führt nun eine begrenzte, deduplizierte Liste mit höchstens zwölf Einträgen.
2. **Ungetrennte Vertrauensentscheidung:** Jeder Eintrag wird jetzt separat und nur lesend gegen Ordner, Indexdatei, Scanart, Stammordner und SQLite-Sitzung geprüft.
3. **Unklare Auswahl:** Die Startseite zeigt Ordner, Index und Prüfstatus aller Einträge und erlaubt eine gezielte Einzelentscheidung.
4. **Unsichtbare veraltete Hinweise:** Ein vorübergehend fehlender Ordner oder Index bleibt sichtbar, wird aber nicht gestartet und erst nach ausdrücklichem Verwerfen entfernt.
5. **Unbeabsichtigtes gemeinsames Entfernen:** Erfolgreiche Fortsetzung und bewusstes Verwerfen betreffen ausschließlich den ausgewählten Eintrag.
6. **Parallele Statuszugriffe:** Die Wiederanlaufliste besitzt eine lokale Dateisperre und atomare private Veröffentlichung.
7. **Vorlagenänderung ohne Rückfallkopie:** Ersetzen und Löschen können vorher optional eine geprüfte, zeitgestempelte JSON-Sicherung erzeugen.
8. **Ungeprüfte Konfigurationskopie:** Quelle und Kopie werden auf Symlinkfreiheit, UTF-8-JSON, Objektstruktur, Schema, Vorlagenliste, Inhalt und SHA-256 geprüft.
9. **Änderung trotz Sicherungsfehler:** Eine fehlgeschlagene Sicherung stoppt die nachfolgende Vorlagenänderung.
10. **CLI-Wachstum:** Doppelte Sicherungslogik ließ `cli_search.py` über die Architekturgrenze wachsen. Die Logik liegt nun in einem kleinen gemeinsamen Fachmodul; die 500-Zeilen-Grenze wird wieder eingehalten.

## Verbleibende Grenzen

1. **Listenlimit:** Es werden höchstens zwölf Indexdateien vorgemerkt. Beim Überschreiten fällt ausschließlich der älteste interne Hinweis aus der Liste; Index- und Originaldateien bleiben unverändert.
2. **Kein automatisches Verwerfen:** Nicht mehr startbare Einträge bleiben bewusst sichtbar, bis der Nutzer sie einzeln verwirft.
3. **Keine Diagnose-CLI:** Die vollständige Mehrfachübersicht ist derzeit primär über die interaktive Startseite erreichbar. Ein rein lesender JSON-Diagnosebefehl ist noch offen.
4. **Keine geführte Konfigurations-Wiederherstellung:** Sicherungen können geprüft und einzeln gelöscht werden, aber noch nicht über einen eigenen geführten Vergleichsassistenten zurückgespielt werden.
5. **Einzeldatei-Grenze:** Während des Hashens einer sehr großen Datei kann nicht innerhalb dieser Datei fortgesetzt werden; höchstens dieser Einzelhash wird wiederholt.
6. **Erkannte Sicherungsnamen:** Beliebig benannte manuelle Kopien werden aus Sicherheitsgründen nicht automatisch als löschbar eingestuft.
7. **Keine automatische Rotation:** Auch viele oder alte Konfigurationssicherungen werden niemals automatisch gelöscht.
8. **Keine absolute Hardwaregarantie:** Defekter Datenträger, volles oder beschädigtes Dateisystem, falsche Controllercache-Zusagen, Kerneldefekt und physischer Verlust bleiben außerhalb des Anwendungsschutzes.
9. **Reale Laienabnahme offen:** Automatisierte Dialogtests ersetzen keine Beobachtung einer unerfahrenen Person.

## Schutzverträge

- Wiederanlauf nur für `index build` und `index rescan`.
- Ein Eintrag pro normalisierter Indexdatei; höchstens zwölf Einträge.
- SQLite-Prüfung über URI `mode=ro` und `query_only`.
- Kein Shell-Aufruf; ausschließlich geprüfte Argumentlisten.
- Nicht startbare Einträge werden nicht automatisch ausgeführt oder entfernt.
- Verwerfen erfordert eine bewusste Einzelentscheidung.
- Konfigurationssicherung ist optional und erfolgt vor der Änderung.
- Ohne erfolgreiche Sicherungsprüfung keine nachfolgende Änderung.
- Keine automatische Rotation, Sammellöschung oder Alterslöschung.
- Aktive Dateien und unbekannte Pfade sind nicht löschbar.
- Symlinks werden weder überschrieben noch gelöscht.
- Originaldateien bleiben schreibgeschützt.

## Praktische Folge

```bash
datenbanktool start
datenbanktool check --database index.sqlite3
datenbanktool index backups list index.sqlite3
```

Die Anwendung stellt ihren eigenen Softwarezustand kontrolliert wieder her, behauptet aber keine Lauffähigkeit unabhängig von Hardware und Betriebssystem.
