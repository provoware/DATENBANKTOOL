from __future__ import annotations

from datenbanktool.core.layered_help import HelpTopic


FOLDER_TIMELINE_TOPIC = HelpTopic(
    name="folder-timeline",
    title="Ordner-Zeitreihe",
    quick=(
        "Zeigt Größe und Dateizahl eines relativen Ordners über mehrere "
        "abgeschlossene Scans."
    ),
    purpose=(
        "Wertet gespeicherte Scan-Sitzungen chronologisch aus und macht Wachstum, "
        "Rückgang, Verschwinden und Wiederauftauchen verständlich sichtbar."
    ),
    writes=(
        "Rein lesend; nur ausdrücklich gewählte JSON-, CSV- oder HTML-Berichte "
        "werden atomar geschrieben."
    ),
    risk="Sehr gering; SQLite und Originaldateien werden ausschließlich gelesen.",
    use_when=(
        "Wenn die Entwicklung eines bestimmten Ordners oder des gesamten "
        "Stammordners über mehrere Scans nachvollzogen werden soll."
    ),
    before=(
        "Mindestens zwei abgeschlossene Scans desselben Stammordners werden benötigt.",
        "Der Ordnerpfad ist relativ zum gescannten Stammordner; '.' bedeutet alles.",
        "Absolute Pfade und '..' werden aus Sicherheitsgründen abgelehnt.",
        "Elternordner enthalten bewusst alle Dateien ihrer Unterordner.",
    ),
    steps=(
        "Indexdatenbank auswählen.",
        "Relativen Ordnerpfad eingeben oder '.' für den gesamten Scan verwenden.",
        "Optional älteste und neueste Scan-ID festlegen.",
        "Anzahl der Zeitpunkte zwischen 2 und 500 wählen.",
        "Optional JSON, CSV oder HTML samt neuem Berichtspfad auswählen.",
        "Geplanten Befehl prüfen und die chronologische Ausgabe lesen.",
        "Bei HTML zusätzlich die zwei beschrifteten Trendgrafiken für Größe und Dateizahl prüfen.",
    ),
    success=(
        "Mindestens zwei chronologische Zeitpunkte erscheinen; Status, Differenzen, "
        "Minimum, Maximum und Gesamtänderung sind plausibel."
    ),
    problems=(
        "Es werden mindestens zwei Scans benötigt: denselben Stammordner erneut prüfen und abschließen.",
        "Keine passenden Sitzungen: Scan-IDs und gemeinsamen Stammordner kontrollieren.",
        "Ungültiger Ordnerpfad: führenden Schrägstrich und '..' entfernen.",
        "Ordner bleibt bei null: Schreibweise und Groß-/Kleinschreibung im Scan prüfen.",
        "Bericht existiert bereits: neuen Namen wählen oder bewusst --overwrite-report nutzen.",
        "Zu viele Zeitpunkte: Grenze auf höchstens 500 reduzieren.",
    ),
    example=(
        "datenbanktool index folder-timeline index.sqlite3 Musik "
        "--html musik-verlauf.html"
    ),
    keywords=(
        "zeitreihe",
        "verlauf",
        "trend",
        "ordnerwachstum",
        "dateizahl",
        "speicherentwicklung",
        "diagramm",
        "grafik",
    ),
)


def timeline_topic(name: str) -> HelpTopic | None:
    return FOLDER_TIMELINE_TOPIC if name.strip().casefold() == "folder-timeline" else None


def timeline_matches(query: str) -> bool:
    needle = query.strip().casefold()
    if not needle:
        return True
    topic = FOLDER_TIMELINE_TOPIC
    text = " ".join(
        (topic.name, topic.title, topic.quick, topic.use_when, *topic.keywords)
    ).casefold()
    return needle in text or all(part in text for part in needle.split())


def timeline_error_help(exit_code: int) -> tuple[str, ...]:
    topic = FOLDER_TIMELINE_TOPIC
    return (
        f"Die Ordner-Zeitreihe wurde mit Fehlercode {exit_code} beendet.",
        "Die Startseite hat Index und Originaldateien nicht verändert.",
        "Prüfe zuerst:",
        *(f"- {problem}" for problem in topic.problems[:5]),
        "Ausführliche Hilfe: datenbanktool help folder-timeline --level guided",
    )
