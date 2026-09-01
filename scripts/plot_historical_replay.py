"""Plot cumulative historical replay snapshots without future-data leakage."""

import argparse
import json
import math
from datetime import timedelta
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter, MaxNLocator

from wildfirewatch.ingestion import load_detections
from wildfirewatch.replay import replay_detections

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PERIMETER = Path("data/reference/lahaina_fire_perimeter_usgs_object_2.geojson")
DEFAULT_OUTPUT = Path("evaluation/results/lahaina_replay_one_to_one.png")


def resolve_project_path(path: Path) -> Path:
    """Resolve a CLI path relative to the repository root."""
    return path if path.is_absolute() else PROJECT_ROOT / path


def load_outer_ring(path: Path) -> list[list[float]]:
    """Load the outer ring from the expected local Polygon GeoJSON."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        ring = payload["features"][0]["geometry"]["coordinates"][0]
    except (OSError, json.JSONDecodeError, KeyError, IndexError, TypeError):
        raise SystemExit(
            "Reference Polygon is unavailable. "
            "Run scripts/download_reference_perimeter.py first."
        ) from None

    if not isinstance(ring, list) or len(ring) < 3:
        raise SystemExit("Reference Polygon has no valid outer ring.")
    return ring


def main() -> None:
    """Generate one subplot per chronological replay frame."""
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--perimeter", type=Path, default=DEFAULT_PERIMETER)
    parser.add_argument("--cluster-distance-km", type=float, default=2.0)
    parser.add_argument("--event-distance-km", type=float, default=10.0)
    parser.add_argument("--max-time-gap-hours", type=float, default=13.0)
    parser.add_argument(
        "--tracking-method",
        choices=["baseline", "one_to_one"],
        default="one_to_one",
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    csv_path = resolve_project_path(args.csv_path)
    perimeter_path = resolve_project_path(args.perimeter)
    detections = load_detections(csv_path)
    ring = load_outer_ring(perimeter_path)
    frames = replay_detections(
        detections=detections,
        cluster_distance_km=args.cluster_distance_km,
        event_distance_km=args.event_distance_km,
        max_time_gap=timedelta(hours=args.max_time_gap_hours),
        tracking_method=args.tracking_method,
    )
    if not frames:
        raise SystemExit("The historical dataset contains no replay frames.")

    ring_longitudes = [coordinate[0] for coordinate in ring]
    ring_latitudes = [coordinate[1] for coordinate in ring]
    all_longitudes = ring_longitudes + [d.longitude for d in detections]
    all_latitudes = ring_latitudes + [d.latitude for d in detections]
    longitude_padding = (max(all_longitudes) - min(all_longitudes)) * 0.06
    latitude_padding = (max(all_latitudes) - min(all_latitudes)) * 0.06
    mean_latitude = sum(all_latitudes) / len(all_latitudes)

    figure, axes = plt.subplots(
        1,
        len(frames),
        figsize=(16, 5.8),
        sharex=True,
        sharey=True,
    )
    axes = [axes] if len(frames) == 1 else list(axes)

    for axis, frame in zip(axes, frames):
        available_detections = [
            detection
            for detection in detections
            if detection.acquired_at_utc <= frame.timestamp
        ]
        axis.fill(
            ring_longitudes,
            ring_latitudes,
            color="#8bcf8b",
            alpha=0.28,
            label="Reference perimeter",
        )
        axis.plot(ring_longitudes, ring_latitudes, color="#2f6f3e", linewidth=1.2)
        axis.scatter(
            [detection.longitude for detection in available_detections],
            [detection.latitude for detection in available_detections],
            color="#d1495b",
            edgecolors="white",
            linewidths=0.35,
            s=25,
            alpha=0.82,
            label="Available FIRMS detections",
            zorder=3,
        )
        axis.scatter(
            [event.centroid_longitude for event in frame.events],
            [event.centroid_latitude for event in frame.events],
            color="#2463a6",
            edgecolors="white",
            linewidths=0.8,
            marker="X",
            s=90,
            label="Candidate-event centroids",
            zorder=4,
        )
        for event in frame.events:
            axis.annotate(
                f"E{event.event_id}",
                (event.centroid_longitude, event.centroid_latitude),
                xytext=(5, 5),
                textcoords="offset points",
                fontsize=8,
                weight="bold",
            )

        axis.set_title(
            f"{frame.timestamp:%Y-%m-%d %H:%M UTC}\n"
            f"available={len(available_detections)}, events={len(frame.events)}",
            fontsize=10,
        )
        axis.set_xlim(
            min(all_longitudes) - longitude_padding,
            max(all_longitudes) + longitude_padding,
        )
        axis.set_ylim(
            min(all_latitudes) - latitude_padding,
            max(all_latitudes) + latitude_padding,
        )
        axis.set_aspect(1 / math.cos(math.radians(mean_latitude)))
        axis.xaxis.set_major_locator(MaxNLocator(nbins=4))
        axis.xaxis.set_major_formatter(FormatStrFormatter("%.3f"))
        axis.tick_params(axis="x", labelrotation=20, labelsize=8)
        axis.set_xlabel("Longitude")
        axis.grid(alpha=0.2)

    axes[0].set_ylabel("Latitude")
    handles, labels = axes[0].get_legend_handles_labels()
    figure.legend(
        handles,
        labels,
        loc="lower center",
        bbox_to_anchor=(0.5, 0.055),
        ncols=3,
        frameon=False,
    )
    figure.suptitle(
        f"Lahaina historical replay — {args.tracking_method.replace('_', '-')} tracking",
        fontsize=14,
        weight="bold",
        y=0.98,
    )
    figure.text(
        0.5,
        0.018,
        "Thermal anomalies and candidate events; not emergency or ground-truth data.",
        ha="center",
        fontsize=9,
        color="#555555",
    )
    figure.subplots_adjust(
        left=0.06,
        right=0.985,
        top=0.84,
        bottom=0.2,
        wspace=0.3,
    )

    output_path = resolve_project_path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output_path, dpi=180)
    plt.close(figure)
    print(f"Saved {len(frames)} replay panels to {output_path}")


if __name__ == "__main__":
    main()
