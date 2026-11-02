"""Trip planning use case: routes -> checkpoints -> weather -> risk -> recommendation."""

from datetime import timedelta

from .checkpoints import sample_checkpoints
from .geometry import METERS_PER_MILE, simplify
from .recommendation import explain, rank, score_route
from .risk import assess
from .services import tomtom, weather

ROUTE_LABELS = ("A", "B", "C")


def plan_trip(origin, destination, departure, load_lb, interval_miles):
    """origin/destination are dicts with lat, lon and label; departure is an aware datetime."""
    routes = tomtom.fetch_routes(
        (origin["lat"], origin["lon"]), (destination["lat"], destination["lon"]), departure, load_lb
    )
    checkpoints_per_route = [sample_checkpoints(route, interval_miles, departure) for route in routes]

    # One batched weather lookup for every checkpoint on every route.
    all_checkpoints = [c for checkpoints in checkpoints_per_route for c in checkpoints]
    forecasts = iter(weather.get_forecasts([(c.lat, c.lon) for c in all_checkpoints]))

    route_payloads, scores = [], []
    for label, route, checkpoints in zip(ROUTE_LABELS, routes, checkpoints_per_route):
        checkpoint_payloads, segments = [], []
        for checkpoint in checkpoints:
            conditions = next(forecasts).at(checkpoint.eta)
            risk = assess(conditions.wind_mph, conditions.rain_in_hr, conditions.snow_in_hr, load_lb)
            segments.append((checkpoint.segment_miles, risk.level))
            checkpoint_payloads.append(
                {
                    "index": checkpoint.index,
                    "mile": round(checkpoint.mile, 1),
                    "lat": round(checkpoint.lat, 5),
                    "lon": round(checkpoint.lon, 5),
                    "eta": _iso(checkpoint.eta),
                    "segment_miles": round(checkpoint.segment_miles, 2),
                    "weather": conditions.to_dict(),
                    "risk": risk.to_dict(),
                }
            )
        score = score_route(segments, route.duration_s)
        scores.append(score)
        route_payloads.append(
            {
                "id": label,
                "distance_miles": round(route.distance_m / METERS_PER_MILE, 1),
                "duration_s": round(route.duration_s),
                "departure": _iso(departure),
                "arrival": _iso(departure + timedelta(seconds=route.duration_s)),
                # GeoJSON order: [lon, lat].
                "geometry": [[round(lon, 5), round(lat, 5)] for lat, lon in simplify(route.points)],
                "score": score.to_dict(),
                "checkpoints": checkpoint_payloads,
            }
        )

    order = rank(scores)
    for position, index in enumerate(order, start=1):
        route_payloads[index]["rank"] = position
        route_payloads[index]["recommended"] = position == 1
    best = order[0]
    runner_up = scores[order[1]] if len(order) > 1 else None

    return {
        "origin": origin,
        "destination": destination,
        "departure": _iso(departure),
        "load_lb": load_lb,
        "interval_miles": interval_miles,
        "recommended_route_id": route_payloads[best]["id"],
        "recommendation_reason": explain(scores[best], runner_up),
        "routes": route_payloads,
    }


def _iso(moment):
    return moment.replace(microsecond=0).isoformat().replace("+00:00", "Z")
