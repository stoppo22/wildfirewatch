"""Test for evaluation"""

from datetime import datetime, timedelta, timezone

from wildfirewatch.evaluation import (
    EvaluationResult,
    calculate_detection_reduction_ratio,
    count_false_merges,
    count_false_splits,
    calculate_event_continuity_ratio,
    evaluate_assignments,
    track_labeled_clusters,
)
from wildfirewatch.models import Detection


def test_count_false_splits_counts_extra_predicted_events():
    assignments = [
        ("fire_a", 1),
        ("fire_a", 1),
        ("fire_a", 2),
        ("fire_b", 3),
    ]

    actual = count_false_splits(assignments)

    assert actual == 1


def test_count_false_splits_returns_zero_without_splits():
    assignments = [
        ("fire_a", 1),
        ("fire_a", 1),
        ("fire_b", 2),
    ]

    actual = count_false_splits(assignments)

    assert actual == 0


def test_count_false_splits_returns_zero_for_empty_assignments():
    actual = count_false_splits([])

    assert actual == 0


def test_count_false_merges_counts_real_events_joined_together():
    assignments = [
        ("fire_a", 1),
        ("fire_b", 1),
        ("fire_c", 2),
    ]

    actual = count_false_merges(assignments)

    assert actual == 1


def test_calculate_detection_reduction_ratio():
    actual = calculate_detection_reduction_ratio(
        detection_count=4,
        predicted_event_ids=[1, 1, 2, 2],
    )

    assert actual == 0.5


def test_calculate_detection_reduction_ratio_returns_zero_when_empty():
    assert (
        calculate_detection_reduction_ratio(
            detection_count=0,
            predicted_event_ids=[],
        )
        == 0.0
    )


def test_calculate_event_continuity_ratio():
    assignments = [
        ("fire_a", 1),
        ("fire_a", 1),
        ("fire_a", 2),
    ]

    actual = calculate_event_continuity_ratio(assignments)

    assert actual == 0.5


def test_calculate_event_continuity_ratio_is_not_measurable_without_transitions():
    assignments = [("fire_a", 1)]

    assert calculate_event_continuity_ratio(assignments) is None


def test_track_labeled_clusters_uses_real_tracking_assignments():
    first_time = datetime(2026, 8, 31, 10, 0, tzinfo=timezone.utc)
    second_time = datetime(2026, 8, 31, 12, 0, tzinfo=timezone.utc)

    def detection(latitude, longitude, acquired_at_utc):
        return Detection(
            latitude=latitude,
            longitude=longitude,
            acquired_at_utc=acquired_at_utc,
            frp=10.0,
            confidence="n",
            satellite="N20",
            day_night="D",
        )

    labeled_clusters = [
        ("fire_a", [detection(0.0, 0.0, first_time)]),
        ("fire_b", [detection(1.0, 1.0, first_time)]),
        ("fire_a", [detection(0.0, 0.01, second_time)]),
        ("fire_b", [detection(1.0, 1.01, second_time)]),
    ]

    actual = track_labeled_clusters(
        labeled_clusters,
        max_distance_km=5.0,
        max_time_gap=timedelta(hours=3),
    )

    assert actual == [
        ("fire_a", 1),
        ("fire_b", 2),
        ("fire_a", 1),
        ("fire_b", 2),
    ]
    assert evaluate_assignments(actual, detection_count=4) == EvaluationResult(
        false_splits=0,
        false_merges=0,
        detection_reduction_ratio=0.5,
        event_continuity_ratio=1.0,
    )
