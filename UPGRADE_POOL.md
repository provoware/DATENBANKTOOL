# Upgrade-Pool

Stand: Version `0.19.0-alpha.1`

Upgrades werden erst umgesetzt, wenn Eingaben, Ausgaben, Fehlerfälle, Sicherheitsgrenzen und Registry-Eintrag festgelegt sind.

| Priorität | Upgrade | Nutzen | Sicherheitsgrenze |
|---|---|---|---|
| Hoch | Reale Laienabnahme | Diagnose, Startbarkeit und Protokollentscheidung mit unerfahrener Person prüfen | ausschließlich synthetische oder ausdrücklich freigegebene Testdaten |
| Hoch | Wiederherstellungsprotokoll-Prüfbefehl | Einen vorhandenen Restore-Nachweis später gegen Dateien und SHA-256 prüfen | vollständig lesend; keine Wiederherstellung, Änderung oder Löschung |
| Mittel | Geführte Protokollauswahl | Optionalen Protokollpfad im bestehenden Restore-Assistenten erfassen | nur neuer expliziter Pfad; kein Vorschlag, Überschreiben oder Automatismus |
| Mittel | Mehrordner-Zeitreihe | Mehrere wichtige Ordner gemeinsam beobachten | Eltern- und Kindwerte nicht addieren |
| Mittel | Abnahmehistorie | Leistung und Stabilität mehrerer Läufe vergleichen | Berichte nur lesen |
| Niedrig | Barrierefreie GUI | Nutzung ohne Kommandozeile | gleiche Validierungs-, Bestätigungs- und Rückfallverträge wie CLI |

## Bereits umgesetzt

- Originaldatei-Schreibzugriffe technisch gesperrt.
- SQLite-Index mit Migration, Prozesslock, Backup, Restore und Repair.
- `WAL`, `synchronous=FULL` und zeit-/mengenbegrenztes Autosave.
- Begrenzte Wiederanlaufliste für bis zu zwölf verschiedene Indexdateien.
- Geführte Auswahl, Fortsetzung und bewusstes Einzelverwerfen.
- Rein lesender Terminal- und JSON-Diagnosebefehl für alle Wiederanläufe.
- Diagnose zeigt Prüfstatus, Ordner, Index, Sitzung, Phase und Startbarkeit.
- Diagnose startet oder verwirft nichts und verändert Status- sowie Indexdateien nicht.
- Optionale, geprüfte JSON-Sicherung vor Vorlagenänderungen.
- Sicherungskatalog mit Gesundheitsprüfung und bestätigter Einzellöschung.
- Rein lesender Vergleich einer Konfigurationssicherung mit ihrer aktiven Datei.
- Geführte Einzelwiederherstellung nur für grün geprüfte Konfigurationssicherungen.
- Automatische geprüfte Rückfallsicherung und automatischer Rückfall bei Prüfversagen.
- Optionales inhaltsfreies Restore-Protokoll über einen ausdrücklich angegebenen neuen Pfad.
- Restore-Protokoll mit UTC, drei Pfaden und drei SHA-256-Werten; keine Inhalte oder Geheimnisse.
- Protokolle werden nicht automatisch benannt, ausgewählt, rotiert oder gelöscht.
- Symlink-Ziele bei dauerhaften Schreib- und Löschoperationen gesperrt.
- Scanner, Suche, Berichte, Ordnervergleich, Zeitreihe, Vorlagen und Trendgrenzen.
- Abnahmeprofile mit 600, 10.000 und 100.000 Dateien.
