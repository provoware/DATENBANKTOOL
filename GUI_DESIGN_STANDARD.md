# GUI-Designstandard — Neon-Workspace

## Ziel

Das Einzelkonzept **„Duplikate, Umbenennen & Listen — Workspace“** ist ab dieser Iteration das verbindliche Layout- und Erscheinungsbildmuster für die grafische Oberfläche des DATENBANKTOOL.

Die GUI bleibt eine additive Bedienebene über dem bestehenden sicherheitsorientierten Kern. Originaldatei-Sperre, CLI-Verträge, Recovery, Restore-Prüfung und Crash-Journal werden nicht aufgeweicht.

## Verbindlicher Aufbau

1. **Linke Navigation**
   - Analyse & Inventur
   - Schnellmodi & Presets
   - Duplikate & Umbenennen
   - Listen & Ergebnisse
   - Testsystem & Prüfläufe
   - Transparenz & Monitor
   - Einstellungen
   - Protokolle

2. **Projektkopf oben mittig**
   - aktuelles Projekt
   - Quellen/Laufwerke
   - letzter Scan
   - Datei-/Ordnerzahlen
   - sichtbarer Sicherheitsmodus

3. **Übersichts- und Arbeitszone**
   - KPI-Karten
   - Speicherbelegung
   - Aufräumpotenzial
   - Workload
   - Sicherheitsstatus

4. **Detailbereich direkt darunter**
   - workflowabhängige Tabs
   - Filter und Suche
   - große Listen-/Tabellenfläche
   - Vorschau vor jeder Änderung
   - Vorher-/Nachher-Darstellung

5. **Rechte Assistenzspalte**
   - Was passiert gerade?
   - Warum passiert es?
   - Sicherheitsstatus
   - Nächste Schritte
   - Schnellaktionen
   - verständliche Warnungen und Lösungsvorschläge

6. **Permanente Statusleiste unten**
   - Speicherübersicht
   - CPU/RAM/I/O
   - Fortschritt
   - Restzeit
   - Undo/Papierkorb/Protokoll
   - Aktivitätsjournal

## Farb- und Interaktionssprache

Referenztheme:

- Hintergrund: `#050b0e`
- Panel: `#071419`
- alternatives Panel: `#0a1b20`
- Neon-Türkis: `#00f0b5`
- Türkis dunkel: `#0bb98e`
- Primäre sichere Aktion / Grün: `#19d66b`
- Warnung / Gold-Orange: `#ffb000`
- Gefahr / Rot: `#ff4d4d`

Regeln:

- Grün bedeutet sichere, explizite Aktion oder bestätigten Zustand.
- Orange/Gold bedeutet Prüfung, Hinweis oder ausstehende Entscheidung.
- Rot bedeutet Fehler, Konflikt oder potenziell destruktive Aktion.
- Kritische Bedeutung darf nie ausschließlich über Farbe vermittelt werden.
- Originaldatenänderungen erhalten niemals eine unauffällige Ein-Klick-Aktion.

## Sicherheits-UX

Jeder schreibende Workflow folgt sichtbar:

`Analyse -> Vorschlag -> Vorschau -> Testlauf -> Freigabe -> Ausführung -> Bericht`

Verbindlich sichtbar:

- Nur lesender Zugriff
- Testlauf zuerst
- Papierkorb
- Undo & Rollback
- Protokollierung
- eindeutiger Hinweis, ob Originaldaten betroffen sind

## Profi-Umbauplan

1. Designvertrag und zentrale Tokens festlegen.
2. Additive Desktop-Hülle ohne Eingriff in den CLI-Kern schaffen.
3. Navigation und Projektkontext implementieren.
4. KPI-, Speicher-, Last- und Sicherheitsmodule anbinden.
5. Detail-/Listenworkspace als primäre Arbeitsfläche etablieren.
6. Duplikat- und Umbenennungsworkflow zuerst vollständig anbinden.
7. Schnellmodi und editierbare Presets ergänzen.
8. Testordner, Sandbox und automatische Prüfläufe integrieren.
9. Assistenz-/Feedbackschicht mit Was/Warum/Nächster-Schritt vereinheitlichen.
10. Audit-Trail, Dauer, Restzeit und Berichte in jeder Aktion sichtbar machen.
11. Tastaturbedienung, Kontrast, Skalierung und Screenreader-Texte härten.
12. Reale Kubuntu-Abnahme durchführen und erst danach Standardstart auf GUI umstellen.

## Aktueller Implementierungsstand dieser Iteration

- zentraler GUI-Vertrag: `src/datenbanktool/gui_model.py`
- additive native GUI-Hülle: `src/datenbanktool/gui_app.py`
- Start ausschließlich explizit über `datenbanktool gui`
- bestehendes `datenbanktool start` bleibt unverändert Terminal-first
- GUI-Toolkit wird erst bei `gui` lazy importiert
- Design- und Sicherheitsvertrag besitzt automatisierte Tests

## Nächster technischer Schritt

Die statischen Beispielwerte im Workspace durch eine **rein lesende ViewModel-/Adapter-Schicht** ersetzen, die vorhandene Index-, Such-, Duplikat- und Statistikdaten aus dem bestehenden Kern bezieht, ohne UI-Code direkt mit Datenbank- oder Dateisystemoperationen zu koppeln.

## Alternative Verbesserung mit hohem Nutzen und geringem Risiko

Vor der Datenanbindung einen kleinen **GUI-Screenshot-/Layout-Gate** ergänzen, der Mindestgrößen, sichtbare Pflichtzonen, Kontrast-Tokens und das Vorhandensein der Sicherheitsanzeigen prüft. Dadurch wird verhindert, dass spätere Funktionsarbeit das bestätigte Layoutmuster schleichend zerstört.
