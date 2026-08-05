# Schwachstellen und Grenzen

Stand: Version `0.18.0-alpha.1`

## Behobene Schwachstellen

1. **Sicherung ohne verständliche Wirkungsvorschau:** Ein rein lesender Vergleich zeigt nun exakt, welche Vorlagen hinzukämen, entfernt, ersetzt oder unverändert blieben.
2. **Beliebiger Wiederherstellungspfad:** Nur ein Eintrag aus der frisch aufgebauten Sicherungsübersicht ist zulässig.
3. **Falscher Sicherungstyp:** Der Assistent akzeptiert ausschließlich grün geprüfte Such- oder Zeitreihen-Konfigurationssicherungen; Indexsicherungen bleiben getrennt.
4. **Veraltete Vergleichsgrundlage:** Aktive Datei und Sicherung werden unmittelbar vor dem Überschreiben nochmals gegen ihre SHA-256-Werte geprüft.
5. **Überschreiben ohne Rückfallkopie:** Vor jeder Mutation wird zwingend eine neue geprüfte Rückfallsicherung der aktiven Datei erzeugt.
6. **Teilweise oder unbestätigte Wiederherstellung:** Die Veröffentlichung ist atomar und wird anschließend bytegenau, per SHA-256 und über das vollständige Vorlagenschema geprüft.
7. **Fehler nach dem Überschreiben:** Scheitert die Nachprüfung, wird automatisch die neue Rückfallsicherung zurückgespielt und erneut validiert.
8. **Unklare Benutzerentscheidung:** Dateiname und vollständiger Wiederherstellungsbefehl müssen ausdrücklich bestätigt werden.
9. **Unnötiges Überschreiben:** Bytegenau identische Sicherung und aktive Konfiguration werden ohne Mutation abgelehnt.
10. **Versteckte Aufräumautomatik:** Ausgewählte Sicherung und Rückfallsicherung bleiben erhalten; Rotation und automatische Löschung existieren nicht.

## Verbleibende Grenzen

1. **Aktive Datei muss existieren:** Der Assistent erzeugt aus einer Sicherung keine neue Konfigurationsart. Verglichen wird stets mit einer vorhandenen aktiven Such- oder Zeitreihen-Datei.
2. **Erkannte Dateinamen:** Nur unterstützte Sicherungsnamensmuster werden katalogisiert. Beliebig benannte manuelle Kopien bleiben aus Sicherheitsgründen ausgeschlossen.
3. **Dateiebene statt Einzelauswahl innerhalb der Sicherung:** Wiederhergestellt wird die vollständige Vorlagendatei, nicht eine frei zusammengestellte Teilmenge einzelner Vorlagen.
4. **Keine automatische Auswahl:** Das Tool bestimmt niemals selbstständig, welche Sicherung „die beste“ ist.
5. **Keine automatische Rotation:** Auch viele oder alte Sicherungen werden nicht automatisch entfernt.
6. **Keine Wiederherstellung bei gelbem Status:** Unbekannte Schemaversionen werden angezeigt, aber nicht automatisch konvertiert oder zurückgespielt.
7. **Keine Diagnose-CLI für Wiederanläufe:** Die vollständige Mehrfachübersicht ist weiterhin primär über die interaktive Startseite erreichbar.
8. **Einzeldatei-Grenze beim Scannen:** Während des Hashens einer sehr großen Datei kann nicht innerhalb dieses Hashvorgangs fortgesetzt werden.
9. **Keine absolute Hardwaregarantie:** Defekter Datenträger, beschädigtes oder volles Dateisystem, Kerneldefekt und physischer Verlust bleiben außerhalb des Anwendungsschutzes.
10. **Reale Laienabnahme offen:** Automatisierte Dialogtests ersetzen keine Beobachtung einer unerfahrenen Person.

## Schutzverträge

- Vergleich ist rein lesend.
- Wiederherstellung betrifft genau eine aktive Konfigurationsdatei.
- Katalogmitgliedschaft, grüner Status, exakter Dateiname und `--yes` sind zwingend.
- Symlinks, beschädigte Dateien, unbekannte Pfade und Indexsicherungen werden abgelehnt.
- Vor jeder Mutation entsteht eine geprüfte Rückfallsicherung.
- Kein Überschreiben bei veränderten Prüfsummen seit dem Vergleich.
- Atomare Veröffentlichung mit Dateimodus `0600`.
- Vollständige Nachprüfung nach der Veröffentlichung.
- Automatischer Rückfall bei fehlgeschlagener Nachprüfung.
- Keine automatische Auswahl, Rotation, Sammel- oder Alterslöschung.
- Originaldateien bleiben schreibgeschützt.

## Praktische Folge

```bash
datenbanktool index backups compare index.sqlite3 SICHERUNG
datenbanktool index backups restore index.sqlite3 SICHERUNG \
  --confirm-name EXAKTER_DATEINAME --yes
```

Der Vertrag schützt den eigenen Konfigurationszustand kontrolliert, ersetzt jedoch keine externe Datenträgersicherung.
