from datetime import datetime, timedelta, timezone

import pytest
from django.core.cache import cache

from routing.services import weather
from routing.services.http import ExternalServiceError

START = datetime(2026, 11, 3, 0, 0, tzinfo=timezone.utc)


@pytest.fixture(autouse=True)
def clear_cache():
    cache.clear()


def hourly(hours=4, **overrides):
    series = {
        "time": [int(START.timestamp()) + 3600 * i for i in range(hours)],
        "wind_speed_10m": [10.0, 20.0, 30.0, 40.0][:hours],
        "wind_gusts_10m": [15.0] * hours,
        "rain": [0.0, 0.1, 0.2, None][:hours],
        "showers": [0.0, 0.05, 0.0, 0.0][:hours],
        "snowfall": [0.0, 0.0, 1.5, 0.0][:hours],
        "temperature_2m": [30.0, 32.0, 34.0, 36.0][:hours],
        "weather_code": [0, 61, 73, 3][:hours],
    }
    series.update(overrides)
    return series


def make_forecast():
    series = hourly()
    return weather.Forecast(times=series["time"], hourly=series)


def test_conditions_on_the_hour():
    c = make_forecast().at(START + timedelta(hours=1))
    assert c.wind_mph == 20
    assert c.rain_in_hr == pytest.approx(0.15)  # rain + showers
    assert c.weather_code == 61


def test_wind_interpolates_but_precipitation_uses_containing_hour():
    c = make_forecast().at(START + timedelta(hours=1, minutes=30))
    assert c.wind_mph == pytest.approx(25)
    assert c.temp_f == pytest.approx(33)
    # 01:30 falls in the hour ending 02:00, whose totals are rain 0.2, snow 1.5.
    assert c.rain_in_hr == pytest.approx(0.2)
    assert c.snow_in_hr == pytest.approx(1.5)


def test_missing_values_count_as_zero():
    assert make_forecast().at(START + timedelta(hours=3)).rain_in_hr == 0


def test_outside_forecast_window_raises():
    with pytest.raises(ExternalServiceError):
        make_forecast().at(START + timedelta(hours=10))


def test_snap_to_grid():
    assert weather.snap(39.7392, -104.9903) == (39.7, -105.0)


def test_get_forecasts_batches_dedupes_and_caches(monkeypatch):
    requests_made = []

    def fake_get_json(url, params=None, service=""):
        count = len(params["latitude"].split(","))
        requests_made.append(count)
        items = [{"hourly": hourly()} for _ in range(count)]
        return items if count > 1 else items[0]

    monkeypatch.setattr(weather, "get_json", fake_get_json)
    monkeypatch.setattr(weather, "BATCH_SIZE", 2)

    # The first two points share a grid cell.
    points = [(39.71, -104.99), (39.74, -105.01), (40.5, -104.0), (41.5, -103.0)]
    forecasts = weather.get_forecasts(points)
    assert len(forecasts) == 4
    assert forecasts[0] is forecasts[1]
    assert requests_made == [2, 1]

    weather.get_forecasts(points)
    assert requests_made == [2, 1], "second call should be served from cache"


def test_location_count_mismatch_raises(monkeypatch):
    monkeypatch.setattr(weather, "get_json", lambda *a, **k: [{"hourly": hourly()}])
    with pytest.raises(ExternalServiceError):
        weather.get_forecasts([(30, -100), (31, -101)])
