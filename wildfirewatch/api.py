"""Expose WildfireWatch data through an HTTP API."""

import sqlite3
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict

from wildfirewatch.database import (
    load_fire_events,
    load_land_cover_context,
)
from wildfirewatch.models import EventObservation, FireEvent
from wildfirewatch.scoring import (
    calculate_priority_score,
    classify_priority_level,
)
from wildfirewatch.environment import land_cover_name
from wildfirewatch.event_metrics import (
    calculate_centroid_path_km,
    calculate_mean_frp_change,
    calculate_radius_change_km,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATABASE_PATH = PROJECT_ROOT / "data" / "wildfirewatch.db"

app = FastAPI(
    title="WildfireWatch",
    version="0.7.0",
)


class ApiResponse(BaseModel):
    """Reject unexpected fields in public API response models."""

    model_config = ConfigDict(extra="forbid")


class HealthResponse(ApiResponse):
    """Describe the health endpoint response."""

    status: str


class PriorityResponse(ApiResponse):
    """Describe a review-priority score and its explainable contributions."""

    score: float
    level: str
    persistence_points: float
    frp_trend_points: float
    spatial_growth_points: float


class ObservationResponse(ApiResponse):
    """Describe one chronological observation of a candidate event."""

    first_seen_utc: datetime
    last_seen_utc: datetime
    centroid_latitude: float
    centroid_longitude: float
    max_radius_km: float
    detection_count: int
    total_frp: float
    mean_frp: float


class EventSummaryResponse(ApiResponse):
    """Describe one candidate event in the event-list response."""

    event_id: int
    centroid_latitude: float
    centroid_longitude: float
    first_seen_utc: datetime
    last_seen_utc: datetime
    duration_hours: float
    detection_count: int
    land_cover: str | None
    priority: PriorityResponse


class EventDetailResponse(EventSummaryResponse):
    """Describe one candidate event with metrics and observation history."""

    centroid_path_km: float
    radius_change_km: float
    mean_frp_change: float
    observations: list[ObservationResponse]


def observation_to_response(
    observation: EventObservation,
) -> ObservationResponse:
    """Convert an internal event observation into its API representation."""
    if observation.detection_count <= 0:
        raise ValueError("observation detection_count must be positive")

    mean_frp = observation.total_frp / observation.detection_count

    return ObservationResponse(
        first_seen_utc=observation.first_seen_utc,
        last_seen_utc=observation.last_seen_utc,
        centroid_latitude=observation.centroid_latitude,
        centroid_longitude=observation.centroid_longitude,
        max_radius_km=observation.max_radius_km,
        detection_count=observation.detection_count,
        total_frp=observation.total_frp,
        mean_frp=mean_frp,
    )


def event_to_summary(
    event: FireEvent,
    land_cover: str | None = None,
) -> EventSummaryResponse:
    """Convert an internal fire event into its public API summary."""

    score = calculate_priority_score(event)
    duration_hours = event.duration.total_seconds() / 3600

    return EventSummaryResponse(
        event_id=event.event_id,
        centroid_latitude=event.centroid_latitude,
        centroid_longitude=event.centroid_longitude,
        first_seen_utc=event.first_seen_utc,
        last_seen_utc=event.last_seen_utc,
        duration_hours=duration_hours,
        detection_count=event.detection_count,
        land_cover=land_cover,
        priority=PriorityResponse(
            score=score.total,
            level=classify_priority_level(score.total),
            persistence_points=score.persistence_points,
            frp_trend_points=score.frp_trend_points,
            spatial_growth_points=score.spatial_growth_points,
        ),
    )


def event_to_detail(
    event: FireEvent,
    land_cover: str | None = None,
) -> EventDetailResponse:
    """Convert an internal event into its detailed API representation."""
    summary = event_to_summary(
        event,
        land_cover=land_cover,
    )

    return EventDetailResponse(
        **summary.model_dump(),
        centroid_path_km=calculate_centroid_path_km(event),
        radius_change_km=calculate_radius_change_km(event),
        mean_frp_change=calculate_mean_frp_change(event),
        observations=[
            observation_to_response(observation) for observation in event.observations
        ],
    )


def load_event_summaries(
    database_path: Path,
) -> list[EventSummaryResponse]:
    """Load persisted events and convert them into public API summaries."""
    connection = sqlite3.connect(database_path)
    summaries = []

    try:
        events = load_fire_events(connection)

        for event in events:
            context = load_land_cover_context(
                connection,
                event.event_id,
            )
            land_cover = (
                land_cover_name(context.class_code) if context is not None else None
            )
            summaries.append(
                event_to_summary(
                    event,
                    land_cover=land_cover,
                )
            )
    finally:
        connection.close()

    return summaries


def load_event_detail(
    database_path: Path,
    event_id: int,
) -> EventDetailResponse | None:
    """Load one persisted event with context, metrics, and observations."""
    connection = sqlite3.connect(database_path)

    try:
        events = load_fire_events(connection)

        for event in events:
            if event.event_id == event_id:
                context = load_land_cover_context(
                    connection,
                    event.event_id,
                )
                land_cover = (
                    land_cover_name(context.class_code) if context is not None else None
                )

                return event_to_detail(
                    event,
                    land_cover=land_cover,
                )
    finally:
        connection.close()

    return None


@app.get("/api/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Report whether the API is running."""
    return HealthResponse(status="ok")


@app.get("/api/events", response_model=list[EventSummaryResponse])
def list_events() -> list[EventSummaryResponse]:
    """Return summaries of all persisted candidate events."""
    return load_event_summaries(DEFAULT_DATABASE_PATH)


@app.get("/api/events/{event_id}", response_model=EventDetailResponse)
def get_event(event_id: int) -> EventDetailResponse:
    """Return one persisted candidate event by ID."""
    detail = load_event_detail(
        DEFAULT_DATABASE_PATH,
        event_id,
    )

    if detail is None:
        raise HTTPException(
            status_code=404,
            detail="Event not found",
        )

    return detail
