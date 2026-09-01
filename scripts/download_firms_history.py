"""Download a small historical FIRMS area query without exposing its MAP_KEY."""

import argparse
import os
from datetime import date
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def parse_date(value: str) -> date:
    """Parse an ISO date supplied on the command line."""
    return date.fromisoformat(value)


def main() -> None:
    """Download one bounded historical FIRMS CSV query."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default="VIIRS_NOAA20_SP")
    parser.add_argument("--area", required=True, help="west,south,east,north")
    parser.add_argument("--date", required=True, type=parse_date)
    parser.add_argument("--days", required=True, type=int, choices=range(1, 6))
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    load_dotenv(PROJECT_ROOT / ".env")
    map_key = os.getenv("FIRMS_MAP_KEY")
    if not map_key or map_key == "replace_with_your_firms_map_key":
        raise SystemExit("FIRMS_MAP_KEY is missing from the local .env file.")

    url = (
        "https://firms.modaps.eosdis.nasa.gov/api/area/csv/"
        f"{quote(map_key, safe='')}/{quote(args.source, safe='')}/"
        f"{quote(args.area, safe=',.-')}/{args.days}/{args.date.isoformat()}"
    )
    request = Request(url, headers={"User-Agent": "WildfireWatch/0.3"})

    try:
        with urlopen(request, timeout=60) as response:
            csv_bytes = response.read()
    except (HTTPError, URLError, TimeoutError) as error:
        raise SystemExit(
            "FIRMS download failed. Check the MAP_KEY, query parameters, and network."
        ) from error

    if not csv_bytes.startswith(b"latitude,longitude,"):
        raise SystemExit("FIRMS returned an unexpected response instead of a CSV.")

    output_path = args.output
    if not output_path.is_absolute():
        output_path = PROJECT_ROOT / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(csv_bytes)

    row_count = max(0, len(csv_bytes.splitlines()) - 1)
    print(f"Saved {row_count} FIRMS detections to {output_path}")


if __name__ == "__main__":
    main()
