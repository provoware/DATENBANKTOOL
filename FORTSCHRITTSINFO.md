# FORTSCHRITTSINFO

## Aktueller Stand

**Version:** `0.4.0-alpha.1`  
**Status:** 🟡 `BACKUPKERN / AUFBAU`  
**Fortschritt:** `[■■■■■■□□□□] 60 %`

| Bereich | Status | Kurzdetail |
|---|---|---|
| Repository-Basis | 🟢 | Clean Foundation steht |
| Architekturtrennung | 🟢 | Basis/Config/Data/Runtime getrennt |
| Dokumentation | 🟢 | Kernunterlagen angelegt |
| CI / Tests | 🟢 | Pflicht-Gates aktiv |
| Logging | 🟢 | JSONL + TXT-Basis vorhanden |
| Persistenz | 🟢 | SQLite-Schema v1 + Migrationen + Integritätsprüfung |
| Transaktionsvertrag | 🟢 | PRE/POST, Commit/Rollback, Operation-ID und Evidence aktiv |
| Recovery-Journal | 🟢 | JSONL-Zustandsjournal + Start-Gate aktiv |
| Backup Engine | 🟢 | WAL-Snapshot + Manifest v1 + unabhängige Verifikation |
| Restore | 🟡 | P0-011B Staging-Restore noch gesperrt |
| Fachmodule | 🟡 | bauen später auf gemeinsamem Datenkern auf |
| reale UI-Abnahme | 🔴 | noch nicht durchgeführt |

## Neu in diesem Stand

- SQLite-Sicherung nutzt die SQLite-Backup-API statt einfacher Dateikopie.
- WAL-Quellen werden konsistent in einen eigenständigen Snapshot überführt.
- Jedes Backup erhält eine eindeutige `bkp-...`-ID.
- Manifest v1 speichert SHA-256, Dateigröße, Schema-Version, UTC-Zeit und Integritätsstatus.
- `quick_check` und `foreign_key_check` werden auf dem Snapshot ausgeführt.
- Ein zweites Verifikations-Gate misst Hash, Größe, Schema und Integrität erneut.
- Noch nicht veröffentlichte Sicherungen heißen `.incomplete_*` und gelten niemals als gültig.
- Erst ein verifiziertes Staging-Backup wird atomar als `backup_status_verified_*` veröffentlicht.
- Manipulierte Snapshot- oder Manifestdateien werden von der gültigen Backup-Liste ausgeschlossen.

## Nächster sinnvoller Schritt

**P0-011B – Staging-Restore mit Integritätsprüfung und atomarem Austausch.**

Ziel: Ein verifiziertes Backup wird zunächst ausschließlich in eine Staging-Datenbank
überführt. Erst nach erneutem Hash-, Schema-, `quick_check`- und Fremdschlüssel-Gate
darf ein atomarer Austausch der produktiven Datenbank vorbereitet werden.

## Release-Regel

`STABLE` erst nach grünem Persistenz-, Recovery-, Backup/Restore-, UI-, A11y- und Regression-Gate.
