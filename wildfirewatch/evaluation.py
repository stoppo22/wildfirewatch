"""Evaluate the quality of predicted fire events."""

from dataclasses import dataclass
from datetime import timedelta

from wildfirewatch.models import Detection, FireEvent
from wildfirewatch.tracking import update_events


@dataclass(frozen=True)
class EvaluationResult:
    """Metrics calculated for one reproducible tracking evaluation."""

    false_splits: int
    false_merges: int
    detection_reduction_ratio: float
    event_continuity_ratio: float | None


def count_false_splits(assignments):
    predicted_ids_by_true_event = {}

    for true_event_id, predicted_event_id in assignments:
        if true_event_id not in predicted_ids_by_true_event:
            predicted_ids_by_true_event[true_event_id] = set()

        predicted_ids_by_true_event[true_event_id].add(predicted_event_id)

    false_splits = 0

    for predicted_ids in predicted_ids_by_true_event.values():
        false_splits += len(predicted_ids) - 1

    return false_splits


def count_false_merges(assignments):
    true_ids_by_predicted_event = {}

    for true_event_id, predicted_event_id in assignments:
        if predicted_event_id not in true_ids_by_predicted_event:
            true_ids_by_predicted_event[predicted_event_id] = set()

        true_ids_by_predicted_event[predicted_event_id].add(true_event_id)

    false_merges = 0

    for true_ids in true_ids_by_predicted_event.values():
        false_merges += len(true_ids) - 1

    return false_merges


def calculate_detection_reduction_ratio(detection_count, predicted_event_ids):
    if detection_count == 0:
        return 0.0

    predicted_event_count = len(set(predicted_event_ids))

    return (detection_count - predicted_event_count) / detection_count


def calculate_event_continuity_ratio(assignments):
    predicted_ids_by_true_event = {}

    for true_event_id, predicted_event_id in assignments:
        if true_event_id not in predicted_ids_by_true_event:
            predicted_ids_by_true_event[true_event_id] = []

        predicted_ids_by_true_event[true_event_id].append(predicted_event_id)

    continuous_transitions = 0
    total_transitions = 0

    for predicted_ids in predicted_ids_by_true_event.values():
        for previous_id, current_id in zip(
            predicted_ids,
            predicted_ids[1:],
        ):
            total_transitions += 1

            if previous_id == current_id:
                continuous_transitions += 1

    if total_transitions == 0:
        return None

    return continuous_transitions / total_transitions


def track_labeled_clusters(
    labeled_clusters: list[tuple[str, list[Detection]]],
    max_distance_km: float,
    max_time_gap: timedelta,
) -> list[tuple[str, int]]:
    """Track labeled clusters and return true/predicted event ID pairs."""
    events: list[FireEvent] = []
    assignments: list[tuple[str, int]] = []

    for true_event_id, cluster in labeled_clusters:
        previous_detection_counts = {
            event.event_id: event.detection_count for event in events
        }
        events = update_events(
            events=events,
            clusters=[cluster],
            max_distance_km=max_distance_km,
            max_time_gap=max_time_gap,
        )
        changed_event_ids = [
            event.event_id
            for event in events
            if event.detection_count != previous_detection_counts.get(event.event_id, 0)
        ]

        if len(changed_event_ids) != 1:
            raise RuntimeError("Expected exactly one event assignment per cluster.")

        assignments.append((true_event_id, changed_event_ids[0]))

    return assignments


def evaluate_assignments(
    assignments: list[tuple[str, int]],
    detection_count: int,
) -> EvaluationResult:
    """Calculate all evaluation metrics for a set of tracking assignments."""
    predicted_event_ids = [predicted_event_id for _, predicted_event_id in assignments]

    return EvaluationResult(
        false_splits=count_false_splits(assignments),
        false_merges=count_false_merges(assignments),
        detection_reduction_ratio=calculate_detection_reduction_ratio(
            detection_count=detection_count,
            predicted_event_ids=predicted_event_ids,
        ),
        event_continuity_ratio=calculate_event_continuity_ratio(assignments),
    )
