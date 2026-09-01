from dataclasses import dataclass
from datetime import datetime, timedelta

from wildfirewatch.clustering import cluster_detections
from wildfirewatch.models import Detection, FireEvent
from wildfirewatch.tracking import update_events, update_events_one_to_one


@dataclass(frozen=True)
class ReplayFrame:
    timestamp: datetime
    detection_count: int
    cluster_count: int
    events: tuple[FireEvent, ...]


def group_detections_by_time(detections):
    detections_by_time = {}

    for detection in detections:
        timestamp = detection.acquired_at_utc

        if timestamp not in detections_by_time:
            detections_by_time[timestamp] = []

        detections_by_time[timestamp].append(detection)

    frames = []

    for timestamp in sorted(detections_by_time):
        frames.append((timestamp, detections_by_time[timestamp]))

    return frames


def replay_detections(
    detections: list[Detection],
    cluster_distance_km: float,
    event_distance_km: float,
    max_time_gap: timedelta,
    tracking_method: str = "baseline",
) -> list[ReplayFrame]:
    if tracking_method == "baseline":
        update_function = update_events
    elif tracking_method == "one_to_one":
        update_function = update_events_one_to_one
    else:
        raise ValueError(f"Unknown tracking method: {tracking_method}")

    events = []
    replay_frames = []

    for timestamp, frame_detections in group_detections_by_time(detections):
        clusters = cluster_detections(
            frame_detections,
            max_distance_km=cluster_distance_km,
        )
        events = update_function(
            events=events,
            clusters=clusters,
            max_distance_km=event_distance_km,
            max_time_gap=max_time_gap,
        )
        frame = ReplayFrame(
            timestamp=timestamp,
            detection_count=len(frame_detections),
            cluster_count=len(clusters),
            events=tuple(events),
        )
        replay_frames.append(frame)

    return replay_frames
