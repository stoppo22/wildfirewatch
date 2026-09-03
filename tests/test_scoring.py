"""Tests for interpretable candidate-event priority scoring."""

from datetime import datetime, timedelta, timezone

import pytest

from wildfirewatch.models import EventObservation, FireEvent
from wildfirewatch.scoring import (
    calculate_frp_trend_component,
    calculate_persistence_component,
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
