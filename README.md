# WildfireWatch

[![CI](https://github.com/stoppo22/wildfirewatch/actions/workflows/ci.yml/badge.svg)](https://github.com/stoppo22/wildfirewatch/actions/workflows/ci.yml)

WildfireWatch is a learning-first Python project for turning raw NASA FIRMS
active-fire detections into clean, tested candidate fire events.

> **Status:** v0.7.0 is complete. A tested FastAPI backend now serves persisted
> candidate events to a local interactive map and event-detail view.

FIRMS detections are satellite-observed thermal anomalies. They are not
necessarily confirmed wildfires, and WildfireWatch is not an emergency,
safety, or authoritative fire-detection system.

## At a glance

```mermaid
flowchart LR
    A[NASA FIRMS<br/>thermal anomalies] --> B[Normalize<br/>Detection objects]
    B --> H[(SQLite<br/>detections)]
    H -- new only --> C[Spatial<br/>clustering]
    C --> D[Track candidate<br/>events over time]
    D <--> I[(SQLite events<br/>and history)]
    D --> E[Historical<br/>replay]
    D --> F[Evaluation<br/>metrics]
    G[Reference<br/>perimeter] --> F
    D --> J[Persistence, FRP trend,<br/>spatial growth]
    J --> K[Explainable<br/>review priority]
    I --> L[WorldCover<br/>context]
    L -. displayed alongside .-> K
    K --> M[FastAPI<br/>JSON API]
    M --> N[Interactive map<br/>and event details]
```

![Three-panel Lahaina historical replay](evaluation/results/lahaina_replay_one_to_one.png)

Red points are cumulative FIRMS thermal-anomaly detections, blue crosses are
candidate-event centroids, and the green area is a reference perimeter. Each
panel uses only information available by its timestamp.

| Reproducible evidence | Measured result |
| --- | --- |
| Historical subset | 56 detections across 3 acquisition timestamps |
| Final replay comparison | baseline: 1 event; one-to-one: 2 events |
| Reference-perimeter coverage | 67.86% of detections inside or on the polygon |

These results describe this bounded experiment. They are not wildfire
confirmation, emergency guidance, or globally validated tracking accuracy.

## v0.0.0 scope

The current code can:

- read a small fixed NASA FIRMS VIIRS NOAA-20 NRT CSV sample;
- convert raw CSV strings into typed `Detection` objects;
- combine FIRMS acquisition date and time into timezone-aware UTC datetimes;
- preserve only the fields needed by the current domain model;
- return an empty list for an empty CSV file;
- fail visibly when required fields or valid values are missing;
- format detection count and acquisition-time range summaries;
- run the current ingestion pipeline from the command line;
- format Python source and test files consistently with Black;
- verify behavior with a small pytest suite.

This version does **not** include clustering, event tracking, historical
replay, databases, APIs, web maps, Earth Engine, priority scoring, machine
learning, or deployment.

## v0.1.0 scope

WildfireWatch now calculates the great-circle distance between two geographic
coordinates with the Haversine formula and a mean Earth radius of 6,371 km.
Tests cover identical points, one degree of longitude at the equator,
symmetry, and an approximate Rome-to-Milan distance.

The current clustering baseline compares every pair of detections and connects
pairs within a configurable distance threshold. Connected detections are
grouped transitively, so an A-B-C chain forms one candidate cluster even when A
and C exceed the threshold. The function preserves input order within its
output clusters. It is available as Python code but is not yet part of the
command-line pipeline.

Each non-empty cluster can be summarized as a typed `ClusterSummary` containing
its detection count and arithmetic-mean latitude/longitude centroid. Asking for
the summary of an empty cluster raises `ValueError`, because its centroid is
undefined.

## v0.2.0 scope

`ClusterSummary` now also records the earliest and latest acquisition times in
each cluster. A minimal `FireEvent` model records a stable integer ID, first and
last observation times, a centroid, and cumulative detection count. Its
`duration` property is calculated from the first and last observation times, so
the same information is not stored twice.
Clusters are associated with an existing event only when both the geographic
distance and elapsed-time thresholds are satisfied; otherwise, a new stable
event ID is created. When several events are compatible, the nearest one is
selected. Its cumulative centroid is updated with a detection-count-weighted
mean. Each event retains immutable observation snapshots containing the
cluster's time range, centroid, detection count, and total FRP. The cumulative
path between consecutive centroids can be calculated from that history. This
is an observation-based movement proxy, not proof of physical fire movement.
The difference between the last and first observed radii provides a simple net
spatial-growth proxy. All intermediate radii remain available in the history,
because the net value alone can hide expansion and contraction between them.

## v0.4.0 scope

WildfireWatch now stores normalized detections, candidate-event summaries, and
ordered event observations in a local SQLite database. Exact normalized
detections are idempotent, while event rows use UPSERT semantics so an existing
stable `event_id` is updated instead of duplicated. Foreign keys protect the
event-to-observation relationship.

The incremental pipeline loads stored events after a restart, processes only
new detections in chronological frames, applies one-to-one tracking, and saves
the updated state in one caller-owned transaction. A dedicated command logs
received detections, newly inserted detections, and stored event count.
GitHub Actions runs all tests and checks Black on every push and pull request.

## Data flow

The command-line program currently runs the reproducible ingestion path:

```text
FIRMS CSV
    -> csv.DictReader
    -> one raw dictionary per row
    -> detection_from_row
    -> Detection objects
    -> human-readable summary
```

The Python library also supports the v0.2 processing path:

```text
Detection objects
    -> spatial clusters
    -> ClusterSummary objects
    -> spatiotemporal association
    -> FireEvent objects with observation history
    -> centroid-path and radius-change metrics
```

The v0.3 evaluation path is:

```text
controlled labels + clusters
    -> real v0.2 tracker assignments
    -> false-split, false-merge, reduction, and continuity metrics
    -> spatial/temporal threshold experiments
    -> measured JSON reports
```

The historical replay path is:

```text
saved historical FIRMS CSV
    -> detections grouped by acquisition timestamp
    -> clustering of only the new detections in each frame
    -> incremental event updates without future information
    -> immutable chronological frame snapshots
```

The spatial reference evaluation path is:

```text
historical FIRMS detections + local reference Polygon
    -> point-in-polygon checks
    -> inside-or-boundary detection coverage ratio
    -> measured JSON report with explicit limitations
```

See [evaluation and replay notes](docs/evaluation-and-replay.md) for the
methodology, commands, measured results, and limitations.

The v0.6.0 scoring path is:

```text
persisted candidate events
    -> normalized persistence, mean-FRP trend, and radius-growth components
    -> explicit weighted 0-100 score
    -> low/medium/high review-priority label and contribution breakdown
    -> rankings compared under multiple weights and thresholds
```

## Detection model

| Internal field | FIRMS source | Normalization |
| --- | --- | --- |
| `latitude` | `latitude` | string to `float` |
| `longitude` | `longitude` | string to `float` |
| `acquired_at_utc` | `acq_date` + `acq_time` | zero-pad `HHMM`, parse, attach UTC |
| `frp` | `frp` | string to `float` |
| `confidence` | `confidence` | retained as a string |
| `satellite` | `satellite` | retained as a string |
| `day_night` | `daynight` | renamed and retained as a string |

The raw sample retains all original source columns. The internal model keeps
only fields that have a concrete purpose in v0.0.0.

## Cluster summary model

| Field | Meaning |
| --- | --- |
| `detection_count` | number of detections in the cluster |
| `total_frp` | sum of detection FRP values in the cluster, in MW |
| `centroid_latitude` | arithmetic mean of detection latitudes |
| `centroid_longitude` | arithmetic mean of detection longitudes |
| `max_radius_km` | maximum distance from the centroid to a detection |
| `first_seen_utc` | earliest acquisition time in the cluster |
| `last_seen_utc` | latest acquisition time in the cluster |

## Requirements

- Python 3.11 or newer
- Git

The application uses `python-dotenv` to load the private FIRMS MAP_KEY from a
local `.env` file and Matplotlib to generate the static replay visualization.
`pytest` and Black are optional development dependencies used for tests and
code formatting.

## Setup

These commands target macOS and Linux shells:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

The editable installation means changes to the local source code are used
without reinstalling the package after every edit.

## Run the local API

First create or update the local SQLite database using the incremental
processing command. Then start the development server:

```bash
python -m uvicorn wildfirewatch.api:app --reload
```

Open `http://127.0.0.1:8000` to use the local event explorer. The sidebar lists
persisted candidate events, the map places them at their centroids, and a
selection shows timestamps, detections, land cover, evolution metrics, and the
three explainable contributions to review priority. Marker colors represent
heuristic review priority, not wildfire certainty, danger, or emergency risk.

The v0.7 application exposes:

| Method and path | Behavior |
| --- | --- |
| `GET /` | open the local interactive candidate-event map |
| `GET /api/health` | report that the API is running |
| `GET /api/events` | return all persisted candidate-event summaries |
| `GET /api/events/{event_id}` | return one event with metrics, priority, land cover, and observation history, or `404` when absent |
| `GET /docs` | open FastAPI's generated interactive API documentation |

By default the API reads the ignored local database at
`data/wildfirewatch.db`. The server is a local development interface, not an
emergency-monitoring or public deployment.

## Run the current pipeline

Run the committed sample from the repository root:

```bash
python -m wildfirewatch data/raw/viirs_noaa20_nrt_sample.csv
```

Expected output for the committed sample:

```text
Detections: 5
First acquired (UTC): 2025-06-06T00:01:00+00:00
Last acquired (UTC): 2025-06-06T00:01:00+00:00
```

## Run incremental SQLite processing

Process a FIRMS CSV into a persistent local database:

```bash
python -m scripts.run_incremental_processing \
  data/raw/viirs_noaa20_nrt_sample.csv \
  --database data/wildfirewatch.db
```

Run the same command again to verify idempotency. The log reports the number
of received detections, newly inserted detections, and stored candidate
events; the second run should report `new=0`. Local `*.db`, `*.sqlite`, and
`*.sqlite3` files are ignored by Git.

The command commits detection and event changes together. If processing
raises an exception, it rolls the transaction back before closing the
connection. See [persistence and incremental processing](docs/persistence-and-incremental-processing.md)
for the schema, data flow, guarantees, and current limitations.

## Enrich events with land-cover context

WildfireWatch v0.5 uses the
[ESA WorldCover 10 m 2021 v200](https://developers.google.com/earth-engine/datasets/catalog/ESA_WorldCover_v200)
dataset through Google Earth Engine. Register a noncommercial Earth Engine
Cloud project, authenticate locally, and add its project ID to the ignored
`.env` file:

```text
EARTH_ENGINE_PROJECT=your-google-cloud-project-id
```

Enrich the events already stored in SQLite:

```bash
python scripts/enrich_events.py data/wildfirewatch.db
```

The command samples the WorldCover `Map` band at each event centroid and
caches the code, sampled coordinates, and dataset ID in SQLite. Running it a
second time reuses cached values instead of repeating Earth Engine requests.
On the committed Lahaina sample, the first run reports `2 fetched, 0 cached`
and the second reports `0 fetched, 2 cached`.

This is contextual information, not a fire classification: a centroid labeled
`built_up`, for example, does not mean that the entire event area is urban or
that the thermal anomaly was caused by an urban fire. See
[environmental context](docs/environmental-context.md) for the schema,
testing strategy, reproducible result, and current limitations.

## Rank candidate events and analyze sensitivity

Print an explainable ranking of the events stored in SQLite:

```bash
python scripts/rank_events.py data/wildfirewatch.db
```

Generate the reproducible sensitivity report:

```bash
python scripts/run_scoring_sensitivity.py data/wildfirewatch.db
```

The report compares the default configuration with persistence-heavy,
FRP-trend-heavy, spatial-growth-heavy, lenient-threshold, and strict-threshold
scenarios. In the bounded two-event Lahaina replay, event 1 remains first in
all six scenarios, while its score ranges from 19.74 to 59.21. Both FRP-trend
and spatial-growth contributions are zero in this replay, so this result shows
stability of the ordering only for the available events; it does not validate
the selected weights. See [priority scoring](docs/priority-scoring.md) for the
formulas, measured results, and limitations.

## Run the tests

With the virtual environment activated:

```bash
python -m pytest
```

GitHub Actions runs the complete test suite and `black --check` automatically
on every push and pull request using Python 3.11, the project's minimum
supported version. The CI badge at the top of this README links to the latest
workflow runs.

## Run the v0.3 experiments

Regenerate the controlled synthetic threshold report:

```bash
python scripts/run_synthetic_evaluation.py
```

Regenerate the initial Lahaina historical replay:

```bash
python scripts/run_historical_replay.py \
  data/raw/viirs_noaa20_sp_lahaina_2023-08-08_2023-08-12.csv
```

Download the local reference perimeter and regenerate spatial coverage:

```bash
python scripts/download_reference_perimeter.py
python scripts/run_spatial_evaluation.py \
  data/raw/viirs_noaa20_sp_lahaina_2023-08-08_2023-08-12.csv
```

The measured coverage is 67.86% across 56 detections. It is a spatial
consistency measure against one reference perimeter, not an accuracy,
precision, or recall claim.

Generate the static one-to-one replay visualization:

```bash
python scripts/plot_historical_replay.py \
  data/raw/viirs_noaa20_sp_lahaina_2023-08-08_2023-08-12.csv
```

The panels contain 49, 53, and 56 cumulative detections. Each panel uses only
detections acquired by its timestamp, so the image demonstrates the replay's
no-future-data behavior as well as the final two-event one-to-one result.

The historical downloader reads `FIRMS_MAP_KEY` from a local `.env` file that
is ignored by Git. Copy `.env.example` to `.env`, replace the placeholder, and
never commit or share the resulting file.

The tests currently document:

- construction of the `Detection` data model;
- short and four-digit FIRMS acquisition times;
- invalid acquisition times;
- raw-row normalization;
- missing required fields;
- loading every row of the fixed sample;
- empty-file behavior;
- empty and non-empty summaries;
- the complete command-line pipeline and its output;
- geographic distance edge cases, known approximate distances, and symmetry;
- empty, singleton, nearby, distant, and transitively connected clustering
  cases;
- cluster count, centroid, temporal range, FRP, radius, and empty-cluster error
  behavior;
- event creation, compatible updates, stable IDs, spatial/temporal non-matches,
  nearest-event selection, and observation-free windows;
- event duration, observation history, centroid path, radius change, and empty
  history behavior.
- point-in-polygon behavior for internal, external, boundary, and invalid
  polygons, plus historical detection coverage calculations.
- WorldCover class-name mapping, SQLite context round trips, cache reuse, and
  missing-value behavior without network access in CI.
- priority-component normalization, contribution totals, classification
  boundaries, deterministic ranking, and weight-sensitive ordering.
- generation of an explainable scoring-sensitivity report from SQLite.

## Format the code

With the virtual environment activated, apply the project's formatting rules
to the application and tests:

```bash
python -m black wildfirewatch tests
```

To check formatting without changing any files:

```bash
python -m black --check wildfirewatch tests
```

Black formats Python source layout consistently. It does not replace tests,
which verify behavior, or a linter, which can identify certain code-quality
problems.

## Error behavior

| Input | Current behavior |
| --- | --- |
| Empty CSV file | returns an empty list |
| Invalid date, time, or numeric value | raises `ValueError` |
| Missing required dictionary field | raises `KeyError` |
| Missing file | raises `FileNotFoundError` |
| Empty cluster passed to `summarize_cluster` | raises `ValueError` |

Input and parsing errors are intentionally visible in these early versions.
Silently skipping malformed rows could hide data loss. More contextual error
messages may be introduced later without concealing the original failure.

## Data provenance

`data/raw/viirs_noaa20_nrt_sample.csv` is a fixed, manually curated five-row
subset displayed in NASA's official
[FIRMS API tutorial](https://firms.modaps.eosdis.nasa.gov/content/academy/data_api/firms_api_use.html).
It uses the `VIIRS_NOAA20_NRT` dataset and retains all 14 columns shown by the
tutorial. The fixed subset avoids requiring an API key during early learning
and keeps tests reproducible.

NASA describes the underlying NOAA-20 VIIRS product as a near-real-time active
fire detection product with a nominal 375 m resolution. See the
[NASA Earthdata product page](https://www.earthdata.nasa.gov/data/catalog/lancemodis-vj114img-nrt-2)
and [sample data notes](data/README.md).

The v0.3 work also includes a bounded `VIIRS_NOAA20_SP` historical CSV around
Lahaina for 8--12 August 2023. The saved subset contains 56 thermal-anomaly
detections in three acquisition timestamps. It supports chronological replay;
it is not labeled wildfire ground truth. Exact query parameters and the
reproducible download command are documented in
[evaluation and replay notes](docs/evaluation-and-replay.md).

The spatial evaluation downloads one public Lahaina reference polygon from a
feature service published in the USGS ArcGIS organization. The downloaded
GeoJSON is ignored by Git because the service item exposes no explicit
license; source metadata and the reproducible command are recorded in
[data notes](data/README.md).

## Project structure

```text
wildfirewatch/
├── wildfirewatch/
│   ├── clustering.py
│   ├── database.py
│   ├── environment.py
│   ├── evaluation.py
│   ├── evaluation_scenarios.py
│   ├── event_metrics.py
│   ├── experiments.py
│   ├── geo.py
│   ├── ingestion.py
│   ├── models.py
│   ├── pipeline.py
│   ├── replay.py
│   ├── scoring.py
│   ├── spatial_evaluation.py
│   ├── summary.py
│   └── tracking.py
├── .github/workflows/ci.yml
├── tests/
├── scripts/
├── evaluation/results/
├── data/
│   ├── README.md
│   ├── raw/
│   └── reference/  (downloaded locally, ignored by Git)
├── docs/
├── README.md
├── roadmap.md
└── pyproject.toml
```

## Learning approach

WildfireWatch has two equal goals:

1. learn Python, testing, algorithms, and software engineering deeply;
2. become an honest, explainable portfolio project.

Core logic and tests are developed in small learning-focused steps. Mechanical
setup and documentation work may be automated, but important design and
algorithm decisions must remain understandable to the project owner.

See [roadmap.md](roadmap.md) for planned versions and project milestones.

## Current limitations

- The datasets remain small: one five-row ingestion sample and one bounded
  56-row historical replay subset from a single VIIRS source.
- NRT detections are not ground truth and may include non-wildfire thermal
  anomalies.
- Environmental context currently samples one 2021 WorldCover pixel at each
  event centroid and may not represent the full event area.
- Priority scores are transparent ranking heuristics, not validated danger,
  spread, severity, or emergency-risk predictions. The current weights and
  thresholds are exploratory.
- The two-event Lahaina sensitivity report is dominated by persistence because
  both measured FRP-trend and spatial-growth contributions are zero. It cannot
  establish general stability or scientific validity.
- The current model performs type conversion but does not yet validate
  coordinate ranges or normalize confidence/day-night codes.
- Geographic distances approximate Earth as a sphere with a mean radius; they
  are suitable for the current baseline, not survey-grade measurements.
- Clustering currently uses only spatial distance and ignores acquisition time,
  FRP, confidence, and satellite source.
- Transitive connections can create long chains whose endpoints are farther
  apart than the configured threshold.
- Comparing every pair of detections has quadratic time complexity and is not
  intended yet for large datasets.
- Arithmetic-mean latitude/longitude centroids are intended for small local
  clusters and do not handle poles or the antimeridian specially.
- Event association assumes observation windows are processed chronologically
  and uses fixed spatial and temporal thresholds rather than a validated
  probabilistic model.
- When several events are compatible, the nearest centroid wins; equal-distance
  ties retain the first event in input order.
- Events are retained unchanged during empty observation windows; v0.2.0 does
  not assign active/inactive status or prune old event history.
- Centroid path and radius change describe changes in satellite observations;
  they are not validated measurements of physical fire spread or burned area.
- The main `python -m wildfirewatch` command still exposes only ingestion;
  incremental processing, evaluation, and replay use dedicated scripts.
- Incremental processing assumes newly encountered detections arrive in
  chronological order. Previously unseen late data may form a separate event.
- SQLite usage is currently local and single-process oriented; concurrent
  writers and schema migrations are not yet supported.
- Synthetic labels verify controlled behavior but are not validation against
  confirmed wildfire perimeters.
- The historical replay uses exploratory thresholds. In its third frame the
  baseline associates two spatial clusters with one event, while the
  one-to-one alternative produces two events; neither result alone proves the
  number of real wildfires.
- The measured 67.86% reference-perimeter coverage is not tracking accuracy.
  One perimeter cannot validate predicted event identities or temporal
  associations, and boundary/reference uncertainty is not modeled.
- The replay visualization is a static evaluation artifact, not a live map or
  emergency-monitoring interface.
