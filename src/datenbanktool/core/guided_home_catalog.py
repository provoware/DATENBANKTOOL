from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MenuAction:
    key: str
    help_topic: str
    builder_name: str
    confirmation_required: bool = False


ACTIONS = (
    MenuAction("1", "search", "search"),
    MenuAction("2", "folders", "folders"),
    MenuAction("3", "changes", "changes"),
    MenuAction("4", "status", "status"),
    MenuAction("5", "build", "build", True),
    MenuAction("6", "rescan", "rescan", True),
    MenuAction("7", "backup", "backup", True),
    MenuAction("8", "presets", "presets"),
    MenuAction("9", "explain", "explain"),
    MenuAction("10", "folder-compare", "folder_compare"),
    MenuAction("11", "folder-timeline", "folder_timeline"),
    MenuAction("12", "timeline-presets", "timeline_presets_manage", True),
)


FIELD_HELP = {
    "database": (
        "SQLite-Indexdatei, zum Beispiel /home/name/Dokumente/index.sqlite3. "
        "Hier ist kein Ordnerpfad gemeint."
    ),
    "root": (
        "Ordner mit den Originaldateien, zum Beispiel /home/name/Bilder. "
        "Der Ordner wird nur gelesen."
    ),
    "search_text": (
        "Ein oder mehrere Wörter. Leer zeigt alle Treffer einer optionalen Vorlage."
    ),
    "preset": (
        "Exakter Name einer gespeicherten Suchvorlage. Leer überspringt die Vorlage."
    ),
    "hash_duplicates": (
        "Ja vergleicht Inhalte über Prüfsummen. Das ist sicher, bei großen Beständen "
        "aber langsamer."
    ),
    "backup_output": (
        "Optionaler neuer Sicherungspfad. Leer erzeugt automatisch einen sicheren Namen."
    ),
    "timeline_preset_choice": (
        "Nummer oder exakten Namen einer angezeigten Zeitreihen-Vorlage eingeben. "
        "Leer bedeutet, den Ordner manuell einzugeben."
    ),
    "timeline_preset_name": (
        "Verständlicher eindeutiger Name mit 1 bis 64 Zeichen. Vorhandene Namen "
        "werden über die Startseite nicht überschrieben."
    ),
    "timeline_preset_existing_name": (
        "Exakter Name einer vorhandenen Zeitreihen-Vorlage. Groß- und "
        "Kleinschreibung ist egal, der Name muss aber eindeutig vorhanden sein."
    ),
    "timeline_preset_manage": (
        "Anzeigen ist rein lesend. Ersetzen schreibt eine vorhandene Vorlage bewusst "
        "neu. Löschen entfernt eine Vorlage erst nach Namensprüfung und Bestätigung."
    ),
    "timeline_preset_delete_name": (
        "Zur Sicherheit den angezeigten Vorlagennamen noch einmal exakt eingeben. "
        "So wird kein ähnlich benannter Eintrag versehentlich gelöscht."
    ),
    "timeline_preset_description": (
        "Optionaler kurzer Zweck der Vorlage, höchstens 240 Zeichen."
    ),
    "timeline_folder": (
        "Relativer Pfad innerhalb des gescannten Stammordners, zum Beispiel Musik "
        "oder Bilder/2026. Ein Punkt bedeutet den gesamten Stammordner. Absolute "
        "Pfade und '..' sind nicht erlaubt."
    ),
    "timeline_from_session": (
        "Optional die älteste abgeschlossene Scan-ID. Leer verwendet die ältesten "
        "noch innerhalb der gewählten Höchstzahl liegenden Scans."
    ),
    "timeline_to_session": (
        "Optional die neueste abgeschlossene Scan-ID. Leer verwendet automatisch "
        "den neuesten abgeschlossenen Scan."
    ),
    "timeline_limit": (
        "Höchstens so viele neueste Zeitpunkte laden. Zulässig sind 2 bis 500; "
        "100 ist ein übersichtlicher Standard."
    ),
    "timeline_size_threshold": (
        "Optionaler Prozentwert ab 0. Leer deaktiviert die Größenwarnung. "
        "Geprüft wird nur positives Wachstum zum vorherigen sichtbaren Scan."
    ),
    "timeline_file_threshold": (
        "Optionaler Prozentwert ab 0. Leer deaktiviert die Dateizahlwarnung. "
        "Die Warnung bleibt rein lesend und ist keine Schadensbewertung."
    ),
    "timeline_report": (
        "Kein Bericht zeigt nur das Terminal. JSON ist maschinenlesbar, CSV passt "
        "zu LibreOffice Calc und HTML enthält Tabelle sowie lokale Trendgrafiken."
    ),
    "timeline_report_path": (
        "Neuer lokaler Dateipfad mit passender Endung, zum Beispiel "
        "/home/name/Berichte/musik-verlauf.html. Vorhandene Dateien werden nicht "
        "still überschrieben."
    ),
    "confirmation": (
        "Ja startet den angezeigten Befehl. Nein verwirft ihn vollständig."
    ),
    "delete_confirmation": (
        "Ja löscht nur die lokale Vorlage. Datenbank, Stammordner, Originaldateien "
        "und Scan-Ergebnisse bleiben unverändert."
    ),
}
