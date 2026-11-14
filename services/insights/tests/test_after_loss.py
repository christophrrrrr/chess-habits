from datetime import datetime, timedelta

from conftest import api_game

from app.analysis.after_loss import after_loss, skipped_by
from app.analysis.games import GameRecord, prepare

T0 = datetime(2026, 10, 1, 18, 0)


def session(
    start_id: int, day: int, results: list[str], gap_after_loss: int = 20, gap_after_win: int = 300
) -> list[dict]:
    """Games in one session. The next game starts `gap_after_loss` seconds after a loss and
    `gap_after_win` seconds after a win."""
    games, t = [], T0 + timedelta(days=day)
    for k, r in enumerate(results):
        start = t
        end = start + timedelta(minutes=4)
        games.append(api_game(start_id + k, ended_at=end, started_at=start, result=r))
        t = end + timedelta(seconds=gap_after_loss if r == "loss" else gap_after_win)
    return games


def records(raw):
    return prepare([GameRecord.from_api(g) for g in raw])


def by_key(drafts):
    return {d.analysis_key: d for d in drafts}


def test_skipped_by_rules():
    g = GameRecord.from_api(api_game(1, ended_at=T0))
    g.previous_results = ["loss", "loss", "win"]
    assert skipped_by("two_in_a_row", g)
    assert not skipped_by("three_in_a_row", g)
    g.previous_results = ["loss", "win", "loss", "win", "loss"]
    assert skipped_by("three_in_session", g)
    assert not skipped_by("two_in_a_row", g)


def test_requeue_and_result_after_loss():
    raw = []
    for s in range(60):
        raw += session(s * 10, s, ["win", "loss", "loss", "win", "win", "loss"])
    d = by_key(after_loss(records(raw)))
    requeue = d["after_loss_requeue"].contrast
    assert requeue.mean_a > 0.6  # quick requeue after losses (not after the last game)
    assert requeue.mean_b < 0.1
    assert "faster after a loss" in d["after_loss_requeue"].text("finding")[0]
    assert "(exploratory)" in d["after_loss_requeue"].text("exploratory")[0]
    assert "does not change" in d["after_loss_requeue"].text("no_effect")[0]

    result = d["after_loss_result"]
    assert result.contrast is not None
    assert "not enough" in result.text("not_enough_data")[0]
    assert "no tilt larger than" in result.text("no_effect")[0]


def test_result_wording_for_both_directions():
    raw = []
    for s in range(70):
        raw += session(s * 10, s, ["loss", "loss", "win", "win", "loss", "win"])
    result = by_key(after_loss(records(raw)))["after_loss_result"]
    title, summary = result.text("finding")
    if result.contrast.effect < 0:
        assert "below your level" in title
    else:
        assert "above your level" in title
        assert "self-selection" in summary


def test_requeue_slower_after_loss():
    raw = []
    for s in range(60):
        raw += session(
            s * 10, s, ["win", "loss", "win", "loss"], gap_after_loss=900, gap_after_win=20
        )
    d = by_key(after_loss(records(raw)))
    assert d["after_loss_requeue"].contrast.effect < 0
    assert "more time" in d["after_loss_requeue"].text("finding")[0]


def test_stop_loss_rules_that_help():
    raw = []
    for s in range(40):
        # after two losses the player keeps losing: the rule would have helped
        raw += session(s * 10, s, ["win", "loss", "loss", "loss", "loss", "loss"])
    for s in range(40, 80):
        raw += session(s * 10, s, ["win", "win", "win", "win"])
    d = by_key(after_loss(records(raw)))
    rules = {r["rule"]: r for r in d["stop_loss_rules"].details["rules"]}
    assert rules["two_in_a_row"]["skipped_games"] == 120
    assert rules["two_in_a_row"]["verdict"] == "helps"
    assert "would have saved you points" in d["stop_loss_rules"].text("profile")[0]


def test_stop_loss_not_enough_and_costs():
    few = by_key(after_loss(records(session(0, 0, ["win"] * 25))))
    assert "not enough long sessions" in few["stop_loss_rules"].text("profile")[0]
    assert "not enough games" in few["after_loss_requeue"].text("not_enough_data")[0]

    raw = []
    for s in range(40):
        # after two losses the player wins: the rule would have cost points
        raw += session(s * 10, s, ["loss", "loss", "win", "win", "win"])
    for s in range(40, 80):
        raw += session(s * 10, s, ["loss", "win", "loss", "win"])
    d = by_key(after_loss(records(raw)))
    rules = {r["rule"]: r for r in d["stop_loss_rules"].details["rules"]}
    assert rules["two_in_a_row"]["verdict"] == "costs"
    title, summary = d["stop_loss_rules"].text("profile")
    assert "would not have helped" in title
    assert "better than the rest" in summary
