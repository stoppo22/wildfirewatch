"""Tests for SQLite persistence."""

import sqlite3
from datetime import datetime, timezone

from wildfirewatch.models import Detection, FireEvent, EventObservation
from wildfirewatch.database import (
    create_tables,
    insert_detection,
    insert_detections,
    upsert_fire_event,
    load_fire_events,
)


def test_create_tables_creates_detections_table():
    connection = sqlite3.connect(":memory:")

    create_tables(connection)

    actual = connection.execute("""
      SELECT name
      FROM sqlite_master
      WHERE type =  'table'
      AND name = 'detections'
      """).fetchone()

    connection.close()

    assert actual == ("detections",)


def test_insert_detection_saves_detection_values():
    connection = sqlite3.connect(":memory:")
    create_tables(connection)
    detection = Detection(
        latitude=20.878,
        longitude=-156.674,
        acquired_at_utc=datetime(2023, 8, 9, 12, 15, tzinfo=timezone.utc),
        frp=42.5,
        confidence="nominal",
        satellite="NOAA-20",
        day_night="D",
    )

    insert_detection(connection, detection)

    actual = connection.execute("""
        SELECT
            id,
            latitude,
            longitude,
            acquired_at_utc,
            frp,
            confidence,
            satellite,
            day_night
        FROM detections;
    """).fetchone()

    connection.close()

    expected = (
        1,
        20.878,
        -156.674,
        "2023-08-09T12:15:00+00:00",
        42.5,
        "nominal",
        "NOAA-20",
        "D",
    )

    assert actual == expected


def test_detection_persists_after_reopening_database(tmp_path):
    database_path = tmp_path / "wildfirewatch.db"
    connection = sqlite3.connect(database_path)

    create_tables(connection)
    detection = Detection(
        latitude=20.878,
        longitude=-156.674,
        acquired_at_utc=datetime(2023, 8, 9, 12, 15, tzinfo=timezone.utc),
        frp=42.5,
        confidence="nominal",
        satellite="NOAA-20",
        day_night="D",
    )

    insert_detection(connection, detection)

    connection.commit()
    connection.close()

    reopened_connection = sqlite3.connect(database_path)

    actual = reopened_connection.execute("SELECT COUNT(*) FROM detections;").fetchone()

    reopened_connection.close()

    assert actual == (1,)


def test_insert_detection_ignores_exact_duplicate():
    connection = sqlite3.connect(":memory:")
    create_tables(connection)
    detection = Detection(
        latitude=20.878,
        longitude=-156.674,
        acquired_at_utc=datetime(2023, 8, 9, 12, 15, tzinfo=timezone.utc),
        frp=42.5,
        confidence="nominal",
        satellite="NOAA-20",
        day_night="D",
    )
    first_inserted = insert_detection(connection, detection)
    second_inserted = insert_detection(connection, detection)

    actual = connection.execute("""
        SELECT COUNT(*)
        FROM detections;
        """).fetchone()
    connection.close()

    assert first_inserted is True
    assert second_inserted is False
    assert actual == (1,)


def test_insert_detection_keeps_different_timestamp():
    connection = sqlite3.connect(":memory:")
    create_tables(connection)
    first_detection = Detection(
        latitude=20.878,
        longitude=-156.674,
        acquired_at_utc=datetime(2023, 8, 9, 12, 15, tzinfo=timezone.utc),
        frp=42.5,
        confidence="nominal",
        satellite="NOAA-20",
        day_night="D",
    )
    second_detection = Detection(
        latitude=20.878,
        longitude=-156.674,
        acquired_at_utc=datetime(2023, 8, 9, 23, 26, tzinfo=timezone.utc),
        frp=42.5,
        confidence="nominal",
        satellite="NOAA-20",
        day_night="D",
    )
    insert_detection(connection, first_detection)
    insert_detection(connection, second_detection)

    actual = connection.execute("""
        SELECT COUNT(*)
        FROM detections;
        """).fetchone()

    connection.close()

    assert actual == (2,)


def test_insert_detections_counts_only_new_detections():
    connection = sqlite3.connect(":memory:")
    create_tables(connection)

    existing_detection = Detection(
        latitude=20.878,
        longitude=-156.674,
        acquired_at_utc=datetime(2023, 8, 9, 12, 15, tzinfo=timezone.utc),
        frp=42.5,
        confidence="nominal",
        satellite="NOAA-20",
        day_night="D",
    )

    new_detection = Detection(
        latitude=20.878,
        longitude=-156.674,
        acquired_at_utc=datetime(2023, 8, 9, 23, 26, tzinfo=timezone.utc),
        frp=42.5,
        confidence="nominal",
        satellite="NOAA-20",
        day_night="D",
    )

    second_new_detection = Detection(
        latitude=20.878,
        longitude=-156.674,
        acquired_at_utc=datetime(2023, 8, 10, 23, 26, tzinfo=timezone.utc),
        frp=42.5,
        confidence="nominal",
        satellite="NOAA-20",
        day_night="D",
    )

    insert_detection(connection, existing_detection)

    inserted_count = insert_detections(
        connection,
        [existing_detection, new_detection, second_new_detection],
    )

    actual = connection.execute("SELECT COUNT(*) FROM detections;").fetchone()

    connection.close()

    assert inserted_count == 2
    assert actual == (3,)


def test_create_tables_creates_fire_events_table():
    connection = sqlite3.connect(":memory:")

    create_tables(connection)

    actual = connection.execute("""
      SELECT name
      FROM sqlite_master
      WHERE type =  'table'
      AND name = 'fire_events'
      """).fetchone()

    connection.close()

    assert actual == ("fire_events",)


def test_upsert_fire_event_saves_fire_event_values():
    connection = sqlite3.connect(":memory:")
    create_tables(connection)

    fire_event = FireEvent(
        event_id=7,
        first_seen_utc=datetime(2026, 9, 2, 18, 30, tzinfo=timezone.utc),
        last_seen_utc=datetime(2026, 9, 2, 19, 30, tzinfo=timezone.utc),
        centroid_latitude=20.878,
        centroid_longitude=-156.674,
        detection_count=4,
    )

    upsert_fire_event(connection, fire_event)

    actual = connection.execute("""
        SELECT
            event_id,
            first_seen_utc,
            last_seen_utc,
            centroid_latitude,
            centroid_longitude,
            detection_count
        FROM fire_events;
        """).fetchone()

    connection.close()

    expected = (
        7,
        "2026-09-02T18:30:00+00:00",
        "2026-09-02T19:30:00+00:00",
        20.878,
        -156.674,
        4,
    )

    assert actual == expected


def test_upsert_fire_event_updates_existing_event():
    connection = sqlite3.connect(":memory:")
    create_tables(connection)

    original_event = FireEvent(
        event_id=7,
        first_seen_utc=datetime(2026, 9, 2, 18, 30, tzinfo=timezone.utc),
        last_seen_utc=datetime(2026, 9, 2, 19, 30, tzinfo=timezone.utc),
        centroid_latitude=20.878,
        centroid_longitude=-156.674,
        detection_count=4,
    )

    upsert_fire_event(connection, original_event)

    updated_event = FireEvent(
        event_id=7,
        first_seen_utc=datetime(2026, 9, 2, 18, 30, tzinfo=timezone.utc),
        last_seen_utc=datetime(2026, 9, 2, 21, 30, tzinfo=timezone.utc),
        centroid_latitude=22.878,
        centroid_longitude=-158.674,
        detection_count=6,
    )

    upsert_fire_event(connection, updated_event)

    row_count = connection.execute("""
        SELECT COUNT(*)
        FROM fire_events;
    """).fetchone()

    actual = connection.execute("""
        SELECT
            last_seen_utc,
            centroid_latitude,
            centroid_longitude,
            detection_count
        FROM fire_events;
    """).fetchone()

    connection.close()

    expected = (
        "2026-09-02T21:30:00+00:00",
        22.878,
        -158.674,
        6,
    )

    assert row_count == (1,)
    assert actual == expected


def test_upsert_fire_event_saves_event_observations():
    connection = sqlite3.connect(":memory:")
    create_tables(connection)

    observation = EventObservation(
        first_seen_utc=datetime(2026, 9, 2, 18, 30, tzinfo=timezone.utc),
        last_seen_utc=datetime(2026, 9, 2, 19, 30, tzinfo=timezone.utc),
        centroid_latitude=22.878,
        centroid_longitude=-158.674,
        max_radius_km=10,
        detection_count=4,
        total_frp=2,
    )

    second_observation = EventObservation(
        first_seen_utc=datetime(2026, 9, 2, 18, 30, tzinfo=timezone.utc),
        last_seen_utc=datetime(2026, 9, 2, 21, 30, tzinfo=timezone.utc),
        centroid_latitude=20.878,
        centroid_longitude=-156.674,
        max_radius_km=10,
        detection_count=4,
        total_frp=2,
    )

    event = FireEvent(
        event_id=7,
        first_seen_utc=datetime(2026, 9, 2, 18, 30, tzinfo=timezone.utc),
        last_seen_utc=datetime(2026, 9, 2, 21, 30, tzinfo=timezone.utc),
        centroid_latitude=22.878,
        centroid_longitude=-158.674,
        detection_count=4,
        observations=[observation, second_observation],
    )

    upsert_fire_event(connection, event)
    upsert_fire_event(connection, event)

    actual = connection.execute("""
        SELECT
            event_id,
            observation_index,
            first_seen_utc,
            last_seen_utc,
            centroid_latitude,
            centroid_longitude,
            max_radius_km,
            detection_count,
            total_frp
        FROM event_observations
        ORDER BY observation_index;
        """).fetchall()

    connection.close()

    expected = [
        (
            7,
            0,
            "2026-09-02T18:30:00+00:00",
            "2026-09-02T19:30:00+00:00",
            22.878,
            -158.674,
            10,
            4,
            2,
        ),
        (
            7,
            1,
            "2026-09-02T18:30:00+00:00",
            "2026-09-02T21:30:00+00:00",
            20.878,
            -156.674,
            10,
            4,
            2,
        ),
    ]

    assert actual == expected


def test_load_fire_events_restores_event_after_reopening_database(tmp_path):
    database_path = tmp_path / "wildfirewatch.db"
    connection = sqlite3.connect(database_path)

    create_tables(connection)

    observation = EventObservation(
        first_seen_utc=datetime(2026, 9, 2, 18, 30, tzinfo=timezone.utc),
        last_seen_utc=datetime(2026, 9, 2, 19, 30, tzinfo=timezone.utc),
        centroid_latitude=22.878,
        centroid_longitude=-158.674,
        max_radius_km=10,
        detection_count=4,
        total_frp=2,
    )

    event = FireEvent(
        event_id=7,
        first_seen_utc=datetime(2026, 9, 2, 18, 30, tzinfo=timezone.utc),
        last_seen_utc=datetime(2026, 9, 2, 19, 30, tzinfo=timezone.utc),
        centroid_latitude=22.878,
        centroid_longitude=-158.674,
        detection_count=4,
        observations=[observation],
    )

    upsert_fire_event(connection, event)

    connection.commit()
    connection.close()

    reopened_connection = sqlite3.connect(database_path)
    actual = load_fire_events(reopened_connection)
    reopened_connection.close()

    assert actual == [event]
