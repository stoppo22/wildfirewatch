"""Associate detection clusters with fire events."""

from datetime import timedelta

from wildfirewatch.geo import haversine_distance_km
from wildfirewatch.models import Detection, EventObservation, FireEvent
from wildfirewatch.summary import summarize_cluster


def update_events(
    events: list[FireEvent],
    clusters: list[list[Detection]],
    max_distance_km: float,
    max_time_gap: timedelta,
) -> list[FireEvent]:
    updated_events = list(events)
    next_event_id = 1

    if events:
        next_event_id = max(event.event_id for event in events) + 1

    for cluster in clusters:
        summary = summarize_cluster(cluster)
        observation = EventObservation(
            first_seen_utc=summary.first_seen_utc,
            last_seen_utc=summary.last_seen_utc,
            centroid_latitude=summary.centroid_latitude,
            centroid_longitude=summary.centroid_longitude,
            detection_count=summary.detection_count,
            total_frp=summary.total_frp,
            max_radius_km=summary.max_radius_km,
        )

        matching_event_index = None
        closest_distance = None

        for index, event in enumerate(updated_events):
            distance = haversine_distance_km(
                event.centroid_latitude,
                event.centroid_longitude,
                summary.centroid_latitude,
                summary.centroid_longitude,
            )
            time_gap = summary.first_seen_utc - event.last_seen_utc

            if (
                distance <= max_distance_km
                and timedelta(0) <= time_gap <= max_time_gap
                and (closest_distance is None or distance < closest_distance)
            ):
                matching_event_index = index
                closest_distance = distance

        if matching_event_index is not None:
            event = updated_events[matching_event_index]
            new_detection_count = event.detection_count + summary.detection_count
            new_centroid_latitude = (
                event.centroid_latitude * event.detection_count
                + summary.centroid_latitude * summary.detection_count
            ) / new_detection_count

            new_centroid_longitude = (
                event.centroid_longitude * event.detection_count
                + summary.centroid_longitude * summary.detection_count
            ) / new_detection_count

            updated_events[matching_event_index] = FireEvent(
                event_id=event.event_id,
                first_seen_utc=min(event.first_seen_utc, summary.first_seen_utc),
                last_seen_utc=max(event.last_seen_utc, summary.last_seen_utc),
                centroid_latitude=new_centroid_latitude,
                centroid_longitude=new_centroid_longitude,
                detection_count=new_detection_count,
                observations=event.observations + [observation],
            )
            continue

        new_event = FireEvent(
            event_id=next_event_id,
            centroid_latitude=summary.centroid_latitude,
            centroid_longitude=summary.centroid_longitude,
            detection_count=summary.detection_count,
            first_seen_utc=summary.first_seen_utc,
            last_seen_utc=summary.last_seen_utc,
            observations=[observation],
        )
        updated_events.append(new_event)
        next_event_id += 1
    return updated_events
