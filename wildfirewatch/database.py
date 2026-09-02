"""SQLite persistence for WildfireWatch."""

import sqlite3


from wildfirewatch.models import Detection, FireEvent


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

    connection.execute("""
        CREATE TABLE IF NOT EXISTS fire_events (
            event_id INTEGER PRIMARY KEY,
            first_seen_utc TEXT NOT NULL,
            last_seen_utc TEXT NOT NULL,
            centroid_latitude REAL NOT NULL,
            centroid_longitude REAL NOT NULL,
            detection_count INTEGER NOT NULL
        );
        """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS event_observations (
            event_id INTEGER NOT NULL,
            observation_index INTEGER NOT NULL,
            first_seen_utc TEXT NOT NULL,
            last_seen_utc TEXT NOT NULL,
            centroid_latitude REAL NOT NULL,
            centroid_longitude REAL NOT NULL,
            max_radius_km REAL NOT NULL,
            detection_count INTEGER NOT NULL,
            total_frp REAL NOT NULL,
            PRIMARY KEY (
                event_id,
                observation_index
            ),
            FOREIGN KEY (event_id)
                REFERENCES fire_events(event_id)
                ON DELETE CASCADE
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


def insert_detections(
    connection: sqlite3.Connection,
    detections: list[Detection],
) -> int:
    counter = 0

    for detection in detections:
        if insert_detection(connection, detection):
            counter += 1

    return counter


def upsert_fire_event(
    connection: sqlite3.Connection,
    event: FireEvent,
) -> None:
    connection.execute(
        """
        INSERT INTO fire_events (
            event_id,
            first_seen_utc,
            last_seen_utc,
            centroid_latitude,
            centroid_longitude,
            detection_count
        )
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(event_id) DO UPDATE SET
            first_seen_utc = excluded.first_seen_utc,
            last_seen_utc = excluded.last_seen_utc,
            centroid_latitude = excluded.centroid_latitude,
            centroid_longitude = excluded.centroid_longitude,
            detection_count = excluded.detection_count;
        """,
        (
            event.event_id,
            event.first_seen_utc.isoformat(),
            event.last_seen_utc.isoformat(),
            event.centroid_latitude,
            event.centroid_longitude,
            event.detection_count,
        ),
    )

    connection.execute(
        """
        DELETE FROM event_observations
        WHERE event_id = ?;
        """,
        (event.event_id,),
    )

    for observation_index, observation in enumerate(event.observations):
        connection.execute(
            """
            INSERT INTO event_observations (
                event_id,
                observation_index,
                first_seen_utc,
                last_seen_utc,
                centroid_latitude,
                centroid_longitude,
                max_radius_km,
                detection_count,
                total_frp
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                event.event_id,
                observation_index,
                observation.first_seen_utc.isoformat(),
                observation.last_seen_utc.isoformat(),
                observation.centroid_latitude,
                observation.centroid_longitude,
                observation.max_radius_km,
                observation.detection_count,
                observation.total_frp,
            ),
        )
