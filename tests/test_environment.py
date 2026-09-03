"""Tests for environmental context handling."""

import sqlite3
from datetime import datetime, timezone

from wildfirewatch.database import create_tables, upsert_fire_event
from wildfirewatch.environment import (
    get_or_fetch_land_cover_context,
    land_cover_name,
)
from wildfirewatch.models import FireEvent


def test_land_cover_name_returns_name_for_known_code():
    actual = land_cover_name(10)

    assert actual == "tree_cover"


def test_land_cover_name_returns_none_for_unknown_code():
    actual = land_cover_name(999)

    assert actual is None


def test_get_or_fetch_land_cover_context_reuses_cached_value(monkeypatch):
    connection = sqlite3.connect(":memory:")
    create_tables(connection)
    event = FireEvent(
        event_id=7,
        first_seen_utc=datetime(2023, 8, 9, 12, 15, tzinfo=timezone.utc),
        last_seen_utc=datetime(2023, 8, 9, 13, 15, tzinfo=timezone.utc),
        centroid_latitude=20.878,
        centroid_longitude=-156.674,
        detection_count=2,
    )
    upsert_fire_event(connection, event)
    fetch_call_count = 0

    def fake_fetch_land_cover_code(latitude, longitude):
        nonlocal fetch_call_count
        fetch_call_count += 1
        return 50

    monkeypatch.setattr(
        "wildfirewatch.environment.fetch_land_cover_code",
        fake_fetch_land_cover_code,
    )

    first_context = get_or_fetch_land_cover_context(connection, event)
    second_context = get_or_fetch_land_cover_context(connection, event)

    connection.close()

    assert first_context == second_context
    assert first_context is not None
    assert first_context.class_code == 50
    assert fetch_call_count == 1
