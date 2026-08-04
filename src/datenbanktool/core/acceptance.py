from __future__ import annotations

import csv
import json
import os
import random
import resource
import time
import tracemalloc
from dataclasses import asdict, dataclass
from pathlib import Path

from datenbanktool.core.folder_csv import export_folder_csv
from datenbanktool.core.folders import FolderFilter, analyse_folders
from datenbanktool.core.index_database import IndexBuildOptions, build_index
from datenbanktool.core.layered_help import get_topic, render_topic


@dataclass(frozen=True, slots=True)
class AcceptanceProfile:
    name: str
    file_count: int
    folder_count: int
    max_sparse_file_bytes: int
    max_seconds: float
    max_python_memory_mib: int
    description: str

    def validate(self) -> None:
        if not self.name.strip():
            raise ValueError("Abnahmeprofil benötigt einen Namen")
        if self.file_count < 1:
            raise ValueError("Dateizahl muss mindestens 1 sein")
        if self.folder_count < 1:
            raise ValueError("Ordnerzahl muss mindestens 1 sein")
        if self.max_sparse_file_bytes < 1:
            raise ValueError("Maximale Testdateigröße muss mindestens 1 Byte sein")
        if self.max_seconds <= 0:
            raise ValueError("Zeitgrenze muss positiv sein")
        if self.max_python_memory_mib < 1:
            raise ValueError("Speichergrenze muss mindestens 1 MiB sein")


PROFILES = {
    "quick": AcceptanceProfile(
        name="quick",
        file_count=600,
        folder_count=24,
        max_sparse_file_bytes=64 * 1024,
        max_seconds=30.0,
        max_python_memory_mib=256,
        description="Kurze CI- und Installationsprüfung mit 600 Dateien.",
    ),
    "standard": AcceptanceProfile(
        name="standard",
        file_count=10_000,
        folder_count=250,
        max_sparse_file_bytes=512 * 1024,
        max_seconds=600.0,
        max_python_memory_mib=1024,
        description="Realistische lokale Prüfung mit 10.000 Dateien.",
    ),
    "large": AcceptanceProfile(
        name="large",
        file_count=100_000,
        folder_count=1_000,
        max_sparse_file_bytes=2 * 1024 * 1024,
        max_seconds=3600.0,
        max_python_memory_mib=4096,
        description="Großbestandsprüfung mit 100.000 Dateien.",
    ),
}


@dataclass(frozen=True, slots=True)
class AcceptanceCheck:
    name: str
    passed: bool
    observed: str
    limit: str
    explanation: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class AcceptanceResult:
    profile: str
    seed: int
    workspace: str
    file_count: int
    folder_count: int
    logical_size_bytes: int
    duration_seconds: float
    phase_seconds: dict[str, float]
    peak_python_memory_bytes: int
    process_max_rss_bytes: int
    imported_count: int
    index_error_count: int
    folder_rows: int
    checks: tuple[AcceptanceCheck, ...]
    passed: bool
    manual_novice_status: str
    json_report: str
    markdown_report: str
    novice_checklist: str

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["checks"] = [check.to_dict() for check in self.checks]
        return payload


def get_profile(name: str) -> AcceptanceProfile:
    key = name.strip().casefold()
    try:
        return PROFILES[key]
    except KeyError as error:
        raise ValueError(f"Unbekanntes Abnahmeprofil: {name}") from error


def _atomic_write(path: Path, content: str) -> str:
    target = path.resolve(strict=False)
    if target.exists():
        raise FileExistsError(f"Abnahmebericht existiert bereits: {target}")
    temporary = target.with_name(f".{target.name}.tmp-{os.getpid()}")
    try:
        temporary.write_text(content, encoding="utf-8")
        temporary.replace(target)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
    return str(target)


def _safe_workspace(path: Path) -> Path:
    target = path.expanduser().resolve(strict=False)
    if target.exists():
        raise FileExistsError(
            f"Abnahmearbeitsordner existiert bereits: {target}. "
            "Wähle einen neuen leeren Pfad."
        )
    target.mkdir(parents=True, exist_ok=False)
    return target


def _dataset_name(index: int) -> str:
    suffixes = (".txt", ".jpg", ".wav", ".mp4", ".pdf", ".zip", ".py")
    suffix = suffixes[index % len(suffixes)]
    if index % 113 == 0:
        return f" datei mit fragezeichen {index:06d}?.txt"
    if index % 97 == 0:
        return f"Änderung Übersicht {index:06d}{suffix}"
    if index % 89 == 0:
        return f"mehrfach...punkt...{index:06d}{suffix}"
    return f"datei-{index:06d}{suffix}"


def _create_dataset(
    root: Path,
    profile: AcceptanceProfile,
    seed: int,
) -> tuple[int, int]:
    profile.validate()
    randomizer = random.Random(seed)
    logical_size = 0
    for index in range(profile.file_count):
        first = index % profile.folder_count
        second = (index // profile.folder_count) % 8
        folder = root / f"bereich-{first:04d}" / f"gruppe-{second:02d}"
        folder.mkdir(parents=True, exist_ok=True)
        size = 128 + randomizer.randrange(profile.max_sparse_file_bytes)
        target = folder / _dataset_name(index)
        with target.open("xb") as handle:
            handle.truncate(size)
        logical_size += size
    return profile.file_count, logical_size


def _source_manifest(root: Path) -> tuple[tuple[str, int, int], ...]:
    rows: list[tuple[str, int, int]] = []
    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix()):
        if not path.is_file():
            continue
        stat = path.stat()
        rows.append(
            (
                path.relative_to(root).as_posix(),
                int(stat.st_size),
                int(stat.st_mtime_ns),
            )
        )
    return tuple(rows)


def _csv_data_rows(path: Path) -> int:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return max(0, sum(1 for _ in csv.reader(handle, delimiter=";")) - 1)


def _process_max_rss_bytes() -> int:
    value = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return value * 1024


def _check(
    name: str,
    passed: bool,
    observed: object,
    limit: object,
    explanation: str,
) -> AcceptanceCheck:
    return AcceptanceCheck(
        name=name,
        passed=bool(passed),
        observed=str(observed),
        limit=str(limit),
        explanation=explanation,
    )


def _markdown_report(result: AcceptanceResult, profile: AcceptanceProfile) -> str:
    rows = "\n".join(
        "| {status} | {name} | {observed} | {limit} | {explanation} |".format(
            status="BESTANDEN" if check.passed else "NICHT BESTANDEN",
            name=check.name.replace("|", "\\|"),
            observed=check.observed.replace("|", "\\|"),
            limit=check.limit.replace("|", "\\|"),
            explanation=check.explanation.replace("|", "\\|"),
        )
        for check in result.checks
    )
    phases = "\n".join(
        f"- {name}: {seconds:.3f} Sekunden"
        for name, seconds in result.phase_seconds.items()
    )
    return f"""# DATENBANKTOOL – automatisierter Abnahmebericht

## Ergebnis

- Profil: `{result.profile}`
- Beschreibung: {profile.description}
- Gesamtergebnis: **{'BESTANDEN' if result.passed else 'NICHT BESTANDEN'}**
- Zufallsstartwert: `{result.seed}`
- Dateien: {result.file_count}
- logische Testdatengröße: {result.logical_size_bytes} Byte
- Laufzeit: {result.duration_seconds:.3f} Sekunden
- Python-Spitzenspeicher: {result.peak_python_memory_bytes} Byte
- Prozess-Maximal-RSS: {result.process_max_rss_bytes} Byte
- externe Laienabnahme: **NOCH OFFEN**

## Phasen

{phases}

## Automatische Prüfpunkte

| Status | Prüfung | Beobachtet | Grenze | Erklärung |
|---|---|---:|---:|---|
{rows}

## Sicherheitsfazit

Der Testbestand wurde ausschließlich im neu angelegten Arbeitsordner erzeugt. Der
Indexaufbau und die Ordnerauswertung dürfen die erzeugten Quelldateien nicht verändern.
Ein Vorher-/Nachher-Manifest prüft Pfad, Größe und Änderungszeit jeder Testdatei.

## Einordnung

Die automatische Prüfung ersetzt keine echte Beobachtung unerfahrener Nutzer. Die
generierte Laien-Checkliste muss auf einem Zielsystem durch eine reale Testperson
ausgefüllt werden.
"""


def _novice_checklist(profile: AcceptanceProfile, workspace: Path) -> str:
    return f"""# DATENBANKTOOL – Laienabnahme

> Status: Noch nicht durch eine reale Testperson ausgefüllt.

## Testdaten

- Profil: `{profile.name}`
- Dateien: {profile.file_count}
- Arbeitsordner: `{workspace}`
- technische Hilfe während der Aufgaben: nur über die eingebaute Hilfe

## Angaben zur Testperson

- Name oder Kennung:
- Linux-Erfahrung: keine / wenig / mittel
- Datum:
- System:

## Aufgaben

### 1. Startseite öffnen

Befehl: `datenbanktool start`

- [ ] Ohne fremde Erklärung erkannt, wie das Tool beendet wird.
- [ ] Verstanden, welche Funktionen nur lesen und welche schreiben.
- Zeit:
- Irrwege oder unklare Wörter:

### 2. Ordnerübersicht finden

- [ ] Menüpunkt 2 selbstständig gefunden.
- [ ] Bedeutung von „direkt“ und „mit Unterordnern“ verstanden.
- [ ] Ampel zusammen mit ihrer Begründung gelesen.
- Zeit:
- Irrwege oder unklare Wörter:

### 3. CSV-Bericht erzeugen

Befehl:
`datenbanktool index folders {workspace / 'index.sqlite3'} --csv {workspace / 'ordneruebersicht.csv'} --all-pages`

- [ ] Bericht ohne externe Anleitung erzeugt.
- [ ] Schutz vor Überschreiben verstanden.
- [ ] CSV in LibreOffice Calc geöffnet.
- [ ] Platzfresser-Spalten erkannt.
- Zeit:
- Irrwege oder unklare Wörter:

### 4. Hilfe verwenden

- [ ] `?2` oder `g2` in der Startseite gefunden.
- [ ] `datenbanktool help folders --level guided` verstanden.
- [ ] Hilfe beantwortete die konkrete Frage.
- Fehlende Erklärung:

### 5. Sicherheitsverständnis

- [ ] Verstanden, dass der Bericht keine Dateien löscht oder verschiebt.
- [ ] Verstanden, dass Rot nur Prüfbedarf und keinen Schaden bedeutet.
- [ ] Keine gefährliche Fehlannahme festgestellt.

### 6. Fehlerfall

CSV-Befehl ein zweites Mal ohne `--overwrite-report` ausführen.

- [ ] Fehlermeldung verstanden.
- [ ] Sicheren nächsten Schritt erkannt.
- [ ] Keine vorhandene Datei wurde unbemerkt ersetzt.

## Bewertung

Jeweils 1 = unverständlich, 5 = sehr verständlich.

- Orientierung: 1 / 2 / 3 / 4 / 5
- Hilfetexte: 1 / 2 / 3 / 4 / 5
- Sicherheitsverständnis: 1 / 2 / 3 / 4 / 5
- CSV-Ergebnis: 1 / 2 / 3 / 4 / 5
- Gesamtvertrauen: 1 / 2 / 3 / 4 / 5

## Abnahmekriterien

- [ ] Mindestens fünf der sechs Aufgaben ohne technische Fremdhilfe abgeschlossen.
- [ ] Keine kritische Fehlannahme zu Löschen, Verschieben oder Überschreiben.
- [ ] Durchschnittliche Bewertung mindestens 4 von 5.
- [ ] Jeder Abbruch und Fehler ließ einen sicheren nächsten Schritt erkennen.

## Ergebnis

- [ ] BESTANDEN
- [ ] NICHT BESTANDEN

Begründung und konkrete Verbesserungspunkte:
"""


def run_acceptance(
    profile: AcceptanceProfile,
    workspace: Path,
    *,
    seed: int = 20260804,
    max_seconds: float | None = None,
    max_python_memory_mib: int | None = None,
) -> AcceptanceResult:
    profile.validate()
    target = _safe_workspace(workspace)
    dataset = target / "dataset"
    database = target / "index.sqlite3"
    csv_path = target / "ordneruebersicht.csv"
    json_path = target / "acceptance-result.json"
    markdown_path = target / "acceptance-report.md"
    checklist_path = target / "NOVICE_ACCEPTANCE_CHECKLIST.md"
    dataset.mkdir()

    limit_seconds = max_seconds if max_seconds is not None else profile.max_seconds
    limit_memory_mib = (
        max_python_memory_mib
        if max_python_memory_mib is not None
        else profile.max_python_memory_mib
    )
    if limit_seconds <= 0:
        raise ValueError("Zeitgrenze muss positiv sein")
    if limit_memory_mib < 1:
        raise ValueError("Speichergrenze muss mindestens 1 MiB sein")

    phases: dict[str, float] = {}
    started = time.perf_counter()
    tracemalloc.start()
    try:
        phase = time.perf_counter()
        created_count, logical_size = _create_dataset(dataset, profile, seed)
        phases["Testbestand erzeugen"] = time.perf_counter() - phase

        phase = time.perf_counter()
        before_manifest = _source_manifest(dataset)
        phases["Vorvalidierung"] = time.perf_counter() - phase

        phase = time.perf_counter()
        index_result = build_index(
            IndexBuildOptions(
                root=dataset,
                database=database,
                hash_duplicates=False,
                batch_size=500,
            )
        )
        phases["Index aufbauen"] = time.perf_counter() - phase

        phase = time.perf_counter()
        folder_page = analyse_folders(
            database,
            filters=FolderFilter(
                page_size=200,
                top_files=3,
                sort_by="size",
                descending=True,
            ),
            all_rows=True,
        )
        phases["Ordner auswerten"] = time.perf_counter() - phase

        phase = time.perf_counter()
        export_folder_csv(folder_page, csv_path)
        phases["CSV exportieren"] = time.perf_counter() - phase

        phase = time.perf_counter()
        after_manifest = _source_manifest(dataset)
        phases["Nachvalidierung"] = time.perf_counter() - phase
        _, peak_python = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()

    duration = time.perf_counter() - started
    process_rss = _process_max_rss_bytes()
    csv_rows = _csv_data_rows(csv_path)
    csv_has_bom = csv_path.read_bytes().startswith(b"\xef\xbb\xbf")
    folder_help = "\n".join(render_topic(get_topic("folders"), "guided"))
    memory_limit_bytes = limit_memory_mib * 1024 * 1024

    checks = (
        _check(
            "Testdateien vollständig erzeugt",
            created_count == profile.file_count,
            created_count,
            profile.file_count,
            "Deterministischer Dateibestand muss vollständig sein.",
        ),
        _check(
            "Index vollständig",
            index_result.status == "complete",
            index_result.status,
            "complete",
            "Nur ein abgeschlossener Index ist auswertbar.",
        ),
        _check(
            "Alle Dateien importiert",
            index_result.imported_count == profile.file_count,
            index_result.imported_count,
            profile.file_count,
            "Dateizahl im Index muss dem Testbestand entsprechen.",
        ),
        _check(
            "Keine Indexfehler",
            index_result.error_count == 0,
            index_result.error_count,
            0,
            "Der reproduzierbare Bestand darf keine Lesefehler erzeugen.",
        ),
        _check(
            "Ordnerauswertung vorhanden",
            folder_page.total_rows > 0,
            folder_page.total_rows,
            "> 0",
            "Mindestens die Wurzel und erzeugte Ordner müssen erscheinen.",
        ),
        _check(
            "CSV enthält alle Ordner",
            csv_rows == folder_page.total_rows,
            csv_rows,
            folder_page.total_rows,
            "Vollständiger Export darf keine Seite abschneiden.",
        ),
        _check(
            "CSV für LibreOffice codiert",
            csv_has_bom,
            csv_has_bom,
            True,
            "UTF-8-BOM erleichtert die korrekte Zeichenerkennung.",
        ),
        _check(
            "Quelldateien unverändert",
            before_manifest == after_manifest,
            len(after_manifest),
            len(before_manifest),
            "Pfad, Größe und Änderungszeit müssen identisch bleiben.",
        ),
        _check(
            "CSV-Hilfe vorhanden",
            "CSV" in folder_help and "all-pages" in folder_help,
            "CSV und all-pages" if "CSV" in folder_help else "CSV fehlt",
            "beide Begriffe",
            "Laienhilfe muss vollständigen Tabellenexport erklären.",
        ),
        _check(
            "Laufzeitgrenze",
            duration <= limit_seconds,
            f"{duration:.3f} s",
            f"<= {limit_seconds:.3f} s",
            "Gesamtlaufzeit umfasst Erzeugung, Index, Auswertung und Export.",
        ),
        _check(
            "Python-Speichergrenze",
            peak_python <= memory_limit_bytes,
            f"{peak_python} Byte",
            f"<= {memory_limit_bytes} Byte",
            "Gemessen wird der Python-Spitzenspeicher mit tracemalloc.",
        ),
    )
    passed = all(check.passed for check in checks)
    result = AcceptanceResult(
        profile=profile.name,
        seed=seed,
        workspace=str(target),
        file_count=created_count,
        folder_count=profile.folder_count,
        logical_size_bytes=logical_size,
        duration_seconds=duration,
        phase_seconds=phases,
        peak_python_memory_bytes=peak_python,
        process_max_rss_bytes=process_rss,
        imported_count=index_result.imported_count,
        index_error_count=index_result.error_count,
        folder_rows=folder_page.total_rows,
        checks=checks,
        passed=passed,
        manual_novice_status="pending-real-person",
        json_report=str(json_path),
        markdown_report=str(markdown_path),
        novice_checklist=str(checklist_path),
    )
    _atomic_write(
        json_path,
        json.dumps(result.to_dict(), ensure_ascii=False, indent=2) + "\n",
    )
    _atomic_write(markdown_path, _markdown_report(result, profile))
    _atomic_write(checklist_path, _novice_checklist(profile, target))
    return result
