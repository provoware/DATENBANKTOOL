# Schwachstellen

Stand: Version 0.14.0-alpha.1

## Aktualisierte Bewertung dieser Iteration

- Die Paketregistry war durch einen doppelten Versionsschlüssel und ein fehlendes Komma ungültig. Das ist behoben; `registry.json` ist wieder gültiges JSON.
- Paketversion, Anzeigeversion, Projektregistry, Paketmetadaten und Drift-Test verwenden jetzt denselben Stand: `0.14.0-alpha.1` / `0.14.0a1`.
- Mehrfach vorhandene und widersprüchliche Statusblöcke in den Pflichtdokumenten wurden konsolidiert.

## Aktuelle fachliche Grenzen

1. Eine echte Laienabnahme wurde noch nicht durchgeführt. Automatisierte Tests ersetzen keine Beobachtung einer unerfahrenen Person.
2. Nur lokale SQLite-Dateien werden unterstützt; Serverdatenbanken fehlen bewusst.
3. Die Dateisignaturprüfung erkennt SQLite-Dateien, aber keine logischen Schäden jeder Datenbankseite.
4. Zeitreihen-Vorlagen speichern bewusst keine Datenbankpfade, Warnschwellen oder Scan-Ergebnisse. Das ist sicher, erfordert aber Eingaben pro Lauf.
5. Eine Warnschwelle vergleicht nur zwei unmittelbar aufeinanderfolgende sichtbare Scans und ist keine statistische Langzeitanalyse.
6. ROT bedeutet ausschließlich „konfigurierte Trendgrenze erreicht“. Es ist keine Aussage über Beschädigung, Gefahr oder erforderliches Löschen.
7. Je Bericht wird weiterhin ein relativer Ordner dargestellt; Mehrordner-Zeitreihen sind noch offen.
8. Elternordner enthalten rekursive Unterordnerwerte; Eltern- und Kindzeitreihen dürfen nicht ungeprüft addiert werden.
9. GitHub-Actions-Artefakte laufen nach der Aufbewahrungsdauer ab.

## Sicherheitsfazit

Originaldateien werden durch Index-, Berichts- und Startseitenfunktionen nicht automatisch verändert. Vorlagen schreiben ausschließlich eine lokale, atomar freigegebene Konfigurationsdatei. Zeitreihe und Warnschwellen bleiben rein lesend. Bekannte Grenzen rechtfertigen keine Lockerung dieses Sicherheitsvertrags.
