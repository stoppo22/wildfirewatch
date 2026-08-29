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
