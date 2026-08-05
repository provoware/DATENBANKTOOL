# Analyse-Punkte

Stand: Version `0.15.0-alpha.1`

## Gesamtergebnis der Codeanalyse

| Bereich | Befund | Professionelle Korrektur |
|---|---|---|
| Prozessabsturz | Unerwartete Ausnahmen besaßen keine einheitliche äußere Fehlergrenze | Laufjournal, Crashbericht, Code `70`, verständliche Wiederanlaufhilfe |
| Tastaturabbruch | `KeyboardInterrupt` konnte als allgemeiner Fehler behandelt werden | eigener Unterbrechungsstatus, Code `130`, bestätigter Checkpoint bleibt erhalten |
| Autosave | nur mengenabhängige Batches; bei langsamen Dateien zu große Zeitspanne möglich | Zeit- **oder** Mengengrenze: fünf Sekunden oder 500 Einträge, was zuerst eintritt |
| SQLite-Dauerhaftigkeit | `synchronous=NORMAL` war schwächer als der Sicherheitsanspruch | `WAL`, `synchronous=FULL`, bestätigte Transaktionen, passive Checkpoints |
| WAL-Inkonsistenz | optionaler Checkpoint konnte bei offener Leseschleife den sicheren Scan abbrechen | `busy`/`locked` verschiebt nur Wartung; Commit bleibt erfolgreich |
| Dateischreiben | mehrere eigene Temp-Datei-Varianten ohne einheitliches `fsync` | gemeinsame Schicht mit Datei-`fsync`, `os.replace`, Ordner-`fsync` und Restbereinigung |
| Sicherung | geprüfte SQLite-Kopie wurde ohne gemeinsame Veröffentlichungsgrenze umbenannt | Validierung vor dauerhafter Veröffentlichung; kein stilles Überschreiben |
| Wiederherstellung | Austausch der aktiven Indexdatei war atomar, aber nicht vollständig gepuffert | gleiche dauerhafte Veröffentlichung plus Rückfallsicherung |
| Konfiguration | Such- und Zeitreihenvorlagen verwendeten getrennte Schreiblogik | gemeinsame private `0600`-Schreibgrenze |
| Berichte | JSON- und wichtige Ordnerexporte verwendeten unterschiedliche atomare Helfer | an gemeinsame dauerhafte Schreibschicht angebunden |
| Diagnose | keine einfache Vorprüfung für Schreibbarkeit, Laufstatus und SQLite-Integrität | neuer Befehl `datenbanktool check` mit optionalem Nur-Lese-Indexcheck |
| Geheimnisse | Befehlsargumente konnten ungefiltert in einem Crashbericht landen | typische Token-, Passwort-, Secret- und API-Key-Werte werden ausgeblendet |
| Python-Vertrag | Versionstest importierte `tomllib` und brach unter Python 3.10 | kompatible versionsspezifische Prüfung ohne neue Abhängigkeit |
| Nutzeransprache | Fachsprache und interne Fehlerklasse standen teilweise zuerst | Reihenfolge: Alltagssprache → Auswirkung → nächster Schritt → Fachdetail |
| Architektur | neuer Diagnosebefehl war zunächst nicht Teil der vollständigen Eigentümerprüfung | Parser-, Policy- und Modulgrenzentest ergänzt |

## Ausfall- und Regressionstests

Automatisch geprüft werden:

1. vorhandene Zieldatei bleibt ohne Überschreibfreigabe unverändert,
2. simulierter `os.replace`-Fehler erhält die Altdatei und entfernt den Temp-Rest,
3. private Statusdateien besitzen Modus `0600`,
4. Crashberichte enthalten Rückgabecode und Traceback, aber keine geprüften Geheimniswerte,
5. Tastaturabbruch erzeugt Unterbrechungsstatus,
6. unterbrochener Scan wird mit `--resume` vollständig fortgesetzt,
7. SQLite meldet `synchronous=FULL`,
8. Indexdiagnose verändert die Indexdatei nicht,
9. einfache Erklärung erscheint vor `fsync`- und SQLite-Fachdetails,
10. sämtliche öffentlichen Befehle besitzen Handler und Seiteneffektvertrag.

## Bewusst begrenzte Garantie

Die Software kann ihren eigenen Schreib- und Wiederanlaufvertrag prüfen. Sie kann keine defekte Hardware, falsche Controllercache-Zusagen, volles Laufwerk, Dateisystem-/Kerneldefekte oder physischen Verlust verhindern. Deshalb bleiben Sicherungen und reale Zielsystemtests notwendig.

## Wartbarkeitsentscheidung

- Keine pauschale Neuformatierung.
- Keine Freigabe von Originaldateioperationen.
- Keine neue Laufzeitabhängigkeit.
- Neue Sicherheitslogik liegt in kleinen Fachmodulen statt in weiteren Kopien.
- Technische Details bleiben verfügbar, dominieren aber nicht die Nutzerführung.

## Nächste Analysepunkte

1. Gleichzeitige unabhängige Nur-Lese-Befehle im globalen Laufjournal sauber als getrennte Läufe darstellen.
2. Geführten Wiederanlauf auf der Startseite testen.
3. Reale Laienabnahme mit Beobachtung und Rückfragen durchführen.
4. Datenträger-voll- und Neustarttests mit ausschließlich synthetischen Daten dokumentieren.
