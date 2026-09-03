"""Integration tests for the persistent incremental command line."""

import sqlite3
import subprocess
import sys
from pathlib import Path


def test_incremental_cli_is_idempotent(tmp_path):
    project_root = Path(__file__).parents[1]
    sample_path = project_root / "data" / "raw" / "viirs_noaa20_nrt_sample.csv"
    database_path = tmp_path / "wildfirewatch.db"
    command = [
        sys.executable,
        "-m",
        "scripts.run_incremental_processing",
        str(sample_path),
        "--database",
        str(database_path),
    ]

    first_result = subprocess.run(
        command,
        cwd=project_root,
        capture_output=True,
        check=True,
        text=True,
    )
    second_result = subprocess.run(
        command,
        cwd=project_root,
        capture_output=True,
        check=True,
        text=True,
    )

    connection = sqlite3.connect(database_path)
    detection_count = connection.execute("SELECT COUNT(*) FROM detections;").fetchone()
    event_count = connection.execute("SELECT COUNT(*) FROM fire_events;").fetchone()
    connection.close()

    assert "received=5 new=5" in first_result.stderr
    assert "received=5 new=0" in second_result.stderr
    assert detection_count == (5,)
    assert event_count[0] > 0
