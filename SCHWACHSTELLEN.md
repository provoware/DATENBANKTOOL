# Schwachstellen und aktuelle Grenzen

## Aktuell bekannte Grenzen

1. Der Re-Scan muss den Verzeichnisbaum weiterhin vollständig durchlaufen; er spart hauptsächlich Datenbank- und Hasharbeit.
2. Verschiebungen werden nur eindeutig klassifiziert. Mehrdeutige Hardlinks oder identische Mehrfachkopien bleiben getrennte Neu-/Entfernt-Fälle.
3. Hash-basierte Verschiebungserkennung funktioniert nur, wenn die Baseline bereits einen SHA-256-Wert besitzt.
4. Ein Inhalt kann theoretisch bei gleicher Größe, identischer Zeit und identischer Inode unbemerkt bleiben, wenn ein externes Werkzeug Metadaten gezielt zurücksetzt.
5. Der `fcntl.flock`-Lock ist Linux-spezifisch und schützt nur Prozesse, die denselben Lockvertrag respektieren.
6. Externe SQLite-Werkzeuge können die Datenbank weiterhin außerhalb des Tool-Locks verändern.
7. Restore ersetzt die aktive Datenbank atomar für neue Öffnungen; bereits fremd geöffnete Leser können kurzfristig den alten Dateiknoten sehen.
8. Sitzungen werden noch nicht automatisch archiviert oder bereinigt.
9. Fortschrittsereignisse haben beim Verzeichnisscan keine verlässliche Gesamtsumme.
10. FTS5-Suche, Ordneraggregate und GUI fehlen noch.
11. Schreibende Originaldateioperationen bleiben vollständig gesperrt.
12. Ruff, MyPy, Bandit, pip-audit und Coverage sind noch kein verpflichtendes Gate.

## Sicherheitsbewertung

- Originaldateien werden weiterhin nur gelesen.
- Keine Datei wird automatisch gelöscht, verschoben oder umbenannt.
- Backup und Restore prüfen SQLite vor der Übernahme.
- Vor Restore wird standardmäßig eine Sicherheitskopie des Zielindexes erstellt.
- Vorhandene Sicherungen und Berichte werden nicht still überschrieben.
- Re-Scan-Sitzungen verändern frühere Snapshots nicht.

## Kritisch vor schreibenden Dateioperationen

1. Transaktionsjournal.
2. Vorher-Nachher-Planmanifest.
3. Kollisions- und Rechteprüfung.
4. Speicherplatzprüfung.
5. Quarantäne statt Direktlöschung.
6. Idempotente Wiederaufnahme.
7. Automatisierte Undo- und Recoverytests.
