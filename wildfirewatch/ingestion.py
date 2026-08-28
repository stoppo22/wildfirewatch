"""Load and normalize NASA FIRMS active-fire detections."""

import csv
from datetime import datetime, timezone
from pathlib import Path

from wildfirewatch.models import Detection


def parse_acquired_at_utc(acq_date: str, acq_time: str) -> datetime:
    """Combine a FIRMS acquisition date and time into a UTC datetime."""
    padded_time = acq_time.zfill(4)
    date_time = f"{acq_date} {padded_time}"
    parsed_datetime = datetime.strptime(date_time, "%Y-%m-%d %H%M")
    return parsed_datetime.replace(tzinfo=timezone.utc)


def detection_from_row(row: dict[str, str]) -> Detection:
    """Convert one raw FIRMS CSV row into a Detection."""
    return Detection(
        latitude=float(row["latitude"]),
        longitude=float(row["longitude"]),
        acquired_at_utc=parse_acquired_at_utc(
            row["acq_date"],
            row["acq_time"],
        ),
        frp=float(row["frp"]),
        confidence=row["confidence"],
        satellite=row["satellite"],
        day_night=row["daynight"],
    )


def load_detections(path: Path) -> list[Detection]:
    """Load FIRMS detections from a CSV file."""
    detections: list[Detection] = []

    with path.open(encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            detections.append(detection_from_row(row))

    return detections
