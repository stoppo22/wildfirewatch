"""Command-line entry point for WildfireWatch."""

import argparse
from pathlib import Path

from wildfirewatch.ingestion import load_detections
from wildfirewatch.summary import format_detection_summary


def main() -> None:
    """Load a FIRMS CSV file and print a detection summary."""
    parser = argparse.ArgumentParser(
        prog="python -m wildfirewatch",
        description="Load and summarize NASA FIRMS active-fire detections.",
    )
    parser.add_argument(
        "csv_path",
        type=Path,
        help="Path to a NASA FIRMS CSV file.",
    )
    args = parser.parse_args()

    detections = load_detections(args.csv_path)
    print(format_detection_summary(detections))


if __name__ == "__main__":
    main()
