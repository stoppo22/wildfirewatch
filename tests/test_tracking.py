"""Tests for event tracking."""

from datetime import datetime, timedelta, timezone

from wildfirewatch.models import Detection, EventObservation, FireEvent
from wildfirewatch.summary import summarize_cluster
from wildfirewatch.tracking import (
    match_clusters_one_to_one,
    update_events,
    update_events_one_to_one,
)


def make_detection(
    latitude: float,
    longitude: float,
    acquired_at_utc: datetime,
) -> Detection:
    """Create a detection with standard values for tracking tests."""
    return Detection(
        latitude=latitude,
        longitude=longitude,
        acquired_at_utc=acquired_at_utc,
        frp=10.0,
        confidence="n",
        satellite="N20",
        day_night="D",
    )


def test_update_events_creates_event_when_no_events_exist():
    detection = make_detection(
        latitude=10.0,
        longitude=30.0,
        acquired_at_utc=datetime(2026, 8, 29, 12, 0, tzinfo=timezone.utc),
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
            observations=[
                EventObservation(
                    first_seen_utc=datetime(2026, 8, 29, 12, 0, tzinfo=timezone.utc),
                    last_seen_utc=datetime(2026, 8, 29, 12, 0, tzinfo=timezone.utc),
                    centroid_latitude=10.0,
                    centroid_longitude=30.0,
                    detection_count=1,
                    total_frp=10.0,
                    max_radius_km=0.0,
                )
            ],
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
        observations=[
            EventObservation(
                first_seen_utc=datetime(2026, 8, 29, 10, 0, tzinfo=timezone.utc),
                last_seen_utc=datetime(2026, 8, 29, 12, 0, tzinfo=timezone.utc),
                centroid_latitude=10.0,
                centroid_longitude=30.0,
                detection_count=2,
                total_frp=20.0,
                max_radius_km=0.0,
            )
        ],
    )
    new_detection = make_detection(
        latitude=13.0,
        longitude=33.0,
        acquired_at_utc=datetime(2026, 8, 29, 14, 0, tzinfo=timezone.utc),
    )
    actual = update_events(
        events=[existing_event],
        clusters=[[new_detection]],
        max_distance_km=1000.0,
        max_time_gap=timedelta(hours=6),
    )
    expected = [
        FireEvent(
            event_id=7,
            first_seen_utc=datetime(2026, 8, 29, 10, 0, tzinfo=timezone.utc),
            last_seen_utc=datetime(2026, 8, 29, 14, 0, tzinfo=timezone.utc),
            centroid_latitude=11.0,
            centroid_longitude=31.0,
            detection_count=3,
            observations=[
                EventObservation(
                    first_seen_utc=datetime(2026, 8, 29, 10, 0, tzinfo=timezone.utc),
                    last_seen_utc=datetime(2026, 8, 29, 12, 0, tzinfo=timezone.utc),
                    centroid_latitude=10.0,
                    centroid_longitude=30.0,
                    detection_count=2,
                    total_frp=20.0,
                    max_radius_km=0.0,
                ),
                EventObservation(
                    first_seen_utc=datetime(2026, 8, 29, 14, 0, tzinfo=timezone.utc),
                    last_seen_utc=datetime(2026, 8, 29, 14, 0, tzinfo=timezone.utc),
                    centroid_latitude=13.0,
                    centroid_longitude=33.0,
                    detection_count=1,
                    total_frp=10.0,
                    max_radius_km=0.0,
                ),
            ],
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
    new_detection = make_detection(
        latitude=10.0,
        longitude=30.0,
        acquired_at_utc=datetime(2026, 8, 29, 20, 0, tzinfo=timezone.utc),
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
            observations=[
                EventObservation(
                    first_seen_utc=datetime(2026, 8, 29, 20, 0, tzinfo=timezone.utc),
                    last_seen_utc=datetime(2026, 8, 29, 20, 0, tzinfo=timezone.utc),
                    centroid_latitude=10.0,
                    centroid_longitude=30.0,
                    detection_count=1,
                    total_frp=10.0,
                    max_radius_km=0.0,
                )
            ],
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
    new_detection = make_detection(
        latitude=11.0,
        longitude=30.0,
        acquired_at_utc=datetime(2026, 8, 29, 14, 0, tzinfo=timezone.utc),
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
            observations=[
                EventObservation(
                    first_seen_utc=datetime(2026, 8, 29, 14, 0, tzinfo=timezone.utc),
                    last_seen_utc=datetime(2026, 8, 29, 14, 0, tzinfo=timezone.utc),
                    centroid_latitude=11.0,
                    centroid_longitude=30.0,
                    detection_count=1,
                    total_frp=10.0,
                    max_radius_km=0.0,
                )
            ],
        ),
    ]

    assert actual == expected


def test_update_events_chooses_nearest_compatible_event():
    event_7 = FireEvent(
        event_id=7,
        first_seen_utc=datetime(2026, 8, 29, 10, 0, tzinfo=timezone.utc),
        last_seen_utc=datetime(2026, 8, 29, 12, 0, tzinfo=timezone.utc),
        centroid_latitude=0.0,
        centroid_longitude=0.0,
        detection_count=1,
    )
    event_8 = FireEvent(
        event_id=8,
        first_seen_utc=datetime(2026, 8, 29, 10, 0, tzinfo=timezone.utc),
        last_seen_utc=datetime(2026, 8, 29, 12, 0, tzinfo=timezone.utc),
        centroid_latitude=0.0,
        centroid_longitude=0.02,
        detection_count=1,
    )

    new_detection = make_detection(
        latitude=0.0,
        longitude=0.02,
        acquired_at_utc=datetime(2026, 8, 29, 14, 0, tzinfo=timezone.utc),
    )

    actual = update_events(
        events=[event_7, event_8],
        clusters=[[new_detection]],
        max_distance_km=10.0,
        max_time_gap=timedelta(hours=6),
    )
    expected = [
        FireEvent(
            event_id=7,
            first_seen_utc=datetime(2026, 8, 29, 10, 0, tzinfo=timezone.utc),
            last_seen_utc=datetime(2026, 8, 29, 12, 0, tzinfo=timezone.utc),
            centroid_latitude=0.0,
            centroid_longitude=0.0,
            detection_count=1,
        ),
        FireEvent(
            event_id=8,
            first_seen_utc=datetime(2026, 8, 29, 10, 0, tzinfo=timezone.utc),
            last_seen_utc=datetime(2026, 8, 29, 14, 0, tzinfo=timezone.utc),
            centroid_latitude=0.0,
            centroid_longitude=0.02,
            detection_count=2,
            observations=[
                EventObservation(
                    first_seen_utc=datetime(2026, 8, 29, 14, 0, tzinfo=timezone.utc),
                    last_seen_utc=datetime(2026, 8, 29, 14, 0, tzinfo=timezone.utc),
                    centroid_latitude=0.0,
                    centroid_longitude=0.02,
                    detection_count=1,
                    total_frp=10.0,
                    max_radius_km=0.0,
                )
            ],
        ),
    ]

    assert actual == expected


def test_update_events_keeps_existing_event_when_no_clusters_arrive():
    event = FireEvent(
        event_id=7,
        first_seen_utc=datetime(2026, 8, 29, 10, 0, tzinfo=timezone.utc),
        last_seen_utc=datetime(2026, 8, 29, 12, 0, tzinfo=timezone.utc),
        centroid_latitude=0.0,
        centroid_longitude=0.0,
        detection_count=1,
    )

    actual = update_events(
        events=[event],
        clusters=[],
        max_distance_km=10.0,
        max_time_gap=timedelta(hours=6),
    )
    expected = [event]

    assert actual == expected


def test_match_clusters_one_to_one_assigns_only_nearest_cluster_to_event():
    first_time = datetime(2026, 8, 29, 12, 0, tzinfo=timezone.utc)
    second_time = datetime(2026, 8, 29, 14, 0, tzinfo=timezone.utc)
    event = FireEvent(
        event_id=7,
        first_seen_utc=first_time,
        last_seen_utc=first_time,
        centroid_latitude=0.0,
        centroid_longitude=0.0,
        detection_count=1,
    )
    farther_summary = summarize_cluster([make_detection(0.0, 0.02, second_time)])
    nearer_summary = summarize_cluster([make_detection(0.0, 0.01, second_time)])

    actual = match_clusters_one_to_one(
        events=[event],
        summaries=[farther_summary, nearer_summary],
        max_distance_km=10.0,
        max_time_gap=timedelta(hours=3),
    )

    assert actual == {1: 0}


def test_update_events_one_to_one_creates_event_for_unmatched_cluster():
    first_time = datetime(2026, 8, 29, 12, 0, tzinfo=timezone.utc)
    second_time = datetime(2026, 8, 29, 14, 0, tzinfo=timezone.utc)
    event = FireEvent(
        event_id=7,
        first_seen_utc=first_time,
        last_seen_utc=first_time,
        centroid_latitude=0.0,
        centroid_longitude=0.0,
        detection_count=1,
    )
    farther_cluster = [make_detection(0.0, 0.02, second_time)]
    nearer_cluster = [make_detection(0.0, 0.01, second_time)]

    actual = update_events_one_to_one(
        events=[event],
        clusters=[farther_cluster, nearer_cluster],
        max_distance_km=10.0,
        max_time_gap=timedelta(hours=3),
    )

    assert len(actual) == 2
    assert actual[0].event_id == 7
    assert actual[0].detection_count == 2
    assert actual[0].observations[0].centroid_longitude == 0.01
    assert actual[1].event_id == 8
    assert actual[1].detection_count == 1
    assert actual[1].centroid_longitude == 0.02
