"""Group nearby detections into candidate clusters."""

from wildfirewatch.geo import haversine_distance_km
from wildfirewatch.models import Detection


def cluster_detections(
    detections: list[Detection],
    max_distance_km: float,
) -> list[list[Detection]]:
    """Group detections connected within a geographic distance threshold."""
    if not detections:
        return []

    neighbors: list[list[int]] = [[] for _ in detections]
    for first_index in range(len(detections)):
        for second_index in range(first_index + 1, len(detections)):
            first = detections[first_index]
            second = detections[second_index]

            distance_km = haversine_distance_km(
                first.latitude,
                first.longitude,
                second.latitude,
                second.longitude,
            )

            if distance_km <= max_distance_km:
                neighbors[first_index].append(second_index)
                neighbors[second_index].append(first_index)

    visited: set[int] = set()
    clusters: list[list[Detection]] = []

    for index in range(len(neighbors)):
        if index in visited:
            continue

        stack = [index]
        cluster_indices: list[int] = []

        while stack:
            current_index = stack.pop()

            if current_index in visited:
                continue

            visited.add(current_index)
            cluster_indices.append(current_index)
            for neighbor_index in neighbors[current_index]:
                if neighbor_index not in visited:
                    stack.append(neighbor_index)
        cluster = [
            detections[detection_index] for detection_index in sorted(cluster_indices)
        ]
        clusters.append(cluster)

    return clusters
