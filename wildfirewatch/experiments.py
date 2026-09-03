"""Run reproducible tracking evaluation experiments."""

from dataclasses import dataclass
from datetime import timedelta
from time import perf_counter

from wildfirewatch.evaluation import (
    EvaluationResult,
    evaluate_assignments,
    track_labeled_clusters,
)
from wildfirewatch.models import Detection, FireEvent
from wildfirewatch.scoring import (
    PriorityScore,
    ScoringConfig,
    rank_events_by_priority,
)


@dataclass(frozen=True)
class ThresholdExperimentResult:
    """Metrics and runtime measured for one distance threshold."""

    max_distance_km: float
    max_time_gap: timedelta
    metrics: EvaluationResult
    runtime_seconds: float


@dataclass(frozen=True)
class ScoringExperimentResult:
    """Store the ranked events produced by one scoring configuration."""

    name: str
    config: ScoringConfig
    ranked_events: list[tuple[FireEvent, PriorityScore]]


def _evaluate_threshold_configuration(
    labeled_clusters: list[tuple[str, list[Detection]]],
    detection_count: int,
    max_distance_km: float,
    max_time_gap: timedelta,
) -> ThresholdExperimentResult:
    """Run and measure one threshold configuration."""
    started_at = perf_counter()
    assignments = track_labeled_clusters(
        labeled_clusters=labeled_clusters,
        max_distance_km=max_distance_km,
        max_time_gap=max_time_gap,
    )
    metrics = evaluate_assignments(
        assignments=assignments,
        detection_count=detection_count,
    )
    runtime_seconds = perf_counter() - started_at

    return ThresholdExperimentResult(
        max_distance_km=max_distance_km,
        max_time_gap=max_time_gap,
        metrics=metrics,
        runtime_seconds=runtime_seconds,
    )


def evaluate_distance_thresholds(
    labeled_clusters: list[tuple[str, list[Detection]]],
    distance_thresholds_km: list[float],
    max_time_gap: timedelta,
) -> list[ThresholdExperimentResult]:
    """Evaluate the same labeled scenario with multiple distance thresholds."""
    detection_count = sum(len(cluster) for _, cluster in labeled_clusters)
    results: list[ThresholdExperimentResult] = []

    for max_distance_km in distance_thresholds_km:
        results.append(
            _evaluate_threshold_configuration(
                labeled_clusters=labeled_clusters,
                detection_count=detection_count,
                max_distance_km=max_distance_km,
                max_time_gap=max_time_gap,
            )
        )

    return results


def evaluate_time_gap_thresholds(
    labeled_clusters: list[tuple[str, list[Detection]]],
    max_distance_km: float,
    time_gap_thresholds: list[timedelta],
) -> list[ThresholdExperimentResult]:
    """Evaluate the same labeled scenario with multiple time-gap thresholds."""
    detection_count = sum(len(cluster) for _, cluster in labeled_clusters)

    return [
        _evaluate_threshold_configuration(
            labeled_clusters=labeled_clusters,
            detection_count=detection_count,
            max_distance_km=max_distance_km,
            max_time_gap=max_time_gap,
        )
        for max_time_gap in time_gap_thresholds
    ]


def evaluate_scoring_configs(
    events: list[FireEvent],
    named_configs: dict[str, ScoringConfig],
) -> list[ScoringExperimentResult]:
    """Rank the same events with multiple scoring configurations."""
    results = []

    for name, config in named_configs.items():
        ranked_events = rank_events_by_priority(events, config)

        results.append(
            ScoringExperimentResult(
                name=name,
                config=config,
                ranked_events=ranked_events,
            )
        )

    return results
