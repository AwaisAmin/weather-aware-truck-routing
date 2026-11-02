"""Hourly forecasts from Open-Meteo (https://open-meteo.com/en/docs), batched and cached.

Locations are snapped to a 0.1 degree grid (~11 km, close to the forecast models' own
resolution) so nearby checkpoints on different routes share one cached forecast.
"""

import math
from dataclasses import dataclass

from django.core.cache import cache

from .http import ExternalServiceError, get_json

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
HOURLY_FIELDS = ("wind_speed_10m", "wind_gusts_10m", "rain", "showers", "snowfall", "temperature_2m", "weather_code")
FORECAST_DAYS = 8
GRID_DEGREES = 0.1
# Keeps request URLs well under common length limits.
BATCH_SIZE = 100
CACHE_SECONDS = 30 * 60


@dataclass(frozen=True)
class Conditions:
    wind_mph: float
    gust_mph: float
    rain_in_hr: float  # rain + convective showers
    snow_in_hr: float
    temp_f: float
    weather_code: int

    def to_dict(self):
        return {
            "wind_mph": round(self.wind_mph, 1),
            "gust_mph": round(self.gust_mph, 1),
            "rain_in_hr": round(self.rain_in_hr, 3),
            "snow_in_hr": round(self.snow_in_hr, 2),
            "temp_f": round(self.temp_f),
            "weather_code": self.weather_code,
        }


@dataclass(frozen=True)
class Forecast:
    """Hourly series for one grid cell. times are unix seconds (UTC), one per hour."""

    times: list
    hourly: dict

    def at(self, moment):
        """Conditions at an aware datetime.

        Wind and temperature are instantaneous, so they are interpolated between hours.
        Rain and snow are totals for the preceding hour, so the hour that contains the
        moment (the next whole hour) is used as-is.
        """
        t = moment.timestamp()
        start, last = self.times[0], len(self.times) - 1
        position = (t - start) / 3600
        if position < 0 or position > last:
            raise ExternalServiceError("Requested time is outside the forecast window.", status_code=400)
        lower = int(math.floor(position))
        upper = min(lower + 1, last)
        fraction = position - lower
        bucket = min(int(math.ceil(position)), last)

        def blend(name):
            a, b = self._value(name, lower), self._value(name, upper)
            return a + (b - a) * fraction

        return Conditions(
            wind_mph=blend("wind_speed_10m"),
            gust_mph=blend("wind_gusts_10m"),
            rain_in_hr=self._value("rain", bucket) + self._value("showers", bucket),
            snow_in_hr=self._value("snowfall", bucket),
            temp_f=blend("temperature_2m"),
            weather_code=int(self._value("weather_code", bucket)),
        )

    def _value(self, name, index):
        # Open-Meteo returns null where a model has no data; treat it as calm/dry.
        value = self.hourly[name][index]
        return 0.0 if value is None else float(value)


def snap(lat, lon):
    return (round(round(lat / GRID_DEGREES) * GRID_DEGREES, 4), round(round(lon / GRID_DEGREES) * GRID_DEGREES, 4))


def _cache_key(cell):
    return f"wx:{cell[0]:.1f}:{cell[1]:.1f}"


def get_forecasts(locations):
    """Forecast for each (lat, lon) in locations, in the same order."""
    cells = [snap(lat, lon) for lat, lon in locations]
    unique = list(dict.fromkeys(cells))
    found = cache.get_many([_cache_key(c) for c in unique])
    forecasts = {c: found[_cache_key(c)] for c in unique if _cache_key(c) in found}

    missing = [c for c in unique if c not in forecasts]
    for start in range(0, len(missing), BATCH_SIZE):
        batch = missing[start : start + BATCH_SIZE]
        fetched = dict(zip(batch, _fetch(batch)))
        cache.set_many({_cache_key(c): f for c, f in fetched.items()}, CACHE_SECONDS)
        forecasts.update(fetched)

    return [forecasts[c] for c in cells]


def _fetch(cells):
    data = get_json(
        FORECAST_URL,
        params={
            "latitude": ",".join(f"{lat:.1f}" for lat, _ in cells),
            "longitude": ",".join(f"{lon:.1f}" for _, lon in cells),
            "hourly": ",".join(HOURLY_FIELDS),
            "wind_speed_unit": "mph",
            "precipitation_unit": "inch",
            "temperature_unit": "fahrenheit",
            "timezone": "GMT",
            "timeformat": "unixtime",
            "forecast_days": FORECAST_DAYS,
        },
        service="Open-Meteo",
    )
    # A single location comes back as an object, several as a list.
    items = data if isinstance(data, list) else [data]
    if len(items) != len(cells):
        raise ExternalServiceError("Open-Meteo returned an unexpected number of locations.")
    return [Forecast(times=item["hourly"]["time"], hourly=item["hourly"]) for item in items]

