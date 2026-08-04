# Schwachstellen und aktuelle Grenzen

## Ordnervergleich

1. Der Vergleich wertet genau zwei gespeicherte Scan-Sitzungen aus. Eine längere
   Zeitreihe oder Trendgrafik ist noch nicht vorhanden.
2. Beide Sitzungen müssen abgeschlossen sein und denselben gespeicherten Stammordner
   besitzen. Unterschiedliche Ordnerbestände werden bewusst nicht vermischt.
3. Der Vergleich liest nicht automatisch den heutigen Dateisystemstand. Änderungen
   nach dem neueren Scan erscheinen erst nach einem weiteren Re-Scan.
4. Leere Ordner ohne Dateien können nicht dargestellt werden, weil der Index
   Dateieinträge und keine eigenständige Verzeichnisliste speichert.
5. Elternordner enthalten die Summen aller Unterordner. Vergleichszeilen dürfen daher
   nicht addiert werden, sonst werden Dateien mehrfach gezählt.
6. Unveränderte Ordner sind standardmäßig ausgeblendet und müssen mit
   `--type unchanged` ausdrücklich angefordert werden.
7. Ein Ordner mit unveränderter Gesamtgröße, aber geänderter Dateizahl erhält den
   Zustand „Dateizahl geändert“. Welche Einzeldateien betroffen sind, zeigt weiterhin
   der getrennte Dateiänderungsbericht.
8. Prozentwerte sind bei neu entstandenen Ordnern nicht mathematisch sinnvoll; dort
   wird „kein Ausgangswert“ angezeigt.
9. Die rote Wachstumsampel basiert auf einer konfigurierbaren absoluten Schwelle.
   Sie ist keine Aussage über Schaden, Gefahr oder unnötige Dateien.
10. JSON-, CSV- und HTML-Exporte enthalten die aktuell ausgewählte, gefilterte Seite
    und noch nicht automatisch sämtliche Treffer.

## Terminalbedienung und Hilfe

11. Die Oberfläche besitzt noch keine grafischen Dateiauswahlfenster.
12. Pfade werden weiterhin eingegeben oder eingefügt.
13. Die automatische Sitzungswahl wird im Ausgabekopf transparent angezeigt, aber
    noch nicht als interaktiver Auswahldialog angeboten.
14. Hilfetexte sind derzeit deutschsprachig.
15. Die Stichwortsuche der Hilfe ist deterministisch und nicht semantisch.

## Fachliche und technische Grenzen

16. Die normale Ordnerübersicht besitzt JSON und HTML, aber noch keinen CSV-Export.
17. FTS5 durchsucht Metadaten, nicht automatisch den Inhalt aller Dateien.
18. Schreibende Originaldateioperationen bleiben gesperrt.
19. Vor einem stabilen Release fehlen Last-, Speicher- und Bedienabnahmen mit sehr
    großen realen Beständen und Linux-Laien.
20. Die SQLite-Auswertung aggregiert die Dateizeilen beider Sitzungen im Arbeitsspeicher.
    Für extrem große Bestände müssen Laufzeit und Speicherverbrauch noch praktisch
    vermessen werden.

## Sicherheitsfazit

Der Ordnervergleich öffnet SQLite rein lesend, verlangt gleiche Stammordner und führt
keine automatische Dateisystemaktion aus. Berichte werden atomar geschrieben und nur
nach ausdrücklicher Freigabe überschrieben. Keine bekannte Grenze rechtfertigt das
Freischalten automatischer Lösch-, Verschiebe- oder Umbenennungsfunktionen.
