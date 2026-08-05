# Upgrade-Pool

Stand: Version `0.15.0-alpha.1`

Upgrades werden erst umgesetzt, wenn Eingaben, Ausgaben, Fehlerfälle, Wiederanlauf und Registry-Eintrag festgelegt sind.

| Priorität | Upgrade | Nutzen | Sicherheitsgrenze |
|---|---|---|---|
| Hoch | Geführter Wiederanlauf | Unterbrochenen Scan ohne Befehlskenntnis fortsetzen | nur geprüften `--resume`-Befehl anzeigen; Start nach Bestätigung |
| Hoch | Reale Laienabnahme | Sprache, Autosave und Fehlerhilfe mit echter unerfahrener Person prüfen | persönliche Dateien nicht als Testdaten verwenden |
| Mittel | Sicherungsübersicht | Index- und Konfigurationssicherungen verständlich finden | niemals automatisch löschen |
| Mittel | Mehrordner-Zeitreihe | Mehrere wichtige Ordner gemeinsam beobachten | Eltern- und Kindwerte nicht addieren |
| Mittel | Abnahmehistorie | Leistung und Stabilität mehrerer Läufe vergleichen | Berichte nur lesen |
| Niedrig | Barrierefreie GUI | Nutzung ohne Kommandozeile | gleiche Validierungs- und Wiederanlaufverträge wie CLI |

## Bereits umgesetzt

- Originaldateien bleiben technisch schreibgeschützt.
- SQLite-Index mit Migration, Prozesslock, Backup, Restore und Repair.
- `WAL` mit `synchronous=FULL`.
- Autosave spätestens nach fünf Sekunden oder 500 Einträgen.
- Wiederaufnahme von Vollscan und Änderungsprüfung über `--resume`.
- Laufjournal, Crashberichte und Geheimnis-Ausblendung.
- Startklar-Prüfung mit optionalem Nur-Lese-Integritätstest.
- Dauerhafte atomare Dateifreigabe mit Datei- und Ordner-`fsync`.
- Gehärtete Vorlagen-, Berichts-, Sicherungs- und Wiederherstellungsschreibwege.
- Einfache Nutzeransprache vor technischen Einzelheiten.
- Scanner, Suche, Berichte, Ordnervergleich, Zeitreihe, Vorlagen und Trendgrenzen.
- Abnahmeprofile mit 600, 10.000 und 100.000 Dateien.
