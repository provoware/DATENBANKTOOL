from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Callable


@dataclass(frozen=True, slots=True)
class ProgressEvent:
    phase: str
    kind: str
    message: str
    current: int | None = None
    total: int | None = None
    session_id: int | None = None
    details: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


ProgressCallback = Callable[[ProgressEvent], None]


def dispatch_progress(callback: ProgressCallback | None, event: ProgressEvent) -> None:
    if callback is None:
        return
    try:
        callback(event)
    except Exception:
        # Fortschrittsanzeige darf einen sicheren Indexlauf nicht beschädigen.
        return
