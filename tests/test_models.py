"""Tests for WildfireWatch domain models."""

from datetime import datetime, timezone

from wildfirewatch.models import Detection


def test_detection_stores_latitude():
    detection = Detection(
        latitude=41.9,
        longitude=12.5,
        acquired_at_utc=datetime(
            2026, 8, 28, 12, 30, tzinfo=timezone.utc
        ),
        frp=12.4,
        confidence="nominal",
        satellite="Suomi NPP",
        day_night="D",
    )

    assert detection.latitude == 41.9