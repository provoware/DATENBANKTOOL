# DATENBANKTOOL

**Erledigt:** 100.000-Dateien-Large-Abnahme bestanden, geführte Zeitreihen-Vorlagenverwaltung umgesetzt, Registry-Versionierung bereinigt, schreibgeschützte SQLite-Analyse, Tabellenübersicht, validierte Text-/JSON-Ausgabe und automatische Tests.

**Offen:** reale Laienabnahme, Mehrordner-Zeitreihe, Abnahmehistorie, weitere Datenbanktreiber und eine grafische Oberfläche.

**Entwicklungsfortschritt:** **99 %** (Alpha-Funktionsstand stabil; reale Laienabnahme offen).

**Mögliche Upgrades aus `UPGRADE_POOL.md`:** Mehrordner-Zeitreihe, reale Laienabnahme, Abnahmehistorie und später barrierefreie GUI.

> Sicheres Linux-Werkzeug zum Finden, Prüfen und übersichtlichen Strukturieren großer Dateisammlungen.

## Projektstatus

| Bereich | Stand |
|---|---|
| Projektversion | `0.14.0-alpha.1` |
| Paketversion | `0.14.0a1` |
| SQLite-Schema | `3` |
| Entwicklungsfortschritt | **99 %** |
| Erledigte Hauptpunkte | **54** |
| Offene Hauptpunkte | **1** – reale Laienabnahme auf einem Zielsystem durchführen |
| Automatische Originaldateiänderungen | **Gesperrt** |
| Externe Laufzeitabhängigkeiten | **0** |
| Automatisierte Tests | **87/87** unter Python 3.10 und 3.12 |
| Quick-Abnahme | **600 Dateien · 11/11 bestanden** |
| Standard-Abnahme | **10.000 Dateien · 11/11 bestanden** |
| Large-Abnahme | **100.000 Dateien · 11/11 bestanden · 218,722 s · 107.011.474 Byte Python-Peak** |

Das DATENBANKTOOL arbeitet standardmäßig rein lesend. Es erstellt einen lokalen, versionierten SQLite-Index und zeigt Dateibestände, Änderungen, Suchen, Ordnerberichte, Zeitreihen und sichere Exportberichte, ohne Originaldateien zu verändern. Es benötigt Python 3.10 oder neuer und keine zusätzlichen Laufzeitpakete.

## Installation

```bash
python -m pip install -e .
```

## Verwendung

Aktuelle Einstiegspunkte:

```bash
datenbanktool start
datenbanktool help
datenbanktool index build ~/Daten --database index.sqlite3
datenbanktool index status index.sqlite3
```

`start` öffnet die geführte Terminal-Bedienung. `help` erklärt Themen in einfacher Sprache. `index build` erstellt einen lokalen Index für einen Ordner. `index status` zeigt den Zustand eines vorhandenen Index. Weitere aktuelle Indexbefehle sind unter anderem `search`, `folders`, `changes`, `folder-compare`, `folder-timeline`, `presets` und `timeline-presets`. Eingabefehler enden mit Statuscode `2`.

## Lokale Zeitreihen-Vorlagen

Häufig geprüfte relative Ordnerpfade können unter einem verständlichen Namen gespeichert werden. Eine Vorlage enthält bewusst **keinen Datenbankpfad**, keine Scan-Ergebnisse und keine Originaldateien.

```bash
datenbanktool index timeline-presets save Musik Musik/Archiv \
  --description "Wöchentliche Größenprüfung"
```

Verwalten:

```bash
datenbanktool index timeline-presets list
datenbanktool index timeline-presets show Musik
datenbanktool index timeline-presets delete Musik --yes
```

Sicherheitsvertrag:

- Ordnerpfade sind relativ; absolute Pfade und `..` werden abgelehnt.
- Namen besitzen 1 bis 64 Zeichen, Beschreibungen höchstens 240 Zeichen.
- Gleichnamige Vorlagen werden ohne `--replace` nicht überschrieben.
- Löschen benötigt `--yes`.
- Die JSON-Konfiguration wird atomar mit Dateiberechtigung `0600` geschrieben.
- Standardpfad: `$XDG_CONFIG_HOME/datenbanktool/timeline-presets.json` beziehungsweise `~/.config/datenbanktool/timeline-presets.json`.

## Entwicklung

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

Die technische Paketversion wird als PEP 440 in `registry.json` gepflegt (`0.14.0a1`). Die menschenlesbare Projektversion lautet `0.14.0-alpha.1`. Architektur und Qualitätsregeln beschreibt die [Entwicklerdokumentation](ENTWICKLERDOKU.md).
