"""Tests for WildfireWatch domain models."""

from datetime import datetime, timedelta, timezone

from wildfirewatch.models import Detection, FireEvent


def test_detection_stores_latitude():
    detection = Detection(
        latitude=41.9,
        longitude=12.5,
        acquired_at_utc=datetime(2026, 8, 28, 12, 30, tzinfo=timezone.utc),
        frp=12.4,
        confidence="nominal",
        satellite="Suomi NPP",
        day_night="D",
    )

    assert detection.latitude == 41.9


def test_fire_event_duration_is_time_between_first_and_last_seen():
    event = FireEvent(
        event_id=1,
        first_seen_utc=datetime(2026, 8, 29, 10, 0, tzinfo=timezone.utc),
        last_seen_utc=datetime(2026, 8, 29, 14, 0, tzinfo=timezone.utc),
        centroid_latitude=10.0,
        centroid_longitude=30.0,
        detection_count=1,
    )

    actual = event.duration
    expected = timedelta(hours=4)

    assert actual == expected
