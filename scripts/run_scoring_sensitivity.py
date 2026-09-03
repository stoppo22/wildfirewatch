"""Compare event rankings across explicit scoring configurations."""

import argparse
import json
import sqlite3
from dataclasses import asdict
from pathlib import Path

from wildfirewatch.database import load_fire_events
from wildfirewatch.experiments import evaluate_scoring_configs
from wildfirewatch.scoring import ScoringConfig, classify_priority_level

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = Path("evaluation/results/scoring_sensitivity.json")


def resolve_project_path(path: Path) -> Path:
    """Resolve relative command-line paths from the project root."""
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def create_sensitivity_configs() -> dict[str, ScoringConfig]:
    """Return the documented weight and threshold scenarios."""
    return {
        "default": ScoringConfig(),
        "persistence_heavy": ScoringConfig(
            persistence_weight=60.0,
            frp_trend_weight=25.0,
            spatial_growth_weight=15.0,
        ),
        "frp_trend_heavy": ScoringConfig(
            persistence_weight=25.0,
            frp_trend_weight=60.0,
            spatial_growth_weight=15.0,
        ),
        "spatial_growth_heavy": ScoringConfig(
            persistence_weight=25.0,
            frp_trend_weight=20.0,
            spatial_growth_weight=55.0,
        ),
        "lenient_thresholds": ScoringConfig(
            full_score_hours=12.0,
            full_score_mean_frp_increase=10.0,
            full_score_radius_increase_km=1.0,
        ),
        "strict_thresholds": ScoringConfig(
            full_score_hours=48.0,
            full_score_mean_frp_increase=40.0,
            full_score_radius_increase_km=4.0,
        ),
    }


def main() -> None:
    """Run scoring scenarios against persisted events and save a JSON report."""
    parser = argparse.ArgumentParser(
        description="Measure how scoring choices affect candidate-event rankings."
    )
    parser.add_argument("database", type=Path, help="WildfireWatch SQLite database.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    database_path = resolve_project_path(args.database)
    output_path = resolve_project_path(args.output)
    if not database_path.is_file():
        raise SystemExit(f"Database does not exist: {database_path}")

    connection = sqlite3.connect(database_path)
    try:
        events = load_fire_events(connection)
    finally:
        connection.close()

    results = evaluate_scoring_configs(events, create_sensitivity_configs())
    report = {
        "kind": "scoring_sensitivity_analysis",
        "disclaimer": (
            "Heuristic candidate-event review priority; not a validated danger "
            "or emergency-risk score."
        ),
        "event_count": len(events),
        "scenarios": [
            {
                "name": result.name,
                "config": asdict(result.config),
                "ranking": [
                    {
                        "rank": rank,
                        "event_id": event.event_id,
                        "score": round(score.total, 6),
                        "priority": classify_priority_level(score.total),
                        "components": {
                            "persistence_points": round(
                                score.persistence_points,
                                6,
                            ),
                            "frp_trend_points": round(score.frp_trend_points, 6),
                            "spatial_growth_points": round(
                                score.spatial_growth_points,
                                6,
                            ),
                        },
                    }
                    for rank, (event, score) in enumerate(
                        result.ranked_events,
                        start=1,
                    )
                ],
            }
            for result in results
        ],
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Saved scoring sensitivity report to {output_path}")


if __name__ == "__main__":
    main()
