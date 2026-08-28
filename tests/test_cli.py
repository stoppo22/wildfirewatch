"""Integration tests for the WildfireWatch command line."""

import subprocess
import sys
from pathlib import Path


def test_cli_summarizes_sample_file():
    sample_path = (
        Path(__file__).parents[1] / "data" / "raw" / "viirs_noaa20_nrt_sample.csv"
    )

    result = subprocess.run(
        [sys.executable, "-m", "wildfirewatch", str(sample_path)],
        capture_output=True,
        check=True,
        text=True,
    )

    expected = (
        "Detections: 5\n"
        "First acquired (UTC): 2025-06-06T00:01:00+00:00\n"
        "Last acquired (UTC): 2025-06-06T00:01:00+00:00\n"
    )
    assert result.stdout == expected
