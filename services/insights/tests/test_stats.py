import pytest

from app.analysis.stats import (
    actual_score,
    benjamini_hochberg,
    cluster_bootstrap,
    expected_score,
    label_for,
    median,
    pct,
    quantiles,
    to_elo,
    wilson,
)


def test_scores_and_elo():
    assert expected_score(2000, 2000) == pytest.approx(0.5)
    assert expected_score(2400, 2000) == pytest.approx(0.909, abs=0.001)
    assert expected_score(None, 2000) == 0.5
    assert actual_score("draw") == 0.5
    assert actual_score("loss") == 0.0
    assert to_elo(0.1) == pytest.approx(69.5, abs=0.1)
    assert pct(-0.061) == "-6.1"


def test_bootstrap_detects_a_real_difference():
    a = [(i, 0.2 + (i % 3) * 0.01) for i in range(150)]
    b = [(1000 + i, 0.0 + (i % 3) * 0.01) for i in range(150)]
    c = cluster_bootstrap(a, b, n_boot=500)
    assert c.effect == pytest.approx(0.2)
    assert c.ci_low > 0.15
    assert c.p_value < 0.01
    assert c.mde == pytest.approx(2.8 * c.se)
    assert c.n_small == 150


def test_bootstrap_no_difference_and_clusters():
    a = [(i // 4, ((i * 7) % 11) / 10) for i in range(200)]
    b = [(i // 4, ((i * 5) % 11) / 10) for i in range(200)]
    c = cluster_bootstrap(a, b, n_boot=500)
    assert c.ci_low < 0 < c.ci_high
    assert c.p_value > 0.05
    assert cluster_bootstrap([], b) is None
    assert cluster_bootstrap(a, []) is None


def test_bootstrap_is_deterministic():
    a = [(i, float(i % 5)) for i in range(60)]
    b = [(i, float(i % 7)) for i in range(60)]
    assert cluster_bootstrap(a, b, n_boot=300) == cluster_bootstrap(a, b, n_boot=300)


def test_benjamini_hochberg():
    assert benjamini_hochberg([]) == []
    q = benjamini_hochberg([0.01, 0.04, 0.03, 0.5])
    assert q == pytest.approx([0.04, 0.0533, 0.0533, 0.5], abs=1e-3)


def test_labels():
    assert label_for(0.01, 200, 100) == "finding"
    assert label_for(0.08, 200, 100) == "exploratory"
    assert label_for(0.3, 200, 100) == "no_effect"
    assert label_for(0.01, 50, 100) == "not_enough_data"
    assert label_for(None, 500, 100) == "not_enough_data"


def test_wilson_median_quantiles():
    lo, hi = wilson(30, 100)
    assert lo == pytest.approx(0.219, abs=0.01)
    assert hi == pytest.approx(0.396, abs=0.01)
    assert wilson(0, 0) == (0.0, 1.0)
    assert median([]) is None
    assert median([1, 2, 3]) == 2
    assert quantiles([]) is None
    assert quantiles([1, 2, 3, 4, 5]) == (2, 4)
