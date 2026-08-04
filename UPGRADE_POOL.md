# Upgrade-Pool

Stand: Version 0.14.0-alpha.1

Upgrades werden erst umgesetzt, wenn Eingaben, Ausgaben, Fehlerfälle und der passende Registry-Eintrag spezifiziert sind.

| Priorität | Upgrade | Nutzen | Voraussetzung |
| --- | --- | --- | --- |
| Hoch | Mehrordner-Zeitreihe | Mehrere wichtige Ordner in einem Bericht vergleichen | Darstellung überlappender Eltern-/Kindordner eindeutig erklären |
| Hoch | Reale Laienabnahme | Verständlichkeit mit echter unerfahrener Person prüfen | Zielsystem und ausgefüllte Checkliste |
| Mittel | Abnahmehistorie | Messwerte mehrerer Läufe verständlich vergleichen | stabiles JSON-Vergleichsformat |
| Mittel | PostgreSQL-Anbindung | Serverdatenbanken analysieren | Treiber- und Geheimnisverwaltung festlegen |
| Mittel | Schema-Vergleich | Änderungen zwischen zwei Datenbankständen erkennen | stabiles neutrales Schemamodell |
| Niedrig | Barrierefreie GUI | Nutzung ohne Kommandozeile | Bedienkonzept und GUI-Technik auswählen |

## Bereits umgesetzt

- Rein lesender Scanner und versionierter SQLite-Index.
- Inkrementeller Re-Scan, Änderungen, Prozesslock, Backup und Restore.
- Suche, Filter, Pagination und optionale FTS5-Suche.
- Ordnerübersicht, Ordnervergleich, Zeitreihe und vollständige Exporte.
- Lokale validierte Zeitreihen-Vorlagen mit atomarem Schreibvertrag und Modus `0600`.
- Geführte Vorlagenverwaltung mit Anzeigen, Speichern, bewusstem Ersetzen und bestätigtem Löschen.
- Optionale Größen- und Dateizahl-Warnschwellen mit begründeten Warnungen.
- Reproduzierbare Abnahmeprofile mit 600, 10.000 und 100.000 Dateien.
- Registry-Drift-Test und bereinigter Versionsvertrag für `0.14.0-alpha.1`.
