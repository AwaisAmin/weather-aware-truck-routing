"""Weather risk classification for a single checkpoint.

Thresholds follow the assessment's risk table. Where the table's ranges touch
(e.g. rain 0.10-0.25 and 0.25-0.50), the lower bound is inclusive, so 0.25 in/hr is High.
"""

from dataclasses import dataclass
from enum import IntEnum


class RiskLevel(IntEnum):
    LOW = 0
    MODERATE = 1
    HIGH = 2
    SEVERE = 3
    NO_TRAVEL = 4

    @property
    def label(self):
        return self.name.replace("_", " ").title()


# Lower bound of each level above Low: (moderate, high, severe, no_travel).
WIND_MPH_THRESHOLDS = (25, 35, 45, 55)
RAIN_IN_HR_THRESHOLDS = (0.10, 0.25, 0.50)
SNOW_IN_HR_THRESHOLDS = (0.5, 1.0, 2.0)
# Rain and snow reach No Travel only when strictly above the top of the Severe range.
RAIN_NO_TRAVEL_ABOVE = 1.00
SNOW_NO_TRAVEL_ABOVE = 3.0

HEAVY_LOAD_LB = 30_000
VERY_HEAVY_LOAD_LB = 40_000


def _level_from_thresholds(value, thresholds):
    level = RiskLevel.LOW
    for index, lower_bound in enumerate(thresholds, start=1):
        if value >= lower_bound:
            level = RiskLevel(index)
    return level


def classify_wind(wind_mph):
    return _level_from_thresholds(wind_mph, WIND_MPH_THRESHOLDS)


def classify_rain(rain_in_hr):
    if rain_in_hr > RAIN_NO_TRAVEL_ABOVE:
        return RiskLevel.NO_TRAVEL
    return _level_from_thresholds(rain_in_hr, RAIN_IN_HR_THRESHOLDS)


def classify_snow(snow_in_hr):
    if snow_in_hr > SNOW_NO_TRAVEL_ABOVE:
        return RiskLevel.NO_TRAVEL
    return _level_from_thresholds(snow_in_hr, SNOW_IN_HR_THRESHOLDS)


def wind_load_level(wind_mph, load_lb):
    """Minimum risk level imposed by the load rules, or LOW when none applies."""
    if wind_mph >= 55:
        return RiskLevel.NO_TRAVEL
    if wind_mph >= 45 and load_lb > HEAVY_LOAD_LB:
        return RiskLevel.NO_TRAVEL
    if wind_mph >= 35 and load_lb > VERY_HEAVY_LOAD_LB:
        return RiskLevel.SEVERE
    return RiskLevel.LOW


@dataclass(frozen=True)
class RiskAssessment:
    level: RiskLevel
    wind: RiskLevel
    rain: RiskLevel
    snow: RiskLevel
    load_adjusted: bool

    @property
    def drivers(self):
        """Factors responsible for the overall level (empty when the level is Low)."""
        if self.level == RiskLevel.LOW:
            return []
        if self.load_adjusted:
            return ["wind+load"]
        factors = {"wind": self.wind, "rain": self.rain, "snow": self.snow}
        return [name for name, level in factors.items() if level == self.level]

    def to_dict(self):
        return {
            "level": int(self.level),
            "label": self.level.label,
            "wind": int(self.wind),
            "rain": int(self.rain),
            "snow": int(self.snow),
            "load_adjusted": self.load_adjusted,
            "drivers": self.drivers,
        }


def assess(wind_mph, rain_in_hr, snow_in_hr, load_lb):
    """Overall checkpoint risk: the worst of wind, rain, snow and the load rules."""
    wind = classify_wind(wind_mph)
    rain = classify_rain(rain_in_hr)
    snow = classify_snow(snow_in_hr)
    weather_level = max(wind, rain, snow)
    load_level = wind_load_level(wind_mph, load_lb)
    return RiskAssessment(
        level=max(weather_level, load_level),
        wind=wind,
        rain=rain,
        snow=snow,
        load_adjusted=load_level > weather_level,
    )


# Points where each factor's score reaches the next level; used for a continuous score.
_WIND_SCORE_POINTS = ((0, 0), (25, 1), (35, 2), (45, 3), (55, 4))
_RAIN_SCORE_POINTS = ((0, 0), (0.10, 1), (0.25, 2), (0.50, 3), (1.00, 4))
_SNOW_SCORE_POINTS = ((0, 0), (0.5, 1), (1.0, 2), (2.0, 3), (3.0, 4))


def _score(value, points):
    if value >= points[-1][0]:
        return float(points[-1][1])
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        if value < x1:
            return y0 + (y1 - y0) * (value - x0) / (x1 - x0)
    return 0.0


def continuous_score(wind_mph, rain_in_hr, snow_in_hr, load_lb):
    """Risk on a 0-4 scale that rises smoothly within each level, for heatmap shading.

    The integer part tracks the level from `assess` (Low=0 ... No Travel=4), so a
    point is never drawn safer than its classification.
    """
    weather = max(
        _score(wind_mph, _WIND_SCORE_POINTS),
        _score(rain_in_hr, _RAIN_SCORE_POINTS),
        _score(snow_in_hr, _SNOW_SCORE_POINTS),
    )
    level = assess(wind_mph, rain_in_hr, snow_in_hr, load_lb).level
    if level == RiskLevel.NO_TRAVEL:
        return 4.0
    # Clamp into the level's band so shading always agrees with the classification.
    return min(max(weather, float(level)), level + 0.99)
