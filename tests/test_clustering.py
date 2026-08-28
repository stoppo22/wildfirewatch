"""Tests for detection clustering."""

from datetime import datetime, timezone

from wildfirewatch.clustering import cluster_detections
from wildfirewatch.models import Detection


def make_detection(latitude: float, longitude: float) -> Detection:
    """Create a detection with fixed non-geographic fields for tests."""
    return Detection(
        latitude=latitude,
        longitude=longitude,
        acquired_at_utc=datetime(2026, 8, 29, 12, 0, tzinfo=timezone.utc),
        frp=10.0,
        confidence="n",
        satellite="N20",
        day_night="D",
    )


def test_cluster_detections_handles_empty_list():
    actual = cluster_detections([], max_distance_km=5.0)
    assert actual == []


def test_cluster_detections_places_single_detection_in_one_cluster():
    detection = make_detection(latitude=41.9028, longitude=12.4964)

    actual = cluster_detections([detection], max_distance_km=5.0)
    expected = [[detection]]

    assert actual == expected


def test_cluster_detections_groups_nearby_detections():
    first = make_detection(0.0, 0.0)
    second = make_detection(0.0, 0.01)
    detections = [first, second]

    actual = cluster_detections(detections, max_distance_km=1.5)

    assert actual == [[first, second]]


def test_cluster_detections_separates_distant_detections():
    first = make_detection(0.0, 0.0)
    second = make_detection(0.0, 1.0)
    detections = [first, second]

    actual = cluster_detections(detections, max_distance_km=5.0)

    assert actual == [[first], [second]]


def test_cluster_detections_groups_transitively_connected_detections():
    first = make_detection(0.0, 0.0)
    middle = make_detection(0.0, 0.01)
    last = make_detection(0.0, 0.02)
    detections = [first, middle, last]

    actual = cluster_detections(detections, max_distance_km=1.5)

    assert actual == [[first, middle, last]]
