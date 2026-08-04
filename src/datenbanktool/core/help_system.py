from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True, slots=True)
class HelpTopic:
    name: str
    title: str
    purpose: str
    effect: str
    writes: str
    risk: str
    use_when: str
    example: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


_TOPICS = {
    "start": HelpTopic(
        "start",
        "Geführte Terminal-Startseite",
        "Zeigt die wichtigsten Funktionen als nummerierte, erklärte Auswahl.",
        "Fragt benötigte Pfade und Suchwerte schrittweise ab, zeigt den geplanten Befehl und startet ihn ohne Shell-Auswertung.",
        "Die Startseite selbst schreibt nichts. Schreibende Index- oder Sicherungsaktionen benötigen eine zusätzliche Bestätigung.",
        "Gering – jede Aktion zeigt vorher klar, ob nur gelesen oder eine Index-/Sicherungsdatei geschrieben wird.",
        "Wenn DATENBANKTOOL ohne Kenntnis einzelner Befehle bedient werden soll.",
        "datenbanktool start",
    ),
    "folders": HelpTopic(
        "folders",
        "Ordnerübersicht",
        "Zeigt pro Ordner Dateizahl, Speicherbedarf und größte Platzfresser.",
        "Liest einen abgeschlossenen Scan und fasst Unterordner zusammen. Die Ampel priorisiert nur den Prüfbedarf.",
        "Keine Änderung an Index oder Originaldateien. Nur ausdrücklich gewählte JSON-/HTML-Berichte werden erstellt.",
        "Sehr gering – reine Auswertung.",
        "Wenn Speicherfresser, unübersichtliche Ordner oder Häufungen von Namensproblemen gefunden werden sollen.",
        "datenbanktool index folders index.sqlite3 --max-depth 2",
    ),
    "search": HelpTopic(
        "search",
        "Dateisuche",
        "Findet Dateien im gespeicherten Index mit kombinierbaren Filtern.",
        "Die normale Suche öffnet SQLite nur lesend. Ein gespeicherter Filter kann mit --preset geladen werden.",
        "Keine Änderung, außer --build-fulltext-index wird ausdrücklich gewählt.",
        "Sehr gering; FTS5 schreibt nur zusätzliche Suchdaten in den Index.",
        "Wenn Dateien nach Namen, Typ, Größe, Namensproblem oder Duplikatstatus gesucht werden.",
        "datenbanktool index search index.sqlite3 urlaub --category image",
    ),
    "presets": HelpTopic(
        "presets",
        "Suchvorlagen",
        "Speichert häufig verwendete Suchfilter unter einem verständlichen Namen.",
        "Schreibt eine kleine JSON-Datei im Benutzer-Konfigurationsordner. Originaldateien und SQLite-Inhalte bleiben unverändert.",
        "Schreibt oder löscht nur die gewählte Vorlagen-Konfigurationsdatei.",
        "Gering; Überschreiben benötigt --replace, Löschen benötigt --yes.",
        "Wenn dieselbe Suche regelmäßig wiederholt wird.",
        "datenbanktool index presets save grosse-audios --category audio --min-size-mib 100",
    ),
    "changes": HelpTopic(
        "changes",
        "Änderungen seit dem letzten Scan",
        "Zeigt neue, geänderte, verschobene, entfernte und unveränderte Dateien.",
        "Liest die gespeicherte Re-Scan-Sitzung und kann lokale JSON-, CSV- oder HTML-Berichte erzeugen.",
        "Keine Originaldateiänderung. Nur ausdrücklich gewählte Berichtsdateien werden geschrieben.",
        "Sehr gering – reine Auswertung.",
        "Wenn nachvollzogen werden soll, was sich zwischen zwei Scans verändert hat.",
        "datenbanktool index changes index.sqlite3 --type modified",
    ),
    "backup": HelpTopic(
        "backup",
        "Index sichern",
        "Erstellt eine geprüfte Kopie der SQLite-Indexdatenbank.",
        "Verwendet die SQLite-Backup-API und prüft die Sicherung vor Freigabe.",
        "Schreibt eine neue Sicherungsdatei; vorhandene Ziele werden nicht still ersetzt.",
        "Gering – betrifft nur den Index, nicht die gescannten Dateien.",
        "Vor Reparatur, Restore oder wichtigen Entwicklungsänderungen.",
        "datenbanktool index backup index.sqlite3 --output backup.sqlite3",
    ),
    "restore": HelpTopic(
        "restore",
        "Index wiederherstellen",
        "Ersetzt den aktiven Index durch eine geprüfte Sicherung.",
        "Prüft die Sicherung vorher und erstellt standardmäßig eine Rückfallsicherung.",
        "Verändert die Indexdatenbank, niemals die gescannten Originaldateien.",
        "Mittel – deshalb mit Vorprüfung und Rückfallsicherung.",
        "Nur wenn ein früherer Indexstand benötigt wird.",
        "datenbanktool index restore index.sqlite3 --backup backup.sqlite3",
    ),
    "ampel": HelpTopic(
        "ampel",
        "Ampelfarben",
        "Macht Prüfbedarf schneller sichtbar.",
        "Grün bedeutet unauffällig, Gelb bedeutet prüfen, Rot bedeutet dringend prüfen. Die Begründung steht immer daneben.",
        "Keine Datenänderung.",
        "Keine; Farbe ist nur Zusatzinformation und wird nie allein verwendet.",
        "Bei großen Listen und Ordnerübersichten.",
        "datenbanktool --color always index folders index.sqlite3",
    ),
}


def list_topics() -> tuple[HelpTopic, ...]:
    return tuple(sorted(_TOPICS.values(), key=lambda topic: topic.name))


def get_topic(name: str) -> HelpTopic:
    key = name.strip().casefold()
    if key not in _TOPICS:
        raise KeyError(f"Hilfethema nicht gefunden: {name}")
    return _TOPICS[key]
