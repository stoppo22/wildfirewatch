"""Tests for reproducible tracking and scoring experiments."""

from datetime import datetime, timedelta, timezone

from wildfirewatch.evaluation import EvaluationResult
from wildfirewatch.evaluation_scenarios import (
    create_distance_threshold_scenario,
    create_time_gap_threshold_scenario,
)
from wildfirewatch.experiments import (
    evaluate_distance_thresholds,
    evaluate_scoring_configs,
    evaluate_time_gap_thresholds,
)
from wildfirewatch.models import EventObservation, FireEvent
from wildfirewatch.scoring import ScoringConfig


def test_distance_threshold_experiment_exposes_split_and_merge_tradeoff():
    results = evaluate_distance_thresholds(
        labeled_clusters=create_distance_threshold_scenario(),
        distance_thresholds_km=[5.0, 10.0, 20.0],
        max_time_gap=timedelta(hours=3),
    )

    assert [result.metrics for result in results] == [
        EvaluationResult(
            false_splits=2,
            false_merges=0,
            detection_reduction_ratio=0.0,
            event_continuity_ratio=0.0,
        ),
        EvaluationResult(
            false_splits=0,
            false_merges=0,
            detection_reduction_ratio=0.5,
            event_continuity_ratio=1.0,
        ),
        EvaluationResult(
            false_splits=0,
            false_merges=1,
            detection_reduction_ratio=0.75,
            event_continuity_ratio=1.0,
        ),
    ]


def test_time_gap_experiment_exposes_split_and_merge_tradeoff():
    results = evaluate_time_gap_thresholds(
        labeled_clusters=create_time_gap_threshold_scenario(),
        max_distance_km=1.0,
        time_gap_thresholds=[
            timedelta(hours=1),
            timedelta(hours=3),
            timedelta(hours=10),
        ],
    )

    assert [result.metrics for result in results] == [
        EvaluationResult(
            false_splits=2,
            false_merges=0,
            detection_reduction_ratio=0.0,
            event_continuity_ratio=0.0,
        ),
        EvaluationResult(
            false_splits=0,
            false_merges=0,
            detection_reduction_ratio=0.5,
            event_continuity_ratio=1.0,
        ),
        EvaluationResult(
            false_splits=0,
            false_merges=1,
            detection_reduction_ratio=0.75,
            event_continuity_ratio=1.0,
        ),
    ]


def test_scoring_experiment_exposes_weight_sensitive_ranking():
    start = datetime(2023, 8, 9, 12, 0, tzinfo=timezone.utc)
    persistent_event = FireEvent(
        event_id=1,
        first_seen_utc=start,
        last_seen_utc=start + timedelta(hours=24),
        centroid_latitude=20.878,
        centroid_longitude=-156.674,
        detection_count=2,
    )
    trending_event = FireEvent(
        event_id=2,
        first_seen_utc=start,
        last_seen_utc=start + timedelta(hours=1),
        centroid_latitude=20.9,
        centroid_longitude=-156.6,
        detection_count=2,
        observations=[
            EventObservation(
                first_seen_utc=start,
                last_seen_utc=start,
                centroid_latitude=20.9,
                centroid_longitude=-156.6,
                max_radius_km=1.0,
                detection_count=1,
                total_frp=10.0,
            ),
            EventObservation(
                first_seen_utc=start + timedelta(hours=1),
                last_seen_utc=start + timedelta(hours=1),
                centroid_latitude=20.9,
                centroid_longitude=-156.6,
                max_radius_km=1.0,
                detection_count=1,
                total_frp=30.0,
            ),
        ],
    )

    results = evaluate_scoring_configs(
        events=[persistent_event, trending_event],
        named_configs={
            "persistence_only": ScoringConfig(
                persistence_weight=100.0,
                frp_trend_weight=0.0,
                spatial_growth_weight=0.0,
            ),
            "frp_only": ScoringConfig(
                persistence_weight=0.0,
                frp_trend_weight=100.0,
                spatial_growth_weight=0.0,
            ),
        },
    )

    assert [result.name for result in results] == ["persistence_only", "frp_only"]
    assert [event.event_id for event, _ in results[0].ranked_events] == [1, 2]
    assert [event.event_id for event, _ in results[1].ranked_events] == [2, 1]
