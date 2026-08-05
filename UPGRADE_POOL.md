# Upgrade-Pool

Stand: Version `0.21.0-alpha.1`

Upgrades werden erst umgesetzt, wenn Eingaben, Ausgaben, Fehlerfälle, Sicherheitsgrenzen und Registry-Eintrag festgelegt sind.

| Priorität | Upgrade | Nutzen | Sicherheitsgrenze |
|---|---|---|---|
| Hoch | Geführte Kubuntu-Abnahmesitzung | Letzten offenen Hauptpunkt reproduzierbar vorbereiten und dokumentieren | nur neuer synthetischer Arbeitsbereich; keine echten Konfigurationen oder persönlichen Dateien |
| Mittel | Optionaler Prüfberichtsexport | Grün-/Gelb-/Rot-Befund dauerhaft als JSON oder Markdown sichern | nur ausdrücklicher neuer Pfad; kein Überschreiben, keine automatische Benennung, Rotation oder Löschung |
| Mittel | Abnahmehistorie | Leistung und Stabilität mehrerer synthetischer Läufe vergleichen | Berichte nur lesen; keine persönlichen Dateien |
| Mittel | Mehrordner-Zeitreihe | Mehrere wichtige Ordner gemeinsam beobachten | Eltern- und Kindwerte nicht doppelt addieren |
| Niedrig | Barrierefreie GUI | Nutzung ohne Kommandozeile | identische Prüf-, Bestätigungs- und Rückfallverträge wie CLI |

## Bereits umgesetzt

- Originaldatei-Schreibzugriffe technisch gesperrt.
- SQLite-Index mit Migration, Prozesslock, Backup, Restore und Repair.
- Begrenzte Wiederanlaufliste und rein lesende Wiederanlauf-Diagnose.
- Geführte Konfigurations-Wiederherstellung mit automatischer Rückfallsicherung.
- Optionales inhaltsfreies Restore-Protokoll nur bei ausdrücklichem Zielpfad.
- Rein lesender Protokoll-Prüfbefehl mit festem Schema und drei Dateihashes.
- Geführte Protokollprüfung ohne automatische Suche oder Auswahl.
- Geführte optionale Protokollpfaderfassung nach exakter Restore-Bestätigung.
- Vorhandene Protokollziele und Symlinks werden nicht überschrieben.
- Optionaler SHA-256-Pin der Protokolldatei vor jeder Schemaauswertung.
- Keine automatische Pin-Ermittlung, Speicherung oder Historie.
- Terminal- und JSON-Ausgaben mit klaren Grün-/Gelb-/Rot-Befunden.
- Autosave, Crashberichte, Sicherungskatalog und atomare Dateiveröffentlichung.
- Abnahmeprofile mit 600, 10.000 und 100.000 synthetischen Dateien.
