from datetime import datetime, timedelta

from conftest import api_game, interleave

from app.analysis.clock import analyse_clock, clock_profile
from app.analysis.games import GameRecord, prepare

T0 = datetime(2026, 10, 1, 18, 0)
N = 30  # own moves per synthetic game


def calm_clocks() -> list[int]:
    return [1800 - 40 * k for k in range(N)]  # 3+0, ends with 640 tenths


def trouble_clocks(spike: bool = False) -> list[int]:
    own = [1800 - 80 * k for k in range(N)]
    if spike:
        own = [1790] * 3 + [1000] + [1000 - 50 * k for k in range(1, N - 3)]
    return [max(c, 30) for c in own]


def game(i: int, own: list[int], *, result: str, opp=None, **kw) -> dict:
    opp = opp or [1790 - 10 * k for k in range(N)]
    return api_game(
        i,
        ended_at=T0 + timedelta(hours=i),
        clocks=interleave(own, opp),
        result=result,
        **kw,
    )


def records(raw):
    return prepare([GameRecord.from_api(g) for g in raw])


def test_entry_needs_five_more_moves():
    g = GameRecord.from_api(game(1, trouble_clocks(), result="loss"))
    cg = analyse_clock(g)
    assert cg.entry_move is not None
    assert cg.self_inflicted is True
    # same pace, but the game ends right after the clock gets low: no entry
    short = [1800 - 70 * k for k in range(25)]
    cg2 = analyse_clock(GameRecord.from_api(game(2, short, result="loss")))
    assert cg2.entry_move is None
    assert analyse_clock(GameRecord.from_api(api_game(3, ended_at=T0))) is None


def test_clock_profile_and_score_contrast():
    raw = []
    for i in range(120):
        raw.append(game(i, calm_clocks(), result="win"))
    for i in range(120, 240):
        raw.append(
            game(
                i,
                trouble_clocks(spike=i % 2 == 0),
                result="loss",
                termination="opp won on time" if i % 3 == 0 else "opp won by resignation",
                final_material=4 if i % 6 == 0 else -1,
            )
        )
    raw.append(
        game(999, calm_clocks(), result="win", termination="me won on time", final_material=-5)
    )
    drafts = clock_profile(records(raw))
    profile = next(d for d in drafts if d.analysis_key == "clock_profile")
    d = profile.details
    assert d["entry"]["count"] == 120
    assert d["entry"]["rate"] == 120 / 241
    assert d["self_inflicted"]["rate"] == 1.0
    assert d["onset_move"]["median"] > 10
    assert set(d["time_sinks"]["main_cause_share"]) == {"opening", "spikes", "drain"}
    assert d["pace"]["wins"]["20"] > d["pace"]["losses"]["20"]
    assert d["flags"]["lost_on_time"]["winning"] == 20
    assert d["flags"]["won_on_time"]["losing"] == 1
    # Calm wins keep 58% of the clock after move 20: suggested floor 55%.
    assert d["checkpoint"]["move"] == 20
    assert d["checkpoint"]["min_share"] == 0.55
    assert d["checkpoint"]["wins"]["rate"] == 1.0
    assert d["checkpoint"]["trouble_games"]["count"] == 0
    title, summary = profile.text("profile")
    assert "mostly self-inflicted" in title
    assert "Main cause" in summary

    score = next(d for d in drafts if d.analysis_key == "time_trouble_score")
    assert score.contrast.effect < 0
    assert "costs you" in score.text("finding")[0]
    assert "(exploratory)" in score.text("exploratory")[0]
    assert "no score difference" in score.text("no_effect")[0]


def test_small_samples_say_so():
    raw = [game(i, calm_clocks(), result="win") for i in range(25)]
    raw += [game(100 + i, trouble_clocks(), result="loss") for i in range(5)]
    drafts = clock_profile(records(raw))
    profile = next(d for d in drafts if d.analysis_key == "clock_profile")
    assert profile.details["early_estimate"] is True
    assert profile.details["time_sinks"] == {}
    assert profile.details["checkpoint"] is None  # fewer than 30 wins
    assert "Early estimate" in profile.text("profile")[1]
    score = next(d for d in drafts if d.analysis_key == "time_trouble_score")
    assert "not enough games" in score.text("not_enough_data")[0]


def test_too_few_games_in_a_time_control_gives_no_cards():
    assert clock_profile(records([game(i, calm_clocks(), result="win") for i in range(5)])) == []
