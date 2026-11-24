from datetime import datetime, timedelta

from app.analysis.games import GameRecord, prepare
from app.analysis.habits import form, opening_time, premoves, time_of_day, warm_up
from tests.conftest import api_game, interleave

T0 = datetime(2026, 1, 5, 9, 0)


def records(raw: list[dict]) -> list[GameRecord]:
    out = []
    for r in raw:
        opening = r.pop("opening", None)
        g = GameRecord.from_api(r)
        g.opening = opening
        out.append(g)
    return prepare(out)


def sessions(n: int, results_first: str, results_later: str, start: datetime = T0) -> list[dict]:
    """n sessions of 4 back-to-back blitz games, one per day."""
    raw, i = [], 0
    for s in range(n):
        day = start + timedelta(days=s)
        for k in range(4):
            res = results_first if k == 0 else results_later
            raw.append(api_game(i, ended_at=day + timedelta(minutes=5 * k), result=res))
            i += 1
    return raw


def test_warm_up_compares_first_games_with_later_ones():
    [d] = warm_up(records(sessions(120, "loss", "win")))
    assert d.analysis_key == "warm_up" and d.time_class == "blitz"
    assert d.contrast is not None
    assert d.contrast.n_a == 120 and d.contrast.n_b == 360
    assert d.contrast.effect < 0
    title, _ = d.text("finding")
    assert "first game of a session costs you" in title


def test_warm_up_without_enough_sessions():
    [d] = warm_up(records(sessions(10, "loss", "win")))
    title, summary = d.text("not_enough_data")
    assert "not enough sessions" in title and "10 first" in summary


def test_time_of_day_flags_a_bad_window():
    # Mornings lost, evenings won: 30 sessions each, 4 games per session.
    raw = sessions(30, "loss", "loss", start=T0.replace(hour=8))
    raw += [
        dict(g, id=g["id"] + 1000)
        for g in sessions(30, "win", "win", start=T0.replace(hour=20) + timedelta(days=40))
    ]
    [d] = time_of_day(records(raw))
    windows = {w["window"]: w for w in d.details["windows"]}
    assert windows["morning"]["games"] == 120 and windows["evening"]["games"] == 120
    assert windows["morning"]["verdict"] == "worse"
    assert sum(d.details["games_by_hour"]) == 240
    title, summary = d.text("profile")
    assert "below your level in the morning" in title
    assert "Bonferroni" in summary


def test_time_of_day_with_too_few_games():
    [d] = time_of_day(records(sessions(6, "win", "loss")))
    assert all(w["verdict"] == "not_enough_data" for w in d.details["windows"])
    assert "not enough games" in d.text("profile")[0]


def clocks_spending(per_move: list[int], base: int = 1800) -> str:
    """Own clock after each move (tenths) for the given seconds-per-move, opponent mirrors."""
    own, c = [], base
    for s in per_move:
        c -= s * 10
        own.append(max(c, 0))
    return interleave(own, own)


def test_opening_time_by_opening():
    raw = []
    for i in range(60):
        fast = i % 2 == 0
        moves = [2] * 12 + [3] * 20 if fast else [8] * 12 + [3] * 20
        g = api_game(
            i,
            ended_at=T0 + timedelta(hours=i),
            result="win" if fast else "loss",
            clocks=clocks_spending(moves),
        )
        g["opening"] = "Italian Game: Two Knights" if fast else "Caro-Kann Defense: Advance"
        raw.append(g)
    [d] = opening_time(records(raw))
    ops = {o["opening"]: o for o in d.details["openings"]}
    assert set(ops) == {"Italian Game", "Caro-Kann Defense"}
    assert ops["Caro-Kann Defense"]["used"] > ops["Italian Game"]["used"]
    title, summary = d.text("profile")
    assert "of your clock is gone by move 12" in title
    assert "Most in the Caro-Kann Defense" in summary


def test_premoves_only_when_there_is_a_spike():
    def game(i, tenths_last: int) -> dict:
        # 20 normal moves of 3 s, then 15 moves taking `tenths_last` tenths each.
        own, c = [], 600
        for _ in range(20):
            c -= 30
            own.append(c)
        for _ in range(15):
            c -= tenths_last
            own.append(c)
        return api_game(
            i,
            ended_at=T0 + timedelta(hours=i),
            base=60,
            time_class="bullet",
            clocks=interleave(own, own),
            result="win" if i % 2 else "loss",
        )

    premover = records([game(i, 1) for i in range(30)])
    [d] = premoves(premover)
    assert d.analysis_key == "premoves"
    assert 0.3 < d.details["rate"] < 0.5
    assert "premoves" in d.text("profile")[0]

    # 0.2 s moves are not premoves: no spike at 0.1 s, so no card.
    assert premoves(records([game(i, 2) for i in range(30)])) == []


def test_form_by_month():
    raw = []
    for i in range(90):
        month_start = datetime(2026, 1 + i // 30, 1)
        raw.append(
            api_game(
                i, ended_at=month_start + timedelta(hours=i % 30), rating=1900 + 50 * (i // 30)
            )
        )
    [d] = form(records(raw))
    months = d.details["months"]
    assert [m["month"] for m in months] == ["2026-01", "2026-02", "2026-03"]
    assert [m["games"] for m in months] == [30, 30, 30]
    assert d.text("profile")[0] == "Blitz: rating 1900 → 2000 since 2026-01"


def test_opening_families_from_chesscom_names():
    from app.analysis.habits import _family

    assert _family("Caro Kann Defense Exchange Variation 3...cxd5 4.Nf3") == "Caro Kann Defense"
    assert (
        _family("Queens Pawn Opening Chigorin Variation 2...Nf6 3.Bf4")
        == "Queens Pawn Opening Chigorin Variation"
    )
    assert _family("Queens Pawn Opening 1...c6") == "Queens Pawn Opening"
    assert _family("Modern Defense with 1 d4 2.Nc3 Bg7") == "Modern Defense"
    assert _family("Italian Game: Two Knights") == "Italian Game"
    assert _family(None) is None
