from datetime import datetime, timedelta, timezone

import pytest
from django.core.cache import cache

from routing.services import tomtom


@pytest.fixture(autouse=True)
def clear_cache(settings):
    settings.TOMTOM_API_KEY = "test-key"
    cache.clear()


def route_payload(length_m=1000, time_s=100, instructions=((0, 0), (400, 30), (1000, 100))):
    return {
        "summary": {
            "lengthInMeters": length_m,
            "travelTimeInSeconds": time_s,
            "departureTime": "2026-11-03T06:00:00-06:00",
            "arrivalTime": "2026-11-03T06:01:40-06:00",
        },
        "legs": [{"points": [{"latitude": 32.0, "longitude": -96.0}, {"latitude": 32.1, "longitude": -96.1}]}],
        "guidance": {
            "instructions": [{"routeOffsetInMeters": o, "travelTimeInSeconds": t} for o, t in instructions]
        },
    }


def test_parse_route_builds_monotonic_time_profile():
    route = tomtom.parse_route(route_payload(instructions=((0, 0), (400, 30), (400, 35), (900, 80))))
    assert route.points == [(32.0, -96.0), (32.1, -96.1)]
    # Duplicate offsets are dropped and the route end is appended.
    assert route.time_profile == [(0.0, 0.0), (400.0, 30.0), (900.0, 80.0), (1000.0, 100.0)]


def test_detour_point_is_perpendicular_to_the_trip():
    # Due east trip: detours sit north/south of the midpoint.
    lat, lon = tomtom._detour_point((0.0, 0.0), (0.0, 10.0), 0.2)
    assert lat == pytest.approx(2.0)
    assert lon == pytest.approx(5.0)


def test_route_params_use_gross_weight_and_future_departure():
    future = datetime(2099, 1, 1, 10, 44, 30, tzinfo=timezone.utc)
    params = tomtom._route_params(future, load_lb=40_000)
    assert params["vehicleWeight"] == round(75_000 * tomtom.LB_TO_KG)
    # Rounded down to the quarter hour so nearby requests share the route cache.
    assert params["departAt"] == "2099-01-01T10:30:00+00:00"

    past = datetime.now(timezone.utc) - timedelta(hours=1)
    assert tomtom._route_params(past, load_lb=0)["departAt"] == "now"


def test_fetch_routes_adds_detours_when_alternatives_are_missing(monkeypatch):
    calls = []

    def fake_get_json(url, params=None, service=""):
        calls.append(url)
        if len(calls) == 1:
            return {"routes": [route_payload(1000, 100)]}
        # Each detour returns a distinct, longer route.
        return {"routes": [route_payload(1000 + 100 * len(calls), 100 + 20 * len(calls))]}

    monkeypatch.setattr(tomtom, "get_json", fake_get_json)
    routes = tomtom.fetch_routes((32.0, -96.0), (39.0, -105.0), datetime.now(timezone.utc), 20_000)

    assert len(routes) == 3
    assert len(calls) == 3
    assert [r.duration_s for r in routes] == sorted(r.duration_s for r in routes)


def test_fetch_routes_skips_duplicate_detours(monkeypatch):
    monkeypatch.setattr(tomtom, "get_json", lambda *a, **k: {"routes": [route_payload(1000, 100)]})
    routes = tomtom.fetch_routes((32.0, -96.0), (39.0, -105.0), datetime.now(timezone.utc), 20_000)
    assert len(routes) == 1


def test_geocode_endpoint(client, monkeypatch):
    payload = {
        "results": [{"address": {"freeformAddress": "Dallas, TX"}, "position": {"lat": 32.77, "lon": -96.79}}]
    }
    monkeypatch.setattr(tomtom, "get_json", lambda *a, **k: payload)
    response = client.get("/api/geocode/", {"q": "Dallas"})
    assert response.status_code == 200
    assert response.json() == {"results": [{"label": "Dallas, TX", "lat": 32.77, "lon": -96.79}]}


def test_geocode_short_query_returns_nothing(client):
    assert client.get("/api/geocode/", {"q": "D"}).json() == {"results": []}
