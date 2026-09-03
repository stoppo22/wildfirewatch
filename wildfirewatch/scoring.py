"""Calculate interpretable priority components for candidate fire events."""

from wildfirewatch.models import FireEvent


def calculate_persistence_component(
    event: FireEvent,
    full_score_hours: float,
) -> float:
    if full_score_hours <= 0:
        raise ValueError("full_score_hours must be positive")

    duration_hours = event.duration.total_seconds() / 3600
    raw_component = duration_hours / full_score_hours

    return min(max(raw_component, 0.0), 1.0)
