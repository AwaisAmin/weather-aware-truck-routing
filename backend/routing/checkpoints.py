"""Place weather checkpoints along a route and estimate when the truck reaches each one."""

from dataclasses import dataclass
from datetime import timedelta

from .geometry import METERS_PER_MILE, cumulative_distances, interpolate, point_at_distance

SAMPLE_INTERVALS_MILES = (10, 25, 50)


@dataclass(frozen=True)
class Checkpoint:
    index: int
    mile: float
    lat: float
    lon: float
    eta: object  # aware datetime
    # Route miles this checkpoint's weather stands for (half the gap to each neighbour).
    segment_miles: float


def sample_checkpoints(route, interval_miles, departure):
    """Checkpoints every interval_miles from the origin, plus one at the destination.

    route is a tomtom.Route; departure is the aware datetime the truck leaves.
    """
    if interval_miles not in SAMPLE_INTERVALS_MILES:
        raise ValueError(f"interval_miles must be one of {SAMPLE_INTERVALS_MILES}")

    distances = cumulative_distances(route.points)
    # Our straight-segment length differs slightly from TomTom's; rescale so mile
    # markers line up with TomTom's distance and timing data.
    scale = route.distance_m / distances[-1] if distances[-1] else 1.0
    distances = [d * scale for d in distances]

    total_m = route.distance_m
    step_m = interval_miles * METERS_PER_MILE
    offsets = [i * step_m for i in range(int(total_m // step_m) + 1)]
    if total_m - offsets[-1] > 1:
        offsets.append(total_m)

    profile_offsets = [o for o, _ in route.time_profile]
    profile_times = [t for _, t in route.time_profile]

    checkpoints = []
    for index, offset in enumerate(offsets):
        previous_gap = offset - offsets[index - 1] if index > 0 else 0.0
        next_gap = offsets[index + 1] - offset if index + 1 < len(offsets) else 0.0
        lat, lon = point_at_distance(route.points, distances, offset)
        elapsed_s = interpolate(profile_offsets, profile_times, offset)
        checkpoints.append(
            Checkpoint(
                index=index,
                mile=offset / METERS_PER_MILE,
                lat=lat,
                lon=lon,
                eta=departure + timedelta(seconds=elapsed_s),
                segment_miles=(previous_gap + next_gap) / 2 / METERS_PER_MILE,
            )
        )
    return checkpoints
