"""SQLite persistence for WildfireWatch."""

import sqlite3


from wildfirewatch.models import Detection


def create_tables(connection: sqlite3.Connection) -> None:
    connection.execute("""
        CREATE TABLE IF NOT EXISTS detections (
            id INTEGER PRIMARY KEY,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            acquired_at_utc TEXT NOT NULL,
            frp REAL NOT NULL,
            confidence TEXT NOT NULL,
            satellite TEXT NOT NULL,
            day_night TEXT NOT NULL,
            UNIQUE (
                latitude,
                longitude,
                acquired_at_utc,
                frp,
                confidence,
                satellite,
                day_night
            )
        );
        """)


def insert_detection(
    connection: sqlite3.Connection,
    detection: Detection,
) -> bool:

    cursor = connection.execute(
        """
    INSERT OR IGNORE INTO detections (
        latitude,
        longitude,
        acquired_at_utc,
        frp,
        confidence,
        satellite,
        day_night
    )
    VALUES (?, ?, ?, ?, ?, ?, ?);
    """,
        (
            detection.latitude,
            detection.longitude,
            detection.acquired_at_utc.isoformat(),
            detection.frp,
            detection.confidence,
            detection.satellite,
            detection.day_night,
        ),
    )

    return cursor.rowcount == 1
