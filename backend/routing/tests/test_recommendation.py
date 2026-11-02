import pytest

from routing.recommendation import explain, rank, score_route
from routing.risk import RiskLevel

L, M, H, S, N = (
    RiskLevel.LOW,
    RiskLevel.MODERATE,
    RiskLevel.HIGH,
    RiskLevel.SEVERE,
    RiskLevel.NO_TRAVEL,
)


def test_score_route_totals_and_average():
    score = score_route([(10, L), (20, H), (10, S)], duration_s=3600)
    assert score.miles_by_level[H] == 20
    assert score.miles_by_level[S] == 10
    assert score.average_risk == pytest.approx((0 * 10 + 2 * 20 + 3 * 10) / 40)
    assert score.max_level == S


def test_empty_route_scores_zero():
    assert score_route([], duration_s=0).average_risk == 0


def test_fewer_severe_miles_beats_faster_route():
    fast_but_severe = score_route([(90, L), (10, S)], duration_s=3600)
    slow_but_safe = score_route([(50, L), (50, H)], duration_s=7200)
    assert rank([fast_but_severe, slow_but_safe]) == [1, 0]
    assert explain(slow_but_safe, fast_but_severe) == "Recommended: fewer Severe miles than the next best route."


def test_no_travel_ranks_below_severe():
    no_travel = score_route([(99, L), (1, N)], duration_s=3600)
    severe = score_route([(50, S), (50, S)], duration_s=3600)
    assert rank([no_travel, severe]) == [1, 0]


def test_high_miles_then_average_risk_then_time():
    more_high = score_route([(70, L), (30, H)], duration_s=3600)
    less_high = score_route([(80, L), (20, H)], duration_s=9000)
    assert rank([more_high, less_high]) == [1, 0]

    riskier = score_route([(50, L), (50, M)], duration_s=3600)
    calmer = score_route([(90, L), (10, M)], duration_s=9000)
    assert rank([riskier, calmer]) == [1, 0]
    assert explain(calmer, riskier) == "Recommended: lower average risk than the next best route."

    slow = score_route([(100, L)], duration_s=9000)
    fast = score_route([(100, L)], duration_s=3600)
    assert rank([slow, fast]) == [1, 0]
    assert explain(fast, slow) == "Recommended: shorter travel time than the next best route."


def test_float_noise_does_not_decide_ranking():
    a = score_route([(100, L), (10.00001, H)], duration_s=3600)
    b = score_route([(100, L), (10.0, H)], duration_s=7200)
    assert rank([a, b]) == [0, 1]


def test_explain_single_route():
    assert explain(score_route([(1, L)], 1), None) == "Only route available."
