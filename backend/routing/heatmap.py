"""Weather risk on a grid covering the trip corridor, hour by hour from departure."""

import math
from datetime import timedelta

from .risk import continuous_score
from .services import weather

HOURS = 48
# Grid cells within this distance of any route are included (~40 miles).
CORRIDOR_DEGREES = 0.6
# Grid spacing is a multiple of the weather cache grid so cells reuse cached forecasts.
SPACING_STEP_DEGREES = 0.1
MIN_SPACING_DEGREES = 0.2
# Open-Meteo counts each location as one call (free tier: ~600 per minute).
MAX_CELLS = 300


def corridor_cells(routes, buffer_deg=CORRIDOR_DEGREES, max_cells=MAX_CELLS):
    """Grid (lat, lon) cells within buffer_deg of any route, and the grid spacing used.

    routes: lists of (lat, lon) points. Spacing grows until the corridor fits in max_cells.
    """
    points = [p for route in routes for p in route]
    lats = [p[0] for p in points]
    lons = [p[1] for p in points]
    south, north = min(lats) - buffer_deg, max(lats) + buffer_deg
    west, east = min(lons) - buffer_deg, max(lons) + buffer_deg

    spacing = MIN_SPACING_DEGREES
    while True:
        cells = _cells_near(points, south, north, west, east, spacing, buffer_deg)
        if len(cells) <= max_cells:
            return cells, spacing
        spacing = round(spacing + SPACING_STEP_DEGREES, 1)


def _cells_near(points, south, north, west, east, spacing, buffer_deg):
    # Bucket route points by grid cell so each cell only checks nearby points.
    buckets = {}
    for lat, lon in points:
        buckets.setdefault((math.floor(lat / buffer_deg), math.floor(lon / buffer_deg)), []).append((lat, lon))

    def near_route(lat, lon):
        scale = math.cos(math.radians(lat))
        bi, bj = math.floor(lat / buffer_deg), math.floor(lon / buffer_deg)
        for di in (-1, 0, 1):
            for dj in (-1, 0, 1):
                for plat, plon in buckets.get((bi + di, bj + dj), ()):
                    if (lat - plat) ** 2 + ((lon - plon) * scale) ** 2 <= buffer_deg**2:
                        return True
        return False

    cells = []
    lat = math.floor(south / spacing) * spacing
    while lat <= north:
        lon = math.floor(west / spacing) * spacing
        while lon <= east:
            if near_route(lat, lon):
                cells.append((round(lat, 4), round(lon, 4)))
            lon += spacing
        lat += spacing
    return cells


def build_heatmap(routes, departure, load_lb, hours=HOURS):
    """Risk scores (0-4) for each corridor cell at each hour from departure.

    routes: lists of (lat, lon); departure: aware datetime.
    """
    start = departure.replace(minute=0, second=0, microsecond=0)
    cells, spacing = corridor_cells(routes)
    forecasts = weather.get_forecasts(cells)
    times = [start + timedelta(hours=h) for h in range(hours + 1)]

    scores = []
    for forecast in forecasts:
        row = []
        for moment in times:
            c = forecast.at(moment)
            # Tenths keep the payload small; the map only needs this precision.
            row.append(round(continuous_score(c.wind_mph, c.rain_in_hr, c.snow_in_hr, load_lb) * 10))
        scores.append(row)

    return {
        "start": start.isoformat().replace("+00:00", "Z"),
        "hours": hours,
        "spacing_deg": spacing,
        # [lon, lat] (GeoJSON order) per cell; scores[i][h] is cell i at start + h hours, x10.
        "cells": [[lon, lat] for lat, lon in cells],
        "scores": scores,
    }
