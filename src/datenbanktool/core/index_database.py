"""Öffentliche Fassade für den versionierten SQLite-Index."""

from datenbanktool.core.index_build import (
    build_index,
    inspect_index,
    integrity_rows,
    iter_paths,
    repair_index,
)
from datenbanktool.core.index_store import IndexDatabase
from datenbanktool.core.index_types import (
    DEFAULT_BATCH_SIZE,
    SCHEMA_VERSION,
    IndexBuildOptions,
    IndexBuildResult,
    IndexErrorBase,
    IndexStatus,
    RepairResult,
    ResumeCheckpointError,
    UnsupportedSchemaError,
    normalise_database_path,
    source_fingerprint,
    utc_now,
)

__all__ = [
    "DEFAULT_BATCH_SIZE",
    "SCHEMA_VERSION",
    "IndexBuildOptions",
    "IndexBuildResult",
    "IndexDatabase",
    "IndexErrorBase",
    "IndexStatus",
    "RepairResult",
    "ResumeCheckpointError",
    "UnsupportedSchemaError",
    "build_index",
    "inspect_index",
    "integrity_rows",
    "iter_paths",
    "normalise_database_path",
    "repair_index",
    "source_fingerprint",
    "utc_now",
]
