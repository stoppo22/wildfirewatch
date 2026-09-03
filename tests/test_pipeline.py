"""Tests for incremental persistent processing."""

import sqlite3
from datetime import datetime, timedelta, timezone

from wildfirewatch.database import create_tables
from wildfirewatch.models import Detection
from wildfirewatch.pipeline import process_incremental_detections


def test_process_incremental_detections_does_not_reprocess_duplicate():
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

    first_events = process_incremental_detections(
        connection=connection,
        detections=[detection],
        cluster_distance_km=2.0,
        event_distance_km=10.0,
        max_time_gap=timedelta(hours=13),
    )
    second_events = process_incremental_detections(
        connection=connection,
        detections=[detection],
        cluster_distance_km=2.0,
        event_distance_km=10.0,
        max_time_gap=timedelta(hours=13),
    )

    stored_detection_count = connection.execute("""
        SELECT COUNT(*)
        FROM detections;
        """).fetchone()
    connection.close()

    assert len(first_events) == 1
    assert second_events == first_events
    assert second_events[0].detection_count == 1
    assert stored_detection_count == (1,)


def test_incremental_processing_updates_event_after_reopening(tmp_path):
    database_path = tmp_path / "wildfirewatch.db"
    first_connection = sqlite3.connect(database_path)
    create_tables(first_connection)

    first_detection = Detection(
        latitude=20.878,
        longitude=-156.674,
        acquired_at_utc=datetime(2023, 8, 9, 12, 15, tzinfo=timezone.utc),
        frp=42.5,
        confidence="nominal",
        satellite="NOAA-20",
        day_night="D",
    )

    first_events = process_incremental_detections(
        connection=first_connection,
        detections=[first_detection],
        cluster_distance_km=2.0,
        event_distance_km=10.0,
        max_time_gap=timedelta(hours=13),
    )

    first_connection.commit()
    first_connection.close()

    reopened_connection = sqlite3.connect(database_path)

    second_detection = Detection(
        latitude=20.878,
        longitude=-156.674,
        acquired_at_utc=datetime(2023, 8, 9, 13, 15, tzinfo=timezone.utc),
        frp=42.5,
        confidence="nominal",
        satellite="NOAA-20",
        day_night="D",
    )

    updated_events = process_incremental_detections(
        connection=reopened_connection,
        detections=[second_detection],
        cluster_distance_km=2.0,
        event_distance_km=10.0,
        max_time_gap=timedelta(hours=13),
    )

    stored_detection_count = reopened_connection.execute("""
        SELECT COUNT(*)
        FROM detections;
    """).fetchone()

    reopened_connection.commit()
    reopened_connection.close()

    assert len(first_events) == 1
    assert len(updated_events) == 1
    assert updated_events[0].event_id == first_events[0].event_id
    assert updated_events[0].detection_count == 2
    assert len(updated_events[0].observations) == 2
    assert stored_detection_count == (2,)
