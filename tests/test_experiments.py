"""Tests for reproducible tracking experiments."""

from datetime import timedelta

from wildfirewatch.evaluation import EvaluationResult
from wildfirewatch.evaluation_scenarios import (
    create_distance_threshold_scenario,
    create_time_gap_threshold_scenario,
)
from wildfirewatch.experiments import (
    evaluate_distance_thresholds,
    evaluate_time_gap_thresholds,
)


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
