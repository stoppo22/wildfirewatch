"""Controlled synthetic scenarios for reproducible evaluation."""

from datetime import datetime, timezone

from wildfirewatch.models import Detection


def _make_detection(longitude: float, acquired_at_utc: datetime) -> Detection:
    """Create one detection on the equator for a controlled scenario."""
    return Detection(
        latitude=0.0,
        longitude=longitude,
        acquired_at_utc=acquired_at_utc,
        frp=10.0,
        confidence="n",
        satellite="N20",
        day_night="D",
    )


def create_distance_threshold_scenario() -> list[tuple[str, list[Detection]]]:
    """Create a scenario exposing the spatial split/merge trade-off."""
    first_time = datetime(2026, 8, 31, 10, 0, tzinfo=timezone.utc)
    second_time = datetime(2026, 8, 31, 12, 0, tzinfo=timezone.utc)

    return [
        ("fire_a", [_make_detection(0.00, first_time)]),
        ("fire_b", [_make_detection(0.16, first_time)]),
        ("fire_a", [_make_detection(0.06, second_time)]),
        ("fire_b", [_make_detection(0.22, second_time)]),
    ]


def create_time_gap_threshold_scenario() -> list[tuple[str, list[Detection]]]:
    """Create a scenario exposing the temporal split/merge trade-off."""
    return [
        (
            "fire_a",
            [
                _make_detection(
                    0.0,
                    datetime(2026, 8, 31, 0, 0, tzinfo=timezone.utc),
                )
            ],
        ),
        (
            "fire_a",
            [
                _make_detection(
                    0.0,
                    datetime(2026, 8, 31, 2, 0, tzinfo=timezone.utc),
                )
            ],
        ),
        (
            "fire_b",
            [
                _make_detection(
                    0.0,
                    datetime(2026, 8, 31, 10, 0, tzinfo=timezone.utc),
                )
            ],
        ),
        (
            "fire_b",
            [
                _make_detection(
                    0.0,
                    datetime(2026, 8, 31, 12, 0, tzinfo=timezone.utc),
                )
            ],
        ),
    ]
