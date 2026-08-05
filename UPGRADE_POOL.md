# Upgrade-Pool

Stand: Version `0.18.0-alpha.1`

Upgrades werden erst umgesetzt, wenn Eingaben, Ausgaben, Fehlerfälle, Sicherheitsgrenzen und Registry-Eintrag festgelegt sind.

| Priorität | Upgrade | Nutzen | Sicherheitsgrenze |
|---|---|---|---|
| Hoch | Reale Laienabnahme | Auswahl, Sprache, Vergleich und Wiederherstellung mit unerfahrener Person prüfen | ausschließlich synthetische oder ausdrücklich freigegebene Testdaten |
| Hoch | Wiederanlauf-Diagnosebefehl | Mehrere gespeicherte Einträge außerhalb der Startseite prüfen und dokumentieren | rein lesend; keine Ausführung und kein Verwerfen |
| Mittel | Wiederherstellungsprotokoll | Erfolgreichen Restore später eindeutig nachvollziehen | nur Pfade, UTC und Prüfsummen; keine Inhalte, Rotation oder Löschung |
| Mittel | Mehrordner-Zeitreihe | Mehrere wichtige Ordner gemeinsam beobachten | Eltern- und Kindwerte nicht addieren |
| Mittel | Abnahmehistorie | Leistung und Stabilität mehrerer Läufe vergleichen | Berichte nur lesen |
| Niedrig | Barrierefreie GUI | Nutzung ohne Kommandozeile | gleiche Validierungs-, Bestätigungs- und Rückfallverträge wie CLI |

## Bereits umgesetzt

- Originaldatei-Schreibzugriffe technisch gesperrt.
- SQLite-Index mit Migration, Prozesslock, Backup, Restore und Repair.
- `WAL`, `synchronous=FULL` und zeit-/mengenbegrenztes Autosave.
- Begrenzte Wiederanlaufliste für bis zu zwölf verschiedene Indexdateien.
- Geführte Auswahl, Fortsetzung und bewusstes Einzelverwerfen.
- Optionale, geprüfte JSON-Sicherung vor Vorlagenänderungen.
- Sicherungskatalog mit Gesundheitsprüfung und bestätigter Einzellöschung.
- Rein lesender Vergleich einer Konfigurationssicherung mit ihrer aktiven Datei.
- Sichtbare Gruppen für Hinzufügen, Entfernen, Ersetzen und Unverändert.
- Geführte Einzelwiederherstellung nur für grün geprüfte Such- oder Zeitreihen-Sicherungen.
- Exakte Namensbestätigung und `--yes`.
- Automatische geprüfte Rückfallsicherung vor dem Überschreiben.
- SHA-256-Prüfung vor und nach der Mutation.
- Automatischer, erneut geprüfter Rückfall bei fehlgeschlagener Nachprüfung.
- Keine automatische Auswahl, Rotation, Sammellöschung oder Löschung nach Alter.
- Symlink-Ziele bei dauerhaften Schreib- und Löschoperationen gesperrt.
- Scanner, Suche, Berichte, Ordnervergleich, Zeitreihe, Vorlagen und Trendgrenzen.
- Abnahmeprofile mit 600, 10.000 und 100.000 Dateien.
