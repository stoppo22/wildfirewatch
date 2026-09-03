"""Calculate interpretable priority components for candidate fire events."""

from dataclasses import dataclass
from math import isclose

from wildfirewatch.event_metrics import (
    calculate_mean_frp_change,
    calculate_radius_change_km,
)
from wildfirewatch.models import FireEvent


@dataclass(frozen=True)
class ScoringConfig:
    """Store explicit normalization thresholds and point weights."""

    full_score_hours: float = 24.0
    full_score_mean_frp_increase: float = 20.0
    full_score_radius_increase_km: float = 2.0
    persistence_weight: float = 40.0
    frp_trend_weight: float = 35.0
    spatial_growth_weight: float = 25.0

    def __post_init__(self) -> None:
        weights = (
            self.persistence_weight,
            self.frp_trend_weight,
            self.spatial_growth_weight,
        )
        if any(weight < 0 for weight in weights):
            raise ValueError("scoring weights must not be negative")
        if not isclose(sum(weights), 100.0):
            raise ValueError("scoring weights must sum to 100")


@dataclass(frozen=True)
class PriorityScore:
    """Store a total review-priority score and its point contributions."""

    total: float
    persistence_points: float
    frp_trend_points: float
    spatial_growth_points: float


def calculate_persistence_component(
    event: FireEvent,
    full_score_hours: float,
) -> float:
    """Normalize event duration against the configured full-score duration."""
    if full_score_hours <= 0:
        raise ValueError("full_score_hours must be positive")

    duration_hours = event.duration.total_seconds() / 3600
    raw_component = duration_hours / full_score_hours

    return min(max(raw_component, 0.0), 1.0)


def calculate_frp_trend_component(
    event: FireEvent,
    full_score_mean_frp_increase: float,
) -> float:
    """Normalize positive mean-FRP change against its full-score increase."""
    if full_score_mean_frp_increase <= 0:
        raise ValueError("full_score_mean_frp_increase must be positive")

    mean_frp_change = calculate_mean_frp_change(event)
    raw_component = mean_frp_change / full_score_mean_frp_increase

    return min(max(raw_component, 0.0), 1.0)


def calculate_spatial_growth_component(
    event: FireEvent,
    full_score_radius_increase_km: float,
) -> float:
    """Normalize positive radius growth against its full-score increase."""
    if full_score_radius_increase_km <= 0:
        raise ValueError("full_score_radius_increase_km must be positive")

    radius_change_km = calculate_radius_change_km(event)
    raw_component = radius_change_km / full_score_radius_increase_km

    return min(max(raw_component, 0.0), 1.0)


def calculate_priority_score(
    event: FireEvent,
    config: ScoringConfig = ScoringConfig(),
) -> PriorityScore:
    """Calculate an explainable 0-100 review-priority score for an event."""
    persistence_component = calculate_persistence_component(
        event,
        config.full_score_hours,
    )
    frp_trend_component = calculate_frp_trend_component(
        event,
        config.full_score_mean_frp_increase,
    )
    spatial_growth_component = calculate_spatial_growth_component(
        event,
        config.full_score_radius_increase_km,
    )

    persistence_points = persistence_component * config.persistence_weight
    frp_trend_points = frp_trend_component * config.frp_trend_weight
    spatial_growth_points = spatial_growth_component * config.spatial_growth_weight

    total = persistence_points + frp_trend_points + spatial_growth_points

    return PriorityScore(
        total=total,
        persistence_points=persistence_points,
        frp_trend_points=frp_trend_points,
        spatial_growth_points=spatial_growth_points,
    )
