"""Incrementally process a FIRMS CSV into a persistent SQLite database."""

import argparse
import logging
import sqlite3
from datetime import timedelta
from pathlib import Path

from wildfirewatch.database import create_tables
from wildfirewatch.ingestion import load_detections
from wildfirewatch.pipeline import process_incremental_detections

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOGGER = logging.getLogger(__name__)


def resolve_project_path(path: Path) -> Path:
    """Resolve relative command-line paths from the project root."""
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def main() -> None:
    """Process only new CSV detections and persist the resulting events."""
    parser = argparse.ArgumentParser(
        description="Incrementally process FIRMS detections into SQLite."
    )
    parser.add_argument("csv_path", type=Path)
    parser.add_argument(
        "--database",
        type=Path,
        default=Path("data/wildfirewatch.db"),
    )
    parser.add_argument("--cluster-distance-km", type=float, default=2.0)
    parser.add_argument("--event-distance-km", type=float, default=10.0)
    parser.add_argument("--max-time-gap-hours", type=float, default=13.0)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    csv_path = resolve_project_path(args.csv_path)
    database_path = resolve_project_path(args.database)
    database_path.parent.mkdir(parents=True, exist_ok=True)
    detections = load_detections(csv_path)

    connection = sqlite3.connect(database_path)
    try:
        create_tables(connection)
        detection_count_before = connection.execute(
            "SELECT COUNT(*) FROM detections;"
        ).fetchone()[0]
        events = process_incremental_detections(
            connection=connection,
            detections=detections,
            cluster_distance_km=args.cluster_distance_km,
            event_distance_km=args.event_distance_km,
            max_time_gap=timedelta(hours=args.max_time_gap_hours),
        )
        detection_count_after = connection.execute(
            "SELECT COUNT(*) FROM detections;"
        ).fetchone()[0]
        connection.commit()
    except Exception:
        connection.rollback()
        LOGGER.exception("Incremental processing failed; transaction rolled back")
        raise
    finally:
        connection.close()

    LOGGER.info(
        "received=%d new=%d events=%d database=%s",
        len(detections),
        detection_count_after - detection_count_before,
        len(events),
        database_path,
    )


if __name__ == "__main__":
    main()
