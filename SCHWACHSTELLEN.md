# Schwachstellen und Grenzen

Stand: Version `0.15.0-alpha.1`

## Behobene Schwachstellen

1. Unerwartete Ausnahmen verließen den Prozess ohne einheitlichen Crashbericht. Jetzt existiert eine zentrale Fehlergrenze mit Rückgabecode `70`.
2. Tastaturabbruch konnte als allgemeiner Fehler erscheinen. Er wird jetzt als fortsetzbare Unterbrechung mit Code `130` gespeichert.
3. Scan-Autosave war nur an eine Dateimenge gebunden. Jetzt gilt zusätzlich eine Zeitgrenze von standardmäßig fünf Sekunden.
4. SQLite verwendete `synchronous=NORMAL`. Schreibende Indexverbindungen nutzen jetzt `FULL`.
5. Mehrere „atomare“ Schreibhelfer veröffentlichten Dateien ohne Datei- und Ordner-`fsync`. Eine gemeinsame gehärtete Schreibschicht ersetzt diese Varianten schrittweise in den sicherheitsrelevanten Pfaden.
6. Ein passiver WAL-Checkpoint konnte trotz bereits bestätigtem Commit einen laufenden Scan abbrechen. `locked` und `busy` gelten nun korrekt als aufgeschobene Wartung, nicht als verlorener Commit.
7. Der Versionstest setzte irrtümlich Python 3.11 voraus. Er funktioniert wieder unter der zugesagten Mindestversion Python 3.10.
8. Technische Fehlermeldungen standen teilweise vor der eigentlichen Hilfe. Neue zentrale Einstiege nennen Alltagssprache, Auswirkung und nächsten Schritt zuerst.

## Verbleibende Grenzen

1. **Keine absolute Hardwaregarantie:** Defekter Datenträger, fehlerhafter Controllercache, volles Dateisystem, Kernel-/Dateisystemschaden, physischer Verlust oder defekter Arbeitsspeicher können nicht durch Anwendungscode ausgeschlossen werden.
2. **Einzeldatei-Grenze:** Während der Prüfsummenberechnung einer sehr großen Datei kann nicht mitten in dieser Datei fortgesetzt werden. Nach einem Absturz wird höchstens dieser Einzelhash erneut berechnet.
3. **Globales Laufjournal:** `last-run.json` beschreibt den zuletzt gestarteten Prozess. Gleichzeitige unabhängige Befehle können diesen Hinweis gegenseitig ersetzen. Eindeutige Crashberichte bleiben erhalten; schreibende Indexbefehle sind zusätzlich pro Indexdatei gesperrt.
4. **Laufjournal optional:** Ist der Statusordner nicht beschreibbar, darf das Journal den eigentlichen Nur-Lese-Befehl nicht blockieren. `datenbanktool check` meldet diesen Zustand rot.
5. **Passive WAL-Aufräumphase:** Ein blockierter passiver Checkpoint kann verschoben werden. Der bestätigte WAL-Commit bleibt gültig; die WAL-Datei kann bis zum nächsten erfolgreichen Checkpoint größer bleiben.
6. **Reale Laienabnahme offen:** Automatisierte Sprachtests ersetzen keine Beobachtung einer unerfahrenen Person.
7. **Startklar-Prüfung verändert keine Originaldateien**, erzeugt jedoch absichtlich kurzlebige Testdateien in den eigenen Konfigurations- und Statusordnern.
8. **Sicherungen bleiben erforderlich:** Autosave und atomare Veröffentlichung schützen vor Teilwrites, nicht vor Verlust des gesamten Datenträgers.
9. Mehrordner-Zeitreihen und eine grafische Oberfläche sind weiterhin offen.

## Praktische Sicherheitsfolge

Vor wichtigen Arbeiten:

```bash
datenbanktool check --database index.sqlite3
datenbanktool index backup index.sqlite3
```

Nach Unterbrechung:

```bash
datenbanktool index status index.sqlite3
datenbanktool index build ORDNER --database index.sqlite3 --resume
```

## Fazit

Die Anwendung kann den eigenen Softwarezustand jetzt deterministisch und überprüfbar wiederherstellen. Sie behauptet bewusst keine absolute Lauffähigkeit unabhängig von Hardware und Betriebssystem. Originaldatei-Schreibzugriffe bleiben gesperrt.
