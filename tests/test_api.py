"""Tests for the WildfireWatch HTTP API."""

import sqlite3
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from wildfirewatch.api import app, event_to_summary
from wildfirewatch.database import create_tables, upsert_fire_event
from wildfirewatch.models import FireEvent

client = TestClient(app)


def test_health_endpoint_reports_api_is_running():
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_event_to_summary_maps_internal_event_fields():
    start = datetime(2023, 8, 9, 12, 0, tzinfo=timezone.utc)
    event = FireEvent(
        event_id=7,
        first_seen_utc=start,
        last_seen_utc=start + timedelta(hours=2, minutes=30),
        centroid_latitude=20.878,
        centroid_longitude=-156.674,
        detection_count=4,
    )

    summary = event_to_summary(event)

    assert summary.event_id == 7
    assert summary.centroid_latitude == 20.878
    assert summary.centroid_longitude == -156.674
    assert summary.duration_hours == 2.5
    assert summary.detection_count == 4


def test_event_endpoints_read_configured_database(tmp_path, monkeypatch):
    database_path = tmp_path / "wildfirewatch.db"
    start = datetime(2023, 8, 9, 12, 0, tzinfo=timezone.utc)
    event = FireEvent(
        event_id=7,
        first_seen_utc=start,
        last_seen_utc=start + timedelta(hours=2, minutes=30),
        centroid_latitude=20.878,
        centroid_longitude=-156.674,
        detection_count=4,
    )

    connection = sqlite3.connect(database_path)
    try:
        create_tables(connection)
        upsert_fire_event(connection, event)
        connection.commit()
    finally:
        connection.close()

    monkeypatch.setattr(
        "wildfirewatch.api.DEFAULT_DATABASE_PATH",
        database_path,
    )

    response = client.get("/api/events")
    body = response.json()

    assert response.status_code == 200
    assert len(body) == 1
    assert body[0]["event_id"] == 7
    assert body[0]["duration_hours"] == 2.5

    found_response = client.get("/api/events/7")
    missing_response = client.get("/api/events/999")

    assert found_response.status_code == 200
    assert found_response.json()["event_id"] == 7
    assert missing_response.status_code == 404
    assert missing_response.json() == {"detail": "Event not found"}
