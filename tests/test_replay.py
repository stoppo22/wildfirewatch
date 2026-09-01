"""Tests for chronological historical replay."""

from datetime import datetime, timedelta, timezone

from wildfirewatch.models import Detection
from wildfirewatch.replay import (
    group_detections_by_time,
    replay_detections,
)


def make_detection(longitude: float, acquired_at_utc: datetime) -> Detection:
    """Create a small detection for replay tests."""
    return Detection(
        latitude=20.88,
        longitude=longitude,
        acquired_at_utc=acquired_at_utc,
        frp=10.0,
        confidence="n",
        satellite="N20",
        day_night="D",
    )


def test_group_detections_by_time_groups_and_sorts_frames():
    earlier = datetime(2023, 8, 9, 12, 15, tzinfo=timezone.utc)
    later = datetime(2023, 8, 9, 23, 26, tzinfo=timezone.utc)
    late_detection = make_detection(-156.66, later)
    early_detection_a = make_detection(-156.67, earlier)
    early_detection_b = make_detection(-156.68, earlier)

    actual = group_detections_by_time(
        [late_detection, early_detection_a, early_detection_b]
    )

    assert actual == [
        (earlier, [early_detection_a, early_detection_b]),
        (later, [late_detection]),
    ]


def test_replay_frames_do_not_gain_future_detections():
    first_time = datetime(2023, 8, 9, 12, 0, tzinfo=timezone.utc)
    second_time = datetime(2023, 8, 9, 13, 0, tzinfo=timezone.utc)

    detections = [
        make_detection(-156.670, first_time),
        make_detection(-156.671, first_time),
        make_detection(-156.670, second_time),
    ]

    frames = replay_detections(
        detections=detections,
        cluster_distance_km=1.0,
        event_distance_km=2.0,
        max_time_gap=timedelta(hours=2),
    )

    assert len(frames) == 2
    assert frames[0].detection_count == 2
    assert frames[0].cluster_count == 1
    assert frames[0].events[0].detection_count == 2

    assert frames[1].detection_count == 1
    assert frames[1].cluster_count == 1
    assert frames[1].events[0].detection_count == 3


def test_replay_compares_baseline_and_one_to_one_tracking():
    first_time = datetime(2023, 8, 9, 12, 0, tzinfo=timezone.utc)
    second_time = datetime(2023, 8, 9, 13, 0, tzinfo=timezone.utc)
    detections = [
        make_detection(-156.670, first_time),
        make_detection(-156.660, second_time),
        make_detection(-156.650, second_time),
    ]
    parameters = {
        "detections": detections,
        "cluster_distance_km": 0.5,
        "event_distance_km": 5.0,
        "max_time_gap": timedelta(hours=2),
    }

    baseline_frames = replay_detections(
        **parameters,
        tracking_method="baseline",
    )
    one_to_one_frames = replay_detections(
        **parameters,
        tracking_method="one_to_one",
    )

    assert len(baseline_frames[-1].events) == 1
    assert len(one_to_one_frames[-1].events) == 2
