from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DuplicateCandidate:
    file_id: int
    path: str
    size_bytes: int
    modified_utc: str
    warning_count: int = 0
    is_preferred_location: bool = False


@dataclass(frozen=True)
class CandidateScore:
    candidate: DuplicateCandidate
    score: int
    evidence: tuple[str, ...]


@dataclass(frozen=True)
class DuplicateDecision:
    keep_file_id: int | None
    ranked: tuple[CandidateScore, ...]
    confidence: str
    requires_user_review: bool
    explanation: str


def _score(candidate: DuplicateCandidate) -> CandidateScore:
    score = 0
    evidence: list[str] = []
    if candidate.is_preferred_location:
        score += 40
        evidence.append("liegt in einem bevorzugten Original-/Arbeitsordner")
    if candidate.warning_count == 0:
        score += 20
        evidence.append("keine Namenswarnung")
    else:
        score -= min(20, candidate.warning_count * 5)
        evidence.append(f"{candidate.warning_count} Namenshinweis(e)")
    if "backup" in candidate.path.casefold() or "kopie" in candidate.path.casefold():
        score -= 15
        evidence.append("Pfad deutet auf Backup/Kopie")
    else:
        score += 10
        evidence.append("Pfad enthält keinen offensichtlichen Backup-/Kopie-Hinweis")
    if candidate.size_bytes > 0:
        score += 5
        evidence.append("nicht-leere Datei")
    return CandidateScore(candidate, score, tuple(evidence))


def propose_duplicate_keeper(candidates: tuple[DuplicateCandidate, ...]) -> DuplicateDecision:
    """Rank exact-duplicate candidates; never returns a deletion decision."""
    if len(candidates) < 2:
        return DuplicateDecision(
            keep_file_id=None,
            ranked=tuple(_score(item) for item in candidates),
            confidence="none",
            requires_user_review=True,
            explanation="Für eine Duplikatentscheidung werden mindestens zwei Kandidaten benötigt.",
        )
    sizes = {item.size_bytes for item in candidates}
    if len(sizes) != 1:
        return DuplicateDecision(
            keep_file_id=None,
            ranked=tuple(sorted((_score(item) for item in candidates), key=lambda item: item.score, reverse=True)),
            confidence="none",
            requires_user_review=True,
            explanation="Kandidaten haben unterschiedliche Größen und werden deshalb nicht als exakte Gruppe freigegeben.",
        )
    ranked = tuple(
        sorted((_score(item) for item in candidates), key=lambda item: (-item.score, item.candidate.path.casefold()))
    )
    lead = ranked[0]
    runner_up = ranked[1]
    margin = lead.score - runner_up.score
    if margin >= 30:
        confidence = "high"
    elif margin >= 10:
        confidence = "medium"
    else:
        confidence = "low"
    return DuplicateDecision(
        keep_file_id=lead.candidate.file_id,
        ranked=ranked,
        confidence=confidence,
        requires_user_review=True,
        explanation=(
            f"Vorschlag: Datei #{lead.candidate.file_id} behalten. "
            f"Bewertungsabstand {margin} Punkte; Löschaktionen werden ausdrücklich nicht erzeugt."
        ),
    )
