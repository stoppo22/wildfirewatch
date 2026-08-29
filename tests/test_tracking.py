"""Tests for event tracking."""

from datetime import datetime, timedelta, timezone

from wildfirewatch.models import Detection, FireEvent
from wildfirewatch.tracking import update_events


def test_update_events_creates_event_when_no_events_exist():
    detection = Detection(
        latitude=10.0,
        longitude=30.0,
        acquired_at_utc=datetime(2026, 8, 29, 12, 0, tzinfo=timezone.utc),
        frp=10.0,
        confidence="n",
        satellite="N20",
        day_night="D",
    )
    cluster = [detection]
    actual = update_events(
        events=[],
        clusters=[cluster],
        max_distance_km=10.0,
        max_time_gap=timedelta(hours=6),
    )
    expected = [
        FireEvent(
            event_id=1,
            first_seen_utc=datetime(2026, 8, 29, 12, 0, tzinfo=timezone.utc),
            last_seen_utc=datetime(2026, 8, 29, 12, 0, tzinfo=timezone.utc),
            centroid_latitude=10.0,
            centroid_longitude=30.0,
            detection_count=1,
        )
    ]

    assert actual == expected


def test_update_events_updates_compatible_existing_event():
    existing_event = FireEvent(
        event_id=7,
        first_seen_utc=datetime(2026, 8, 29, 10, 0, tzinfo=timezone.utc),
        last_seen_utc=datetime(2026, 8, 29, 12, 0, tzinfo=timezone.utc),
        centroid_latitude=10.0,
        centroid_longitude=30.0,
        detection_count=2,
    )
    new_detection = Detection(
        latitude=10.0,
        longitude=30.0,
        acquired_at_utc=datetime(2026, 8, 29, 14, 0, tzinfo=timezone.utc),
        frp=10.0,
        confidence="n",
        satellite="N20",
        day_night="D",
    )
    actual = update_events(
        events=[existing_event],
        clusters=[[new_detection]],
        max_distance_km=10.0,
        max_time_gap=timedelta(hours=6),
    )
    expected = [
        FireEvent(
            event_id=7,
            first_seen_utc=datetime(2026, 8, 29, 10, 0, tzinfo=timezone.utc),
            last_seen_utc=datetime(2026, 8, 29, 14, 0, tzinfo=timezone.utc),
            centroid_latitude=10.0,
            centroid_longitude=30.0,
            detection_count=3,
        )
    ]

    assert actual == expected


def test_update_events_creates_new_event_when_time_gap_is_too_large():
    existing_event = FireEvent(
        event_id=7,
        first_seen_utc=datetime(2026, 8, 29, 10, 0, tzinfo=timezone.utc),
        last_seen_utc=datetime(2026, 8, 29, 12, 0, tzinfo=timezone.utc),
        centroid_latitude=10.0,
        centroid_longitude=30.0,
        detection_count=2,
    )
    new_detection = Detection(
        latitude=10.0,
        longitude=30.0,
        acquired_at_utc=datetime(2026, 8, 29, 20, 0, tzinfo=timezone.utc),
        frp=10.0,
        confidence="n",
        satellite="N20",
        day_night="D",
    )
    actual = update_events(
        events=[existing_event],
        clusters=[[new_detection]],
        max_distance_km=10.0,
        max_time_gap=timedelta(hours=6),
    )

    expected = [
        FireEvent(
            event_id=7,
            first_seen_utc=datetime(2026, 8, 29, 10, 0, tzinfo=timezone.utc),
            last_seen_utc=datetime(2026, 8, 29, 12, 0, tzinfo=timezone.utc),
            centroid_latitude=10.0,
            centroid_longitude=30.0,
            detection_count=2,
        ),
        FireEvent(
            event_id=8,
            first_seen_utc=datetime(2026, 8, 29, 20, 0, tzinfo=timezone.utc),
            last_seen_utc=datetime(2026, 8, 29, 20, 0, tzinfo=timezone.utc),
            centroid_latitude=10.0,
            centroid_longitude=30.0,
            detection_count=1,
        ),
    ]

    assert actual == expected


def test_update_events_creates_new_event_when_distance_is_too_large():
    existing_event = FireEvent(
        event_id=7,
        first_seen_utc=datetime(2026, 8, 29, 10, 0, tzinfo=timezone.utc),
        last_seen_utc=datetime(2026, 8, 29, 12, 0, tzinfo=timezone.utc),
        centroid_latitude=10.0,
        centroid_longitude=30.0,
        detection_count=2,
    )
    new_detection = Detection(
        latitude=11.0,
        longitude=30.0,
        acquired_at_utc=datetime(2026, 8, 29, 14, 0, tzinfo=timezone.utc),
        frp=10.0,
        confidence="n",
        satellite="N20",
        day_night="D",
    )
    actual = update_events(
        events=[existing_event],
        clusters=[[new_detection]],
        max_distance_km=10.0,
        max_time_gap=timedelta(hours=6),
    )

    expected = [
        FireEvent(
            event_id=7,
            first_seen_utc=datetime(2026, 8, 29, 10, 0, tzinfo=timezone.utc),
            last_seen_utc=datetime(2026, 8, 29, 12, 0, tzinfo=timezone.utc),
            centroid_latitude=10.0,
            centroid_longitude=30.0,
            detection_count=2,
        ),
        FireEvent(
            event_id=8,
            first_seen_utc=datetime(2026, 8, 29, 14, 0, tzinfo=timezone.utc),
            last_seen_utc=datetime(2026, 8, 29, 14, 0, tzinfo=timezone.utc),
            centroid_latitude=11.0,
            centroid_longitude=30.0,
            detection_count=1,
        ),
    ]

    assert actual == expected
