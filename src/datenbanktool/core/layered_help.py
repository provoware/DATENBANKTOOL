from __future__ import annotations

from dataclasses import asdict, dataclass

_LEVELS = frozenset({"quick", "detail", "guided"})


@dataclass(frozen=True, slots=True)
class HelpTopic:
    name: str
    title: str
    quick: str
    purpose: str
    writes: str
    risk: str
    use_when: str
    before: tuple[str, ...]
    steps: tuple[str, ...]
    success: str
    problems: tuple[str, ...]
    example: str
    keywords: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _topic(
    name: str,
    title: str,
    quick: str,
    purpose: str,
    writes: str,
    risk: str,
    use_when: str,
    before: tuple[str, ...],
    steps: tuple[str, ...],
    success: str,
    problems: tuple[str, ...],
    example: str,
    keywords: tuple[str, ...] = (),
) -> HelpTopic:
    return HelpTopic(
        name,
        title,
        quick,
        purpose,
        writes,
        risk,
        use_when,
        before,
        steps,
        success,
        problems,
        example,
        keywords,
    )


_TOPICS = {
    "start": _topic(
        "start",
        "Geführte Startseite",
        "Nummer wählen; Hilfe ist mit h, ?NUMMER, gNUMMER und ? erreichbar.",
        "Führt ohne auswendig gelernte Befehle durch die wichtigsten Funktionen.",
        "Die Startseite selbst schreibt nichts.",
        "Gering; Schreibaktionen benötigen eine zusätzliche Bestätigung.",
        "Wenn eine vollständig geführte Bedienung benötigt wird.",
        ("0 beendet das Tool.", "q bricht nur den aktuellen Schritt ab."),
        (
            "Funktion über ihre Nummer wählen.",
            "Ampel, Wirkung und geplanten Befehl prüfen.",
            "Gelbe Aktionen ausdrücklich bestätigen.",
        ),
        "Nach jeder Aktion erscheint ein Ergebnisstatus und das Menü erneut.",
        ("Bei unklaren Eingaben ? verwenden.",),
        "datenbanktool start",
        ("menü", "laien", "startseite"),
    ),
    "search": _topic(
        "search",
        "Dateien suchen",
        "Findet Dateien nach Suchwort oder gespeicherter Vorlage.",
        "Durchsucht einen abgeschlossenen SQLite-Scan ohne Originaldateien zu öffnen.",
        "Die normale Suche ist rein lesend.",
        "Sehr gering.",
        "Wenn Name, Pfad oder gespeicherte Filter bekannt sind.",
        ("Eine vorhandene .sqlite3-Indexdatei wird benötigt.",),
        (
            "Indexdatenbank wählen.",
            "Suchwort eingeben oder leer lassen.",
            "Optional eine Suchvorlage angeben.",
        ),
        "Trefferzahl und passende Dateipfade werden angezeigt.",
        (
            "Keine Treffer: testweise ohne Suchwort und Vorlage starten.",
            "Datenbank fehlt: vollständigen .sqlite3-Pfad prüfen.",
        ),
        "datenbanktool index search index.sqlite3 urlaub",
        ("finden", "suchwort", "vorlage"),
    ),
    "folders": _topic(
        "folders",
        "Ordnerübersicht",
        "Zeigt Ordnergrößen, Dateizahlen und größte Platzfresser.",
        "Fasst einen abgeschlossenen Scan einschließlich Unterordnern zusammen.",
        "Rein lesend; nur ausdrücklich gewählte Berichte werden geschrieben.",
        "Sehr gering.",
        "Wenn große oder unübersichtliche Ordner gefunden werden sollen.",
        ("Elternordner enthalten bewusst die Werte ihrer Unterordner.",),
        (
            "Indexdatenbank wählen.",
            "Ampel immer zusammen mit Klartext und Begründung lesen.",
            "Eingerückte Platzfresser prüfen.",
        ),
        "Eine stabile Ordnerliste erscheint; es wird nichts aufgeräumt.",
        ("Ordnerzeilen nicht addieren; Unterordner sind bereits enthalten.",),
        "datenbanktool index folders index.sqlite3",
        ("ordner", "größe", "platzfresser", "speicher"),
    ),
    "folder-compare": _topic(
        "folder-compare",
        "Ordner vergleichen",
        "Zeigt, welche Ordner zwischen zwei abgeschlossenen Scans größer oder kleiner wurden.",
        "Vergleicht rekursive Dateizahl und Gesamtgröße pro Ordner in zwei gespeicherten Sitzungen desselben Stammordners.",
        "Rein lesend; nur ausdrücklich gewählte JSON-, CSV- oder HTML-Berichte werden geschrieben.",
        "Sehr gering.",
        "Wenn Speicherwachstum, Rückgang, neue oder nicht mehr vorhandene Ordner nachvollzogen werden sollen.",
        (
            "Mindestens zwei abgeschlossene Scans desselben Stammordners werden benötigt.",
            "Ohne Sitzungsnummern wählt das Tool automatisch das neueste passende Paar.",
        ),
        (
            "Indexdatenbank wählen.",
            "Automatisch gewählte Scan-Nummern im Kopf der Ausgabe prüfen.",
            "Zustand, Größenunterschied, Prozentwert und Dateidifferenz lesen.",
            "Optional Filter oder einen lokalen Bericht wählen.",
        ),
        "Gewachsene, kleinere, neue und nicht mehr vorhandene Ordner werden mit Klartext und Begründung angezeigt.",
        (
            "Nur ein Scan vorhanden: zuerst denselben Ordner erneut prüfen.",
            "Unterschiedliche Stammordner: passende Sitzungsnummern desselben Ordners wählen.",
            "Keine Treffer: Filter oder Mindeständerung reduzieren.",
        ),
        "datenbanktool index folder-compare index.sqlite3",
        ("ordnervergleich", "wachstum", "gewachsen", "kleiner", "speicherverlauf"),
    ),
    "changes": _topic(
        "changes",
        "Änderungen anzeigen",
        "Zeigt neue, geänderte, verschobene und entfernte Dateien.",
        "Vergleicht gespeicherte Scan-Sitzungen ohne Originaldateiänderung.",
        "Rein lesend; optionale Berichte werden nur auf Wunsch erstellt.",
        "Sehr gering.",
        "Wenn Änderungen seit dem letzten Re-Scan nachvollzogen werden sollen.",
        ("Mindestens ein abgeschlossener Re-Scan wird benötigt.",),
        (
            "Indexdatenbank wählen.",
            "Änderungsarten getrennt lesen.",
            "Bei Verschiebungen alten und neuen Pfad vergleichen.",
        ),
        "Die Änderungsliste und ihre Zähler werden angezeigt.",
        ("Fehlt ein Re-Scan, zuerst 'Ordner erneut prüfen' ausführen.",),
        "datenbanktool index changes index.sqlite3",
        ("vergleich", "verschoben", "entfernt"),
    ),
    "status": _topic(
        "status",
        "Indexstatus prüfen",
        "Zeigt letzten Scan, Dateizahl, Fehler und Duplikatgruppen.",
        "Liest nur Verwaltungsdaten aus der SQLite-Datei.",
        "Keine Datenänderung.",
        "Sehr gering.",
        "Wenn Vollständigkeit oder Fehler eines Scans geprüft werden sollen.",
        ("Die Indexdatei muss vorhanden sein.",),
        (
            "Indexdatenbank wählen.",
            "Status complete, interrupted oder failed lesen.",
            "Datei- und Fehlerzähler prüfen.",
        ),
        "Status und letzte Scan-Sitzung werden angezeigt.",
        ("Bei interrupted den Index später mit Wiederaufnahme fortsetzen.",),
        "datenbanktool index status index.sqlite3",
        ("status", "fehler", "vollständig"),
    ),
    "build": _topic(
        "build",
        "Neuen Index anlegen",
        "Erfasst einen Ordner als durchsuchbaren SQLite-Snapshot.",
        "Liest Dateiinformationen und speichert sie in einer Indexdatenbank.",
        "Schreibt nur SQLite; Originaldateien bleiben unverändert.",
        "Gering bis mittel; kontrollierter Indexschreibvorgang.",
        "Beim ersten Erfassen eines Ordners.",
        (
            "Quellordner und Indexziel dürfen nicht verwechselt werden.",
            "Prüfsummen erhöhen Genauigkeit und Laufzeit.",
        ),
        (
            "Quellordner wählen.",
            "Neuen oder passenden .sqlite3-Zielpfad wählen.",
            "Duplikatprüfung entscheiden.",
            "Geplanten Befehl ausdrücklich bestätigen.",
        ),
        "Status complete und eine plausible Dateizahl bestätigen den Erfolg.",
        (
            "Gesperrter Index: anderen DATENBANKTOOL-Prozess prüfen.",
            "Lesefehler: Dateiberechtigungen prüfen.",
        ),
        "datenbanktool index build ~/Daten --database index.sqlite3",
        ("erster scan", "erfassen", "sqlite"),
    ),
    "rescan": _topic(
        "rescan",
        "Ordner erneut prüfen",
        "Erkennt Änderungen seit einem früheren Scan.",
        "Liest denselben Ordner und ergänzt eine neue Scan-Sitzung in SQLite.",
        "Schreibt nur den Index; Originaldateien bleiben unverändert.",
        "Gering bis mittel.",
        "Wenn ein bereits erfasster Ordner erneut geprüft werden soll.",
        ("Ausgangsscan, Ordnerwurzel und Index müssen zusammenpassen.",),
        (
            "Bereits erfassten Ordner wählen.",
            "Zugehörige Indexdatenbank wählen.",
            "Schreibwirkung prüfen und bestätigen.",
        ),
        "Zähler für neu, geändert, verschoben und entfernt erscheinen.",
        ("Ohne Ausgangsscan zuerst einen neuen Index anlegen.",),
        "datenbanktool index rescan ~/Daten --database index.sqlite3",
        ("erneut", "aktualisieren", "vergleichen"),
    ),
    "backup": _topic(
        "backup",
        "Index sichern",
        "Erstellt eine geprüfte Kopie der SQLite-Indexdatenbank.",
        "Nutzt die SQLite-Backup-API und prüft die Kopie.",
        "Schreibt eine neue Sicherungsdatei; Originaldateien bleiben unberührt.",
        "Gering; vorhandene Ziele werden nicht still überschrieben.",
        "Vor Reparatur, Restore oder wichtigen Änderungen.",
        ("Am Ziel muss ausreichend Speicher frei sein.",),
        (
            "Indexdatenbank wählen.",
            "Optional einen neuen Sicherungspfad angeben.",
            "Ziel prüfen und bestätigen.",
        ),
        "Integritätsprüfung und endgültiger Sicherungspfad werden angezeigt.",
        ("Existiert das Ziel bereits, einen neuen Namen wählen.",),
        "datenbanktool index backup index.sqlite3 --output backup.sqlite3",
        ("sicherung", "kopie", "schutz"),
    ),
    "presets": _topic(
        "presets",
        "Suchvorlagen",
        "Zeigt häufig verwendete gespeicherte Suchfilter.",
        "Liest die persönliche Vorlagendatei außerhalb des SQLite-Indexes.",
        "Anzeigen ist rein lesend.",
        "Sehr gering.",
        "Wenn dieselbe Suche regelmäßig wiederholt wird.",
        ("Vorlagen enthalten Filter, aber keinen festen Datenbankpfad.",),
        (
            "Vorlagenliste öffnen.",
            "Namen und Beschreibung prüfen.",
            "Den Namen später in der Dateisuche eintragen.",
        ),
        "Gespeicherte Vorlagen werden ohne Änderung angezeigt.",
        ("Bei unbekannter Vorlage Schreibweise mit der Liste vergleichen.",),
        "datenbanktool index presets list",
        ("vorlage", "filter", "wiederholen"),
    ),
    "explain": _topic(
        "explain",
        "Funktionen erklären",
        "Zeigt kurze, ausführliche oder geführte Hilfe.",
        "Liest ausschließlich den eingebauten Hilfekatalog.",
        "Keine Datenänderung.",
        "Keine.",
        "Wenn Bedeutung, Auswirkung oder nächster Schritt unklar ist.",
        ("Die Hilfe kann mit Alltagsbegriffen durchsucht werden.",),
        (
            "Thema direkt nennen oder mit --find suchen.",
            "Hilfestufe quick, detail oder guided wählen.",
            "Beispiel an eigene Pfade anpassen.",
        ),
        "Zweck, Wirkung, Schritte und typische Probleme werden angezeigt.",
        ("Bei unbekanntem Thema zuerst datenbanktool help ausführen.",),
        "datenbanktool help search --level guided",
        ("hilfe", "anleitung", "problem"),
    ),
    "ampel": _topic(
        "ampel",
        "Ampeln verstehen",
        "Zeigt Lesewirkung, Schreibwirkung oder Prüfbedarf schneller.",
        "Farbe, Statuswort und Begründung werden immer gemeinsam angezeigt.",
        "Die Ampel selbst verändert keine Daten.",
        "Keine.",
        "Bei Menüaktionen, Ordnerlisten und Statusausgaben.",
        ("Ampeln sind keine automatische Schadens- oder Löschentscheidung.",),
        (
            "Farbnamen GRÜN, GELB oder ROT lesen.",
            "Statuswort wie 'Nur lesen' oder 'Bestätigung nötig' lesen.",
            "Begründung nach dem Doppelpunkt lesen.",
        ),
        "Die tatsächliche Wirkung ist vor dem Start verstanden.",
        ("Bei schlechter Erkennbarkeit --color never verwenden.",),
        "datenbanktool help ampel --level guided",
        ("farbe", "grün", "gelb", "rot"),
    ),
}


def list_topics() -> tuple[HelpTopic, ...]:
    return tuple(sorted(_TOPICS.values(), key=lambda topic: topic.name))


def find_topics(query: str) -> tuple[HelpTopic, ...]:
    needle = query.strip().casefold()
    if not needle:
        return list_topics()
    matches = []
    for topic in _TOPICS.values():
        text = " ".join(
            (topic.name, topic.title, topic.quick, topic.use_when, *topic.keywords)
        ).casefold()
        if needle in text or all(part in text for part in needle.split()):
            matches.append(topic)
    return tuple(sorted(matches, key=lambda topic: topic.name))


def get_topic(name: str) -> HelpTopic:
    key = name.strip().casefold()
    if key in _TOPICS:
        return _TOPICS[key]
    matches = find_topics(key)
    hint = (
        f" Meintest du: {', '.join(item.name for item in matches[:3])}?"
        if matches
        else ""
    )
    raise ValueError(f"Hilfethema nicht gefunden: {name}.{hint}")


def render_topic(topic: HelpTopic, level: str = "detail") -> tuple[str, ...]:
    if level not in _LEVELS:
        raise ValueError(f"Unbekannte Hilfestufe: {level}")
    lines = [topic.title, f"Kurz erklärt: {topic.quick}"]
    lines.extend((f"Schreibt: {topic.writes}", f"Risiko: {topic.risk}"))
    if level == "quick":
        return tuple(lines)
    lines.extend((f"Zweck: {topic.purpose}", f"Sinnvoll wenn: {topic.use_when}"))
    if topic.before:
        lines.append("Vorher prüfen:")
        lines.extend(f"- {item}" for item in topic.before)
    lines.extend((f"Erfolg erkennen: {topic.success}", f"Beispiel: {topic.example}"))
    if level == "detail":
        return tuple(lines)
    lines.append("Schritt für Schritt:")
    lines.extend(f"{number}. {step}" for number, step in enumerate(topic.steps, 1))
    if topic.problems:
        lines.append("Typische Probleme und Lösung:")
        lines.extend(f"- {problem}" for problem in topic.problems)
    return tuple(lines)


def error_help(topic_name: str, exit_code: int) -> tuple[str, ...]:
    topic = get_topic(topic_name)
    lines = [
        f"Die Funktion wurde mit Fehlercode {exit_code} beendet.",
        "Die Startseite hat Originaldateien nicht automatisch verändert.",
    ]
    if topic.problems:
        lines.append("Prüfe zuerst:")
        lines.extend(f"- {problem}" for problem in topic.problems[:3])
    lines.append(
        f"Ausführliche Hilfe: datenbanktool help {topic.name} --level guided"
    )
    return tuple(lines)
