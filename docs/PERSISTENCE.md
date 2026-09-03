# Persistenzvertrag · Schema v1

## Zweck

Der Persistenzkern speichert Nutzerdaten lokal und getrennt vom Basistool.
Er ist bewusst generisch, damit spätere Archive, Memos, Prompts, Projekte
und weitere Module denselben Datenkern verwenden können.

## Standardpfad

`data/user/provoware.sqlite3`

Der Ordner ist durch `.gitignore` vom Repository ausgeschlossen.

Optional:

`PROVOWARE_DB_PATH=/anderer/pfad/provoware.sqlite3`

## Technik

- Engine: Python-Standardbibliothek `sqlite3`
- Schema-Version: `1`
- Journalmodus: `WAL`
- Fremdschlüssel: aktiviert
- Busy-Timeout: 5000 ms
- Synchronisation: `NORMAL`
- Migrationen: vorwärts gerichtet
- Migrationserkennung: Versionsnummer + SHA-256-Prüfsumme

## Tabellen

### `schema_migrations`

Nachweis, welche Migration in welcher geprüften Form angewendet wurde.

Felder:

- `version`
- `name`
- `applied_at`
- `checksum`

Zusätzlich wird `PRAGMA user_version` verwendet. Stimmen Historie und
`user_version` nicht überein, wird die Datenbank nicht still weiterbenutzt.

### `entries`

Gemeinsamer Grundbaustein für zukünftige Fachmodule.

Wichtige Felder:

- `id` – stabile interne ID
- `kind` – fachliche Art, zum Beispiel `memo`, `prompt`, `archive`
- `title`
- `content`
- `parent_id` – optionale Ebene/Unterebene
- `favorite`
- `status`
- `metadata_json`
- `created_at`
- `updated_at`

`parent_id` ist ein echter Fremdschlüssel. Ein Eintrag darf nicht sein
eigener direkter Elternknoten sein.

### `tags`

Normalisierte Tag-Namen mit eindeutiger Schreibweise ohne Dubletten
durch `COLLATE NOCASE`.

### `entry_tags`

N:M-Verknüpfung zwischen Einträgen und Tags.

### `app_settings`

Kleine persistente Anwendungseinstellungen als JSON-Wert.

## Migrationen

Jede Migration besitzt:

1. fortlaufende Versionsnummer,
2. stabilen Namen,
3. feste SQL-Anweisungen,
4. berechnete SHA-256-Prüfsumme.

Beim Start wird geprüft:

`Historie → Prüfsumme → user_version → fehlende Migrationen → erneute Prüfung`

Eine bereits angewendete Migration darf nicht nachträglich umgeschrieben werden.
Eine Änderung benötigt eine neue Migration mit neuer Versionsnummer.

## Integritätsprüfung

`Database.integrity_check()` kombiniert:

- `PRAGMA quick_check`
- `PRAGMA foreign_key_check`

Die Prüfung ist erfolgreich, wenn `quick_check` exakt `ok` meldet und keine
Fremdschlüsselverletzung vorhanden ist.

## Minimaler Eintragsspeicher

`EntryStore` kann aktuell:

- Einträge anlegen,
- Einträge anhand ihrer ID lesen,
- Einträge gefiltert auflisten,
- Ebenen über `parent_id` abbilden,
- Favoriten und JSON-Metadaten speichern.

Bewusst noch **nicht** freigegeben sind destructive Fachoperationen wie
produktives Löschen, Massenänderungen oder komplexe Importmutationen.

## Abgrenzung zu P0-010

SQLite-Statements werden bereits atomar ausgeführt. Der vollständige
PROVOWARE-Mutationsvertrag fehlt aber noch.

P0-010 ergänzt:

`PRE → reservieren → Mutation → POST → Commit → Evidence`

sowie:

- definierte Fehlercodes,
- Rollback-Regeln,
- Operation-ID,
- Zustandsmaschine,
- Recovery-Evidence,
- Schutz vor Doppelklick/Parallelmutation.

Erst danach sollen destructive Fachaktionen auf dieser Persistenzschicht aufbauen.
