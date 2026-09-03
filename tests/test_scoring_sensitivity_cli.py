"""Integration test for the scoring sensitivity command line."""

import json
import subprocess
import sys
from pathlib import Path


def test_scoring_sensitivity_cli_saves_explainable_scenarios(tmp_path):
    project_root = Path(__file__).parents[1]
    sample_path = project_root / "data" / "raw" / "viirs_noaa20_nrt_sample.csv"
    database_path = tmp_path / "wildfirewatch.db"
    output_path = tmp_path / "scoring_sensitivity.json"
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

    subprocess.run(
        [
            sys.executable,
            "scripts/run_scoring_sensitivity.py",
            str(database_path),
            "--output",
            str(output_path),
        ],
        cwd=project_root,
        capture_output=True,
        check=True,
        text=True,
    )

    report = json.loads(output_path.read_text(encoding="utf-8"))

    assert report["kind"] == "scoring_sensitivity_analysis"
    assert "not a validated danger" in report["disclaimer"]
    assert report["event_count"] > 0
    assert [scenario["name"] for scenario in report["scenarios"]] == [
        "default",
        "persistence_heavy",
        "frp_trend_heavy",
        "spatial_growth_heavy",
        "lenient_thresholds",
        "strict_thresholds",
    ]
    assert all(
        len(scenario["ranking"]) == report["event_count"]
        for scenario in report["scenarios"]
    )
