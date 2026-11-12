"""Types shared by the analyses."""

from collections.abc import Callable
from dataclasses import dataclass, field

from app.analysis.games import GameRecord
from app.analysis.stats import Contrast

CATEGORIES = ("bullet", "blitz", "rapid", "classical")
# Time controls with fewer games than this get no cards at all.
MIN_CATEGORY_GAMES = 20


@dataclass
class FindingDraft:
    """What an analysis produces. Contrasts get their final label only after the
    Benjamini-Hochberg correction over the whole run, so the wording is a function of it."""

    analysis_key: str
    time_class: str
    kind: str  # "contrast" (A vs B with an interval) or "profile" (descriptive card)
    metric: str  # "score" (residual, score points), "share" (proportion) or "profile"
    text: Callable[[str], tuple[str, str]]  # label -> (title, summary)
    contrast: Contrast | None = None
    min_n: int = 0
    sample_size: int = 0
    details: dict = field(default_factory=dict)


@dataclass(frozen=True)
class Analysis:
    key: str
    name: str
    question: str
    run: Callable[[list[GameRecord]], list[FindingDraft]]


def by_category(games: list[GameRecord]) -> dict[str, list[GameRecord]]:
    groups: dict[str, list[GameRecord]] = {}
    for g in games:
        if g.category in CATEGORIES:
            groups.setdefault(g.category, []).append(g)
    return {cat: gs for cat, gs in groups.items() if len(gs) >= MIN_CATEGORY_GAMES}
