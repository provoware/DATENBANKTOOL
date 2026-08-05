# Schwachstellen und Grenzen

Stand: Version `0.20.0-alpha.1`

## Behobene Schwachstellen

1. **Restore-Protokoll nur beim Schreiben geprüft:** `index backups verify-log` kann einen vorhandenen Nachweis später erneut vollständig kontrollieren.
2. **Unklares oder erweitertes JSON-Schema:** Fehlende und zusätzliche Felder werden abgelehnt; unterstützt wird ausschließlich das feste Schema `1`.
3. **Zeitangaben ohne belastbare Zeitzone:** Beide Zeiten müssen gültige ISO-8601-Werte mit UTC-Offset null sein.
4. **Unlogische Zeitreihenfolge:** Die Protokollerzeugung darf nicht vor dem abgeschlossenen Restore liegen.
5. **Beliebige oder doppelte Pfade:** Genau drei unterschiedliche absolute Dateipfade sind erforderlich.
6. **Unklare Prüfsummen:** Genau drei benannte kleingeschriebene SHA-256-Werte mit jeweils 64 Hexzeichen sind zulässig.
7. **Symlink-Folgen beim Prüfen:** Protokoll und referenzierte Dateien werden mit `O_NOFOLLOW` geöffnet; Symlinks werden nicht verfolgt.
8. **Große Datei vollständig im Speicher:** Referenzdateien werden in Blöcken gestreamt und gehasht.
9. **Fehlen und Abweichung vermischt:** Fehlende Datei wird gelb als unvollständiger Nachweis, Hashabweichung rot als Integritätsfehler dargestellt.
10. **Prüfbefehl mit versteckter Wirkung:** Die Policy besitzt keine Schreibwirkung; es gibt keinen Restore-, Änderungs- oder Löschhandler.

## Verbleibende Grenzen

1. **Pfade sind sensible Metadaten:** Das Protokoll enthält keine Konfigurationsinhalte, aber lokale Dateipfade können Organisationsinformationen offenlegen.
2. **Dateien können später legitim verändert sein:** Eine Hashabweichung beweist nur, dass die aktuelle Datei nicht mehr dem protokollierten Stand entspricht; sie erklärt nicht den Grund.
3. **Fehlende Datei wird nicht rekonstruiert:** Der Prüfbefehl meldet den unvollständigen Nachweis und unternimmt bewusst keine Wiederherstellung.
4. **Nur Schema 1:** Unbekannte künftige Schemata werden nicht automatisch migriert oder interpretiert.
5. **Keine Signatur:** Das Protokoll besitzt drei Inhaltsprüfsummen, ist selbst aber noch nicht durch einen ausdrücklich vorgegebenen Hash oder eine Signatur gebunden.
6. **Keine automatische Protokollsuche:** Der Nutzer muss exakt die zu prüfende Datei auswählen.
7. **Noch keine geführte Startseitenaktion:** Die Prüfung ist derzeit ein Terminalbefehl.
8. **Zeitprüfung ist syntaktisch und logisch begrenzt:** Sie beweist keine vertrauenswürdige Systemuhr zum Erstellungszeitpunkt.
9. **Keine absolute Hardwaregarantie:** Defekter Datenträger, beschädigtes Dateisystem, Kerneldefekt und physischer Verlust bleiben außerhalb des Anwendungsschutzes.
10. **Reale Laienabnahme offen:** Automatisierte Tests ersetzen keine Beobachtung einer unerfahrenen Person.

## Schutzverträge

- Nur ein ausdrücklich angegebener Protokollpfad wird geprüft.
- Protokoll muss normale UTF-8-JSON-Datei sein; Symlink wird abgelehnt.
- Schema, Ereignis, Konfigurationsart, UTC-Zeiten, drei Pfade und drei Hashrollen werden vor dem Dateizugriff geprüft.
- Referenzpfade werden nicht aufgelöst oder über Symlinks verfolgt.
- Dateien werden ausschließlich lesend und gestreamt gehasht.
- Grün nur bei drei vorhandenen und übereinstimmenden Dateien.
- Gelb bei mindestens einer fehlenden Datei ohne weiteren roten Befund.
- Rot bei Hashabweichung, Symlink, falschem Dateityp oder Lesefehler.
- Keine Wiederherstellung, Änderung, Neuanlage oder Löschung.
- Keine automatische Auswahl, Rotation oder Historie.
- Originaldateien bleiben schreibgeschützt.

## Praktische Folge

```bash
datenbanktool index backups verify-log /pfad/restore-nachweis.json
datenbanktool index backups verify-log /pfad/restore-nachweis.json --json
```

Der Prüfbefehl bestätigt einen lokalen Nachweis kontrolliert, ersetzt jedoch keine kryptografische Signatur, externe Datenträgersicherung oder reale Zielsystemabnahme.
