# Environmental context

WildfireWatch v0.5 enriches persisted candidate events with one interpretable
environmental variable: land-cover class from ESA WorldCover 10 m 2021 v200.
This layer is contextual information, not evidence that a thermal anomaly is a
confirmed wildfire or that a particular surface type is burning.

## Data flow

```text
persisted FireEvent centroid
-> SQLite cache lookup by event_id
-> Earth Engine point sample when missing
-> WorldCover numeric class code
-> local readable class name
-> cached event_land_cover row
```

The first lookup for an event can call Earth Engine. Later lookups return the
persisted `LandCoverContext`, avoiding repeated network requests.

## Stored fields

The `event_land_cover` table stores:

- `event_id`, a primary key and foreign key to `fire_events`;
- `class_code`, the WorldCover numeric class;
- `sampled_latitude` and `sampled_longitude`, the exact sampled location;
- `dataset`, the Earth Engine dataset identifier used for provenance.

Deleting a fire event also deletes its environmental context. If Earth Engine
returns no class code, WildfireWatch returns `None` and does not cache a false
value.

## Local setup and execution

Register a noncommercial Earth Engine Cloud project, authenticate the local
Earth Engine CLI, and set the project ID in the ignored `.env` file:

```text
EARTH_ENGINE_PROJECT=your-google-cloud-project-id
```

Run environmental enrichment after incremental processing has populated a
SQLite database:

```bash
python scripts/enrich_events.py data/wildfirewatch.db
```

For the committed Lahaina sample, incremental processing produces two
candidate events. The first enrichment run reports `2 fetched, 0 cached`; the
second reports `0 fetched, 2 cached`.

## Testing strategy

Unit tests replace the network lookup with a controlled local function. They
verify class-name mapping, missing codes, cache reuse, and missing-value
behavior without requiring secrets or network access in CI. A manual
authenticated run verifies the real Earth Engine boundary.

## Current limitations

- The value comes from one pixel at the latest event centroid, not the full
  event footprint.
- WorldCover v200 represents 2021 land cover, while the Lahaina replay covers
  2023.
- A centroid class may not represent a spatially large or heterogeneous event.
- The cache keeps one context row per event and does not automatically refresh
  if the event centroid later moves.
- Earth Engine availability, authentication, and quotas remain external
  dependencies.

These limitations are intentionally explicit. Future work may sample an event
area or refresh context after meaningful movement, but neither is required to
claim a reliable first environmental feature.
