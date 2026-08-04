# Upgrade-Pool

## Einfach verständliche nächste Verbesserungen

1. **Ordner-Zeitreihe** – Größe und Dateizahl eines Ordners über mehrere
   abgeschlossene Scans darstellen.
2. **Vollständiger Vergleichsexport** – mit `--all-pages` alle gefilterten
   Vergleichszeilen als JSON, CSV oder HTML speichern.
3. **Reale Laienabnahme** – die erzeugte Checkliste mit einer unerfahrenen
   Kubuntu-Testperson durchführen und konkrete Verständlichkeitsprobleme beheben.
4. **100.000-Dateien-Zieltest** – das vorhandene `large`-Profil auf der vorgesehenen
   Hardware ausführen und feste Zielwerte dokumentieren.

## Später mögliche Erweiterungen

5. **Grafische Oberfläche** – Schaltflächen und Dateiauswahlfenster statt Texteingaben.
6. **Favoriten** – häufig verwendete Ordner und Indexdateien lokal speichern.
7. **Vorlagen übertragen** – Suchvorlagen exportieren und importieren.
8. **HTML-Startbericht** – wichtige Ergebnisse auf einer lokalen Übersichtsseite bündeln.
9. **Abnahmehistorie** – mehrere JSON-Abnahmeberichte vergleichen, ohne sie zu verändern.
10. **Trendwarnungen** – rein lesend melden, wenn Laufzeit oder Speicher gegenüber einer
    früheren Abnahme deutlich steigen.

## Bereits umgesetzt

- Rein lesender Scanner und SQLite-Index.
- Inkrementeller Re-Scan, Änderungsberichte, Backup und Restore.
- Suche, Filter, Pagination und optionale FTS5-Suche.
- Ordnerübersicht mit Dateizahl, Gesamtgröße, Ampeln und Platzfressern.
- Ordnerübersicht als LibreOffice-kompatible CSV.
- Vollständiger Ordnerexport über `--all-pages`.
- Suchvorlagen und mehrschichtige Laienhilfe.
- Geführte Terminal-Startseite.
- Modulare CLI und maschinenlesbarer Seiteneffektvertrag.
- Rein lesender Ordnervergleich zwischen zwei Scans.
- JSON-, CSV- und HTML-Berichte.
- Reproduzierbare Profile mit 600, 10.000 und 100.000 synthetischen Dateien.
- Laufzeit-, Phasen-, Python-Speicher- und Prozess-RSS-Messung.
- Quelldaten-Manifest vor und nach der Abnahme.
- Elf automatische Kriterien.
- JSON-, Markdown-, CSV- und Laien-Checklistenberichte.
- Quick-Abnahme mit 600 Dateien: 11/11 bestanden.
- Standard-Abnahme mit 10.000 Dateien: 11/11 bestanden.
- Archivierte GitHub-Actions-Abnahmeberichte.
