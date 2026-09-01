"""Run historical replay for a saved FIRMS CSV and export frame snapshots."""

import argparse
import json
from datetime import timedelta
from pathlib import Path

from wildfirewatch.ingestion import load_detections
from wildfirewatch.replay import ReplayFrame, replay_detections

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def frame_to_dict(frame: ReplayFrame) -> dict[str, object]:
    """Convert one replay frame into JSON-compatible values."""
    return {
        "timestamp_utc": frame.timestamp.isoformat(),
        "new_detection_count": frame.detection_count,
        "cluster_count": frame.cluster_count,
        "event_count": len(frame.events),
        "events": [
            {
                "event_id": event.event_id,
                "first_seen_utc": event.first_seen_utc.isoformat(),
                "last_seen_utc": event.last_seen_utc.isoformat(),
                "detection_count": event.detection_count,
                "centroid_latitude": event.centroid_latitude,
                "centroid_longitude": event.centroid_longitude,
                "duration_hours": event.duration.total_seconds() / 3600,
            }
            for event in frame.events
        ],
    }


def main() -> None:
    """Load detections, replay them chronologically, and save JSON frames."""
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--cluster-distance-km", type=float, default=2.0)
    parser.add_argument("--event-distance-km", type=float, default=10.0)
    parser.add_argument("--max-time-gap-hours", type=float, default=13.0)
    parser.add_argument(
        "--tracking-method",
        choices=["baseline", "one_to_one"],
        default="baseline",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("evaluation/results/lahaina_replay.json"),
    )
    args = parser.parse_args()

    csv_path = args.csv_path
    if not csv_path.is_absolute():
        csv_path = PROJECT_ROOT / csv_path
    detections = load_detections(csv_path)
    frames = replay_detections(
        detections=detections,
        cluster_distance_km=args.cluster_distance_km,
        event_distance_km=args.event_distance_km,
        max_time_gap=timedelta(hours=args.max_time_gap_hours),
        tracking_method=args.tracking_method,
    )
    report = {
        "kind": "historical_active_fire_replay",
        "source_csv": str(csv_path.relative_to(PROJECT_ROOT)),
        "parameters": {
            "cluster_distance_km": args.cluster_distance_km,
            "event_distance_km": args.event_distance_km,
            "max_time_gap_hours": args.max_time_gap_hours,
            "tracking_method": args.tracking_method,
        },
        "limitations": (
            "FIRMS active-fire detections are thermal anomalies, not confirmed "
            "wildfire ground truth. Replay parameters are exploratory."
        ),
        "frames": [frame_to_dict(frame) for frame in frames],
    }

    output_path = args.output
    if not output_path.is_absolute():
        output_path = PROJECT_ROOT / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    print(f"Saved {len(frames)} replay frames to {output_path}")
    for frame in frames:
        print(
            f"{frame.timestamp.isoformat()}: "
            f"detections={frame.detection_count}, "
            f"clusters={frame.cluster_count}, events={len(frame.events)}"
        )


if __name__ == "__main__":
    main()
