# Schwachstellen

## Aktuell begrenzt

- Nur lokale SQLite-Dateien werden unterstützt; Serverdatenbanken fehlen bewusst.
- Die Dateisignaturprüfung erkennt SQLite-Dateien, aber keine logischen Schäden jeder Datenbankseite.
- Die Struktur wird vollständig eingelesen; extrem viele Tabellen sind noch nicht mit Messwerten abgesichert.

## Bereits abgesichert

- Die Datenbank wird im schreibgeschützten Modus geöffnet.
- Leere, fehlende, nicht reguläre und offensichtlich ungültige Dateien werden abgewiesen.
- Tabellenbezeichner werden als Parameter an SQLite übergeben und nicht in SQL-Text eingesetzt.

Sicherheitsrelevante Fehler sollen ohne sensible Dateiinhalte, Zugangsdaten oder Stapelspuren ausgegeben werden.
