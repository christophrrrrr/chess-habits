from datetime import datetime, timedelta

import pytest
from conftest import api_game, session_games

from app.analysis.analyses import reached_time_trouble, session_fatigue, tilt, time_trouble
from app.analysis.games import GameRecord, assign_sessions
from app.analysis.stats import actual_score, compare, expected_score, pct

T0 = datetime(2026, 10, 1, 18, 0)


def records(raw: list[dict]) -> list[GameRecord]:
    return assign_sessions([GameRecord.from_api(g) for g in raw])


def test_expected_score():
    assert expected_score(2000, 2000) == pytest.approx(0.5)
    assert expected_score(2400, 2000) == pytest.approx(0.909, abs=0.001)
    assert expected_score(None, 2000) == 0.5
    assert actual_score("win") == 1.0
    assert actual_score("draw") == 0.5
    assert actual_score("loss") == 0.0


def test_compare_confidence_levels():
    assert compare([0.5] * 10, [0.0] * 10).confidence == "insufficient"
    assert compare([], [0.1, 0.2]).confidence == "insufficient"
    strong = compare([-0.5, -0.4] * 40, [0.1, 0.2] * 40)
    assert strong.confidence == "high"
    assert strong.effect == pytest.approx(-0.6)
    assert strong.ci_low < strong.effect < strong.ci_high
    noise = compare([0.5, -0.5] * 40, [0.5, -0.5] * 40)
    assert noise.confidence == "low"
    assert compare([0.1] * 40, [0.1] * 40).confidence == "low"
    assert compare([0.2] * 40, [0.1] * 40).confidence == "high"
    assert pct(-0.061) == "-6.1"


def test_sessions_are_split_by_gaps_and_skip_daily():
    raw = session_games(1, T0, ["win", "loss", "win"])
    raw += session_games(10, T0 + timedelta(hours=5), ["loss", "loss"])
    raw.append(api_game(99, ended_at=T0 + timedelta(minutes=7), time_class="daily", base=None))
    games = {g.id: g for g in records(raw)}
    assert [games[i].session_index for i in (1, 2, 3)] == [1, 2, 3]
    assert games[1].session_id != games[10].session_id
    assert games[3].previous_result == "loss"
    assert games[11].previous_results == ["loss"]
    assert games[10].previous_result is None
    assert games[99].session_id == -1


def test_tilt_detects_drop_after_losses():
    raw = []
    for s in range(40):
        # win, loss, then a loss again (after loss) / win otherwise
        raw += session_games(s * 10, T0 + timedelta(days=s), ["win", "loss", "loss", "win"])
        raw += session_games(s * 10 + 5, T0 + timedelta(days=s, hours=6), ["win", "win", "win"])
    findings = tilt(records(raw))
    assert len(findings) == 1
    f = findings[0]
    assert f.time_class == "blitz"
    assert f.comparison.effect < 0
    assert f.comparison.significant
    assert "worse right after a loss" in f.title
    assert f.details["after_two_losses_n"] == 40


def test_tilt_insufficient_and_no_effect():
    few = tilt(records(session_games(1, T0, ["loss", "win", "loss", "win"])))
    assert few[0].comparison.confidence == "insufficient"
    assert "not enough" in few[0].title

    raw = []
    for s in range(60):
        raw += session_games(s * 10, T0 + timedelta(days=s), ["loss", "win", "win", "loss", "loss"])
    neutral = tilt(records(raw))[0]
    assert neutral.comparison.confidence in ("low", "medium", "high")


def test_session_fatigue_buckets():
    raw = []
    for s in range(15):
        results = ["win"] * 5 + ["loss"] * 5
        raw += session_games(s * 100, T0 + timedelta(days=s), results)
    f = session_fatigue(records(raw))[0]
    assert f.comparison.effect == pytest.approx(-1.0)
    assert "drop in long sessions" in f.title
    assert f.details["buckets"]["1-2"]["n"] == 30
    assert f.details["buckets"]["11+"]["n"] == 0


def _clocks(min_tenths: int) -> str:
    # 10 plies; the player (white) ends at min_tenths
    own = [1800, 1500, 1200, 900, min_tenths]
    opp = [1790, 1600, 1400, 1300, 1200]
    return ",".join(str(c) for pair in zip(own, opp, strict=True) for c in pair)


def test_time_trouble():
    g = GameRecord.from_api(api_game(1, ended_at=T0, clocks=_clocks(100)))
    assert reached_time_trouble(g) is True  # 10.0s < 18s
    g = GameRecord.from_api(api_game(2, ended_at=T0, clocks=_clocks(400)))
    assert reached_time_trouble(g) is False
    assert reached_time_trouble(GameRecord.from_api(api_game(3, ended_at=T0))) is None

    raw = []
    for k in range(40):
        raw.append(
            api_game(
                k,
                ended_at=T0 + timedelta(days=k),
                clocks=_clocks(100),
                result="loss",
                detail="timeout" if k % 2 else "resigned",
            )
        )
        raw.append(api_game(100 + k, ended_at=T0 + timedelta(days=k, hours=3), clocks=_clocks(900)))
    f = time_trouble(records(raw))[0]
    assert f.details["share"] == pytest.approx(0.5)
    assert f.details["timeout_losses"] == 20
    assert "costs you points" in f.title


def test_black_clocks_and_unknown_time_classes():
    g = GameRecord.from_api(api_game(1, ended_at=T0, clocks="10,20,30,40", color="black"))
    assert g.own_clocks == [20, 40]
    assert tilt(records([api_game(1, ended_at=T0, time_class="daily", base=None)])) == []


def test_strength_uses_pre_game_ratings():
    # chess.com reports post-game ratings: 2000 -> win -> 2010 -> loss -> 2000
    raw = [
        api_game(1, ended_at=T0, rating=2000, opp=2000),
        api_game(2, ended_at=T0 + timedelta(minutes=5), result="win", rating=2010, opp=1990),
        api_game(3, ended_at=T0 + timedelta(minutes=10), result="loss", rating=2000, opp=2010),
    ]
    games = {g.id: g for g in records(raw)}
    # opponent of game 2 had 2000 before the game (lost 10 points)
    assert games[2].opponent_rating == 2000
    # opponent of game 3 had 2000 before the game (gained 10 points)
    assert games[3].opponent_rating == 2000
    assert games[3].strength == 2000
    assert games[2].residual == pytest.approx(0.5)
