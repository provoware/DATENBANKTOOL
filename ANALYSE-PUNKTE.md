# Analyse-Punkte

## Muss-Funktionen

1. Sehr große Verzeichnisbäume speicherschonend und abbrechbar inventarisieren.
2. Dateien nach Typ, Endung, MIME-Typ und später echtem Medieninhalt klassifizieren.
3. Namen, Pfade, Größen, Zeiten, Rechte, Eigentümer, Links und Dateisystemgrenzen erfassen.
4. Schnelle Suche über Namen, Pfade, Metadaten und optional Textinhalte ermöglichen.
5. Große Dateien und große Ordner sichtbar machen.
6. Leere, unzugängliche, tief verschachtelte und ungewöhnlich benannte Pfade erkennen.
7. Exakte Duplikate sicher über Größen-Vorfilter und kryptografische Hashes bestimmen.
8. Ähnliche Bilder, Audios, Videos und Texte getrennt von exakten Duplikaten behandeln.
9. Archive ohne unkontrolliertes Entpacken inventarisieren und prüfen.
10. Codeprojekte, Repositories, Abhängigkeiten, Buildreste und mehrfach kopierte Projekte erkennen.
11. Linux-zulässige und plattformübergreifend problematische Dateinamen unterscheiden.
12. Umbenennungsregeln mit echter Vorher-Nachher-Vorschau anbieten.
13. Zielkonflikte, Namenskollisionen und Groß-/Kleinschreibung vor Änderungen prüfen.
14. Sortierregeln transparent und als überprüfbaren Plan darstellen.
15. Kopieren, Verschieben und Umbenennen nur transaktional ausführen.
16. Löschen ausschließlich über Papierkorb oder Quarantäne anbieten.
17. Jede Änderung mit Undo-Manifest dokumentieren.
18. Abbruch und Absturz ohne halbfertige unbekannte Zustände überstehen.
19. Arbeit pausieren, fortsetzen und nach Neustart wieder aufnehmen.
20. Berichte in JSON, CSV und HTML exportieren; PDF später ergänzen.

## Medienfokus

21. Bilder als Kacheln und große Vorschau anzeigen.
22. Audio vorhören, Wellenform und technische Metadaten anzeigen.
23. Video mit Vorschaubild, Dauer, Auflösung, Codec und Fehlerstatus anzeigen.
24. Textdateien mit Kodierungserkennung und sicherer Vorschau darstellen.
25. PDFs und Dokumente nur über abgesicherte Vorschaukomponenten öffnen.
26. Beschädigte oder unvollständige Medien erkennen.
27. Falsch benannte Dateiendungen erkennen.
28. Metadaten wie Künstler, Album, Titel, Datum, Kamera und Auflösung nutzbar machen.
29. Playlists, Begleitdateien, Untertitel und Projektbeziehungen berücksichtigen.
30. Mediengruppen nicht allein anhand des Dateinamens bilden.

## Laienfreundlichkeit

31. Start mit einem klaren Hauptweg: Ordner wählen und prüfen.
32. Einfach-, Geführt- und Expertenmodus trennen.
33. Standardmäßig niemals verändern oder löschen.
34. Technische Funde in Alltagssprache erklären.
35. Ursache, Wirkung, Risiko und nächste sichere Aktion gemeinsam anzeigen.
36. Kritische Aktionen nicht hinter unklaren Symbolen verstecken.
37. Beispiele aus den echten Dateien des Nutzers in Regelvorschauen zeigen.
38. Fortschritt, verbleibende Arbeit und aktuelle Aktivität sichtbar machen.
39. Pause und Abbruch jederzeit ermöglichen.
40. Fehler einzelner Dateien sammeln, ohne den gesamten Auftrag zu verlieren.
41. Keine vorausgewählten Löschkandidaten verwenden.
42. Original und Kopie bei Duplikaten nicht automatisch behaupten.
43. Mehrdeutige Fälle als Entscheidungsliste statt automatische Aktion behandeln.
44. Vor jeder Ausführung eine verständliche Gesamtwirkung anzeigen.
45. Nach jeder Ausführung Ergebnis, Fehler und Wiederherstellungsweg anzeigen.
46. Große Schriften, klare Kontraste, Tastaturführung und Touchziele berücksichtigen.
47. Hilfetexte direkt am Problem statt nur in einem Handbuch anbieten.
48. Sichere Voreinstellungen und rücksetzbare Profile verwenden.

## Robustheit und Datenschutz

49. Vollständig lokal und offline funktionieren.
50. Keine Telemetrie ohne ausdrückliche Zustimmung.
51. Symbolischen Links standardmäßig nicht folgen.
52. Dateisystemschleifen, Mountwechsel und Bind-Mounts erkennen.
53. Externe Datenträger, NTFS, exFAT und schreibgeschützte Medien berücksichtigen.
54. Rechtefehler, verschwindende Dateien und parallele Änderungen tolerieren.
55. Millionen Einträge nicht vollständig im Arbeitsspeicher halten.
56. Hashing nach Größe gruppieren und ressourcenschonend drosseln.
57. Berichte atomar schreiben und nicht still überschreiben.
58. Datenbank und Journal versionieren, prüfen und reparieren können.
59. Dateiinhalte niemals für Logs vervielfältigen.
60. Geheimnisse, Zugangsdaten und sensible Textdateien in Vorschauen besonders behandeln.
61. Erweiterungen klar vom Sicherheitskern trennen.
62. Qualitätsgates, reproduzierbare Tests und reale Dateisystemtests einführen.

## Architektur-Fazit

Das Tool darf nicht als normaler Dateimanager beginnen. Die belastbare Reihenfolge lautet:

1. Inventarisieren.
2. Analysieren.
3. Verständlich gruppieren.
4. Änderungsplan erzeugen.
5. Plan vollständig validieren.
6. Transaktion mit Journal ausführen.
7. Ergebnis prüfen.
8. Undo und Wiederherstellung bereitstellen.

Der aktuelle Stand implementiert ausschließlich die ersten beiden Stufen als sicheren Basiskern.
