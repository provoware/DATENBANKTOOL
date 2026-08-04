# Upgrade-Pool

## Einfach verständliche nächste Verbesserungen

1. **Zeitreihen-Vorlagen** – häufig geprüfte relative Ordnerpfade lokal speichern und
   direkt in der geführten Startseite auswählen.
2. **Trendgrenzen** – optionale Warnschwellen für starkes Größen- oder Dateiwachstum
   rein lesend und mit verständlicher Begründung anzeigen.
3. **Reale Laienabnahme** – die vorhandene Checkliste mit einer unerfahrenen
   Kubuntu-Testperson durchführen und konkrete Verständlichkeitsprobleme beheben.
4. **100.000-Dateien-Zieltest** – das vorhandene `large`-Profil auf Zielhardware
   ausführen und Referenzwerte dokumentieren.

## Später mögliche Erweiterungen

5. **Mehrere Ordner vergleichen** – ausgewählte Ordner gemeinsam als rein lesende
   Zeitreihen darstellen.
6. **Zeitabstandsachse** – Diagrammpunkte optional nach realem Scan-Zeitabstand statt
   nur nach Scan-Reihenfolge positionieren.
7. **HTML-Startbericht** – aktuelle Ordnerstände, Vergleiche und Zeitreihen bündeln.
8. **Grafische Oberfläche** – Schaltflächen und Dateiauswahlfenster statt Texteingaben.
9. **Abnahmehistorie** – mehrere JSON-Abnahmeberichte rein lesend vergleichen.
10. **Exportprofil** – bevorzugtes Zeitreihenformat und Berichtsziel lokal speichern.

## Bereits umgesetzt

- Rein lesender Scanner und versionierter SQLite-Index.
- Inkrementeller Re-Scan, Änderungen, Prozesslock, Backup und Restore.
- Suche, kombinierbare Filter, Pagination und optionale FTS5-Suche.
- Ordnerübersicht mit Ampeln, Platzfressern und vollständigem Calc-CSV-Export.
- Rein lesender Ordnervergleich und vollständiger `--all-pages`-Export.
- Rein lesende Ordner-Zeitreihe über mehrere abgeschlossene Scans.
- Zeitreihenwerte für Dateizahl, Größe, Differenzen, Prozentwerte und Zustände.
- Atomare JSON-, Calc-CSV- und Offline-HTML-Zeitreihenberichte.
- Eigener Startseitenpunkt 11 für die Ordner-Zeitreihe.
- Validierter Dialog für Ordner, Sitzungen, Zeitpunkte und Berichte.
- Detail-, Schritt-für-Schritt-, Feld- und Fehlerhilfe.
- Hilfezentrum und Alltagswortsuche für `folder-timeline`.
- Zwei lokale barrierefreie SVG-Trendgrafiken.
- Tastaturfokussierbare Datenpunkte und vollständige Wertetabelle.
- Skriptfreies HTML ohne externe Ressourcen.
- Sichere relative Pfadprüfung und strenger Stammordnervertrag.
- Modulare CLI und maschinenlesbarer Seiteneffektvertrag.
- Reproduzierbare Abnahmeprofile mit 600, 10.000 und 100.000 Dateien.
- Laufzeit-, Speicher- und Quelldatenprüfung mit archivierten Berichten.
- 0.12-Funktionsprüfung mit 77 Tests je Python-Version sowie Quick und Standard 11/11.
