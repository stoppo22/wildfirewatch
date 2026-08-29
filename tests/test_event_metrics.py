"""Tests for metrics derived from fire event history."""

from datetime import datetime, timezone

import pytest

from wildfirewatch.event_metrics import (
    calculate_centroid_path_km,
    calculate_radius_change_km,
)
from wildfirewatch.models import EventObservation, FireEvent


def test_calculate_centroid_path_km_sums_consecutive_movements():
    event_observation_a = EventObservation(
        first_seen_utc=datetime(2026, 8, 29, 10, 0, tzinfo=timezone.utc),
        last_seen_utc=datetime(2026, 8, 29, 10, 0, tzinfo=timezone.utc),
        detection_count=1,
        total_frp=10.0,
        centroid_latitude=0.0,
        centroid_longitude=0.0,
        max_radius_km=0.0,
    )
    event_observation_b = EventObservation(
        first_seen_utc=datetime(2026, 8, 29, 12, 0, tzinfo=timezone.utc),
        last_seen_utc=datetime(2026, 8, 29, 12, 0, tzinfo=timezone.utc),
        detection_count=1,
        total_frp=10.0,
        centroid_latitude=0.0,
        centroid_longitude=1.0,
        max_radius_km=0.0,
    )
    event_observation_c = EventObservation(
        first_seen_utc=datetime(2026, 8, 29, 14, 0, tzinfo=timezone.utc),
        last_seen_utc=datetime(2026, 8, 29, 14, 0, tzinfo=timezone.utc),
        detection_count=1,
        total_frp=10.0,
        centroid_latitude=0.0,
        centroid_longitude=2.0,
        max_radius_km=0.0,
    )
    event = FireEvent(
        event_id=1,
        first_seen_utc=datetime(2026, 8, 29, 10, 0, tzinfo=timezone.utc),
        last_seen_utc=datetime(2026, 8, 29, 14, 0, tzinfo=timezone.utc),
        centroid_latitude=0.0,
        centroid_longitude=1.0,
        detection_count=3,
        observations=[
            event_observation_a,
            event_observation_b,
            event_observation_c,
        ],
    )

    actual = calculate_centroid_path_km(event)
    expected = 222.39

    assert actual == pytest.approx(expected, abs=0.1)


def test_calculate_radius_change_km_compares_first_and_last_observation():
    first = EventObservation(
        first_seen_utc=datetime(2026, 8, 29, 10, 0, tzinfo=timezone.utc),
        last_seen_utc=datetime(2026, 8, 29, 10, 0, tzinfo=timezone.utc),
        detection_count=1,
        total_frp=10.0,
        centroid_latitude=0.0,
        centroid_longitude=2.0,
        max_radius_km=2.0,
    )
    second = EventObservation(
        first_seen_utc=datetime(2026, 8, 29, 14, 0, tzinfo=timezone.utc),
        last_seen_utc=datetime(2026, 8, 29, 14, 0, tzinfo=timezone.utc),
        detection_count=1,
        total_frp=10.0,
        centroid_latitude=0.0,
        centroid_longitude=2.0,
        max_radius_km=5.0,
    )
    event = FireEvent(
        event_id=1,
        first_seen_utc=datetime(2026, 8, 29, 10, 0, tzinfo=timezone.utc),
        last_seen_utc=datetime(2026, 8, 29, 14, 0, tzinfo=timezone.utc),
        centroid_latitude=0.0,
        centroid_longitude=2.0,
        detection_count=2,
        observations=[
            first,
            second,
        ],
    )

    actual = calculate_radius_change_km(event)
    expected = 3.0

    assert actual == expected


def test_history_metrics_are_zero_without_observations():
    event = FireEvent(
        event_id=1,
        first_seen_utc=datetime(2026, 8, 29, 10, 0, tzinfo=timezone.utc),
        last_seen_utc=datetime(2026, 8, 29, 10, 0, tzinfo=timezone.utc),
        centroid_latitude=0.0,
        centroid_longitude=0.0,
        detection_count=0,
    )

    assert calculate_centroid_path_km(event) == 0.0
    assert calculate_radius_change_km(event) == 0.0
