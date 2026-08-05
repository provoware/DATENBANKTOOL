# Upgrade-Pool

Stand: Version `0.16.0-alpha.1`

Upgrades werden erst umgesetzt, wenn Eingaben, Ausgaben, Fehlerfälle, Wiederanlauf und Registry-Eintrag festgelegt sind.

| Priorität | Upgrade | Nutzen | Sicherheitsgrenze |
|---|---|---|---|
| Hoch | Mehrere unabhängige Wiederanläufe | Unterbrochene Scans verschiedener Indexdateien getrennt fortsetzen | begrenzte Liste; jeden Eintrag erneut nur lesend validieren und einzeln bestätigen |
| Hoch | Reale Laienabnahme | Sprache und Entscheidungen mit echter unerfahrener Person prüfen | persönliche Dateien nicht als Testdaten verwenden |
| Mittel | Konfigurations-Sicherung vor Änderung | Vorlagen vor Ersetzen oder Löschen leichter zurückholen | nur neue zeitgestempelte Sicherung; keine automatische Rotation |
| Mittel | Mehrordner-Zeitreihe | Mehrere wichtige Ordner gemeinsam beobachten | Eltern- und Kindwerte nicht addieren |
| Mittel | Abnahmehistorie | Leistung und Stabilität mehrerer Läufe vergleichen | Berichte nur lesen |
| Niedrig | Barrierefreie GUI | Nutzung ohne Kommandozeile | gleiche Validierungs-, Bestätigungs- und Wiederanlaufverträge wie CLI |

## Bereits umgesetzt

- Originaldatei-Schreibzugriffe technisch gesperrt.
- SQLite-Index mit Migration, Prozesslock, Backup, Restore und Repair.
- `WAL`, `synchronous=FULL` und zeit-/mengenbegrenztes Autosave.
- Vollscan und Re-Scan über `--resume` fortsetzbar.
- Geführte Erkennung und Bestätigung eines unterbrochenen Scans auf der Startseite.
- Dauerhafter eigener Wiederanlaufdatensatz neben dem allgemeinen Laufjournal.
- Startklar-Prüfung, Crashberichte und Geheimnis-Ausblendung.
- Index- und Konfigurationssicherungen nach Alter, Größe und Zustand prüfbar.
- Genau eine katalogisierte Sicherung nach exakter Bestätigung löschbar.
- Keine automatische Rotation, Sammellöschung oder Löschung nach Alter.
- Symlink-Ziele bei dauerhaften Schreib- und Löschoperationen gesperrt.
- Scanner, Suche, Berichte, Ordnervergleich, Zeitreihe, Vorlagen und Trendgrenzen.
- Abnahmeprofile mit 600, 10.000 und 100.000 Dateien.
