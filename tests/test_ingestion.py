"""Tests for FIRMS data ingestion."""

from datetime import datetime, timezone
from pathlib import Path

import pytest

from wildfirewatch.ingestion import (
    detection_from_row,
    load_detections,
    parse_acquired_at_utc,
)
from wildfirewatch.models import Detection


def test_parse_acquired_at_utc_pads_short_time():
    actual = parse_acquired_at_utc("2025-06-06", "1")
    expected = datetime(2025, 6, 6, 0, 1, tzinfo=timezone.utc)

    assert actual == expected


def test_parse_acquired_at_utc_parses_four_digit_time():
    actual = parse_acquired_at_utc("2025-06-06", "1425")
    expected = datetime(2025, 6, 6, 14, 25, tzinfo=timezone.utc)

    assert actual == expected


def test_parse_acquired_at_utc_rejects_invalid_time():
    with pytest.raises(ValueError):
        parse_acquired_at_utc("2025-06-06", "2561")


def test_detection_from_row_converts_needed_fields():
    row = {
        "latitude": "-16.28359",
        "longitude": "29.40531",
        "acq_date": "2025-06-06",
        "acq_time": "1",
        "frp": "1.17",
        "confidence": "n",
        "satellite": "N20",
        "daynight": "N",
    }

    actual = detection_from_row(row)
    expected = Detection(
        latitude=-16.28359,
        longitude=29.40531,
        acquired_at_utc=datetime(2025, 6, 6, 0, 1, tzinfo=timezone.utc),
        frp=1.17,
        confidence="n",
        satellite="N20",
        day_night="N",
    )

    assert actual == expected


def test_load_detections_loads_every_sample_row():
    sample_path = (
        Path(__file__).parents[1] / "data" / "raw" / "viirs_noaa20_nrt_sample.csv"
    )
    detections = load_detections(sample_path)

    assert len(detections) == 5


def test_load_detections_returns_empty_list_for_empty_file(
    tmp_path: Path,
):
    empty_file = tmp_path / "empty.csv"
    empty_file.write_text("", encoding="utf-8")

    detections = load_detections(empty_file)

    assert detections == []


def test_detection_from_row_rejects_missing_required_field():
    row = {
        "longitude": "29.40531",
        "acq_date": "2025-06-06",
        "acq_time": "1",
        "frp": "1.17",
        "confidence": "n",
        "satellite": "N20",
        "daynight": "N",
    }

    with pytest.raises(KeyError):
        detection_from_row(row)
