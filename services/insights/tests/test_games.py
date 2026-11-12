from datetime import datetime, timedelta

from conftest import api_game, interleave

from app.analysis.games import GameRecord, prepare

T0 = datetime(2026, 10, 1, 18, 0)


def rec(**kw) -> GameRecord:
    return GameRecord.from_api(api_game(1, ended_at=T0, **kw))


def test_time_control_and_category():
    assert rec(base=180, inc=2).t_est == 260
    assert rec(base=None).t_est is None
    assert rec(time_class="rapid", base=600).category == "rapid"
    assert rec(time_class="rapid", base=1800).category == "classical"
    assert rec(time_class="rapid", base=900, inc=15).category == "classical"


def test_clock_helpers_white_and_black():
    # 3+2: own clocks after moves 1..3 and opponent clocks
    white = rec(base=180, inc=2, clocks=interleave([1800, 1700, 1500], [1790, 1650, 1600]))
    assert white.clock_before(1) == 1800
    assert white.clock_before(3) == 1700
    assert white.opponent_clock_before(1) == 1800  # black has not moved yet
    assert white.opponent_clock_before(3) == 1650
    assert white.time_spent(3) == (1700 + 20 - 1500) / 10

    black = rec(color="black", base=60, clocks=interleave([590, 500], [595, 580], "black"))
    assert black.own_clocks == [590, 500]
    assert black.opponent_clocks == [595, 580]
    assert black.opponent_clock_before(1) == 595
    assert black.opponent_clock_before(2) == 580
    assert black.opponent_clock_before(9) == 600


def test_results_on_time():
    assert rec(result="loss", termination="opp won on time").lost_on_time
    assert rec(result="win", termination="chrisaxm won on time").won_on_time
    assert not rec(result="loss", termination="opp won by resignation").lost_on_time


def test_sessions_use_end_to_start_gap():
    raw = [
        api_game(1, ended_at=T0, result="loss"),
        api_game(2, ended_at=T0 + timedelta(minutes=5), started_at=T0 + timedelta(seconds=40)),
        api_game(3, ended_at=T0 + timedelta(hours=2), started_at=T0 + timedelta(minutes=50)),
        api_game(4, ended_at=T0 + timedelta(minutes=1), time_class="daily", base=None),
    ]
    games = {g.id: g for g in prepare([GameRecord.from_api(g) for g in raw])}
    assert games[1].session_index == 1
    assert games[2].previous is games[1]
    assert games[2].previous_results == ["loss"]
    assert games[1].next_start_gap == timedelta(seconds=40)
    assert games[3].session_index == 1  # 45 minutes after game 2 ended
    assert games[4].session_index == 0


def test_missing_start_time_is_estimated():
    raw = [api_game(1, ended_at=T0), api_game(2, ended_at=T0 + timedelta(minutes=10))]
    raw[1]["started_at"] = None
    games = prepare([GameRecord.from_api(g) for g in raw])
    assert games[1].previous is games[0]


def test_strength_uses_pre_game_ratings():
    # chess.com reports post-game ratings: 2000 -> win -> 2010 -> loss -> 2000
    raw = [
        api_game(1, ended_at=T0, rating=2000, opp=2000),
        api_game(2, ended_at=T0 + timedelta(minutes=5), result="win", rating=2010, opp=1990),
        api_game(3, ended_at=T0 + timedelta(minutes=10), result="loss", rating=2000, opp=2010),
    ]
    games = {g.id: g for g in prepare([GameRecord.from_api(g) for g in raw])}
    assert games[2].opponent_rating == 2000
    assert games[3].opponent_rating == 2000
    assert games[3].strength == 2000
    assert abs(games[2].residual - 0.5) < 1e-9
