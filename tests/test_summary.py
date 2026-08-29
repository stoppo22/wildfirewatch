"""Tests for detection summaries."""

from datetime import datetime, timezone

import pytest

from wildfirewatch.models import Detection
from wildfirewatch.summary import format_detection_summary, summarize_cluster


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


def test_summarize_cluster_calculates_basic_values():
    first = Detection(
        latitude=10.0,
        longitude=30.0,
        acquired_at_utc=datetime(2026, 8, 29, 12, 0, tzinfo=timezone.utc),
        frp=10.0,
        confidence="n",
        satellite="N20",
        day_night="D",
    )

    second = Detection(
        latitude=20.0,
        longitude=50.0,
        acquired_at_utc=datetime(2026, 8, 29, 14, 0, tzinfo=timezone.utc),
        frp=20.0,
        confidence="n",
        satellite="N20",
        day_night="D",
    )

    actual = summarize_cluster([first, second])

    assert actual.detection_count == 2
    assert actual.centroid_latitude == 15.0
    assert actual.centroid_longitude == 40.0
    assert actual.total_frp == 30.0
    assert actual.first_seen_utc == datetime(2026, 8, 29, 12, 0, tzinfo=timezone.utc)
    assert actual.last_seen_utc == datetime(2026, 8, 29, 14, 0, tzinfo=timezone.utc)


def test_summarize_cluster_rejects_empty_cluster():
    with pytest.raises(ValueError):
        summarize_cluster([])


def test_summarize_cluster_calculates_max_radius():
    first_detection = Detection(
        latitude=0.0,
        longitude=0.0,
        acquired_at_utc=datetime(2026, 8, 29, 10, 0, tzinfo=timezone.utc),
        frp=10.0,
        confidence="n",
        satellite="N20",
        day_night="D",
    )
    second_detection = Detection(
        latitude=0.0,
        longitude=2.0,
        acquired_at_utc=datetime(2026, 8, 29, 10, 0, tzinfo=timezone.utc),
        frp=10.0,
        confidence="n",
        satellite="N20",
        day_night="D",
    )

    actual = summarize_cluster([first_detection, second_detection])

    assert actual.max_radius_km == pytest.approx(111.2, abs=0.1)
