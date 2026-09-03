"""Calculate interpretable priority components for candidate fire events."""

from wildfirewatch.event_metrics import (
    calculate_mean_frp_change,
    calculate_radius_change_km,
)
from wildfirewatch.models import FireEvent


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
