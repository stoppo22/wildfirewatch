"""Tests for metrics derived from fire event history."""

from datetime import datetime, timezone

import pytest

from wildfirewatch.event_metrics import calculate_centroid_path_km
from wildfirewatch.models import EventObservation, FireEvent


def test_calculate_centroid_path_km_sums_consecutive_movements():
    event_observation_a = EventObservation(
        first_seen_utc=datetime(2026, 8, 29, 10, 0, tzinfo=timezone.utc),
        last_seen_utc=datetime(2026, 8, 29, 10, 0, tzinfo=timezone.utc),
        detection_count=1,
        total_frp=10.0,
        centroid_latitude=0.0,
        centroid_longitude=0.0,
    )
    event_observation_b = EventObservation(
        first_seen_utc=datetime(2026, 8, 29, 12, 0, tzinfo=timezone.utc),
        last_seen_utc=datetime(2026, 8, 29, 12, 0, tzinfo=timezone.utc),
        detection_count=1,
        total_frp=10.0,
        centroid_latitude=0.0,
        centroid_longitude=1.0,
    )
    event_observation_c = EventObservation(
        first_seen_utc=datetime(2026, 8, 29, 14, 0, tzinfo=timezone.utc),
        last_seen_utc=datetime(2026, 8, 29, 14, 0, tzinfo=timezone.utc),
        detection_count=1,
        total_frp=10.0,
        centroid_latitude=0.0,
        centroid_longitude=2.0,
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
