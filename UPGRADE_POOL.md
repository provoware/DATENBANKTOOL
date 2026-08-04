# Upgrade-Pool

## Einfach verständliche nächste Verbesserungen

1. **Geführte Zeitreihenbedienung** – Ordner-Zeitreihe als eigenen Startseitenpunkt
   mit Detail-, Schritt-, Feld- und Fehlerhilfe anbieten.
2. **Barrierefreie Trendgrafiken** – Größe und Dateizahl im Offline-HTML zusätzlich
   als lokal erzeugte SVG-Liniengrafiken darstellen.
3. **Reale Laienabnahme** – die vorhandene Checkliste mit einer unerfahrenen
   Kubuntu-Testperson durchführen und konkrete Verständlichkeitsprobleme beheben.
4. **100.000-Dateien-Zieltest** – das vorhandene `large`-Profil auf Zielhardware
   ausführen und Referenzwerte dokumentieren.

## Später mögliche Erweiterungen

5. **Mehrere Ordner vergleichen** – ausgewählte Ordner gemeinsam als rein lesende
   Zeitreihen darstellen.
6. **Trendgrenzen** – sichtbare Warnschwellen für starkes Wachstum definieren.
7. **Zeitreihen-Vorlagen** – häufig geprüfte relative Ordnerpfade lokal speichern.
8. **Grafische Oberfläche** – Schaltflächen und Dateiauswahlfenster statt Texteingaben.
9. **HTML-Startbericht** – aktuelle Ordnerstände, Vergleiche und Zeitreihen bündeln.
10. **Abnahmehistorie** – mehrere JSON-Abnahmeberichte rein lesend vergleichen.

## Bereits umgesetzt

- Rein lesender Scanner und versionierter SQLite-Index.
- Inkrementeller Re-Scan, Änderungen, Prozesslock, Backup und Restore.
- Suche, kombinierbare Filter, Pagination und optionale FTS5-Suche.
- Ordnerübersicht mit Ampeln, Platzfressern und vollständigem Calc-CSV-Export.
- Rein lesender Ordnervergleich zwischen zwei Scans.
- Vollständiger Vergleichsexport über `--all-pages` für JSON, CSV und HTML.
- Rein lesende Ordner-Zeitreihe über mehrere abgeschlossene Scans.
- Zeitreihenwerte für Dateizahl, Größe, Differenzen, Prozentwerte und Zustände.
- Atomare JSON-, Calc-CSV- und Offline-HTML-Zeitreihenberichte.
- Sichere relative Pfadprüfung und strenger Stammordnervertrag.
- Suchvorlagen und mehrschichtige Laienhilfe.
- Geführte Terminal-Startseite.
- Modulare CLI und maschinenlesbarer Seiteneffektvertrag.
- Reproduzierbare Abnahmeprofile mit 600, 10.000 und 100.000 Dateien.
- Laufzeit-, Speicher- und Quelldatenprüfung mit archivierten Berichten.
- Finale 0.11-Prüfung mit 71 Tests je Python-Version sowie Quick und Standard 11/11.
