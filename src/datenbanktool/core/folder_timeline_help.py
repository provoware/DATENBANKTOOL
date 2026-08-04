from __future__ import annotations

from datenbanktool.core.layered_help import HelpTopic


FOLDER_TIMELINE_TOPIC = HelpTopic(
    name="folder-timeline",
    title="Ordner-Zeitreihe",
    quick=(
        "Zeigt Größe und Dateizahl eines relativen Ordners über mehrere "
        "abgeschlossene Scans und kann rein lesende Trendgrenzen markieren."
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
        "Eine gespeicherte Zeitreihen-Vorlage kann den relativen Ordner liefern.",
        "Absolute Pfade und '..' werden aus Sicherheitsgründen abgelehnt.",
        "Trendgrenzen vergleichen nur positives Wachstum mit dem vorherigen sichtbaren Scan.",
        "Elternordner enthalten bewusst alle Dateien ihrer Unterordner.",
    ),
    steps=(
        "Indexdatenbank auswählen.",
        "Optional eine gespeicherte Zeitreihen-Vorlage wählen.",
        "Relativen Ordnerpfad prüfen oder '.' für den gesamten Scan verwenden.",
        "Optional älteste und neueste Scan-ID festlegen.",
        "Anzahl der Zeitpunkte zwischen 2 und 500 wählen.",
        "Optional Prozentgrenzen für Größen- und Dateizahlwachstum eingeben.",
        "Optional JSON, CSV oder HTML samt neuem Berichtspfad auswählen.",
        "Geplanten Befehl prüfen und die chronologische Ausgabe lesen.",
        "Bei ROT immer Messwert, Schwelle und Klartextbegründung gemeinsam lesen.",
        "Bei HTML zusätzlich lokale Trendgrafiken und vollständige Wertetabelle prüfen.",
    ),
    success=(
        "Mindestens zwei chronologische Zeitpunkte erscheinen; Status, Differenzen, "
        "Trendgrenzen, Minimum, Maximum und Gesamtänderung sind plausibel."
    ),
    problems=(
        "Es werden mindestens zwei Scans benötigt: denselben Stammordner erneut prüfen und abschließen.",
        "Vorlage fehlt: Namen mit 'timeline-presets list' prüfen.",
        "Keine passenden Sitzungen: Scan-IDs und gemeinsamen Stammordner kontrollieren.",
        "Ungültiger Ordnerpfad: führenden Schrägstrich und '..' entfernen.",
        "Ungültige Trendgrenze: endliche Zahl zwischen 0 und 1000000 Prozent verwenden.",
        "Ordner bleibt bei null: Schreibweise und Groß-/Kleinschreibung im Scan prüfen.",
        "Bericht existiert bereits: neuen Namen wählen oder bewusst --overwrite-report nutzen.",
        "Zu viele Zeitpunkte: Grenze auf höchstens 500 reduzieren.",
    ),
    example=(
        "datenbanktool index folder-timeline index.sqlite3 --preset Musik "
        "--warn-size-growth-percent 25 --html musik-verlauf.html"
    ),
    keywords=(
        "zeitreihe",
        "verlauf",
        "trend",
        "trendgrenze",
        "warnschwelle",
        "ordnerwachstum",
        "dateizahl",
        "speicherentwicklung",
        "diagramm",
        "grafik",
    ),
)


TIMELINE_PRESETS_TOPIC = HelpTopic(
    name="timeline-presets",
    title="Zeitreihen-Vorlage speichern",
    quick=(
        "Speichert häufig geprüfte relative Ordnerpfade lokal und macht sie auf "
        "der geführten Startseite auswählbar."
    ),
    purpose=(
        "Verhindert wiederholte Pfadeingaben, ohne Datenbankpfade, Scan-Ergebnisse "
        "oder Originaldateien in der Vorlage abzulegen."
    ),
    writes=(
        "Schreibt ausschließlich eine lokale JSON-Konfigurationsdatei mit "
        "Dateiberechtigung 600."
    ),
    risk=(
        "Gering; vorhandene Namen werden nicht still ersetzt und Löschen benötigt "
        "eine ausdrückliche Bestätigung."
    ),
    use_when="Wenn derselbe relative Ordner regelmäßig als Zeitreihe geprüft wird.",
    before=(
        "Gespeichert wird nur ein relativer Ordner oder '.'.",
        "Absolute Pfade und '..' sind unzulässig.",
        "Ein vorhandener Name bleibt ohne --replace unverändert.",
    ),
    steps=(
        "Vorlagenname mit höchstens 64 Zeichen wählen.",
        "Relativen Ordnerpfad eingeben und prüfen.",
        "Optional eine kurze Beschreibung ergänzen.",
        "Geplanten Konfigurationsschreibvorgang bestätigen.",
        "Vorlage später unter Ordner-Zeitreihe auswählen.",
    ),
    success=(
        "Die Vorlage erscheint in 'timeline-presets list' und auf der geführten "
        "Zeitreihenseite mit Name, Ordner und Beschreibung."
    ),
    problems=(
        "Name existiert bereits: neuen Namen wählen oder bewusst --replace nutzen.",
        "Ungültiger Pfad: absolute Angaben und '..' entfernen.",
        "Beschädigte Vorlagendatei: Fehlermeldung sichern und Datei nicht blind ersetzen.",
        "Löschen verweigert: --yes nur nach Prüfung des Namens verwenden.",
    ),
    example=(
        "datenbanktool index timeline-presets save Musik Musik/Archiv "
        "--description 'Regelmäßige Größenprüfung'"
    ),
    keywords=(
        "zeitreihen-vorlage",
        "ordnervorlage",
        "favorit",
        "häufiger ordner",
        "speichern",
        "überschreibschutz",
    ),
)


_TIMELINE_TOPICS = {
    FOLDER_TIMELINE_TOPIC.name: FOLDER_TIMELINE_TOPIC,
    TIMELINE_PRESETS_TOPIC.name: TIMELINE_PRESETS_TOPIC,
}


def timeline_topics() -> tuple[HelpTopic, ...]:
    return tuple(sorted(_TIMELINE_TOPICS.values(), key=lambda topic: topic.name))


def timeline_topic(name: str) -> HelpTopic | None:
    return _TIMELINE_TOPICS.get(name.strip().casefold())


def find_timeline_topics(query: str) -> tuple[HelpTopic, ...]:
    needle = query.strip().casefold()
    if not needle:
        return timeline_topics()
    matches: list[HelpTopic] = []
    for topic in _TIMELINE_TOPICS.values():
        text = " ".join(
            (topic.name, topic.title, topic.quick, topic.use_when, *topic.keywords)
        ).casefold()
        if needle in text or all(part in text for part in needle.split()):
            matches.append(topic)
    return tuple(sorted(matches, key=lambda topic: topic.name))


def timeline_matches(query: str) -> bool:
    return bool(find_timeline_topics(query))


def timeline_error_help(exit_code: int) -> tuple[str, ...]:
    topic = FOLDER_TIMELINE_TOPIC
    return (
        f"Die Ordner-Zeitreihe wurde mit Fehlercode {exit_code} beendet.",
        "Die Startseite hat Index und Originaldateien nicht verändert.",
        "Prüfe zuerst:",
        *(f"- {problem}" for problem in topic.problems[:7]),
        "Ausführliche Hilfe: datenbanktool help folder-timeline --level guided",
    )


def timeline_preset_error_help(exit_code: int) -> tuple[str, ...]:
    topic = TIMELINE_PRESETS_TOPIC
    return (
        f"Die Zeitreihen-Vorlage wurde mit Fehlercode {exit_code} nicht gespeichert.",
        "Index und Originaldateien wurden nicht verändert.",
        "Prüfe zuerst:",
        *(f"- {problem}" for problem in topic.problems),
        "Ausführliche Hilfe: datenbanktool help timeline-presets --level guided",
    )
