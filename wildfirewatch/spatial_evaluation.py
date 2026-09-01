"""Utilities for spatial reference evaluation."""

from wildfirewatch.models import Detection


def point_in_polygon(
    longitude: float,
    latitude: float,
    ring: list[list[float]],
) -> bool:
    if len(ring) < 3:
        return False

    inside = False
    previous_index = len(ring) - 1

    for current_index in range(len(ring)):
        current_longitude, current_latitude = ring[current_index]
        previous_longitude, previous_latitude = ring[previous_index]

        if point_on_segment(
            longitude=longitude,
            latitude=latitude,
            start_longitude=previous_longitude,
            start_latitude=previous_latitude,
            end_longitude=current_longitude,
            end_latitude=current_latitude,
        ):
            return True

        crosses_latitude = (current_latitude > latitude) != (
            previous_latitude > latitude
        )

        if crosses_latitude:
            intersection_longitude = previous_longitude + (
                latitude - previous_latitude
            ) * (current_longitude - previous_longitude) / (
                current_latitude - previous_latitude
            )

            if longitude < intersection_longitude:
                inside = not inside

        previous_index = current_index

    return inside


def point_on_segment(
    longitude: float,
    latitude: float,
    start_longitude: float,
    start_latitude: float,
    end_longitude: float,
    end_latitude: float,
) -> bool:
    cross_product = (latitude - start_latitude) * (end_longitude - start_longitude) - (
        longitude - start_longitude
    ) * (end_latitude - start_latitude)

    if abs(cross_product) > 1e-12:
        return False

    within_longitude = (
        min(start_longitude, end_longitude)
        <= longitude
        <= max(start_longitude, end_longitude)
    )

    within_latitude = (
        min(start_latitude, end_latitude)
        <= latitude
        <= max(start_latitude, end_latitude)
    )

    return within_longitude and within_latitude


def detection_coverage_ratio(
    detections: list[Detection],
    ring: list[list[float]],
) -> float | None:
    if not detections:
        return None

    inside_count = 0

    for detection in detections:
        if point_in_polygon(
            longitude=detection.longitude,
            latitude=detection.latitude,
            ring=ring,
        ):
            inside_count += 1

    return inside_count / len(detections)
