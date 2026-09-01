"""Associate detection clusters with fire events."""

from datetime import timedelta

from wildfirewatch.geo import haversine_distance_km
from wildfirewatch.models import (
    ClusterSummary,
    Detection,
    EventObservation,
    FireEvent,
)
from wildfirewatch.summary import summarize_cluster


def _observation_from_summary(summary: ClusterSummary) -> EventObservation:
    """Create one immutable event observation from a cluster summary."""
    return EventObservation(
        first_seen_utc=summary.first_seen_utc,
        last_seen_utc=summary.last_seen_utc,
        centroid_latitude=summary.centroid_latitude,
        centroid_longitude=summary.centroid_longitude,
        detection_count=summary.detection_count,
        total_frp=summary.total_frp,
        max_radius_km=summary.max_radius_km,
    )


def _update_event_from_summary(
    event: FireEvent,
    summary: ClusterSummary,
) -> FireEvent:
    """Return an event updated with one additional cluster summary."""
    new_detection_count = event.detection_count + summary.detection_count
    new_centroid_latitude = (
        event.centroid_latitude * event.detection_count
        + summary.centroid_latitude * summary.detection_count
    ) / new_detection_count
    new_centroid_longitude = (
        event.centroid_longitude * event.detection_count
        + summary.centroid_longitude * summary.detection_count
    ) / new_detection_count

    return FireEvent(
        event_id=event.event_id,
        first_seen_utc=min(event.first_seen_utc, summary.first_seen_utc),
        last_seen_utc=max(event.last_seen_utc, summary.last_seen_utc),
        centroid_latitude=new_centroid_latitude,
        centroid_longitude=new_centroid_longitude,
        detection_count=new_detection_count,
        observations=event.observations + [_observation_from_summary(summary)],
    )


def _create_event_from_summary(
    event_id: int,
    summary: ClusterSummary,
) -> FireEvent:
    """Create a new event from one cluster summary."""
    return FireEvent(
        event_id=event_id,
        centroid_latitude=summary.centroid_latitude,
        centroid_longitude=summary.centroid_longitude,
        detection_count=summary.detection_count,
        first_seen_utc=summary.first_seen_utc,
        last_seen_utc=summary.last_seen_utc,
        observations=[_observation_from_summary(summary)],
    )


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
            updated_events[matching_event_index] = _update_event_from_summary(
                event,
                summary,
            )
            continue

        new_event = _create_event_from_summary(
            next_event_id,
            summary,
        )
        updated_events.append(new_event)
        next_event_id += 1
    return updated_events


def match_clusters_one_to_one(
    events: list[FireEvent],
    summaries: list[ClusterSummary],
    max_distance_km: float,
    max_time_gap: timedelta,
) -> dict[int, int]:
    candidates = []
    for event_index, event in enumerate(events):
        for cluster_index, summary in enumerate(summaries):
            distance = haversine_distance_km(
                event.centroid_latitude,
                event.centroid_longitude,
                summary.centroid_latitude,
                summary.centroid_longitude,
            )

            time_gap = summary.first_seen_utc - event.last_seen_utc

            if distance <= max_distance_km and timedelta(0) <= time_gap <= max_time_gap:
                candidates.append(
                    (
                        distance,
                        event.event_id,
                        event_index,
                        cluster_index,
                    )
                )

    matches = {}
    used_event_indexes = set()
    used_cluster_indexes = set()

    for _, _, event_index, cluster_index in sorted(candidates):
        if event_index in used_event_indexes or cluster_index in used_cluster_indexes:
            continue

        matches[cluster_index] = event_index
        used_event_indexes.add(event_index)
        used_cluster_indexes.add(cluster_index)

    return matches


def update_events_one_to_one(
    events: list[FireEvent],
    clusters: list[list[Detection]],
    max_distance_km: float,
    max_time_gap: timedelta,
) -> list[FireEvent]:
    """Update events with at most one cluster match per event and frame."""
    summaries = [summarize_cluster(cluster) for cluster in clusters]
    matches = match_clusters_one_to_one(
        events=events,
        summaries=summaries,
        max_distance_km=max_distance_km,
        max_time_gap=max_time_gap,
    )
    updated_events = list(events)
    next_event_id = 1

    if events:
        next_event_id = max(event.event_id for event in events) + 1

    for cluster_index, summary in enumerate(summaries):
        if cluster_index in matches:
            event_index = matches[cluster_index]
            updated_events[event_index] = _update_event_from_summary(
                updated_events[event_index],
                summary,
            )
            continue

        updated_events.append(
            _create_event_from_summary(
                next_event_id,
                summary,
            )
        )
        next_event_id += 1

    return updated_events
