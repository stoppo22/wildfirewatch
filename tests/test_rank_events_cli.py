"""Integration tests for the candidate-event ranking command line."""

import subprocess
import sys
from pathlib import Path


def test_rank_events_cli_prints_explainable_scores(tmp_path):
    project_root = Path(__file__).parents[1]
    sample_path = project_root / "data" / "raw" / "viirs_noaa20_nrt_sample.csv"
    database_path = tmp_path / "wildfirewatch.db"
    subprocess.run(
        [
            sys.executable,
            "-m",
            "scripts.run_incremental_processing",
            str(sample_path),
            "--database",
            str(database_path),
        ],
        cwd=project_root,
        capture_output=True,
        check=True,
        text=True,
    )

    result = subprocess.run(
        [sys.executable, "scripts/rank_events.py", str(database_path)],
        cwd=project_root,
        capture_output=True,
        check=True,
        text=True,
    )

    assert "not a danger or emergency-risk score" in result.stdout
    assert "event=1 score=" in result.stdout
    assert "persistence=" in result.stdout
    assert "frp_trend=" in result.stdout
    assert "spatial_growth=" in result.stdout
    assert "land_cover=unavailable" in result.stdout
