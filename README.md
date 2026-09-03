# PROVOWARE DATENBANKTOOL

![Status](https://img.shields.io/badge/Status-DATENKERN%20%2F%20AUFBAU-ffd43b?style=flat-square)
![CI](https://img.shields.io/badge/CI-Pflicht-29d3c2?style=flat-square)
![Sprache](https://img.shields.io/badge/Toolsprache-Deutsch-8b5cf6?style=flat-square)

## 🟡 Projektstatus

`[■■■■□□□□□□] 40 % · DATENKERN / AUFBAU`

Die Clean Foundation steht. Mit `0.2.0-alpha.1` ist zusätzlich der erste echte
Persistenzkern vorhanden: SQLite-Schema, versionierte Migrationen,
Integritätsprüfung und ein generischer hierarchischer Eintragsspeicher.

Der unmittelbare Stand vor dem Clean Rebuild bleibt zusätzlich auf
`backup/pre-clean-rebuild-20260903` gesichert.

## Ziel

PROVOWARE DATENBANKTOOL soll ein lokal betreibbares, laienfreundliches
und robustes Datenbank-/Wissenswerkzeug werden.

Die Architektur trennt konsequent:

- **Basistool** – Programmcode und feste UI-Grundlage
- **Konfiguration** – versionierbare Standardwerte, keine privaten Einstellungen
- **Nutzerdaten** – lokal, nicht im Repository
- **Laufzeitdaten** – Logs, Caches, Backups und Sessions; nicht im Repository
- **Dokumentation** – Laien- und Entwicklerwissen getrennt
- **Tests & Werkzeuge** – reproduzierbare Qualitätskontrolle

## Schnellstart

```bash
python3 -m src.server
```

Danach im Browser öffnen:

`http://127.0.0.1:8765`

Die lokale Datenbank wird beim ersten Start automatisch unter
`data/user/provoware.sqlite3` angelegt und auf die aktuelle Schema-Version migriert.

Optional kann der Datenbankpfad gesetzt werden:

```bash
PROVOWARE_DB_PATH=/anderer/pfad/provoware.sqlite3 python3 -m src.server
```

## Datenkern

Der aktuelle Persistenzkern verwendet die Python-Standardbibliothek `sqlite3`.

Enthalten sind:

- Schema-Version `1`
- Migrationen mit SHA-256-Prüfsumme
- SQLite-Fremdschlüssel
- WAL-Journalmodus
- `PRAGMA quick_check` und Fremdschlüsselprüfung
- hierarchische Einträge über `parent_id`
- Tags und Eintrag-Tag-Zuordnung
- App-Einstellungen
- generischer `EntryStore` für zukünftige Archiv- und Dashboardmodule

Der vollständige Vertrag steht in `docs/PERSISTENCE.md`.

## Ampeln

- 🟢 **GRÜN** – Prüfung bestanden / normaler Betrieb
- 🟡 **GELB** – Hinweis / noch nicht releasefertig
- 🔴 **ROT** – Fehler / Gate blockiert
- 🟣 **INFO** – Erklärung, Tipp oder Entwicklungsdetail

## Wichtige Dokumente

| Datei | Zweck |
|---|---|
| `TODO.md` | aktuelle Abhakliste |
| `FORTSCHRITTSINFO.md` | kompakter Status |
| `ENTWICKLUNGSPLAN.md` | Roadmap |
| `REGRESSIONSPOOL.md` | wiederkehrende Fehlerprüfungen |
| `AGENTS.md` | verbindliche Entwicklungsregeln |
| `DEVELOPER_HANDBOOK.md` | Architektur & Entwicklerwissen |
| `LAIENHILFE.md` | einfache Hilfe & Tipps |
| `DEBUGGING_LOGGING.md` | Logging-/Fehlerstandard |
| `docs/PERSISTENCE.md` | Datenbank-, Schema- und Migrationsvertrag |
| `MANIFEST.json` | maschinenlesbare Projektstandards |

## Datenschutz

Das Repository enthält **keine echten Nutzerdaten, Accounts, E-Mails,
Tokens, Passwörter, Browserprofile, Backups oder Betriebslogs**.
Beispielwerte müssen eindeutig als Beispiel gekennzeichnet sein.

## Entwicklungsprinzip

`Besprechen → Implementieren → Formatieren → Prüfen → Regression → Status aktualisieren → Merge`

Nächster P0-Schritt ist der formale Recovery-/Transaktionsvertrag für alle
Datenänderungen. Vor einer STABLE-Kennzeichnung müssen alle Release-Gates in
`MANIFEST.json` und `REGRESSIONSPOOL.md` grün sein.
