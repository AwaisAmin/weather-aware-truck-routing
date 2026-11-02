from datetime import datetime, timedelta, timezone

import pytest

from routing.checkpoints import sample_checkpoints
from routing.geometry import METERS_PER_MILE, cumulative_distances, haversine_m, interpolate, simplify
from routing.services.tomtom import Route

DEPARTURE = datetime(2026, 11, 3, 12, 0, tzinfo=timezone.utc)


def straight_route(miles, hours, time_profile=None):
    """A due-north route of the given length along the prime meridian."""
    meters = miles * METERS_PER_MILE
    end_lat = meters / 111_195.0  # meters per degree of latitude
    points = [(end_lat * i / 100, 0.0) for i in range(101)]
    return Route(
        distance_m=meters,
        duration_s=hours * 3600,
        departure="",
        arrival="",
        points=points,
        time_profile=time_profile or [(0.0, 0.0), (meters, hours * 3600)],
    )


def test_haversine_one_degree_latitude():
    assert haversine_m((0, 0), (1, 0)) == pytest.approx(111_195, rel=1e-3)


def test_interpolate_clamps_and_blends():
    assert interpolate([0, 10], [0, 100], -5) == 0
    assert interpolate([0, 10], [0, 100], 2.5) == 25
    assert interpolate([0, 10], [0, 100], 50) == 100


@pytest.mark.parametrize("interval, expected_count", [(10, 11), (25, 5), (50, 3)])
def test_checkpoint_count_includes_origin_and_destination(interval, expected_count):
    checkpoints = sample_checkpoints(straight_route(100, 2), interval, DEPARTURE)
    assert len(checkpoints) == expected_count
    assert checkpoints[0].mile == 0
    assert checkpoints[-1].mile == pytest.approx(100)


def test_segment_miles_cover_whole_route():
    checkpoints = sample_checkpoints(straight_route(110, 2), 25, DEPARTURE)
    assert [round(c.mile) for c in checkpoints] == [0, 25, 50, 75, 100, 110]
    assert sum(c.segment_miles for c in checkpoints) == pytest.approx(110)
    assert checkpoints[0].segment_miles == pytest.approx(12.5)
    assert checkpoints[-1].segment_miles == pytest.approx(5)


def test_eta_follows_time_profile_not_average_speed():
    meters = 100 * METERS_PER_MILE
    # First half is slow (city): 50 miles in 1.5 h, then 50 miles in 0.5 h.
    profile = [(0.0, 0.0), (meters / 2, 5400.0), (meters, 7200.0)]
    checkpoints = sample_checkpoints(straight_route(100, 2, profile), 25, DEPARTURE)
    etas = [c.eta - DEPARTURE for c in checkpoints]
    assert etas == [
        timedelta(0),
        timedelta(minutes=45),
        timedelta(minutes=90),
        timedelta(minutes=105),
        timedelta(minutes=120),
    ]


def test_checkpoint_positions_lie_on_route():
    route = straight_route(100, 2)
    checkpoints = sample_checkpoints(route, 50, DEPARTURE)
    assert checkpoints[1].lon == 0.0
    assert checkpoints[1].lat == pytest.approx(route.points[-1][0] / 2, rel=1e-3)


def test_invalid_interval_rejected():
    with pytest.raises(ValueError):
        sample_checkpoints(straight_route(100, 2), 15, DEPARTURE)


def test_simplify_drops_collinear_points_and_keeps_corners():
    line = [(0, x / 10) for x in range(11)] + [(y / 10, 1) for y in range(1, 11)]
    simplified = simplify(line, tolerance_deg=0.001)
    assert simplified == [(0, 0.0), (0, 1.0), (1.0, 1)]
    assert cumulative_distances(simplified)[-1] == pytest.approx(cumulative_distances(line)[-1])
