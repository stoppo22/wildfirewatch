"""Expose WildfireWatch data through an HTTP API."""

import sqlite3
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from wildfirewatch.database import load_fire_events
from wildfirewatch.models import FireEvent

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATABASE_PATH = PROJECT_ROOT / "data" / "wildfirewatch.db"

app = FastAPI(
    title="WildfireWatch",
    version="0.7.0",
)


class HealthResponse(BaseModel):
    """Describe the health endpoint response."""

    status: str


class EventSummaryResponse(BaseModel):
    """Describe one candidate event in the event-list response."""

    event_id: int
    centroid_latitude: float
    centroid_longitude: float
    first_seen_utc: datetime
    last_seen_utc: datetime
    duration_hours: float
    detection_count: int


def event_to_summary(event: FireEvent) -> EventSummaryResponse:
    """Convert an internal fire event into its public API summary."""
    duration_hours = event.duration.total_seconds() / 3600

    return EventSummaryResponse(
        event_id=event.event_id,
        centroid_latitude=event.centroid_latitude,
        centroid_longitude=event.centroid_longitude,
        first_seen_utc=event.first_seen_utc,
        last_seen_utc=event.last_seen_utc,
        duration_hours=duration_hours,
        detection_count=event.detection_count,
    )


def load_event_summaries(
    database_path: Path,
) -> list[EventSummaryResponse]:
    """Load persisted events and convert them into public API summaries."""
    connection = sqlite3.connect(database_path)

    try:
        events = load_fire_events(connection)
    finally:
        connection.close()

    return [event_to_summary(event) for event in events]


@app.get("/api/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Report whether the API is running."""
    return HealthResponse(status="ok")


@app.get("/api/events", response_model=list[EventSummaryResponse])
def list_events() -> list[EventSummaryResponse]:
    """Return summaries of all persisted candidate events."""
    return load_event_summaries(DEFAULT_DATABASE_PATH)


@app.get("/api/events/{event_id}", response_model=EventSummaryResponse)
def get_event(event_id: int) -> EventSummaryResponse:
    """Return one persisted candidate event by ID."""
    events = load_event_summaries(DEFAULT_DATABASE_PATH)

    for event in events:
        if event.event_id == event_id:
            return event

    raise HTTPException(
        status_code=404,
        detail="Event not found",
    )
