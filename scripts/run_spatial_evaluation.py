"""Evaluate FIRMS detections against a local spatial reference perimeter."""

import argparse
import json
from pathlib import Path

from wildfirewatch.ingestion import load_detections
from wildfirewatch.spatial_evaluation import detection_coverage_ratio

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PERIMETER = Path("data/reference/lahaina_fire_perimeter_usgs_object_2.geojson")
DEFAULT_OUTPUT = Path("evaluation/results/lahaina_spatial_coverage.json")
REFERENCE_SERVICE = (
    "https://services.arcgis.com/v01gqwM5QqNysAAi/ArcGIS/rest/services/"
    "Lahaina_Fire_Perimeter/FeatureServer/6"
)


def resolve_project_path(path: Path) -> Path:
    """Resolve a CLI path relative to the repository root."""
    return path if path.is_absolute() else PROJECT_ROOT / path


def load_reference_ring(path: Path) -> list[list[float]]:
    """Load the outer ring from the expected single-Polygon GeoJSON."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        features = payload["features"]
        feature = features[0]
        if len(features) != 1 or feature["geometry"]["type"] != "Polygon":
            raise ValueError
        ring = feature["geometry"]["coordinates"][0]
    except (OSError, json.JSONDecodeError, KeyError, IndexError, TypeError, ValueError):
        raise SystemExit(
            "Reference file must contain exactly one GeoJSON Polygon. "
            "Run scripts/download_reference_perimeter.py first."
        ) from None

    if not isinstance(ring, list) or len(ring) < 3:
        raise SystemExit("Reference Polygon has no valid outer ring.")
    return ring


def main() -> None:
    """Calculate and save the historical spatial coverage report."""
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--perimeter", type=Path, default=DEFAULT_PERIMETER)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    csv_path = resolve_project_path(args.csv_path)
    perimeter_path = resolve_project_path(args.perimeter)
    detections = load_detections(csv_path)
    ring = load_reference_ring(perimeter_path)
    coverage_ratio = detection_coverage_ratio(detections, ring)

    report = {
        "kind": "historical_spatial_reference_evaluation",
        "source_csv": csv_path.relative_to(PROJECT_ROOT).as_posix(),
        "reference_geojson": perimeter_path.relative_to(PROJECT_ROOT).as_posix(),
        "reference": {
            "service": REFERENCE_SERVICE,
            "object_id": 2,
            "incident_name": "Lahaina",
            "source": "2023 NIFS",
            "map_method": "Auto-generated",
        },
        "detection_count": len(detections),
        "coverage_ratio": coverage_ratio,
        "limitations": (
            "Coverage measures the fraction of FIRMS thermal-anomaly points "
            "inside or on one reference perimeter. It is not tracking accuracy, "
            "confirmed wildfire ground truth, or temporal validation."
        ),
    }

    output_path = resolve_project_path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(
        f"Saved spatial coverage for {len(detections)} detections " f"to {output_path}"
    )


if __name__ == "__main__":
    main()
