# FORTSCHRITTSINFO

## Aktueller Stand

**Version:** `0.5.0-alpha.1`  
**Status:** 🟡 `RESTOREKERN / AUFBAU`  
**Fortschritt:** `[■■■■■■■□□□] 70 %`

| Bereich | Status | Kurzdetail |
|---|---|---|
| Repository-Basis | 🟢 | Clean Foundation steht |
| Architekturtrennung | 🟢 | Basis/Config/Data/Runtime getrennt |
| Dokumentation | 🟢 | Kernunterlagen angelegt |
| CI / Tests | 🟢 | Pflicht-Gates aktiv |
| Logging | 🟢 | JSONL + TXT-Basis vorhanden |
| Persistenz | 🟢 | SQLite-Schema v1 + exklusives Restore-Zugriffsfenster |
| Transaktionsvertrag | 🟢 | PRE/POST, Commit/Rollback, Operation-ID und Evidence aktiv |
| Recovery-Journal | 🟢 | JSONL-Zustandsjournal + Start-Gate aktiv |
| Backup Engine | 🟢 | WAL-Snapshot + Manifest v1 + unabhängige Verifikation |
| Restore Engine | 🟢 | Staging-Gate + Rollback-Snapshot + atomarer Swap + POSTCHECK |
| Fachmodule | 🟡 | bauen später auf gemeinsamem Datenkern auf |
| reale UI-Abnahme | 🔴 | noch nicht durchgeführt |

## Neu in diesem Stand

- Backup wird unmittelbar vor jedem Restore erneut verifiziert.
- Restore-Daten werden zuerst in eine separate Staging-Datei geschrieben.
- Staging muss SHA-256, Schema-Version, `quick_check` und Fremdschlüsselprüfung bestehen.
- Produktive Nutzdaten werden vor dem grünen Staging-Gate nicht ausgetauscht.
- Vor dem Swap entsteht ein verifizierter Rollback-Snapshot des bisherigen Produktivstands.
- Kritische Mutationen und Restore teilen sich einen zentralen Datenbank-Gate.
- Während des Swap-Fensters blockiert ein exklusives Datenbankzugriffsfenster
  neue prozessinterne Verbindungen.
- Aktive SQLite-Seitendateien führen vor dem Swap zum Abbruch.
- `SWAPPING` wird mit Restore-Hash, vorherigem Hash und Rollback-Pfad protokolliert.
- Nach dem Swap ist ein vollständiger produktiver POSTCHECK Pflicht.
- Fehler nach `SWAPPED` führen zum geprüften Rücktausch des vorherigen Produktivstands.
- `COMMITTED` wird ausschließlich nach grünem POSTCHECK und finaler Evidence vergeben.
- `POST /api/restore/execute` verlangt ein verifiziertes Backup und die exakte
  Bestätigung `DATENBANK WIEDERHERSTELLEN`.

## Nächster sinnvoller Schritt

**P0-012 – reale Browser-Endabnahme unter Kubuntu/KDE + Chrome.**

Ziel: den Daten-, Recovery-, Backup- und Restorekern im realen Zielsystem prüfen.
Dazu gehören Start, Statusendpunkte, Fehlerdarstellung und kritische Bedienpfade.

## Release-Regel

`STABLE` erst nach grünem Persistenz-, Recovery-, Backup/Restore-, UI-, A11y-
und Regression-Gate.
