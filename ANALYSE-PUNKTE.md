# Analyse-Punkte

Stand: Version 0.14.0-alpha.1

| Bereich | Befund | Maßnahme / Status |
| --- | --- | --- |
| Nutzerfreundlichkeit | Zeitreihen-Vorlagen waren auf der Startseite nur speicher- und auswählbar | Punkt 12 ist jetzt ein Untermenü für Anzeigen, Speichern, Ersetzen und Löschen |
| Robustheit | Löschen über eine geführte Oberfläche kann bei ähnlichen Namen riskant sein | Exakte Namenswiederholung und Ja/Nein-Bestätigung sind vorgeschaltet |
| Hilfesystem | Ersetzen und Löschen benötigten eigene Feldhilfe | Feld- und Fehlertexte erklären Namen, Ersetzen und Löschwirkung |

Stand: Version 0.1.0
Stand: Version 0.13.0-alpha.2

| Bereich | Befund | Maßnahme / Status |
| --- | --- | --- |
| Schwachstellen | Beliebige Dateien könnten als Datenbank übergeben werden | Signatur, Existenz und Dateityp werden validiert |
| Fehlerfreiheit | SQLite-Fehler waren nicht behandelt | Einheitlicher `DatabaseError` und Exitcode 2 |
| Inkonsistenzen | Zuvor gab es keine definierte Ausgabe | Stabile Text- und JSON-Strukturen eingeführt |
| Redundanzen | Pfadprüfung könnte je Befehl doppelt entstehen | Zentral in `validate_database` gebündelt |
| Vereinheitlichung | Zwei Versionsschreibweisen können driften | `registry.json` führt PEP-440-Version und Anzeigeversion; Drift-Test gleicht CLI, Doku und Projektregistry ab |
| Wartbarkeit | Kein Quellcodeaufbau vorhanden | CLI, Kernlogik, Konfiguration und Tests getrennt |
| Komplexität | Zusätzliche Treiber würden den MVP überladen | Bewusst auf SQLite und Standardbibliothek begrenzt |
| Prüfungsqualität | Keine Prüfungen vorhanden | Erfolgs-, Validierungs- und JSON-Fehlerfälle getestet |
| Erscheinungsbild | Keine Oberfläche vorhanden | Ruhige, einheitliche Textausgabe; GUI bleibt Upgrade |
| Barrierefreiheit | CLI ist screenreader-tauglich, aber nicht geführt | Einfache Begriffe und vollständige `--help`-Texte |
| Nutzerfreundlichkeit | Fehler könnten technische Details zeigen | Handlungsnahe deutsche Fehlermeldungen |
| Stabilität | Schreibzugriff wäre ein Datenrisiko | SQLite-Verbindung erzwingt `mode=ro` |
| Laienfreundlichkeit | Fachbegriff „SQLite“ bleibt nötig | README erklärt Zweck und Beispiele knapp |
| Abhängigkeiten | Externe Pakete erhöhen Pflegeaufwand | Keine Laufzeitabhängigkeiten |
| Inkonsistenzen | Alter README-MVP-Block widersprach dem aktuellen 0.13-Status | Startstatus, offene Hauptpunkte und aktuelle Einstiegspunkte konsolidiert |

## Nächste Analyse

Vor der nächsten Funktionsrunde sind reale Laienabnahme, 100.000-Dateien-Zielmessung und eine geführte Vorlagenverwaltung zu bewerten.

## Ergebnis dieser Iteration

DATENBANKTOOL besitzt jetzt sichere lokale Zeitreihen-Vorlagen und optionale,
rein lesende Trendgrenzen. Häufig geprüfte relative Ordner sind direkt auf der
Startseite auswählbar. Auffälliges Größen- oder Dateizahlwachstum erscheint in
Terminal und Berichten mit Messwert, Warnschwelle und konkreter Begründung.

## Vollständig gelöste Vorlagenpunkte

1. Eigene Vorlagendomäne getrennt von Suchvorlagen.
2. Speicherung ohne Datenbankpfad oder Scan-Inhalte.
3. Gemeinsame relative Ordnerprüfung mit der Zeitreihenlogik.
4. Ablehnung absoluter Pfade und Elternnavigation.
5. Normalisierte Namen und begrenzte Beschreibungen.
6. Atomare JSON-Freigabe.
7. Linux-Dateiberechtigung `0600`.
8. Überschreibschutz ohne `--replace`.
9. Bestätigtes Löschen über `--yes`.
10. CLI-Funktionen list, show, save und delete.
11. Zeitreihenaufruf über `--preset`.
12. Kontrollierter Ausschluss gleichzeitiger Ordner- und Vorlagenangabe.
13. Nummerierte Auswahl auf Startseitenpunkt 11.
14. Auswahl per Nummer oder exaktem Namen.
15. Manueller Rückfall bei leerer oder nicht lesbarer Vorlagenliste.
16. Bestätigter Startseitenpunkt 12 zum Speichern.
17. Detail-, Schritt-, Feld- und Fehlerhilfe.

## Vollständig gelöste Trendgrenzenpunkte

18. Optionale Größenwachstumsgrenze.
19. Optionale Dateizahlwachstumsgrenze.
20. Vergleich mit dem vorherigen sichtbaren Scan.
21. Prüfung ausschließlich positiven Wachstums.
22. Sichere Behandlung eines Null-Ausgangswerts.
23. Endlichkeits- und Bereichsvalidierung.
24. Getrennte Datei- und Größenprozente.
25. Getrennter fachlicher Verlauf und Warnstatus.
26. ROT ausschließlich bei erreichter konfigurierter Schwelle.
27. Messwert und Schwelle in jeder Begründung.
28. Ausdrücklicher Hinweis gegen Schadens- oder Löschinterpretation.
29. Konsistente Terminal-, JSON-, CSV- und HTML-Darstellung.
30. Sichtbare SVG-Markierung mit dem Wort `Warnung`.
31. Zugängliche ARIA-Beschreibung jedes ausgelösten Punktes.

## Architekturentscheidungen

### Vorlagen getrennt von Suchfiltern

`core/timeline_presets.py` besitzt ein eigenes Schema. Dadurch können Suchfilter und
Zeitreihenordner nicht versehentlich vermischt werden. Vorlagen bleiben klein und
enthalten keine Pfade zur SQLite-Datenbank.

### Doppelte Validierung

Vorlagen werden beim Schreiben und erneut beim Lesen normalisiert. Der geführte Dialog
validiert Schwellen vorab; der öffentliche CLI-Parser und `FolderTimelineOptions`
prüfen erneut. Beschädigte oder manuell manipulierte Konfigurationen werden nicht
blind übernommen.

### Warnstatus überschreibt keinen Verlauf

`FolderTimelinePoint.status` beschreibt weiterhin den tatsächlichen Übergang wie
`grown` oder `shrunk`. `threshold_triggered`, `threshold_reasons` und die Ampel bilden
den optionalen Warnvertrag. Auswertungsdaten und Nutzerwarnung bleiben damit getrennt.

### Sichtbarer Scan als Vergleichsbasis

Prozentwerte beziehen sich auf den direkten vorherigen Punkt der tatsächlich
angezeigten Zeitreihe. Dies ist deterministisch und entspricht der Terminal- und
Berichtsreihenfolge. Der erste sichtbare Punkt bleibt Ausgangswert.

### Keine automatische Reaktion

Eine erreichte Grenze erzeugt nur Text und Darstellung. Es gibt keinen Callback für
Löschen, Verschieben, Scanstart oder andere Folgeaktionen. Damit bleibt die Funktion
rein diagnostisch.

## Verbesserte Prüfqualität

Die neuen Tests decken ab:

- Vorlagen-Roundtrip und Fall-unabhängige Namensauflösung,
- Modus `0600`, atomaren Überschreibschutz und bewusstes Ersetzen,
- Ablehnung unsicherer Ordnerpfade,
- Löschbestätigung,
- Parser, Handler, `CommandPolicy` und Modulzuständigkeit,
- Startseiten-Auswahl per Nummer,
- bestätigtes Speichern über Punkt 12,
- deutsches Dezimalkomma und Zahlenbereiche,
- gleichzeitigen Größen- und Dateizahl-Treffer,
- Null-, NaN-, Unendlich- und Grenzwertfälle,
- Gründe in Terminal, JSON, CSV, HTML und SVG,
- Skript- und Netzwerkfreiheit des HTML-Berichts,
- Detail-, Schritt-, Feld- und Fehlerhilfe.

Gesamtstand:

- 87 Tests unter Python 3.10,
- 87 Tests unter Python 3.12,
- Warnungen als Fehler,
- Quick-Abnahme 11/11,
- Standard-Abnahme 11/11,
- Large-Abnahme 11/11 auf Zielhardware.

## 0.13-Funktionsreferenz

Run `30927676213`, Funktionscommit
`8ded929533f806c739a7139b47d16379a788cfb0`:

| Profil | Dateien | Kriterien | Laufzeit | Python-Spitzenspeicher |
|---|---:|---:|---:|---:|
| Quick | 600 | 11/11 | 1,129 s | 1.324.226 Byte |
| Standard | 10.000 | 11/11 | 18,150 s | 13.398.233 Byte |
| Large | 100.000 | 11/11 | 218,722 s | 107.011.474 Byte |

## Erkannte nächste Analysepunkte

1. Geführtes Anzeigen, Ersetzen und Löschen der Vorlagen ergänzen.
2. Mehrere Ordner in einem klar getrennten Trendbericht darstellen.
3. Reale Zeitabstände optional auf der x-Achse abbilden.
4. Reale Laienabnahme auf Kubuntu durchführen.
5. Abnahmehistorie für mehrere Large-Läufe rein lesend vergleichbar machen.
6. Später grafische Pfadauswahldialoge ergänzen.
7. Bei der nächsten Release-Erhöhung zuerst `registry.json`, `project_registry.json` und `pyproject.toml` gemeinsam aktualisieren.

## Fazit

Die Large-Abnahme ist vermessen und blieb deutlich unter den Grenzen von 3.600 Sekunden und 4.096 MiB Python-Speicher. Beide Aufträge sind vollständig umgesetzt und automatisch abgesichert. Vorlagen
Die Versionierung ist jetzt zusätzlich gegen Drift abgesichert. Beide vorherigen Fachaufträge bleiben vollständig umgesetzt und automatisch abgesichert. Vorlagen
reduzieren wiederholte Eingaben, ohne sensible oder unnötige Pfade zu speichern.
Trendgrenzen erhöhen die Sichtbarkeit auffälligen Wachstums, bleiben aber strikt
rein lesend und frei von automatischen Entscheidungen. Offen bleibt bewusst nur die
menschliche Laienabnahme.

## Ergebnis der Wartungsiteration 0.13.0-alpha.2

- Fehlerfreiheit: Der doppelte alte CLI-Kopf wurde entfernt; `from __future__ import annotations` steht wieder am Dateianfang.
- Robustheit: Negative Parser-Tests sichern ungültige Ganzzahlen, nicht endliche Prozentwerte und unbekannte Berichtsformate ab.
- Wartbarkeit: Startseiten-Kataloge, Eingabeparser und orchestrierende Klasse bleiben klar getrennt.
- Konsistenz: Registry und Info-Dateien verweisen auf denselben aktuellen Entwicklungsstand.
