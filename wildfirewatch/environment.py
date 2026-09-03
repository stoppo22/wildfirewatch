"""Environmental context extraction for WildfireWatch."""

import ee

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
