"""Benchmark the local SQLite processing path on a fixed FIRMS sample."""

import argparse
import json
import sqlite3
from datetime import timedelta
from pathlib import Path
from statistics import median
from tempfile import TemporaryDirectory
from time import perf_counter

from wildfirewatch.database import create_tables
from wildfirewatch.ingestion import load_detections
from wildfirewatch.pipeline import process_incremental_detections

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CSV = Path("data/raw/viirs_noaa20_sp_lahaina_2023-08-08_2023-08-12.csv")
DEFAULT_OUTPUT = Path("evaluation/results/lahaina_pipeline_benchmark.json")


def resolve_project_path(path: Path) -> Path:
    """Resolve a relative path from the repository root."""
    return path if path.is_absolute() else PROJECT_ROOT / path


def process_once(csv_path: Path) -> tuple[int, int, float]:
    """Process one fresh local database and return counts plus elapsed time."""
    started_at = perf_counter()
    detections = load_detections(csv_path)

    with TemporaryDirectory() as temporary_directory:
        database_path = Path(temporary_directory) / "wildfirewatch.db"
        connection = sqlite3.connect(database_path)
        try:
            create_tables(connection)
            events = process_incremental_detections(
                connection=connection,
                detections=detections,
                cluster_distance_km=2.0,
                event_distance_km=10.0,
                max_time_gap=timedelta(hours=13.0),
            )
            connection.commit()
        finally:
            connection.close()

    elapsed_seconds = perf_counter() - started_at
    return len(detections), len(events), elapsed_seconds


def main() -> None:
    """Run repeated cold SQLite processing and save a compact JSON report."""
    parser = argparse.ArgumentParser(
        description="Benchmark the Lahaina processing pipeline on fresh SQLite databases."
    )
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--runs", type=int, default=15)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    if args.runs < 1:
        raise SystemExit("--runs must be positive")

    csv_path = resolve_project_path(args.csv)
    output_path = resolve_project_path(args.output)
    durations: list[float] = []
    detection_count = 0
    event_count = 0

    for _ in range(args.runs):
        detection_count, event_count, elapsed_seconds = process_once(csv_path)
        durations.append(elapsed_seconds)

    report = {
        "kind": "local_pipeline_benchmark",
        "scope": (
            "CSV loading, SQLite schema creation, incremental clustering, "
            "event tracking, and SQLite commit on a fresh local database."
        ),
        "dataset": csv_path.relative_to(PROJECT_ROOT).as_posix(),
        "detection_count": detection_count,
        "event_count": event_count,
        "run_count": args.runs,
        "duration_seconds": {
            "median": median(durations),
            "minimum": min(durations),
            "maximum": max(durations),
        },
        "limitations": (
            "Wall-clock timings depend on the local machine and are not a "
            "cross-hardware performance comparison."
        ),
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
