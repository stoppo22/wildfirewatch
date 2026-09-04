"""Tests for the WildfireWatch HTTP API."""

import sqlite3
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from wildfirewatch.api import (
    HealthResponse,
    app,
    event_to_summary,
    observation_to_response,
)
from wildfirewatch.database import (
    create_tables,
    upsert_fire_event,
    upsert_land_cover_context,
)
from wildfirewatch.models import EventObservation, FireEvent, LandCoverContext
from wildfirewatch.scoring import calculate_priority_score

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

    expected_score = calculate_priority_score(event)

    summary = event_to_summary(event)

    assert summary.event_id == 7
    assert summary.centroid_latitude == 20.878
    assert summary.centroid_longitude == -156.674
    assert summary.duration_hours == 2.5
    assert summary.detection_count == 4
    assert summary.priority.score == expected_score.total
    assert summary.priority.persistence_points == expected_score.persistence_points
    assert summary.priority.level == "low"
    assert summary.land_cover is None


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
        observations=[
            EventObservation(
                first_seen_utc=start,
                last_seen_utc=start + timedelta(hours=2, minutes=30),
                centroid_latitude=20.878,
                centroid_longitude=-156.674,
                max_radius_km=1.5,
                detection_count=4,
                total_frp=60.0,
            )
        ],
    )

    context = LandCoverContext(
        event_id=7,
        class_code=50,
        sampled_latitude=20.878,
        sampled_longitude=-156.674,
        dataset="ESA/WorldCover/v200",
    )

    connection = sqlite3.connect(database_path)
    try:
        create_tables(connection)
        upsert_fire_event(connection, event)
        upsert_land_cover_context(connection, context)
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
    assert body[0]["priority"]["level"] == "low"
    assert body[0]["land_cover"] == "built_up"

    found_response = client.get("/api/events/7")
    found_body = found_response.json()
    missing_response = client.get("/api/events/999")

    assert found_response.status_code == 200
    assert found_body["event_id"] == 7
    assert len(found_body["observations"]) == 1
    assert found_body["observations"][0]["mean_frp"] == 15.0
    assert missing_response.status_code == 404
    assert missing_response.json() == {"detail": "Event not found"}


def test_response_models_reject_unknown_fields():
    with pytest.raises(ValidationError):
        HealthResponse(
            status="ok",
            unexpected="value",
        )


def test_observation_to_response_rejects_zero_detections():
    now = datetime(2023, 8, 9, 12, 0, tzinfo=timezone.utc)
    observation = EventObservation(
        first_seen_utc=now,
        last_seen_utc=now,
        centroid_latitude=20.878,
        centroid_longitude=-156.674,
        max_radius_km=0.0,
        detection_count=0,
        total_frp=0.0,
    )

    with pytest.raises(
        ValueError,
        match="observation detection_count must be positive",
    ):
        observation_to_response(observation)
