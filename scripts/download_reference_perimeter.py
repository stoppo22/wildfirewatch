"""Download the selected Lahaina reference perimeter from an ArcGIS service."""

import argparse
import json
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_URL = (
    "https://services.arcgis.com/v01gqwM5QqNysAAi/ArcGIS/rest/services/"
    "Lahaina_Fire_Perimeter/FeatureServer/6/query"
    "?where=OBJECTID%3D2"
    "&outFields=OBJECTID%2Cpoly_IncidentName%2Cpoly_MapMethod%2Cpoly_GISAcres%2C"
    "poly_Source%2Cpoly_PolygonDateTime"
    "&returnGeometry=true&outSR=4326&f=geojson"
)
DEFAULT_OUTPUT = Path("data/reference/lahaina_fire_perimeter_usgs_object_2.geojson")


def validate_reference_geojson(payload: object) -> dict:
    """Validate the narrow GeoJSON shape expected by the spatial evaluation."""
    if not isinstance(payload, dict) or payload.get("type") != "FeatureCollection":
        raise ValueError("Reference response is not a GeoJSON FeatureCollection.")

    features = payload.get("features")
    if not isinstance(features, list) or len(features) != 1:
        raise ValueError("Reference response must contain exactly one feature.")

    feature = features[0]
    geometry = feature.get("geometry") if isinstance(feature, dict) else None
    properties = feature.get("properties") if isinstance(feature, dict) else None

    if not isinstance(geometry, dict) or geometry.get("type") != "Polygon":
        raise ValueError("Reference feature must contain one Polygon geometry.")
    if not isinstance(properties, dict) or properties.get("OBJECTID") != 2:
        raise ValueError("Reference feature does not have the expected OBJECTID=2.")

    return payload


def main() -> None:
    """Download and save the selected public reference perimeter."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    request = Request(REFERENCE_URL, headers={"User-Agent": "WildfireWatch/0.3"})
    try:
        with urlopen(request, timeout=60) as response:
            payload = json.load(response)
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as error:
        raise SystemExit(
            "Reference perimeter download failed. Check the service and network."
        ) from error

    try:
        geojson = validate_reference_geojson(payload)
    except ValueError as error:
        raise SystemExit(str(error)) from error

    output_path = args.output
    if not output_path.is_absolute():
        output_path = PROJECT_ROOT / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(geojson, indent=2) + "\n",
        encoding="utf-8",
    )

    feature = geojson["features"][0]
    coordinate_count = len(feature["geometry"]["coordinates"][0])
    print(
        f"Saved one reference polygon ({coordinate_count} coordinates) to {output_path}"
    )


if __name__ == "__main__":
    main()
