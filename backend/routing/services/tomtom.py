"""TomTom geocoding and truck routing.

Docs: https://developer.tomtom.com/search-api/documentation and
https://developer.tomtom.com/routing-api/documentation
"""

import hashlib
import json
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from urllib.parse import quote

from django.conf import settings
from django.core.cache import cache

from .http import ExternalServiceError, get_json

SEARCH_URL = "https://api.tomtom.com/search/2/search/{query}.json"
ROUTE_URL = "https://api.tomtom.com/routing/1/calculateRoute/{locations}/json"

LB_TO_KG = 0.45359237
# The user enters cargo weight; TomTom wants gross vehicle weight.
# Assume a typical empty tractor-trailer (tare) of 35,000 lb.
TRUCK_TARE_LB = 35_000

ROUTE_OPTIONS = 3
# Detour offsets (fraction of the straight-line distance) used when TomTom returns
# fewer than ROUTE_OPTIONS alternatives: left/right of the midpoint, then wider.
FALLBACK_DETOUR_OFFSETS = (0.15, -0.15, 0.3, -0.3)
# Routes whose length and duration both differ by less than this are treated as duplicates.
DUPLICATE_TOLERANCE = 0.01

DEPARTURE_ROUNDING_MINUTES = 15

GEOCODE_CACHE_SECONDS = 24 * 60 * 60
ROUTE_CACHE_SECONDS = 10 * 60


@dataclass
class Route:
    distance_m: float
    duration_s: float
    departure: str
    arrival: str
    # (lat, lon) pairs along the route.
    points: list
    # (offset_m, elapsed_s) pairs, increasing; used to estimate arrival time anywhere on the route.
    time_profile: list = field(default_factory=list)


def _api_key():
    if not settings.TOMTOM_API_KEY:
        raise ExternalServiceError("TOMTOM_API_KEY is not configured.", status_code=500)
    return settings.TOMTOM_API_KEY


def _cache_key(prefix, payload):
    digest = hashlib.sha1(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    return f"{prefix}:{digest}"


def geocode(query, limit=5):
    """Place suggestions for free text, limited to the US (and neighbours) for trucking."""
    query = query.strip()
    if len(query) < 2:
        return []
    key = _cache_key("geocode", [query.lower(), limit])
    cached = cache.get(key)
    if cached is not None:
        return cached

    data = get_json(
        SEARCH_URL.format(query=quote(query, safe="")),
        params={
            "key": _api_key(),
            "limit": limit,
            "typeahead": "true",
            "countrySet": "US,CA,MX",
            "idxSet": "Geo,PAD,Addr,Str,POI",
        },
        service="TomTom search",
    )
    results = [
        {
            "label": item["address"].get("freeformAddress") or item.get("poi", {}).get("name", query),
            "lat": item["position"]["lat"],
            "lon": item["position"]["lon"],
        }
        for item in data.get("results", [])
    ]
    cache.set(key, results, GEOCODE_CACHE_SECONDS)
    return results


def fetch_routes(origin, destination, depart_at, load_lb):
    """Up to ROUTE_OPTIONS distinct truck routes, fastest first.

    origin/destination are (lat, lon); depart_at is an aware datetime.
    """
    params = _route_params(depart_at, load_lb)
    key = _cache_key("routes", [origin, destination, params])
    cached = cache.get(key)
    if cached is not None:
        return cached

    routes = _request_routes([origin, destination], params, max_alternatives=ROUTE_OPTIONS - 1)
    for offset in FALLBACK_DETOUR_OFFSETS:
        if len(routes) >= ROUTE_OPTIONS:
            break
        via = _detour_point(origin, destination, offset)
        try:
            candidates = _request_routes([origin, via, destination], params, max_alternatives=0)
        except ExternalServiceError:
            continue  # e.g. the detour point is unreachable (water); try the next one
        routes.extend(c for c in candidates if not _is_duplicate(c, routes))

    if not routes:
        raise ExternalServiceError("No truck route found between these locations.", status_code=404)
    routes = sorted(routes, key=lambda r: r.duration_s)[:ROUTE_OPTIONS]
    cache.set(key, routes, ROUTE_CACHE_SECONDS)
    return routes


def _route_params(depart_at, load_lb):
    now = datetime.now(timezone.utc)
    gross_kg = round((TRUCK_TARE_LB + load_lb) * LB_TO_KG)
    # Truck alternatives take TomTom several seconds. Rounding the departure lets nearby
    # requests share a cached result; checkpoint ETAs still use the exact departure.
    depart_at = depart_at.replace(
        minute=depart_at.minute - depart_at.minute % DEPARTURE_ROUNDING_MINUTES, second=0, microsecond=0
    )
    return {
        "travelMode": "truck",
        "vehicleCommercial": "true",
        "vehicleWeight": gross_kg,
        "routeType": "fastest",
        "traffic": "true",
        # TomTom rejects departure times in the past.
        "departAt": "now" if depart_at <= now else depart_at.astimezone(timezone.utc).isoformat(timespec="seconds"),
        "instructionsType": "coded",
        "computeTravelTimeFor": "none",
    }


def _request_routes(locations, params, max_alternatives):
    path = ":".join(f"{lat:.6f},{lon:.6f}" for lat, lon in locations)
    data = get_json(
        ROUTE_URL.format(locations=path),
        params={"key": _api_key(), "maxAlternatives": max_alternatives, **params},
        service="TomTom routing",
    )
    return [parse_route(item) for item in data.get("routes", [])]


def parse_route(item):
    summary = item["summary"]
    points = [(p["latitude"], p["longitude"]) for leg in item["legs"] for p in leg["points"]]
    distance = float(summary["lengthInMeters"])
    duration = float(summary["travelTimeInSeconds"])

    profile = [(0.0, 0.0)]
    for instruction in item.get("guidance", {}).get("instructions", []):
        offset = float(instruction["routeOffsetInMeters"])
        elapsed = float(instruction["travelTimeInSeconds"])
        if offset > profile[-1][0] and elapsed >= profile[-1][1]:
            profile.append((offset, elapsed))
    if profile[-1][0] < distance:
        profile.append((distance, duration))

    return Route(
        distance_m=distance,
        duration_s=duration,
        departure=summary["departureTime"],
        arrival=summary["arrivalTime"],
        points=points,
        time_profile=profile,
    )


def _detour_point(origin, destination, offset_fraction):
    """A point beside the origin-destination midpoint, offset perpendicular to the straight line."""
    (lat1, lon1), (lat2, lon2) = origin, destination
    mid_lat, mid_lon = (lat1 + lat2) / 2, (lon1 + lon2) / 2
    # Work in a locally flat frame where one unit is roughly one degree of latitude.
    scale = math.cos(math.radians(mid_lat))
    dx, dy = (lon2 - lon1) * scale, lat2 - lat1
    return (mid_lat + dx * offset_fraction, mid_lon - dy * offset_fraction / scale)


def _is_duplicate(candidate, routes):
    return any(
        abs(candidate.distance_m - r.distance_m) / r.distance_m < DUPLICATE_TOLERANCE
        and abs(candidate.duration_s - r.duration_s) / r.duration_s < DUPLICATE_TOLERANCE
        for r in routes
    )
