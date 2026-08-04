from __future__ import annotations

from pathlib import Path

from datenbanktool.core.models import FileCategory

_EXTENSION_GROUPS: dict[FileCategory, frozenset[str]] = {
    FileCategory.AUDIO: frozenset({".aac", ".aiff", ".alac", ".flac", ".m4a", ".mid", ".midi", ".mp3", ".ogg", ".opus", ".wav", ".wma"}),
    FileCategory.VIDEO: frozenset({".avi", ".flv", ".m2ts", ".m4v", ".mkv", ".mov", ".mp4", ".mpeg", ".mpg", ".ts", ".webm", ".wmv"}),
    FileCategory.IMAGE: frozenset({".avif", ".bmp", ".gif", ".heic", ".jpeg", ".jpg", ".png", ".svg", ".tif", ".tiff", ".webp"}),
    FileCategory.TEXT: frozenset({".csv", ".ini", ".log", ".md", ".rst", ".toml", ".tsv", ".txt", ".yaml", ".yml"}),
    FileCategory.ARCHIVE: frozenset({".7z", ".bz2", ".gz", ".rar", ".tar", ".tgz", ".xz", ".zip", ".zst"}),
    FileCategory.CODE: frozenset({".c", ".cc", ".cpp", ".css", ".go", ".h", ".hpp", ".html", ".java", ".js", ".json", ".jsx", ".kt", ".lua", ".php", ".py", ".rb", ".rs", ".sh", ".sql", ".ts", ".tsx", ".xml"}),
    FileCategory.DOCUMENT: frozenset({".doc", ".docx", ".epub", ".odf", ".odp", ".ods", ".odt", ".pdf", ".ppt", ".pptx", ".rtf", ".xls", ".xlsx"}),
}


def classify_path(path: Path) -> FileCategory:
    suffix = path.suffix.casefold()
    for category, extensions in _EXTENSION_GROUPS.items():
        if suffix in extensions:
            return category
    return FileCategory.OTHER
