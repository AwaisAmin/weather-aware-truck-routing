"""Small geodesic helpers for polylines of (lat, lon) points."""

import math
from bisect import bisect_right

EARTH_RADIUS_M = 6_371_008.8
METERS_PER_MILE = 1609.344


def haversine_m(a, b):
    lat1, lon1 = map(math.radians, a)
    lat2, lon2 = map(math.radians, b)
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(h))


def cumulative_distances(points):
    """Distance in meters from the first point to each point."""
    distances = [0.0]
    for previous, current in zip(points, points[1:]):
        distances.append(distances[-1] + haversine_m(previous, current))
    return distances


def interpolate(xs, ys, x):
    """Piecewise-linear y at x; xs must be increasing. Clamps outside the range."""
    if x <= xs[0]:
        return ys[0]
    if x >= xs[-1]:
        return ys[-1]
    i = bisect_right(xs, x)
    x0, x1, y0, y1 = xs[i - 1], xs[i], ys[i - 1], ys[i]
    return y0 if x1 == x0 else y0 + (y1 - y0) * (x - x0) / (x1 - x0)


def point_at_distance(points, distances, target_m):
    """The (lat, lon) located target_m along the polyline."""
    if target_m <= 0:
        return points[0]
    if target_m >= distances[-1]:
        return points[-1]
    i = bisect_right(distances, target_m)
    d0, d1 = distances[i - 1], distances[i]
    t = 0.0 if d1 == d0 else (target_m - d0) / (d1 - d0)
    (lat0, lon0), (lat1, lon1) = points[i - 1], points[i]
    return (lat0 + (lat1 - lat0) * t, lon0 + (lon1 - lon0) * t)


def simplify(points, tolerance_deg=0.0005):
    """Ramer-Douglas-Peucker simplification (iterative), keeping endpoints.

    The default tolerance is about 50 m, invisible at route-overview zoom levels.
    """
    if len(points) < 3:
        return list(points)
    keep = [False] * len(points)
    keep[0] = keep[-1] = True
    stack = [(0, len(points) - 1)]
    while stack:
        start, end = stack.pop()
        (ay, ax), (by, bx) = points[start], points[end]
        dx, dy = bx - ax, by - ay
        length_sq = dx * dx + dy * dy
        max_dist, index = 0.0, None
        for i in range(start + 1, end):
            py, px = points[i]
            if length_sq == 0:
                dist = math.hypot(px - ax, py - ay)
            else:
                dist = abs(dy * (px - ax) - dx * (py - ay)) / math.sqrt(length_sq)
            if dist > max_dist:
                max_dist, index = dist, i
        if index is not None and max_dist > tolerance_deg:
            keep[index] = True
            stack.append((start, index))
            stack.append((index, end))
    return [p for p, k in zip(points, keep) if k]
