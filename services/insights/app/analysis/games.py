"""Game records as the analyses see them, built from the games service's JSON."""

import statistics
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from app.analysis.stats import actual_score, expected_score

SESSION_GAP = timedelta(minutes=30)
# Half-width of the window of the player's own games used to estimate their true strength.
STRENGTH_WINDOW = 25


@dataclass
class GameRecord:
    id: int
    time_class: str
    ended_at: datetime
    color: str
    result: str
    result_detail: str
    rating: int | None
    opponent_rating: int | None
    base_seconds: int | None
    increment_seconds: int | None
    ply_count: int
    clocks: list[int] | None  # tenths of a second after each ply
    # Filled in by assign_sessions().
    session_id: int = 0
    session_index: int = 0  # 1 = first game of the session
    previous_result: str | None = None  # result of the previous game in the same session
    previous_results: list[str] = field(default_factory=list)  # all earlier games in session
    # Filled in by assign_strength(): smoothed rating around this game.
    strength: float | None = None

    @property
    def residual(self) -> float:
        """Actual minus expected score, using the smoothed strength (see assign_strength)."""
        own = self.strength if self.strength is not None else self.rating
        return actual_score(self.result) - expected_score(own, self.opponent_rating)

    @property
    def own_clocks(self) -> list[int]:
        if not self.clocks:
            return []
        return self.clocks[0::2] if self.color == "white" else self.clocks[1::2]

    @classmethod
    def from_api(cls, data: dict) -> "GameRecord":
        clocks = None
        if data.get("clocks"):
            clocks = [int(c) for c in data["clocks"].split(",") if c]
        return cls(
            id=data["id"],
            time_class=data["time_class"],
            ended_at=datetime.fromisoformat(data["ended_at"]),
            color=data["player_color"],
            result=data["result"],
            result_detail=data.get("result_detail", ""),
            rating=data.get("player_rating"),
            opponent_rating=data.get("opponent_rating"),
            base_seconds=data.get("base_seconds"),
            increment_seconds=data.get("increment_seconds"),
            ply_count=data.get("ply_count", 0),
            clocks=clocks,
        )


def assign_strength(games: list[GameRecord]) -> None:
    """Estimate pre-game ratings and the player's true strength at each game.

    chess.com reports ratings *after* the game, so using them directly leaks the result
    into the expectation. The player's pre-game rating is the post-game rating of their
    previous game in the same time class; the opponent's pre-game rating is approximated by
    adding back the points they lost or gained (rating changes are close to zero-sum).

    Even the pre-game rating is noisy (a little too low after losses, too high after wins),
    which fakes a "bounce back after a loss" effect. So expectation uses the median
    pre-game rating of the surrounding games (STRENGTH_WINDOW before and after).
    """
    by_tc: dict[str, list[GameRecord]] = {}
    for g in sorted(games, key=lambda g: g.ended_at):
        if g.rating is not None:
            by_tc.setdefault(g.time_class, []).append(g)
    for gs in by_tc.values():
        pre: list[int] = []
        for i, g in enumerate(gs):
            before = gs[i - 1].rating if i > 0 else g.rating
            pre.append(before)
            if g.opponent_rating is not None:
                g.opponent_rating = g.opponent_rating + (g.rating - before)
        for i, g in enumerate(gs):
            lo, hi = max(0, i - STRENGTH_WINDOW), min(len(gs), i + STRENGTH_WINDOW + 1)
            g.strength = statistics.median(pre[lo:hi])


def assign_sessions(games: list[GameRecord]) -> list[GameRecord]:
    """Sort games by time and group them into sessions.

    A new session starts when the gap between the end of one game and the end of the next
    is longer than the next game's own maximum duration plus SESSION_GAP. Daily
    (correspondence) games are never part of a session.
    """
    ordered = sorted(games, key=lambda g: g.ended_at)
    assign_strength(ordered)
    session_id = 0
    prev: GameRecord | None = None
    history: list[str] = []
    for g in ordered:
        if g.time_class == "daily" or g.base_seconds is None:
            g.session_id, g.session_index, g.previous_result = -1, 0, None
            continue
        max_duration = timedelta(seconds=2 * g.base_seconds + 2 * 60 * (g.increment_seconds or 0))
        if prev is None or g.ended_at - prev.ended_at > max_duration + SESSION_GAP:
            session_id += 1
            history = []
        g.session_id = session_id
        g.session_index = len(history) + 1
        g.previous_result = history[-1] if history else None
        g.previous_results = list(history)
        history.append(g.result)
        prev = g
    return ordered
