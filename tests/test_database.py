"""Tests for SQLite persistence."""

import sqlite3
from datetime import datetime, timezone

from wildfirewatch.models import Detection
from wildfirewatch.database import create_tables, insert_detection


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
    insert_detection(connection, detection)
    insert_detection(connection, detection)

    actual = connection.execute("""
        SELECT COUNT(*)
        FROM detections;
        """).fetchone()
    connection.close()

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
