"""Rank persisted candidate events with an explainable review-priority score."""

import argparse
import sqlite3
from pathlib import Path

from wildfirewatch.database import load_fire_events, load_land_cover_context
from wildfirewatch.environment import land_cover_name
from wildfirewatch.scoring import (
    ScoringConfig,
    classify_priority_level,
    rank_events_by_priority,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def resolve_project_path(path: Path) -> Path:
    """Resolve relative command-line paths from the project root."""
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Rank candidate events for review with transparent heuristics."
    )
    parser.add_argument("database", type=Path, help="WildfireWatch SQLite database.")
    parser.add_argument("--full-score-hours", type=float, default=24.0)
    parser.add_argument("--full-score-mean-frp-increase", type=float, default=20.0)
    parser.add_argument("--full-score-radius-increase-km", type=float, default=2.0)
    parser.add_argument("--persistence-weight", type=float, default=40.0)
    parser.add_argument("--frp-trend-weight", type=float, default=35.0)
    parser.add_argument("--spatial-growth-weight", type=float, default=25.0)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    database_path = resolve_project_path(args.database)
    if not database_path.is_file():
        raise SystemExit(f"Database does not exist: {database_path}")

    try:
        config = ScoringConfig(
            full_score_hours=args.full_score_hours,
            full_score_mean_frp_increase=args.full_score_mean_frp_increase,
            full_score_radius_increase_km=args.full_score_radius_increase_km,
            persistence_weight=args.persistence_weight,
            frp_trend_weight=args.frp_trend_weight,
            spatial_growth_weight=args.spatial_growth_weight,
        )
    except ValueError as error:
        raise SystemExit(str(error)) from error

    connection = sqlite3.connect(database_path)
    try:
        events = load_fire_events(connection)
        ranked_events = [
            (
                event,
                score,
                load_land_cover_context(connection, event.event_id),
            )
            for event, score in rank_events_by_priority(events, config)
        ]
    finally:
        connection.close()

    print("Candidate-event review priority; not a danger or emergency-risk score.")
    for event, score, context in ranked_events:
        level = classify_priority_level(score.total)
        context_name = (
            land_cover_name(context.class_code) if context is not None else None
        )
        print(
            f"event={event.event_id} score={score.total:.1f}/100 " f"priority={level}"
        )
        print(
            f"  persistence={score.persistence_points:.1f}/"
            f"{config.persistence_weight:.1f} "
            f"frp_trend={score.frp_trend_points:.1f}/"
            f"{config.frp_trend_weight:.1f} "
            f"spatial_growth={score.spatial_growth_points:.1f}/"
            f"{config.spatial_growth_weight:.1f} "
            f"land_cover={context_name or 'unavailable'}"
        )


if __name__ == "__main__":
    main()
