"""Geographic distance calculations."""

from math import atan2, cos, radians, sin, sqrt

EARTH_RADIUS_KM = 6371.0


def haversine_distance_km(
    latitude_1: float,
    longitude_1: float,
    latitude_2: float,
    longitude_2: float,
) -> float:
    """Return the geographic distance between two points in kilometres."""
    latitude_1_rad = radians(latitude_1)
    latitude_2_rad = radians(latitude_2)
    latitude_difference = radians(latitude_2 - latitude_1)
    longitude_difference = radians(longitude_2 - longitude_1)
    haversine_value = (
        sin(latitude_difference / 2) ** 2
        + cos(latitude_1_rad) * cos(latitude_2_rad) * sin(longitude_difference / 2) ** 2
    )
    central_angle = 2 * atan2(
        sqrt(haversine_value),
        sqrt(1 - haversine_value),
    )
    return EARTH_RADIUS_KM * central_angle
