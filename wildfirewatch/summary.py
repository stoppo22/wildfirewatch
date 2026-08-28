"""Create human-readable summaries of FIRMS detections."""

from wildfirewatch.models import Detection


def format_detection_summary(detections: list[Detection]) -> str:
    """Return a short human-readable summary of detections."""
    if not detections:
        return "Detections: 0"

    first_acquired = min(
        detection.acquired_at_utc for detection in detections
    )
    last_acquired = max(
        detection.acquired_at_utc for detection in detections
    )

    return (
        f"Detections: {len(detections)}\n"
        f"First acquired (UTC): {first_acquired.isoformat()}\n"
        f"Last acquired (UTC): {last_acquired.isoformat()}"
    )
