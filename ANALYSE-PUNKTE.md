# Analyse-Punkte

## Ergebnis dieser Iteration

DATENBANKTOOL kann die normale Ordnerübersicht jetzt vollständig als
LibreOffice-kompatible CSV speichern. Zusätzlich existiert eine reproduzierbare
Abnahmepipeline mit synthetischen Beständen, festen Laufzeit- und Speichergrenzen,
Quelldatenprüfung, maschinenlesbaren Berichten und einer klar getrennten realen
Laien-Checkliste.

## Vollständig gelöste CSV-Punkte

1. `index folders` akzeptiert `--csv PFAD`.
2. UTF-8-BOM erleichtert die korrekte Erkennung deutscher Sonderzeichen.
3. Semikolon ist für typische deutsche LibreOffice-Einstellungen geeignet.
4. Ampelstufe, Status und Begründung stehen getrennt bereit.
5. Direkte und rekursive Dateizahlen werden nicht vermischt.
6. Direkte und rekursive Bytegrößen sind maschinell berechenbar.
7. Namenshinweise und Duplikatzahlen besitzen eigene Spalten.
8. Platzfresser werden als stabile Pfad-/Byte-Paare ausgegeben.
9. CSV wird atomar geschrieben.
10. Vorhandene Ziele werden nicht still überschrieben.
11. `--all-pages` exportiert alle gefilterten Ordner.
12. Terminalausgabe bleibt paginiert und übersichtlich.
13. Der tatsächliche Exportumfang wird sichtbar genannt.
14. `--all-pages` ohne Bericht wird kontrolliert abgelehnt.
15. JSON und HTML profitieren ebenfalls von der vollständigen Auswertung.
16. Vollständigkeit über mehr als eine Terminalseite wird automatisch geprüft.

## Vollständig gelöste Abnahmepunkte

17. Neuer öffentlicher Befehl `datenbanktool acceptance`.
18. Drei feste Profile mit 600, 10.000 und 100.000 Dateien.
19. Reproduzierbare Dateigrößen über festen Seed.
20. Unterschiedliche Endungen, Leerzeichen, Umlaute und auffällige Namen.
21. Sparse-Dateien begrenzen physischen Speicherbedarf.
22. Arbeitsordner muss neu und nicht vorhanden sein.
23. Vorhandene Ordner und deren Inhalte bleiben unangetastet.
24. Gesamtlaufzeit wird gemessen.
25. Einzelne Phasen werden separat gemessen.
26. Python-Spitzenspeicher wird mit `tracemalloc` gemessen.
27. Prozess-Maximal-RSS wird zusätzlich protokolliert.
28. Quelldaten werden vor und nach dem Lauf manifestiert.
29. Pfad, Größe und `mtime_ns` müssen unverändert bleiben.
30. Indexstatus und importierte Dateizahl werden geprüft.
31. Indexfehler müssen null sein.
32. CSV-Zeilenanzahl muss der vollständigen Ordnerauswertung entsprechen.
33. CSV-BOM wird geprüft.
34. Hilfe muss CSV und `--all-pages` erklären.
35. Laufzeit muss innerhalb der Profilgrenze liegen.
36. Python-Spitzenspeicher muss innerhalb der Profilgrenze liegen.
37. JSON-Bericht wird erzeugt.
38. Markdown-Bericht wird erzeugt.
39. Vollständige Ordner-CSV wird erzeugt.
40. Reale Laien-Checkliste wird erzeugt.
41. Reale Laienprüfung wird nicht fälschlich als abgeschlossen bezeichnet.
42. Quick- und Standardprofile laufen in GitHub Actions.
43. Beide Berichtssets werden als Artefakte archiviert.
44. 66 Tests laufen unter Python 3.10 und 3.12 erfolgreich.
45. Externe Laufzeitabhängigkeiten bleiben bei null.

## Nachgewiesene Referenzwerte

| Profil | Dateien | Kriterien | Laufzeit | Python-Spitzenspeicher |
|---|---:|---:|---:|---:|
| Quick | 600 | 11/11 | 1,086 s | 1.326.097 Byte |
| Standard | 10.000 | 11/11 | 17,781 s | 13.394.783 Byte |

Die Werte stammen aus GitHub Actions auf Ubuntu 24.04 und Python 3.12. Sie sind ein
reproduzierbarer Referenzpunkt, keine Hardwaregarantie.

## Zentrale Architekturentscheidungen

### Vollständige Auswertung und Terminalseite trennen

`analyse_folders(..., all_rows=True)` erzeugt die vollständige gefilterte und sortierte
Ordnerliste genau einmal. `paginate_folder_page()` schneidet daraus nur die sichtbare
Terminalseite. Dadurch ist der Export vollständig, ohne die Aggregation doppelt
auszuführen.

### Vollständigkeit bleibt ausdrücklich

Das frühere Verhalten – Bericht der aktuellen Seite – bleibt kompatibel.
`--all-pages` ist sichtbar und absichtlich. So erkennt der Nutzer vorab, dass mehr
Zeilen verarbeitet und geschrieben werden.

### CSV in eigenem Core-Modul

`core/folder_csv.py` enthält nur CSV-Struktur und atomaren Byte-Schreibvorgang. Die
Ordneranalyse bleibt frei von Formatlogik, und der CLI-Handler bleibt überschaubar.

### Abnahmedaten sind keine Originaldateien

`CommandPolicy` besitzt `writes_test_data`. Dieser Seiteneffekt bedeutet ausschließlich
synthetische Daten in einem neuen Arbeitsordner. Er ist ausdrücklich getrennt von
`writes_original_files`, das weiterhin technisch verboten bleibt.

### Kein automatisches Aufräumen nach Fehlern

Ein fehlgeschlagener Abnahmelauf wird nicht automatisch gelöscht. Der unvollständige
Arbeitsstand kann geprüft werden; eine falsche Pfadannahme führt nicht zu einer
gefährlichen Bereinigung.

### Technische und menschliche Abnahme trennen

Automatische Kriterien prüfen reproduzierbare Fakten. Die Checkliste prüft Orientierung,
Hilfen, Sicherheitsverständnis und Fehlermeldungen mit einer realen Person. Der Status
bleibt `pending-real-person`, bis diese Prüfung wirklich durchgeführt wurde.

### Quick und Standard in CI, Large auf Zielhardware

600 Dateien erkennen schnelle Regressionen. 10.000 Dateien bilden einen realistischen
Bestand. 100.000 Dateien bleiben verfügbar, werden aber nicht bei jedem Commit erzeugt,
um CI-Ressourcen und Laufzeit kontrolliert zu halten.

## Erkannte nächste Analysepunkte

1. Reale Laienabnahme mit der erzeugten Checkliste durchführen.
2. `large`-Profil auf der vorgesehenen Kubuntu-Hardware vermessen.
3. Vergleichsexporte um einen eigenen `--all-pages`-Schalter erweitern.
4. Ordnergrößen über mehr als zwei Scan-Sitzungen als Zeitreihe auswerten.
5. Native Speichergrenze ergänzend zum Python-Spitzenspeicher definieren.
6. Abnahmeberichte mehrerer Versionen rein lesend vergleichen.
7. Fehlgeschlagene Abnahmearbeitsordner mit einem separaten rein lesenden
   Diagnosebefehl erklären.
8. Checklistenergebnisse später kontrolliert in JSON übertragen.

## Fazit

Die beiden technischen Hauptpunkte sind abgeschlossen und automatisch belegt. Die
Ordnerübersicht lässt sich ohne Seitenverlust in Calc öffnen. Die Abnahmepipeline
prüft einen realistischen Bestand mit 10.000 Dateien und schützt die Quelldaten durch
harte Pfad- und Manifestregeln. Offen bleibt bewusst nur der Teil, der tatsächlich eine
reale unerfahrene Person benötigt.
