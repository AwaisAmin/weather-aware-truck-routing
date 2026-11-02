from datetime import datetime, timedelta, timezone

import pytest

from routing import planner
from routing.geometry import METERS_PER_MILE
from routing.services.http import ExternalServiceError
from routing.services.tomtom import Route
from routing.services.weather import Conditions

ORIGIN = {"lat": 32.78, "lon": -96.80, "label": "Dallas, TX"}
DESTINATION = {"lat": 39.74, "lon": -104.99, "label": "Denver, CO"}


def route(miles, hours, lon):
    meters = miles * METERS_PER_MILE
    end_lat = 32.0 + meters / 111_195.0
    return Route(
        distance_m=meters,
        duration_s=hours * 3600,
        departure="",
        arrival="",
        points=[(32.0 + (end_lat - 32.0) * i / 10, lon) for i in range(11)],
        time_profile=[(0.0, 0.0), (meters, hours * 3600)],
    )


class FakeForecast:
    def __init__(self, wind_mph):
        self.wind_mph = wind_mph

    def at(self, moment):
        return Conditions(self.wind_mph, self.wind_mph, 0.0, 0.0, 50.0, 0)


@pytest.fixture
def fake_services(monkeypatch):
    # Route A is fastest but windy (40 mph); B and C are calm, C is faster than B.
    routes = [route(100, 2, lon=-97.0), route(120, 3, lon=-98.0), route(110, 2.5, lon=-99.0)]
    monkeypatch.setattr(planner.tomtom, "fetch_routes", lambda *a, **k: routes)
    monkeypatch.setattr(
        planner.weather,
        "get_forecasts",
        lambda locations: [FakeForecast(40 if lon == -97.0 else 5) for _, lon in locations],
    )


def request_body(**overrides):
    body = {
        "origin": ORIGIN,
        "destination": DESTINATION,
        "departure": (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat(),
        "load_lb": 42_000,
        "interval_miles": 25,
    }
    body.update(overrides)
    return body


def test_plan_recommends_safest_then_fastest(client, fake_services):
    response = client.post("/api/plan/", request_body(), content_type="application/json")
    assert response.status_code == 200
    data = response.json()

    assert data["recommended_route_id"] == "C"
    # The runner-up (B) is also calm, so C wins on time.
    assert data["recommendation_reason"] == "Recommended: shorter travel time than the next best route."
    by_id = {r["id"]: r for r in data["routes"]}
    assert [by_id[i]["rank"] for i in "ABC"] == [3, 2, 1]

    # 40 mph wind with a 42,000 lb load is Severe under the load rules.
    route_a = by_id["A"]
    assert route_a["score"]["max_label"] == "Severe"
    assert route_a["score"]["miles_by_level"]["severe"] == pytest.approx(100, abs=0.1)
    assert route_a["checkpoints"][0]["risk"]["drivers"] == ["wind+load"]
    assert [c["mile"] for c in route_a["checkpoints"]] == [0, 25, 50, 75, 100]
    assert route_a["geometry"][0] == [-97.0, 32.0]


def test_light_load_changes_the_recommendation(client, fake_services):
    data = client.post("/api/plan/", request_body(load_lb=20_000), content_type="application/json").json()
    # 40 mph is only High for a light truck; B and C have no High miles, so C still wins.
    assert data["recommended_route_id"] == "C"
    by_id = {r["id"]: r for r in data["routes"]}
    assert by_id["A"]["score"]["max_label"] == "High"


def test_past_departure_means_now(client, fake_services):
    past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    data = client.post("/api/plan/", request_body(departure=past), content_type="application/json").json()
    departure = datetime.fromisoformat(data["departure"].replace("Z", "+00:00"))
    assert abs(departure - datetime.now(timezone.utc)) < timedelta(minutes=1)


@pytest.mark.parametrize(
    "overrides, field",
    [
        ({"load_lb": -1}, "load_lb"),
        ({"interval_miles": 15}, "interval_miles"),
        ({"departure": (datetime.now(timezone.utc) + timedelta(days=9)).isoformat()}, "departure"),
        ({"destination": ORIGIN}, "non_field_errors"),
    ],
)
def test_invalid_requests(client, overrides, field):
    response = client.post("/api/plan/", request_body(**overrides), content_type="application/json")
    assert response.status_code == 400
    assert field in response.json()


def test_upstream_failure_is_reported(client, monkeypatch):
    def fail(*args, **kwargs):
        raise ExternalServiceError("No truck route found between these locations.", status_code=404)

    monkeypatch.setattr(planner.tomtom, "fetch_routes", fail)
    response = client.post("/api/plan/", request_body(), content_type="application/json")
    assert response.status_code == 404
    assert response.json() == {"detail": "No truck route found between these locations."}
