# Analyse-Punkte

Stand: Version 0.1.0

| Bereich | Befund | Maßnahme / Status |
| --- | --- | --- |
| Schwachstellen | Beliebige Dateien könnten als Datenbank übergeben werden | Signatur, Existenz und Dateityp werden validiert |
| Fehlerfreiheit | SQLite-Fehler waren nicht behandelt | Einheitlicher `DatabaseError` und Exitcode 2 |
| Inkonsistenzen | Zuvor gab es keine definierte Ausgabe | Stabile Text- und JSON-Strukturen eingeführt |
| Redundanzen | Pfadprüfung könnte je Befehl doppelt entstehen | Zentral in `validate_database` gebündelt |
| Vereinheitlichung | Kein verbindlicher Versionsort vorhanden | `registry.json` ist alleinige Quelle |
| Wartbarkeit | Kein Quellcodeaufbau vorhanden | CLI, Kernlogik, Konfiguration und Tests getrennt |
| Komplexität | Zusätzliche Treiber würden den MVP überladen | Bewusst auf SQLite und Standardbibliothek begrenzt |
| Prüfungsqualität | Keine Prüfungen vorhanden | Erfolgs-, Validierungs- und JSON-Fehlerfälle getestet |
| Erscheinungsbild | Keine Oberfläche vorhanden | Ruhige, einheitliche Textausgabe; GUI bleibt Upgrade |
| Barrierefreiheit | CLI ist screenreader-tauglich, aber nicht geführt | Einfache Begriffe und vollständige `--help`-Texte |
| Nutzerfreundlichkeit | Fehler könnten technische Details zeigen | Handlungsnahe deutsche Fehlermeldungen |
| Stabilität | Schreibzugriff wäre ein Datenrisiko | SQLite-Verbindung erzwingt `mode=ro` |
| Laienfreundlichkeit | Fachbegriff „SQLite“ bleibt nötig | README erklärt Zweck und Beispiele knapp |
| Abhängigkeiten | Externe Pakete erhöhen Pflegeaufwand | Keine Laufzeitabhängigkeiten |

## Nächste Analyse

Vor dem CSV-Export sind Formel-Injektion in Tabellenprogrammen, Überschreiben vorhandener Dateien und große Ergebnismengen zu bewerten.
