# Upgrade-Pool

Stand: Version `0.17.0-alpha.1`

Upgrades werden erst umgesetzt, wenn Eingaben, Ausgaben, Fehlerfälle, Wiederanlauf und Registry-Eintrag festgelegt sind.

| Priorität | Upgrade | Nutzen | Sicherheitsgrenze |
|---|---|---|---|
| Hoch | Reale Laienabnahme | Auswahl, Sprache und Sicherungsentscheidung mit unerfahrener Person prüfen | ausschließlich synthetische oder ausdrücklich freigegebene Testdaten |
| Hoch | Wiederanlauf-Diagnosebefehl | Mehrere gespeicherte Einträge außerhalb der Startseite prüfen und dokumentieren | rein lesend; keine Ausführung und kein Verwerfen |
| Mittel | Geführte Konfigurations-Wiederherstellung | Einzelne geprüfte Vorlagensicherung kontrolliert zurückholen | vorher Rückfallsicherung; exakte Auswahl und Bestätigung; keine Automatik |
| Mittel | Mehrordner-Zeitreihe | Mehrere wichtige Ordner gemeinsam beobachten | Eltern- und Kindwerte nicht addieren |
| Mittel | Abnahmehistorie | Leistung und Stabilität mehrerer Läufe vergleichen | Berichte nur lesen |
| Niedrig | Barrierefreie GUI | Nutzung ohne Kommandozeile | gleiche Validierungs-, Bestätigungs- und Wiederanlaufverträge wie CLI |

## Bereits umgesetzt

- Originaldatei-Schreibzugriffe technisch gesperrt.
- SQLite-Index mit Migration, Prozesslock, Backup, Restore und Repair.
- `WAL`, `synchronous=FULL` und zeit-/mengenbegrenztes Autosave.
- Vollscan und Re-Scan über `--resume` fortsetzbar.
- Begrenzte Wiederanlaufliste für bis zu zwölf verschiedene Indexdateien.
- Deduplizierung pro Indexdatei und Dateisperre für parallele Zugriffe.
- Getrennte Nur-Lese-Prüfung jedes Wiederanlaufeintrags.
- Geführte Auswahl, Fortsetzung und bewusstes Einzelverwerfen.
- Nicht startbare Einträge bleiben bis zur ausdrücklichen Entscheidung sichtbar.
- Startklar-Prüfung, Crashberichte und Geheimnis-Ausblendung.
- Index- und Konfigurationssicherungen nach Alter, Größe und Zustand prüfbar.
- Optionale, geprüfte und zeitgestempelte JSON-Sicherung vor Vorlagenänderungen.
- Sicherungsprüfung über Struktur, Schema, Vorlagenzahl und SHA-256.
- Keine automatische Rotation, Sammellöschung oder Löschung nach Alter.
- Symlink-Ziele bei dauerhaften Schreib- und Löschoperationen gesperrt.
- Scanner, Suche, Berichte, Ordnervergleich, Zeitreihe, Vorlagen und Trendgrenzen.
- Abnahmeprofile mit 600, 10.000 und 100.000 Dateien.
