"""Game records as the analyses see them, built from the games service's JSON.

Definitions follow docs/definitions.md.
"""

import statistics
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from app.analysis.stats import actual_score, expected_score

# A new session starts when more than this passes between the end of one game and the
# start of the next.
SESSION_GAP = timedelta(minutes=30)
# Half-width of the window of the player's own games used to estimate their true strength.
STRENGTH_WINDOW = 25
# Live games whose estimated duration T_est is at least this long count as classical
# (chess.com files them under rapid).
CLASSICAL_FROM_SECONDS = 1500


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
    started_at: datetime | None = None
    termination: str | None = None
    final_material: int | None = None
    opening: str | None = None  # chess.com's opening name, e.g. "Italian Game: Two Knights"
    # Deep analysis from the player's browser (None until it has run for this game).
    position_keys: list[str] | None = None  # position before own moves 1-20
    engine_moves: list[dict] | None = None  # Stockfish rows for own moves (schemas.EngineMove)
    final_cp: int | None = None  # final position, centipawns from the player's side
    # Filled in by prepare().
    session_id: int = 0
    session_index: int = 0  # 1 = first game of the session, 0 = not in a session (daily)
    previous: "GameRecord | None" = None  # previous game in the same session
    previous_results: list[str] = field(default_factory=list)
    next_start_gap: timedelta | None = None  # end of this game -> start of the next one
    strength: float | None = None

    # ---- results ------------------------------------------------------------------------

    @property
    def residual(self) -> float:
        """Actual minus expected score, using the smoothed strength (see assign_strength)."""
        own = self.strength if self.strength is not None else self.rating
        return actual_score(self.result) - expected_score(own, self.opponent_rating)

    @property
    def lost_on_time(self) -> bool:
        return self.result == "loss" and "won on time" in (self.termination or "")

    @property
    def won_on_time(self) -> bool:
        return self.result == "win" and "won on time" in (self.termination or "")

    # ---- time control -------------------------------------------------------------------

    @property
    def t_est(self) -> float | None:
        """Estimated game length per player in seconds: base + 40 x increment."""
        if not self.base_seconds:
            return None
        return self.base_seconds + 40 * (self.increment_seconds or 0)

    @property
    def category(self) -> str:
        """Time class used for findings; long 'rapid' games count as classical."""
        if self.time_class == "rapid" and (self.t_est or 0) >= CLASSICAL_FROM_SECONDS:
            return "classical"
        return self.time_class

    # ---- clocks (tenths of a second) ----------------------------------------------------

    @property
    def own_clocks(self) -> list[int]:
        if not self.clocks:
            return []
        return self.clocks[0::2] if self.color == "white" else self.clocks[1::2]

    @property
    def opponent_clocks(self) -> list[int]:
        if not self.clocks:
            return []
        return self.clocks[1::2] if self.color == "white" else self.clocks[0::2]

    def clock_before(self, k: int) -> float:
        """Own clock (tenths) just before own move k (1-based)."""
        own = self.own_clocks
        return float(self.base_seconds or 0) * 10 if k == 1 else float(own[k - 2])

    def opponent_clock_before(self, k: int) -> float:
        """Opponent's clock (tenths) at the moment the player starts thinking on own move k."""
        opp = self.opponent_clocks
        # White's move k follows black's move k-1; black's move k follows white's move k.
        idx = k - 2 if self.color == "white" else k - 1
        if idx < 0 or idx >= len(opp):
            return float(self.base_seconds or 0) * 10
        return float(opp[idx])

    def time_spent(self, k: int) -> float:
        """Seconds thought on own move k (chess.com adds the increment after the move)."""
        own = self.own_clocks
        return (self.clock_before(k) + 10 * (self.increment_seconds or 0) - own[k - 1]) / 10

    @classmethod
    def from_api(cls, data: dict) -> "GameRecord":
        clocks = None
        if data.get("clocks"):
            clocks = [int(c) for c in data["clocks"].split(",") if c]
        started = data.get("started_at")
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
            started_at=datetime.fromisoformat(started) if started else None,
            termination=data.get("termination"),
            final_material=data.get("final_material"),
            opening=data.get("opening"),
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


def _start(g: GameRecord) -> datetime:
    """Start time; estimated from the end and the maximum duration if the PGN had none."""
    if g.started_at is not None:
        return g.started_at
    return g.ended_at - timedelta(seconds=2 * (g.t_est or 0))


def prepare(games: list[GameRecord]) -> list[GameRecord]:
    """Sort by time, estimate strength and group live games into sessions.

    A session ends when more than SESSION_GAP passes between the end of a game and the start
    of the next one. Daily (correspondence) games are never part of a session.
    """
    ordered = sorted(games, key=lambda g: g.ended_at)
    assign_strength(ordered)
    session_id = 0
    prev: GameRecord | None = None
    history: list[str] = []
    for g in ordered:
        if g.time_class == "daily" or g.base_seconds is None:
            g.session_index = 0
            continue
        gap = _start(g) - prev.ended_at if prev is not None else None
        if prev is not None:
            prev.next_start_gap = gap
        if gap is None or gap > SESSION_GAP:
            session_id += 1
            history = []
            g.previous = None
        else:
            g.previous = prev
        g.session_id = session_id
        g.session_index = len(history) + 1
        g.previous_results = list(history)
        history.append(g.result)
        prev = g
    return ordered
