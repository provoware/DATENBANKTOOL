from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath


@dataclass(frozen=True)
class TestFile:
    path: str
    size_bytes: int
    category: str
    duplicate_key: str | None = None


@dataclass(frozen=True)
class ValidationResult:
    check_id: str
    title: str
    passed: bool
    detail: str


@dataclass(frozen=True)
class TestRunReport:
    files_seen: int
    total_bytes: int
    passed: int
    failed: int
    warnings: int
    results: tuple[ValidationResult, ...]


DEFAULT_TEST_FOLDER = (
    TestFile("Fotos/IMG_0001.JPG", 2_400_000, "image", "photo-a"),
    TestFile("Fotos/IMG_0001_Kopie.JPG", 2_400_000, "image", "photo-a"),
    TestFile("Videos/clip_01.mp4", 48_000_000, "video"),
    TestFile("Musik/demo_mix.wav", 16_000_000, "audio"),
    TestFile("Dokumente/Bericht final.docx", 82_000, "document"),
    TestFile("Dokumente/notizen.txt", 4_000, "document"),
    TestFile("Projekte/toolprojekt.zip", 12_000_000, "archive"),
    TestFile("System/cache.tmp", 130_000, "system"),
    TestFile("Unklar/datei_ohne_endung", 24_000, "unknown"),
)


def run_validation(files: tuple[TestFile, ...] = DEFAULT_TEST_FOLDER) -> TestRunReport:
    """Validate planning rules entirely in memory; never touches original files."""
    results: list[ValidationResult] = []
    paths = [PurePosixPath(item.path) for item in files]

    results.append(ValidationResult(
        "unique-paths",
        "Keine kollidierenden Testpfade",
        len(paths) == len(set(paths)),
        "Jeder simulierte Pfad muss eindeutig bleiben.",
    ))
    results.append(ValidationResult(
        "non-negative-size",
        "Dateigrößen plausibel",
        all(item.size_bytes >= 0 for item in files),
        "Negative Dateigrößen werden vor jedem Workflow abgelehnt.",
    ))
    results.append(ValidationResult(
        "categories",
        "Kategorien vorhanden",
        all(bool(item.category.strip()) for item in files),
        "Jede Testdatei besitzt eine explizite Kategorie.",
    ))
    duplicate_keys = [item.duplicate_key for item in files if item.duplicate_key]
    results.append(ValidationResult(
        "duplicate-sample",
        "Duplikat-Muster prüfbar",
        len(duplicate_keys) > len(set(duplicate_keys)),
        "Der Musterordner enthält mindestens eine absichtliche Duplikatgruppe.",
    ))
    results.append(ValidationResult(
        "mixed-content",
        "Gemischte Sammlung abgedeckt",
        len({item.category for item in files}) >= 6,
        "Bilder, Videos, Audio, Dokumente, Archive und Stör-/Unklarfälle sollen enthalten sein.",
    ))
    results.append(ValidationResult(
        "non-destructive",
        "Nur Simulation",
        True,
        "Das Testlabor arbeitet ausschließlich mit unveränderlichen In-Memory-Testobjekten.",
    ))

    failed = sum(not result.passed for result in results)
    warnings = sum(item.category in {"system", "unknown"} for item in files)
    return TestRunReport(
        files_seen=len(files),
        total_bytes=sum(item.size_bytes for item in files),
        passed=len(results) - failed,
        failed=failed,
        warnings=warnings,
        results=tuple(results),
    )
