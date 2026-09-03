"""Tests for interpretable candidate-event priority scoring."""

from datetime import datetime, timedelta, timezone

import pytest

from wildfirewatch.models import EventObservation, FireEvent
from wildfirewatch.scoring import (
    PriorityScore,
    ScoringConfig,
    calculate_frp_trend_component,
    calculate_persistence_component,
    calculate_priority_score,
    calculate_spatial_growth_component,
    classify_priority_level,
)


def make_event(duration_hours: float) -> FireEvent:
    start = datetime(2023, 8, 9, 12, 0, tzinfo=timezone.utc)
    return FireEvent(
        event_id=1,
        first_seen_utc=start,
        last_seen_utc=start + timedelta(hours=duration_hours),
        centroid_latitude=20.878,
        centroid_longitude=-156.674,
        detection_count=2,
    )


def test_persistence_component_is_half_at_half_threshold():
    event = make_event(duration_hours=12)

    actual = calculate_persistence_component(
        event,
        full_score_hours=24,
    )

    assert actual == 0.5


def test_persistence_component_is_zero_for_new_event():
    event = make_event(duration_hours=0)

    actual = calculate_persistence_component(event, full_score_hours=24)

    assert actual == 0.0


def test_persistence_component_is_capped_at_one():
    event = make_event(duration_hours=36)

    actual = calculate_persistence_component(event, full_score_hours=24)

    assert actual == 1.0


def test_persistence_component_rejects_non_positive_threshold():
    event = make_event(duration_hours=12)

    with pytest.raises(ValueError, match="full_score_hours must be positive"):
        calculate_persistence_component(event, full_score_hours=0)


def test_frp_trend_component_is_half_at_half_threshold():
    event = make_event(duration_hours=2)
    event.observations = [
        EventObservation(
            first_seen_utc=event.first_seen_utc,
            last_seen_utc=event.first_seen_utc,
            centroid_latitude=event.centroid_latitude,
            centroid_longitude=event.centroid_longitude,
            max_radius_km=1.0,
            detection_count=2,
            total_frp=40.0,
        ),
        EventObservation(
            first_seen_utc=event.last_seen_utc,
            last_seen_utc=event.last_seen_utc,
            centroid_latitude=event.centroid_latitude,
            centroid_longitude=event.centroid_longitude,
            max_radius_km=1.0,
            detection_count=2,
            total_frp=60.0,
        ),
    ]

    actual = calculate_frp_trend_component(
        event,
        full_score_mean_frp_increase=20,
    )

    assert actual == 0.5


def test_frp_trend_component_rejects_non_positive_threshold():
    event = make_event(duration_hours=2)

    with pytest.raises(
        ValueError,
        match="full_score_mean_frp_increase must be positive",
    ):
        calculate_frp_trend_component(
            event,
            full_score_mean_frp_increase=0,
        )


def test_spatial_growth_component_is_half_at_half_threshold():
    event = make_event(duration_hours=2)
    event.observations = [
        EventObservation(
            first_seen_utc=event.first_seen_utc,
            last_seen_utc=event.first_seen_utc,
            centroid_latitude=event.centroid_latitude,
            centroid_longitude=event.centroid_longitude,
            max_radius_km=1.0,
            detection_count=1,
            total_frp=10.0,
        ),
        EventObservation(
            first_seen_utc=event.last_seen_utc,
            last_seen_utc=event.last_seen_utc,
            centroid_latitude=event.centroid_latitude,
            centroid_longitude=event.centroid_longitude,
            max_radius_km=2.0,
            detection_count=1,
            total_frp=10.0,
        ),
    ]

    actual = calculate_spatial_growth_component(
        event,
        full_score_radius_increase_km=2,
    )

    assert actual == 0.5


def test_spatial_growth_component_rejects_non_positive_threshold():
    event = make_event(duration_hours=2)

    with pytest.raises(
        ValueError,
        match="full_score_radius_increase_km must be positive",
    ):
        calculate_spatial_growth_component(
            event,
            full_score_radius_increase_km=0,
        )


def test_priority_score_preserves_total_and_component_points():
    event = make_event(duration_hours=12)
    event.observations = [
        EventObservation(
            first_seen_utc=event.first_seen_utc,
            last_seen_utc=event.first_seen_utc,
            centroid_latitude=event.centroid_latitude,
            centroid_longitude=event.centroid_longitude,
            max_radius_km=1.0,
            detection_count=2,
            total_frp=40.0,
        ),
        EventObservation(
            first_seen_utc=event.last_seen_utc,
            last_seen_utc=event.last_seen_utc,
            centroid_latitude=event.centroid_latitude,
            centroid_longitude=event.centroid_longitude,
            max_radius_km=2.0,
            detection_count=2,
            total_frp=60.0,
        ),
    ]

    actual = calculate_priority_score(event)

    assert actual == PriorityScore(
        total=50.0,
        persistence_points=20.0,
        frp_trend_points=17.5,
        spatial_growth_points=12.5,
    )


def test_scoring_config_rejects_weights_that_do_not_sum_to_100():
    with pytest.raises(ValueError, match="scoring weights must sum to 100"):
        ScoringConfig(persistence_weight=41.0)


def test_scoring_config_rejects_negative_weight():
    with pytest.raises(ValueError, match="scoring weights must not be negative"):
        ScoringConfig(
            persistence_weight=-1.0,
            frp_trend_weight=76.0,
        )


@pytest.mark.parametrize(
    ("total_score", "expected"),
    [
        (0.0, "low"),
        (32.0, "low"),
        (33.0, "medium"),
        (66.0, "medium"),
        (67.0, "high"),
        (100.0, "high"),
    ],
)
def test_classify_priority_level_respects_boundaries(total_score, expected):
    assert classify_priority_level(total_score) == expected


@pytest.mark.parametrize("total_score", [-1.0, 101.0])
def test_classify_priority_level_rejects_out_of_range_score(total_score):
    with pytest.raises(ValueError, match="total_score must be between 0 and 100"):
        classify_priority_level(total_score)
