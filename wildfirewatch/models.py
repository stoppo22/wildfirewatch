"""Domain data models for WildfireWatch."""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Detection:
    latitude: float
    longitude: float
    acquired_at_utc: datetime
    frp: float
    confidence: str
    satellite: str
    day_night: str


@dataclass
class ClusterSummary:
    detection_count: int
    centroid_latitude: float
    centroid_longitude: float
