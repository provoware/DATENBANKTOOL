# Upgrade-Pool

Stand: Version `0.20.0-alpha.1`

Upgrades werden erst umgesetzt, wenn Eingaben, Ausgaben, Fehlerfälle, Sicherheitsgrenzen und Registry-Eintrag festgelegt sind.

| Priorität | Upgrade | Nutzen | Sicherheitsgrenze |
|---|---|---|---|
| Hoch | Reale Laienabnahme | Diagnose, Restore und Protokollprüfung mit unerfahrener Person prüfen | ausschließlich synthetische oder ausdrücklich freigegebene Testdaten |
| Hoch | Geführte Protokollprüfung | Restore-Nachweis ohne freie Terminaleingabe prüfen | exakter Nutzerpfad; kein Suchen, Starten, Ändern oder Löschen |
| Mittel | Optionaler Protokoll-SHA-Pin | Verwechslung oder Austausch der Protokolldatei vor Schemaauswertung erkennen | nur ausdrücklich übergebener SHA-256; keine Speicherung oder automatische Ermittlung |
| Mittel | Geführte Protokollerzeugung | Optionalen neuen Protokollpfad im Restore-Assistenten erfassen | nur neuer expliziter Pfad; kein Vorschlag oder Überschreiben |
| Mittel | Mehrordner-Zeitreihe | Mehrere wichtige Ordner gemeinsam beobachten | Eltern- und Kindwerte nicht addieren |
| Niedrig | Barrierefreie GUI | Nutzung ohne Kommandozeile | gleiche Validierungs-, Bestätigungs- und Rückfallverträge wie CLI |

## Bereits umgesetzt

- Originaldatei-Schreibzugriffe technisch gesperrt.
- SQLite-Index mit Migration, Prozesslock, Backup, Restore und Repair.
- `WAL`, `synchronous=FULL` und zeit-/mengenbegrenztes Autosave.
- Begrenzte Wiederanlaufliste und rein lesende Wiederanlauf-Diagnose.
- Optionale geprüfte JSON-Sicherung vor Vorlagenänderungen.
- Sicherungskatalog mit Gesundheitsprüfung und bestätigter Einzellöschung.
- Rein lesender Vergleich und geführte Einzelwiederherstellung einer Konfigurationssicherung.
- Automatische geprüfte Rückfallsicherung und automatischer Rückfall bei Prüfversagen.
- Optionales inhaltsfreies Restore-Protokoll über einen ausdrücklich angegebenen neuen Pfad.
- Restore-Protokoll mit UTC, drei Pfaden und drei SHA-256-Werten; keine Inhalte oder Geheimnisse.
- Rein lesender Terminal- und JSON-Prüfbefehl für genau ein ausgewähltes Restore-Protokoll.
- Strenge Schema-, UTC-, Pfad- und Hashvalidierung vor dem Dateivergleich.
- Dateivergleich mit `O_NOFOLLOW`, gestreamtem SHA-256 und getrennten Zuständen für Übereinstimmung, Fehlen und Abweichung.
- Keine automatische Protokollbenennung, Auswahl, Rotation oder Löschung.
- Scanner, Suche, Berichte, Ordnervergleich, Zeitreihe, Vorlagen und Trendgrenzen.
- Abnahmeprofile mit 600, 10.000 und 100.000 Dateien.
