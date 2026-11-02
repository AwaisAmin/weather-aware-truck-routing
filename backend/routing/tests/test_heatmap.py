from datetime import datetime, timedelta, timezone

import pytest

from routing import heatmap
from routing.risk import continuous_score
from routing.services.weather import Conditions


@pytest.mark.parametrize(
    "wind, rain, snow, load, expected",
    [
        (0, 0, 0, 0, 0.0),
        (30, 0, 0, 0, 1.5),  # halfway through Moderate wind
        (0, 0.175, 0, 0, 1.5),  # halfway through Moderate rain
        (0, 0, 1.5, 0, 2.5),  # halfway through High snow
        (40, 0, 0, 45_000, 3.0),  # load rule lifts High wind to Severe
        (0, 1.0, 0, 0, 3.99),  # 1.00 in/hr is still Severe
        (0, 1.01, 0, 0, 4.0),
        (60, 0, 0, 0, 4.0),
    ],
)
def test_continuous_score(wind, rain, snow, load, expected):
    assert continuous_score(wind, rain, snow, load) == pytest.approx(expected, abs=0.01)


def test_corridor_cells_stay_near_route():
    route = [(35.0, -100.0 + i * 0.1) for i in range(51)]  # 5 degrees due east
    cells, spacing = heatmap.corridor_cells([route], buffer_deg=0.6)
    assert spacing == heatmap.MIN_SPACING_DEGREES
    assert all(34.4 - 1e-9 <= lat <= 35.6 + 1e-9 for lat, _ in cells)
    assert all(-100.6 - 1e-9 <= lon <= -94.4 + 1e-9 for _, lon in cells)
    assert (35.0, -97.0) in cells


def test_corridor_spacing_grows_to_respect_cell_limit():
    route = [(30.0 + i * 0.2, -100.0 + i * 0.2) for i in range(60)]
    cells, spacing = heatmap.corridor_cells([route], max_cells=100)
    assert len(cells) <= 100
    assert spacing > heatmap.MIN_SPACING_DEGREES
    # Spacing stays on the weather cache grid.
    assert round(spacing * 10) == pytest.approx(spacing * 10)


class FakeForecast:
    def __init__(self, start):
        self.start = start

    def at(self, moment):
        hours = (moment - self.start).total_seconds() / 3600
        # Wind ramps up 1 mph per hour.
        return Conditions(hours, hours, 0.0, 0.0, 50.0, 0)


def test_build_heatmap_scores_each_hour(monkeypatch):
    departure = datetime(2026, 11, 3, 6, 40, tzinfo=timezone.utc)
    start = departure.replace(minute=0)
    monkeypatch.setattr(heatmap.weather, "get_forecasts", lambda cells: [FakeForecast(start) for _ in cells])

    result = heatmap.build_heatmap([[(35.0, -100.0), (35.0, -99.0)]], departure, load_lb=0, hours=48)

    assert result["start"] == "2026-11-03T06:00:00Z"
    assert len(result["scores"]) == len(result["cells"])
    row = result["scores"][0]
    assert len(row) == 49
    assert row[0] == 0
    assert row[30] == 15  # 30 mph -> 1.5
    assert row == sorted(row)


def test_heatmap_endpoint(client, monkeypatch):
    monkeypatch.setattr(
        heatmap.weather, "get_forecasts", lambda cells: [FakeForecast(datetime.now(timezone.utc)) for _ in cells]
    )
    body = {
        "routes": [[[-100.0, 35.0], [-99.0, 35.0]]],
        "departure": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
        "load_lb": 20_000,
    }
    response = client.post("/api/heatmap/", body, content_type="application/json")
    assert response.status_code == 200
    data = response.json()
    assert data["hours"] == 48
    assert data["cells"] and len(data["scores"][0]) == 49


def test_heatmap_endpoint_rejects_bad_coordinates(client):
    body = {
        "routes": [[[-100.0, 135.0], [-99.0, 35.0]]],
        "departure": datetime.now(timezone.utc).isoformat(),
        "load_lb": 0,
    }
    assert client.post("/api/heatmap/", body, content_type="application/json").status_code == 400
