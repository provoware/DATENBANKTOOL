# Schwachstellen

## Aktuell begrenzt

- Versionen haben zwei zulässige Schreibweisen; automatisierte Drift-Prüfung verhindert Abweichungen zwischen Registry, CLI und Dokumentation.
- Nur lokale SQLite-Dateien werden unterstützt; Serverdatenbanken fehlen bewusst.
- Die Dateisignaturprüfung erkennt SQLite-Dateien, aber keine logischen Schäden jeder Datenbankseite.
- Die Struktur wird vollständig eingelesen; extrem viele Tabellen sind noch nicht mit Messwerten abgesichert.
- Status- und Upgrade-Angaben müssen bei künftigen Änderungen weiterhin zwischen
  README, TODO, Upgrade-Pool und Projektregistry synchron gehalten werden.

## Bereits abgesichert

- Die Datenbank wird im schreibgeschützten Modus geöffnet.
- Leere, fehlende, nicht reguläre und offensichtlich ungültige Dateien werden abgewiesen.
- Tabellenbezeichner werden als Parameter an SQLite übergeben und nicht in SQL-Text eingesetzt.

Sicherheitsrelevante Fehler sollen ohne sensible Dateiinhalte, Zugangsdaten oder Stapelspuren ausgegeben werden.
# Schwachstellen und aktuelle Grenzen

## Zeitreihen-Vorlagen

1. Vorlagen speichern bewusst nur relative Ordnerpfade, Namen und Beschreibungen. Ein
   Datenbankpfad wird nicht gespeichert und muss pro Lauf gewählt werden.
2. Warnschwellen, Scan-Grenzen und Berichtspfade sind nicht Bestandteil einer Vorlage.
   Dadurch bleibt die Vorlage sicher und leicht verständlich, erfordert aber weitere
   Eingaben pro Lauf.
3. Die Startseite kann Vorlagen speichern und auswählen. Anzeigen, Ersetzen und Löschen
   sind derzeit über direkte CLI-Befehle verfügbar, noch nicht als geführtes Untermenü.
4. Ein beschädigtes Vorlagen-JSON wird kontrolliert abgelehnt. Die Startseite erlaubt
   weiterhin eine manuelle Ordnerangabe, repariert die Datei aber nicht automatisch.
5. Modus `0600` schützt die Datei unter normalen Linux-Berechtigungen. Eine Sicherung
   oder Synchronisierung durch externe Programme liegt außerhalb des Tools.
6. Namen werden ohne Beachtung der Groß-/Kleinschreibung als identisch behandelt.
7. Löschen benötigt `--yes`; es gibt derzeit kein eigenes Undo-Journal für
   Konfigurationsvorlagen.

## Trendgrenzen

8. Eine Warnschwelle vergleicht nur zwei unmittelbar aufeinanderfolgende sichtbare
   Scans. Sie ist keine statistische Langzeitanalyse.
9. Werden ältere Scans durch `--limit` ausgeblendet, bezieht sich der erste sichtbare
   Punkt auf keinen davorliegenden ausgeblendeten Punkt und bleibt Ausgangswert.
10. Bei einem vorherigen Wert von null ist keine normale Prozentänderung berechenbar.
    Der Prozentwert bleibt leer und löst keine Prozentwarnung aus.
11. Eine Schwelle von `0` markiert jedes positive Wachstum. Das ist gültig, kann aber
    viele Warnungen erzeugen.
12. Sehr hohe Schwellen bis 1.000.000 Prozent sind zulässig, um kleine Ausgangsbestände
    kontrolliert abbilden zu können.
13. ROT bedeutet ausschließlich „konfigurierte Trendgrenze erreicht“. Es ist keine
    Aussage über Beschädigung, Gefahr oder erforderliches Löschen.
14. Größen- und Dateizahlgrenze können gleichzeitig auslösen; beide Begründungen werden
    gemeinsam ausgegeben.
15. Die normale Verlaufsklassifikation bleibt getrennt. Ein gewachsener Ordner kann
    deshalb fachlich `Gewachsen` sein, während der Warnstatus `Trendgrenze erreicht`
    lautet.

## Geführte Bedienung und Berichte

16. Die Startseite besitzt keine grafische Dateiauswahl.
17. Pro geführtem Lauf kann ein Exportformat gewählt werden; mehrere Formate sind über
    den direkten CLI-Befehl möglich.
18. Vorhandene Berichte werden nicht still überschrieben.
19. SVG-Punkte werden nach Scan-Reihenfolge, nicht proportional zum realen Zeitabstand
    positioniert.
20. Bei 500 Punkten entstehen viele fokussierbare SVG-Elemente. Die vollständige Tabelle
    bleibt die kompaktere Alternative.
21. Je Bericht wird weiterhin ein relativer Ordner dargestellt.
22. Elternordner enthalten rekursive Unterordnerwerte; Eltern- und Kindzeitreihen dürfen
    nicht ungeprüft addiert werden.
23. Leere Ordner ohne Dateien erscheinen nicht im aktuellen Dateisnapshot-Schema.

## Großbestands- und Laienabnahme

24. Das `large`-Profil mit 100.000 Dateien wurde noch nicht auf Zielhardware ausgeführt.
25. Eine echte Laienabnahme wurde noch nicht durchgeführt. Automatisierte Tests ersetzen
    keine Beobachtung einer unerfahrenen Person.
26. Sparse-Testdateien bilden Metadatenleistung besser ab als reale vollständig gefüllte
    Mediendateien.
27. GitHub-Actions-Artefakte laufen nach der Aufbewahrungsdauer ab.

## 0.13-Funktionsreferenz

- 87/87 Tests unter Python 3.10 und Python 3.12.
- Quick: 600 Dateien, 11/11 Kriterien, 1,129 Sekunden.
- Standard: 10.000 Dateien, 11/11 Kriterien, 18,150 Sekunden.
- Diese CI-Werte sind Referenzen und keine Zusage für andere Hardware.

## Sicherheitsfazit

Vorlagen schreiben ausschließlich eine lokale, atomar freigegebene Konfigurationsdatei.
Zeitreihe und Warnschwellen bleiben rein lesend. Warnungen lösen weder Schreibzugriffe
noch automatische Folgeaktionen aus. Originaldateioperationen bleiben gesperrt. Die
bekannten Grenzen rechtfertigen keine Lockerung dieses Sicherheitsvertrags.
