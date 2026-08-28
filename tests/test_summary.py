"""Tests for detection summaries."""

from datetime import datetime, timezone

from wildfirewatch.models import Detection
from wildfirewatch.summary import format_detection_summary


def test_format_detection_summary_handles_empty_list():
    actual = format_detection_summary([])
    expected = "Detections: 0"

    assert actual == expected


def test_format_detection_summary_reports_count_and_time_range():
    later_detection = Detection(
        latitude=0.0,
        longitude=0.0,
        acquired_at_utc=datetime(2025, 6, 6, 14, 25, tzinfo=timezone.utc),
        frp=1.0,
        confidence="n",
        satellite="N20",
        day_night="N",
    )
    earlier_detection = Detection(
        latitude=0.0,
        longitude=0.0,
        acquired_at_utc=datetime(2025, 6, 6, 0, 1, tzinfo=timezone.utc),
        frp=1.0,
        confidence="n",
        satellite="N20",
        day_night="N",
    )
    detections = [later_detection, earlier_detection]

    actual = format_detection_summary(detections)
    expected = (
        "Detections: 2\n"
        "First acquired (UTC): 2025-06-06T00:01:00+00:00\n"
        "Last acquired (UTC): 2025-06-06T14:25:00+00:00"
    )

    assert actual == expected
