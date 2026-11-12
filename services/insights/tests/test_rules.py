from datetime import datetime, timedelta

import httpx
import pytest
from conftest import api_game, interleave, session_games

from app.analysis.games import GameRecord, prepare
from app.analysis.rules import (
    CLOCK_CHECKPOINT,
    STOP_LOSS,
    RuleSpec,
    check_rule,
    clock_units,
    describe,
    stop_units,
)
from app.analysis.stats import label_for

T0 = datetime(2026, 9, 1, 18, 0)
ADOPTED = T0 + timedelta(days=60)
# Blitz 3+0: T_est = 180 s. After own move 20 the clock is 58% (calm) or 10% (rushed, which
# then plays on in time trouble).
CALM = interleave([1800 - 40 * k for k in range(30)], [1790 - 30 * k for k in range(30)])
RUSHED = interleave(
    [1800 - 85 * k for k in range(21)] + [100 - 2 * j for j in range(1, 10)],
    [1790 - 30 * k for k in range(30)],
)
SHORT = interleave([1800 - 40 * k for k in range(15)], [1790 - 30 * k for k in range(15)])


def records(raw):
    return prepare([GameRecord.from_api(g) for g in raw])


def clock_rule(**kw) -> RuleSpec:
    return RuleSpec(
        id=1, time_class="blitz", kind=CLOCK_CHECKPOINT, adopted_at=ADOPTED, move=20,
        min_share=0.3, **kw,
    )  # fmt: skip


def stop_rule(**kw) -> RuleSpec:
    return RuleSpec(
        id=2, time_class="blitz", kind=STOP_LOSS, adopted_at=ADOPTED, stop_rule="two_in_a_row",
        **kw,
    )  # fmt: skip


def clock_games(n_before_kept, n_before_broken, n_after_kept, n_after_broken):
    """One game per hour (no sessions needed): before adoption first, then after."""
    plan = (
        [CALM] * n_before_kept
        + [RUSHED] * n_before_broken
        + [CALM] * n_after_kept
        + [RUSHED] * n_after_broken
    )
    n_before = n_before_kept + n_before_broken
    raw = []
    for i, clocks in enumerate(plan):
        when = (T0 if i < n_before else ADOPTED) + timedelta(hours=i)
        raw.append(api_game(i, ended_at=when, clocks=clocks))
    return records(raw)


def test_describe():
    assert describe(CLOCK_CHECKPOINT, 20, 0.3, None) == (
        "Keep at least 30% of your clock after move 20"
    )
    assert describe(STOP_LOSS, None, None, "two_in_a_row") == "Stop after 2 losses in a row"


def test_clock_units_skip_short_games_and_other_time_classes():
    raw = [
        api_game(1, ended_at=T0, clocks=CALM),
        api_game(2, ended_at=T0 + timedelta(hours=1), clocks=RUSHED),
        api_game(3, ended_at=T0 + timedelta(hours=2), clocks=SHORT),  # never reaches move 20
        api_game(4, ended_at=T0 + timedelta(hours=3), clocks=CALM, time_class="bullet", base=60),
        api_game(5, ended_at=T0 + timedelta(hours=4), clocks=None),
    ]
    units = clock_units(clock_rule(), records(raw))
    assert [(u.cluster, u.kept) for u in units] == [(1, True), (2, False)]
    assert units[1].trouble  # the rushed game ends in time trouble


def test_stop_units_count_games_past_the_stop():
    raw = session_games(0, T0, ["loss", "loss", "win", "win"])  # 2 games past the stop
    raw += session_games(10, T0 + timedelta(days=1), ["win", "loss", "loss"])  # stopped
    raw += session_games(20, T0 + timedelta(days=2), ["win", "loss", "win"])  # never said stop
    units = stop_units(stop_rule(), records(raw))
    assert [(u.kept, u.games_past_stop) for u in units] == [(False, 2), (True, 0)]


def test_clock_rule_kept_more_often_after_adoption():
    games = clock_games(n_before_kept=15, n_before_broken=45, n_after_kept=38, n_after_broken=2)
    draft = check_rule(clock_rule(), games)
    d = draft.details
    assert draft.analysis_key == "rule_check"
    assert d["rule_id"] == 1
    assert (d["before"]["count"], d["before"]["n"]) == (15, 60)
    assert (d["after"]["count"], d["after"]["n"]) == (38, 40)
    assert len(d["strip"]) == 30 and d["strip"][-1]["kept"] is False
    assert d["trouble"]["before"]["rate"] > d["trouble"]["after"]["rate"]
    c = draft.contrast
    assert c.effect == pytest.approx(38 / 40 - 15 / 60)
    assert c.ci_low > 0
    title, summary = draft.text("finding")
    assert "more often since adopting it" in title
    assert "Time trouble" in summary


def test_clock_rule_too_early():
    games = clock_games(n_before_kept=20, n_before_broken=20, n_after_kept=5, n_after_broken=1)
    draft = check_rule(clock_rule(), games)
    label = label_for(0.01, draft.contrast.n_small, draft.min_n)
    assert label == "not_enough_data"
    title, summary = draft.text(label)
    assert title.endswith("(too early)")
    assert "Kept in 5 of 6 games" in summary and "24 to go" in summary


def test_rule_without_games_since_adoption():
    games = clock_games(n_before_kept=10, n_before_broken=10, n_after_kept=0, n_after_broken=0)
    draft = check_rule(clock_rule(), games)
    assert draft.contrast is None
    title, summary = draft.text("not_enough_data")
    assert "No games since you adopted it" in summary


def test_rule_without_baseline():
    games = clock_games(n_before_kept=0, n_before_broken=0, n_after_kept=35, n_after_broken=0)
    _title, summary = check_rule(clock_rule(), games).text("not_enough_data")
    assert "no baseline" in summary
    assert "also needs 30 games from before" in summary


def test_stop_rule_kept_after_adoption():
    raw, i = [], 0
    for day in range(40):  # before: always kept playing after two losses
        raw += session_games(i, T0 + timedelta(days=day), ["loss", "loss", "win", "win"])
        i += 10
    for day in range(35):  # after: always stopped
        raw += session_games(i, ADOPTED + timedelta(days=day), ["win", "loss", "loss"])
        i += 10
    draft = check_rule(stop_rule(), records(raw))
    d = draft.details
    assert d["games_past_stop"] == {"before": 80, "after": 0}
    assert draft.contrast.effect == pytest.approx(1.0)
    title, summary = draft.text("finding")
    assert "more often" in title and "Games played past the stop: 80 before, 0 since" in summary
    title, _ = draft.text("no_effect")
    assert title.endswith("no clear change yet")


def test_rule_broken_more_often_wording():
    games = clock_games(n_before_kept=50, n_before_broken=10, n_after_kept=5, n_after_broken=30)
    draft = check_rule(clock_rule(), games)
    assert draft.contrast.effect < 0
    title, _ = draft.text("exploratory")
    assert "less often than before (exploratory)" in title


# ---- API --------------------------------------------------------------------------------

CHECKPOINT = {"time_class": "blitz", "kind": "clock_checkpoint", "min_share": 0.3}


def test_rule_crud(client):
    resp = client.post("/players/1/rules", json=CHECKPOINT)
    assert resp.status_code == 201, resp.text
    rule = resp.json()
    assert rule["move"] == 20
    assert rule["description"] == "Keep at least 30% of your clock after move 20"
    assert rule["retired_at"] is None

    # One active rule per kind and time class.
    assert client.post("/players/1/rules", json=CHECKPOINT).status_code == 409
    other = client.post(
        "/players/1/rules",
        json={"time_class": "blitz", "kind": "stop_loss", "stop_rule": "three_in_a_row"},
    )
    assert other.status_code == 201
    assert [r["id"] for r in client.get("/players/1/rules").json()] == [
        rule["id"],
        other.json()["id"],
    ]
    assert client.get("/players/2/rules").json() == []

    # Changing the threshold restarts the count.
    patched = client.patch(f"/rules/{rule['id']}", json={"min_share": 0.25, "note": "move faster"})
    assert patched.status_code == 200
    assert patched.json()["min_share"] == 0.25 and patched.json()["note"] == "move faster"
    assert patched.json()["adopted_at"] >= rule["adopted_at"]
    note_only = client.patch(f"/rules/{rule['id']}", json={"note": None})
    assert note_only.json()["adopted_at"] == patched.json()["adopted_at"]
    bad = client.patch(f"/rules/{other.json()['id']}", json={"min_share": 0.2})
    assert bad.status_code == 422

    # Retire, list with and without retired rules, un-retire.
    retired = client.patch(f"/rules/{rule['id']}", json={"retired": True}).json()
    assert retired["retired_at"] is not None
    assert len(client.get("/players/1/rules").json()) == 1
    assert len(client.get("/players/1/rules?include_retired=true").json()) == 2
    client.post("/players/1/rules", json={**CHECKPOINT, "min_share": 0.4})
    assert client.patch(f"/rules/{rule['id']}", json={"retired": False}).status_code == 409

    assert client.get(f"/rules/{rule['id']}").json()["id"] == rule["id"]
    assert client.delete(f"/rules/{rule['id']}").status_code == 204
    assert client.get(f"/rules/{rule['id']}").status_code == 404
    assert client.delete(f"/rules/{rule['id']}").status_code == 404
    assert client.patch(f"/rules/{rule['id']}", json={"note": "x"}).status_code == 404


def test_unretire_without_clash(client):
    rule = client.post("/players/1/rules", json=CHECKPOINT).json()
    client.patch(f"/rules/{rule['id']}", json={"retired": True})
    back = client.patch(f"/rules/{rule['id']}", json={"retired": False})
    assert back.status_code == 200 and back.json()["retired_at"] is None


@pytest.mark.parametrize(
    "body",
    [
        {"time_class": "blitz", "kind": "clock_checkpoint"},  # no threshold
        {**CHECKPOINT, "stop_rule": "two_in_a_row"},
        {"time_class": "blitz", "kind": "stop_loss"},  # no stop rule
        {"time_class": "blitz", "kind": "stop_loss", "stop_rule": "two_in_a_row", "move": 20},
        {**CHECKPOINT, "move": 5},
        {**CHECKPOINT, "min_share": 1.5},
        {**CHECKPOINT, "time_class": "daily"},
        {**CHECKPOINT, "adopted_at": "2999-01-01T00:00:00Z"},
    ],
)
def test_rule_validation(client, body):
    assert client.post("/players/1/rules", json=body).status_code == 422


def test_rule_backdated_with_time_zone(client):
    rule = client.post(
        "/players/1/rules", json={**CHECKPOINT, "adopted_at": "2026-10-01T20:00:00+02:00"}
    ).json()
    assert rule["adopted_at"] == "2026-10-01T18:00:00"


def test_run_checks_active_rules(client, games_api):
    games = []
    for s in range(40):
        games += session_games(s * 10, T0 + timedelta(days=s), ["win", "loss", "loss", "win"],
                               clocks=CALM)  # fmt: skip

    def handler(request):
        return httpx.Response(200, json={"items": games, "total": len(games)})

    games_api.get("/players/1/games").mock(side_effect=handler)
    rule = client.post(
        "/players/1/rules", json={**CHECKPOINT, "adopted_at": (T0 + timedelta(days=20)).isoformat()}
    ).json()
    retired = client.post(
        "/players/1/rules",
        json={"time_class": "blitz", "kind": "stop_loss", "stop_rule": "two_in_a_row"},
    ).json()
    client.patch(f"/rules/{retired['id']}", json={"retired": True})

    run = client.post("/players/1/runs").json()
    checks = [f for f in run["findings"] if f["analysis_key"] == "rule_check"]
    assert len(checks) == 1
    check = checks[0]
    assert check["details"]["rule_id"] == rule["id"]
    assert check["details"]["after"]["n"] == 80 and check["details"]["before"]["n"] == 80
    assert check["label"] == "no_effect"  # kept every time, before and after
