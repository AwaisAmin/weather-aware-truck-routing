import pytest

from routing.risk import RiskLevel, assess, classify_rain, classify_snow, classify_wind

L, M, H, S, N = (
    RiskLevel.LOW,
    RiskLevel.MODERATE,
    RiskLevel.HIGH,
    RiskLevel.SEVERE,
    RiskLevel.NO_TRAVEL,
)


@pytest.mark.parametrize(
    "mph, expected",
    [(0, L), (24.9, L), (25, M), (34.9, M), (35, H), (44.9, H), (45, S), (54.9, S), (55, N), (80, N)],
)
def test_classify_wind(mph, expected):
    assert classify_wind(mph) == expected


@pytest.mark.parametrize(
    "inches, expected",
    [(0, L), (0.09, L), (0.10, M), (0.24, M), (0.25, H), (0.49, H), (0.50, S), (1.00, S), (1.01, N)],
)
def test_classify_rain(inches, expected):
    assert classify_rain(inches) == expected


@pytest.mark.parametrize(
    "inches, expected",
    [(0, L), (0.49, L), (0.5, M), (0.99, M), (1.0, H), (1.99, H), (2.0, S), (3.0, S), (3.01, N)],
)
def test_classify_snow(inches, expected):
    assert classify_snow(inches) == expected


def test_overall_level_is_worst_factor():
    result = assess(wind_mph=10, rain_in_hr=0.3, snow_in_hr=2.5, load_lb=10_000)
    assert result.level == S
    assert result.drivers == ["snow"]
    assert not result.load_adjusted


def test_calm_weather_is_low_with_no_drivers():
    result = assess(wind_mph=5, rain_in_hr=0, snow_in_hr=0, load_lb=45_000)
    assert result.level == L
    assert result.drivers == []


@pytest.mark.parametrize(
    "wind, load, expected, adjusted",
    [
        # >=55 mph: No Travel for any load (already No Travel by the wind table).
        (55, 1_000, N, False),
        # 45-54 mph: No Travel only above 30,000 lb.
        (45, 30_000, S, False),
        (45, 30_001, N, True),
        (54.9, 35_000, N, True),
        # 35-44 mph: Severe only above 40,000 lb.
        (35, 40_000, H, False),
        (35, 40_001, S, True),
        (44.9, 50_000, S, True),
        # Below 35 mph the load does not matter.
        (34.9, 80_000, M, False),
    ],
)
def test_load_rules(wind, load, expected, adjusted):
    result = assess(wind_mph=wind, rain_in_hr=0, snow_in_hr=0, load_lb=load)
    assert result.level == expected
    assert result.load_adjusted is adjusted


def test_load_rule_does_not_lower_worse_weather():
    result = assess(wind_mph=40, rain_in_hr=1.5, snow_in_hr=0, load_lb=45_000)
    assert result.level == N
    assert result.drivers == ["rain"]
    assert not result.load_adjusted


def test_to_dict_shape():
    data = assess(wind_mph=40, rain_in_hr=0, snow_in_hr=0, load_lb=45_000).to_dict()
    assert data == {
        "level": 3,
        "label": "Severe",
        "wind": 2,
        "rain": 0,
        "snow": 0,
        "load_adjusted": True,
        "drivers": ["wind+load"],
    }
