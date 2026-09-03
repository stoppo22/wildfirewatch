"""Incremental persistent processing for WildfireWatch."""

import sqlite3
from datetime import timedelta

from wildfirewatch.models import Detection, FireEvent
from wildfirewatch.database import (
    insert_detection,
    load_fire_events,
    upsert_fire_event,
)
from wildfirewatch.replay import group_detections_by_time
from wildfirewatch.clustering import cluster_detections
from wildfirewatch.tracking import update_events_one_to_one


def process_incremental_detections(
    connection: sqlite3.Connection,
    detections: list[Detection],
    cluster_distance_km: float,
    event_distance_km: float,
    max_time_gap: timedelta,
) -> list[FireEvent]:
    """Process new detections while preserving persisted event state."""
    new_detections = []

    for detection in detections:
        if insert_detection(connection, detection):
            new_detections.append(detection)

    events = load_fire_events(connection)

    if not new_detections:
        return events

    for _timestamp, temporal_group in group_detections_by_time(new_detections):
        clusters = cluster_detections(
            temporal_group,
            max_distance_km=cluster_distance_km,
        )

        events = update_events_one_to_one(
            events=events,
            clusters=clusters,
            max_distance_km=event_distance_km,
            max_time_gap=max_time_gap,
        )

    for updated_event in events:
        upsert_fire_event(connection, updated_event)

    return events
