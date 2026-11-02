"""Score routes by the risk along them and pick the recommended one.

Ranking, best first (from the assessment, with No Travel placed ahead of Severe because
it is strictly worse):
    1. fewest No Travel miles
    2. fewest Severe miles
    3. fewest High miles
    4. lowest average risk (mile-weighted, Low=0 ... No Travel=4)
    5. shortest travel time
"""

from dataclasses import dataclass

from .risk import RiskLevel

# Mile and risk comparisons are rounded so float noise cannot decide a ranking.
MILES_PRECISION = 1
AVG_RISK_PRECISION = 2


@dataclass(frozen=True)
class RouteScore:
    miles_by_level: dict  # RiskLevel -> miles
    average_risk: float
    max_level: RiskLevel
    duration_s: float

    @property
    def sort_key(self):
        miles = {level: round(m, MILES_PRECISION) for level, m in self.miles_by_level.items()}
        return (
            miles[RiskLevel.NO_TRAVEL],
            miles[RiskLevel.SEVERE],
            miles[RiskLevel.HIGH],
            round(self.average_risk, AVG_RISK_PRECISION),
            self.duration_s,
        )

    def to_dict(self):
        return {
            "miles_by_level": {level.name.lower(): round(m, 1) for level, m in self.miles_by_level.items()},
            "average_risk": round(self.average_risk, 2),
            "max_level": int(self.max_level),
            "max_label": self.max_level.label,
        }


def score_route(segments, duration_s):
    """segments: iterable of (miles, RiskLevel), one per checkpoint."""
    miles_by_level = {level: 0.0 for level in RiskLevel}
    weighted = total = 0.0
    max_level = RiskLevel.LOW
    for miles, level in segments:
        miles_by_level[level] += miles
        weighted += miles * level
        total += miles
        max_level = max(max_level, level)
    return RouteScore(
        miles_by_level=miles_by_level,
        average_risk=weighted / total if total else 0.0,
        max_level=max_level,
        duration_s=duration_s,
    )


_CRITERIA = (
    "fewer No Travel miles",
    "fewer Severe miles",
    "fewer High miles",
    "lower average risk",
    "shorter travel time",
)


def rank(scores):
    """Indices of scores ordered best first (stable for exact ties)."""
    return sorted(range(len(scores)), key=lambda i: scores[i].sort_key)


def explain(best, runner_up):
    """Short reason the best route beat the runner-up, from the first criterion that differs."""
    if runner_up is None:
        return "Only route available."
    for criterion, a, b in zip(_CRITERIA, best.sort_key, runner_up.sort_key):
        if a != b:
            return f"Recommended: {criterion} than the next best route."
    return "Recommended: tied with the next best route on every criterion."
