"""Calculate metrics derived from fire event history."""

from wildfirewatch.geo import haversine_distance_km
from wildfirewatch.models import FireEvent


def calculate_centroid_path_km(event: FireEvent) -> float:
    """Return the total path between consecutive event centroids."""
    total_distance_km = 0.0
    for previous, current in zip(
        event.observations,
        event.observations[1:],
    ):
        total_distance_km += haversine_distance_km(
            previous.centroid_latitude,
            previous.centroid_longitude,
            current.centroid_latitude,
            current.centroid_longitude,
        )

    return total_distance_km


def calculate_radius_change_km(event: FireEvent) -> float:
    """Return the radius difference between the last and first observation."""
    if len(event.observations) < 2:
        return 0.0

    first_observation = event.observations[0]
    last_observation = event.observations[-1]

    return last_observation.max_radius_km - first_observation.max_radius_km


def calculate_mean_frp_change(event: FireEvent) -> float:
    """Return the change in mean FRP per detection from first to last observation."""
    if len(event.observations) < 2:
        return 0.0

    first_observation = event.observations[0]
    last_observation = event.observations[-1]

    if first_observation.detection_count <= 0 or last_observation.detection_count <= 0:
        raise ValueError("observation detection_count must be positive")

    first_mean_frp = first_observation.total_frp / first_observation.detection_count
    last_mean_frp = last_observation.total_frp / last_observation.detection_count

    return last_mean_frp - first_mean_frp
