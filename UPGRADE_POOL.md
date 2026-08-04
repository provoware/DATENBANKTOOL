# Upgrade-Pool

## Bereits in 0.14.0-alpha.1 umgesetzt

- Geführtes Startseiten-Untermenü für Zeitreihen-Vorlagen.
- Anzeigen, Speichern, bewusstes Ersetzen und nach Namensprüfung bestätigtes Löschen.

| Priorität | Upgrade | Nutzen | Voraussetzung |
| --- | --- | --- | --- |
| Hoch | Geführte Vorlagenverwaltung | Vorlagen ohne direkte CLI verwalten | Anzeigen, Ersetzen und Löschen laienfreundlich spezifizieren |
| Mittel | PostgreSQL-Anbindung | Serverdatenbanken analysieren | Treiber- und Geheimnisverwaltung festlegen |
| Mittel | Schema-Vergleich | Änderungen zwischen zwei Ständen erkennen | stabiles neutrales Schemamodell |
| Niedrig | Barrierefreie GUI | Nutzung ohne Kommandozeile | Bedienkonzept und GUI-Technik auswählen |

Upgrades werden erst umgesetzt, wenn Eingaben, Ausgaben und Fehlerfälle spezifiziert sind.
Stand: Version 0.13.0-alpha.1

Upgrades werden erst umgesetzt, wenn Eingaben, Ausgaben, Fehlerfälle und der passende Registry-Eintrag spezifiziert sind.

## Einheitlich offene Punkte

1. reale Laienabnahme,
2. `large`-Profil auf Zielhardware,
3. geführte Vorlagenverwaltung,
4. Mehrordner-Zeitreihe.

## Einfach verständliche nächste Verbesserungen

1. **Geführte Vorlagenverwaltung** – Vorlagen auf der Startseite anzeigen, bewusst
   ersetzen und nach Namensprüfung bestätigt löschen.
2. **Mehrordner-Zeitreihe** – mehrere ausgewählte relative Ordner gemeinsam, aber
   klar getrennt als rein lesende Trends darstellen.
3. **Reale Laienabnahme** – die vorhandene Checkliste mit einer unerfahrenen
   Kubuntu-Testperson durchführen und konkrete Verständlichkeitsprobleme beheben.
4. **Abnahmehistorie** – mehrere JSON-Abnahmeberichte rein lesend vergleichen und
   Abweichungen zwischen Zielsystemen verständlich erklären.

## Später mögliche Erweiterungen

5. **Zeitabstandsachse** – Diagrammpunkte optional nach realem Scan-Zeitabstand statt
   nur nach Scan-Reihenfolge positionieren.
6. **HTML-Startbericht** – aktuelle Ordnerstände, Vergleiche und Zeitreihen bündeln.
7. **Grafische Oberfläche** – Schaltflächen und Dateiauswahlfenster statt Texteingaben.
8. **Abnahmehistorie** – mehrere JSON-Abnahmeberichte rein lesend vergleichen.
9. **Exportprofil** – bevorzugtes Zeitreihenformat und Berichtsziel lokal speichern.
10. **Statistische Trendprüfung** – optionale langfristige Abweichungen zusätzlich zu
    den einfachen Übergangsschwellen erklären.

## Bereits umgesetzt

- Rein lesender Scanner und versionierter SQLite-Index.
- Inkrementeller Re-Scan, Änderungen, Prozesslock, Backup und Restore.
- Suche, Filter, Pagination und optionale FTS5-Suche.
- Ordnerübersicht mit Ampeln, Platzfressern und vollständigem Calc-CSV-Export.
- Rein lesender Ordnervergleich und vollständiger `--all-pages`-Export.
- Rein lesende Ordner-Zeitreihe über mehrere abgeschlossene Scans.
- Geführter Startseitenpunkt 11 mit Detail-, Schritt-, Feld- und Fehlerhilfe.
- Zwei lokale barrierefreie SVG-Trendgrafiken ohne Skripte oder externe Ressourcen.
- Lokale validierte Zeitreihen-Vorlagen mit atomarem Schreibvertrag und Modus 0600.
- Vorlagenbefehle list, show, save und bestätigtes delete.
- Direkte Vorlagenauswahl per Nummer oder Name auf der Startseite.
- Bestätigter Startseitenpunkt 12 zum Speichern neuer Vorlagen.
- Optionale Größen- und Dateizahl-Warnschwellen.
- Begründete Warnungen in Terminal, JSON, CSV, HTML und SVG.
- Trennung von Verlaufsklassifikation und Warnstatus.
- Reproduzierbare Abnahmeprofile mit 600, 10.000 und 100.000 Dateien.
- 0.13-Funktionsprüfung mit 86 Tests je Python-Version sowie Quick und Standard 11/11.
- Large-Abnahme auf Zielhardware: 100.000 Dateien, 11/11, 218,722 s, 107.011.474 Byte Python-Peak.
- Startseiten-Kataloge und Eingabeparser in kleine Wartungsmodule getrennt.
- CLI-Importkopf bereinigt und Parser-Fehlerfälle gezielt getestet.
