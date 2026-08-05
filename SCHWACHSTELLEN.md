# Schwachstellen und Grenzen

Stand: Version `0.19.0-alpha.1`

## Behobene Schwachstellen

1. **Wiederanläufe nur in der interaktiven Startseite sichtbar:** `index recovery` zeigt nun alle gespeicherten Einträge im Terminal und als JSON.
2. **Unvollständige Diagnose:** Prüfstatus, Ordner, Indexdatei, Sitzung, Zustand, Phase, Dateizahl, UTC-Zeit und Startbarkeit werden gemeinsam ausgegeben.
3. **Diagnose mit unbeabsichtigter Wirkung:** Der neue Befehl besitzt keine Start-, Verwerfen- oder Löschaktion; Tests bestätigen bytegenau unveränderte Status- und Indexdateien.
4. **Unklare leere Liste:** Keine Einträge liefern einen erfolgreichen, eindeutig strukturierten Terminal- und JSON-Befund.
5. **Restore später nicht nachvollziehbar:** Optional kann nach erfolgreichem Restore ein begrenzter JSON-Nachweis erzeugt werden.
6. **Protokoll könnte Inhalte oder Geheimnisse sammeln:** Das Schema enthält ausschließlich UTC-Zeiten, drei Pfade und drei SHA-256-Werte.
7. **Unbeabsichtigte Protokollerzeugung:** Ohne ausdrücklich angegebenes `--restore-log` entsteht keine Datei.
8. **Protokoll könnte eine Datei überschreiben:** Bestehende Ziele und Symlinks werden abgelehnt; die Veröffentlichung ist atomar und privat mit Modus `0600`.
9. **Protokollfehler könnte erfolgreichen Restore zurückrollen:** Die Konfiguration bleibt im bereits bestätigten Zielstand; nur der optionale Nachweis meldet Teilfehlercode `1`.
10. **Versteckte Protokollverwaltung:** Es gibt keine automatische Benennung, Auswahl, Rotation, Sammel- oder Alterslöschung.

## Verbleibende Grenzen

1. **Diagnose ist absichtlich nur lesend:** Starten oder Verwerfen erfolgt weiterhin ausschließlich über die geführte Startseite beziehungsweise den ausdrücklich gewählten Scanbefehl.
2. **Ungültige interne Wiederanlaufeinträge:** Strukturell nicht erkennbare Datensätze werden nicht als scheinbar nutzbare Kandidaten ausgegeben; die zugrunde liegende Datei wird dabei nicht repariert.
3. **Protokollpfad nur über CLI:** Die geführte Startseite fragt noch nicht nach einem optionalen Protokollziel.
4. **Kein Protokoll-Prüfbefehl:** Das erzeugte JSON wird beim Schreiben bestätigt, kann aber noch nicht später mit einem eigenen Befehl gegen die drei Dateien geprüft werden.
5. **Pfade sind Metadaten:** Ein Protokoll enthält keine Inhalte, aber die drei lokalen Dateipfade können selbst sensible Organisationsinformationen darstellen.
6. **Keine automatische Auswahl oder Ablage:** Das Tool erfindet bewusst keinen Protokollnamen und wählt keinen Ordner.
7. **Kein Überschreiben:** Für jeden Nachweis muss ein neuer freier Zielpfad angegeben werden.
8. **Einzeldatei-Grenze beim Scannen:** Während des Hashens einer sehr großen Datei kann nicht innerhalb dieses Hashvorgangs fortgesetzt werden.
9. **Keine absolute Hardwaregarantie:** Defekter Datenträger, beschädigtes oder volles Dateisystem, Kerneldefekt und physischer Verlust bleiben außerhalb des Anwendungsschutzes.
10. **Reale Laienabnahme offen:** Automatisierte Tests ersetzen keine Beobachtung einer unerfahrenen Person.

## Schutzverträge

- `index recovery` ist vollständig lesend.
- Diagnose verwendet dieselbe getrennte Nur-Lese-Validierung wie die geführte Startseite.
- Kein Diagnose-Handler startet, verwirft oder löscht einen Eintrag.
- JSON-Diagnose enthält keine ANSI-Farbcodes.
- Restore-Protokoll entsteht nur nach erfolgreicher fachlicher Wiederherstellung und nur mit explizitem Pfad.
- Protokoll enthält keine Konfigurationsinhalte, Vorlagen, Argumente oder Geheimnisse.
- Protokollziel darf nicht existieren und kein Symlink sein.
- Atomare Veröffentlichung mit Dateimodus `0600` und vollständiger JSON-Nachprüfung.
- Protokollfehler verändert den bestätigten Restore-Zustand nicht.
- Keine automatische Benennung, Auswahl, Rotation oder Löschung.
- Originaldateien bleiben schreibgeschützt.

## Praktische Folge

```bash
datenbanktool index recovery
datenbanktool index recovery --json

datenbanktool index backups restore index.sqlite3 SICHERUNG \
  --confirm-name EXAKTER_DATEINAME --yes \
  --restore-log /neuer/pfad/restore-nachweis.json
```

Der Vertrag verbessert Diagnose und Nachvollziehbarkeit, ersetzt jedoch keine externe Datenträgersicherung oder reale Zielsystemabnahme.
