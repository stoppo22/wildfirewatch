"""Run controlled threshold experiments and save their measured results."""

import argparse
import json
from datetime import timedelta
from pathlib import Path

from wildfirewatch.evaluation_scenarios import (
    create_distance_threshold_scenario,
    create_time_gap_threshold_scenario,
)
from wildfirewatch.experiments import (
    ThresholdExperimentResult,
    evaluate_distance_thresholds,
    evaluate_time_gap_thresholds,
)


def result_to_dict(result: ThresholdExperimentResult) -> dict[str, object]:
    """Convert one measured result into JSON-compatible values."""
    return {
        "max_distance_km": result.max_distance_km,
        "max_time_gap_hours": result.max_time_gap.total_seconds() / 3600,
        "false_splits": result.metrics.false_splits,
        "false_merges": result.metrics.false_merges,
        "detection_reduction_ratio": result.metrics.detection_reduction_ratio,
        "event_continuity_ratio": result.metrics.event_continuity_ratio,
        "runtime_seconds": result.runtime_seconds,
    }


def main() -> None:
    """Run both synthetic experiments and write a reproducible JSON report."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("evaluation/results/synthetic_thresholds.json"),
    )
    args = parser.parse_args()

    distance_results = evaluate_distance_thresholds(
        labeled_clusters=create_distance_threshold_scenario(),
        distance_thresholds_km=[5.0, 10.0, 20.0],
        max_time_gap=timedelta(hours=3),
    )
    time_results = evaluate_time_gap_thresholds(
        labeled_clusters=create_time_gap_threshold_scenario(),
        max_distance_km=1.0,
        time_gap_thresholds=[
            timedelta(hours=1),
            timedelta(hours=3),
            timedelta(hours=10),
        ],
    )
    report = {
        "kind": "controlled_synthetic_evaluation",
        "limitations": (
            "Synthetic labels test expected algorithm behavior; they are not "
            "validation against confirmed historical wildfires."
        ),
        "distance_threshold_results": [
            result_to_dict(result) for result in distance_results
        ],
        "time_gap_threshold_results": [
            result_to_dict(result) for result in time_results
        ],
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Saved evaluation report to {args.output}")


if __name__ == "__main__":
    main()
