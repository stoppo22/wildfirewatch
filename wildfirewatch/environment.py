"""Environmental context extraction for WildfireWatch."""

import sqlite3

import ee

from wildfirewatch.database import (
    load_land_cover_context,
    upsert_land_cover_context,
)
from wildfirewatch.models import FireEvent, LandCoverContext

WORLD_COVER_DATASET = "ESA/WorldCover/v200"
WORLD_COVER_BAND = "Map"
WORLD_COVER_SCALE_METERS = 10

LAND_COVER_NAMES = {
    10: "tree_cover",
    20: "shrubland",
    30: "grassland",
    40: "cropland",
    50: "built_up",
    60: "bare_or_sparse_vegetation",
    70: "snow_and_ice",
    80: "permanent_water",
    90: "herbaceous_wetland",
    95: "mangroves",
    100: "moss_and_lichen",
}


def land_cover_name(class_code: int) -> str | None:
    return LAND_COVER_NAMES.get(class_code)


def fetch_land_cover_code(
    latitude: float,
    longitude: float,
) -> int | None:
    point = ee.Geometry.Point([longitude, latitude])

    image = ee.ImageCollection(WORLD_COVER_DATASET).first().select(WORLD_COVER_BAND)

    result = (
        image.reduceRegion(
            reducer=ee.Reducer.first(),
            geometry=point,
            scale=WORLD_COVER_SCALE_METERS,
        )
        .get(WORLD_COVER_BAND)
        .getInfo()
    )

    if result is None:
        return None

    return int(result)


def get_or_fetch_land_cover_context(
    connection: sqlite3.Connection,
    event: FireEvent,
) -> LandCoverContext | None:
    cached_context = load_land_cover_context(connection, event.event_id)

    if cached_context is not None:
        return cached_context

    class_code = fetch_land_cover_code(
        event.centroid_latitude,
        event.centroid_longitude,
    )

    if class_code is None:
        return None

    context = LandCoverContext(
        event_id=event.event_id,
        class_code=class_code,
        sampled_latitude=event.centroid_latitude,
        sampled_longitude=event.centroid_longitude,
        dataset=WORLD_COVER_DATASET,
    )

    upsert_land_cover_context(connection, context)

    return context
