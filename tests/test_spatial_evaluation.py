"""Tests for spatial evaluation utilities."""

import pytest
from datetime import datetime, timezone

from wildfirewatch.models import Detection
from wildfirewatch.spatial_evaluation import point_in_polygon, detection_coverage_ratio


def test_point_outside_square():
    square = [
        [-1.0, -1.0],
        [1.0, -1.0],
        [1.0, 1.0],
        [-1.0, 1.0],
        [-1.0, -1.0],
    ]

    actual = point_in_polygon(2.0, 0.0, square)

    assert actual is False


def test_point_inside_square():
    square = [
        [-1.0, -1.0],
        [1.0, -1.0],
        [1.0, 1.0],
        [-1.0, 1.0],
        [-1.0, -1.0],
    ]

    actual = point_in_polygon(0.0, 0.0, square)

    assert actual is True


def test_empty_ring_returns_false():
    actual = point_in_polygon(0.0, 0.0, [])

    assert actual is False


def test_point_on_boundary_is_inside():
    rectangle = [
        [10.0, 0.0],
        [20.0, 0.0],
        [20.0, 1.0],
        [10.0, 1.0],
        [10.0, 0.0],
    ]

    actual = point_in_polygon(20.0, 0.5, rectangle)

    assert actual is True


def test_detection_coverage_is_none_without_detections():
    actual = detection_coverage_ratio([], [])

    assert actual is None


def make_detection(latitude: float, longitude: float) -> Detection:
    detection = Detection(
        latitude=latitude,
        longitude=longitude,
        acquired_at_utc=datetime(2023, 8, 9, tzinfo=timezone.utc),
        frp=10.0,
        confidence="nominal",
        satellite="NOAA-20",
        day_night="D",
    )

    return detection


def test_detection_coverage_counts_inside_detections():
    square = [
        [-1.0, -1.0],
        [1.0, -1.0],
        [1.0, 1.0],
        [-1.0, 1.0],
        [-1.0, -1.0],
    ]

    detections = [
        make_detection(latitude=0.0, longitude=0.0),
        make_detection(latitude=0.0, longitude=1.0),
        make_detection(latitude=0.0, longitude=2.0),
    ]

    actual = detection_coverage_ratio(detections=detections, ring=square)

    assert actual == pytest.approx(2 / 3)
