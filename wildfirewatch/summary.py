"""Create summaries of FIRMS detections and candidate clusters."""

from wildfirewatch.models import ClusterSummary, Detection


def format_detection_summary(detections: list[Detection]) -> str:
    """Return a short human-readable summary of detections."""
    if not detections:
        return "Detections: 0"

    first_acquired = min(detection.acquired_at_utc for detection in detections)
    last_acquired = max(detection.acquired_at_utc for detection in detections)

    return (
        f"Detections: {len(detections)}\n"
        f"First acquired (UTC): {first_acquired.isoformat()}\n"
        f"Last acquired (UTC): {last_acquired.isoformat()}"
    )


def summarize_cluster(cluster: list[Detection]) -> ClusterSummary:
    """Calculate basic summary values for a non-empty cluster."""

    if not cluster:
        raise ValueError("Cannot summarize an empty cluster.")

    detection_count = len(cluster)
    first_seen_utc = min(detection.acquired_at_utc for detection in cluster)
    last_seen_utc = max(detection.acquired_at_utc for detection in cluster)
    centroid_latitude = (
        sum(detection.latitude for detection in cluster) / detection_count
    )

    centroid_longitude = (
        sum(detection.longitude for detection in cluster) / detection_count
    )

    total_frp = sum(detection.frp for detection in cluster)

    return ClusterSummary(
        detection_count=detection_count,
        centroid_latitude=centroid_latitude,
        centroid_longitude=centroid_longitude,
        first_seen_utc=first_seen_utc,
        last_seen_utc=last_seen_utc,
        total_frp=total_frp,
    )
