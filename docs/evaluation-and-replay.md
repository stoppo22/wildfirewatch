# Evaluation and historical replay

This document describes the in-progress WildfireWatch v0.3 evaluation work.
The results below are intentionally separated into controlled synthetic
evaluation and historical active-fire replay. Neither is presented as
validated emergency or wildfire-risk performance.

## Evaluation assignments

Controlled scenarios label each cluster observation with a known synthetic
event ID. The real v0.2 tracker assigns its own integer event ID. Evaluation
uses pairs in this form:

```text
(true synthetic event ID, predicted tracker event ID)
```

This adapter exists only for evaluation. Production FIRMS detections do not
contain a true wildfire-event ID.

## Metrics

- **False splits:** extra predicted IDs associated with the same true event.
- **False merges:** extra true IDs associated with the same predicted event.
- **Detection reduction ratio:** `(raw detections - distinct predicted events)
  / raw detections`.
- **Event continuity ratio:** fraction of consecutive observations of each
  true event that retain the same predicted ID. It is `None` when no
  transition exists to measure.
- **Runtime:** wall-clock duration measured with `perf_counter()` for one tiny
  controlled configuration. These microbenchmarks do not demonstrate
  scalability.

Reduction and continuity must not be interpreted alone. An overly permissive
threshold can produce high reduction and perfect continuity by incorrectly
merging separate events.

## Controlled threshold experiments

Run from the repository root:

```bash
python scripts/run_synthetic_evaluation.py
```

The command writes `evaluation/results/synthetic_thresholds.json`.

### Spatial threshold scenario

Two synthetic events move approximately 6.7 km between observations and begin
approximately 17.8 km apart. Coordinates avoid equal-distance ties.

| Maximum distance | False splits | False merges | Reduction | Continuity |
| ---: | ---: | ---: | ---: | ---: |
| 5 km | 2 | 0 | 0% | 0% |
| 10 km | 0 | 0 | 50% | 100% |
| 20 km | 0 | 1 | 75% | 100% |

### Temporal threshold scenario

Each synthetic event has observations two hours apart. The second event starts
eight hours after the first event's last observation.

| Maximum time gap | False splits | False merges | Reduction | Continuity |
| ---: | ---: | ---: | ---: | ---: |
| 1 hour | 2 | 0 | 0% | 0% |
| 3 hours | 0 | 0 | 50% | 100% |
| 10 hours | 0 | 1 | 75% | 100% |

The middle values are correct only for these controlled scenarios. They are
not claimed as globally optimal tracking parameters.

## Historical FIRMS subset

The historical replay uses one source, `VIIRS_NOAA20_SP`, within a bounded box
around Lahaina. Download credentials stay in a local `.env` file ignored by
Git.

Create `.env` from `.env.example`, insert a private FIRMS MAP_KEY, then run:

```bash
python scripts/download_firms_history.py \
  --source VIIRS_NOAA20_SP \
  --area=-156.75,20.80,-156.55,20.98 \
  --date 2023-08-08 \
  --days 5 \
  --output data/raw/viirs_noaa20_sp_lahaina_2023-08-08_2023-08-12.csv
```

The downloader does not print the request URL or MAP_KEY. The resulting file
contains 56 detections across three acquisition timestamps.

## Chronological replay

Run the baseline and one-to-one methods with the same data and parameters:

```bash
python scripts/run_historical_replay.py \
  data/raw/viirs_noaa20_sp_lahaina_2023-08-08_2023-08-12.csv \
  --tracking-method baseline \
  --output evaluation/results/lahaina_replay_baseline.json

python scripts/run_historical_replay.py \
  data/raw/viirs_noaa20_sp_lahaina_2023-08-08_2023-08-12.csv \
  --tracking-method one_to_one \
  --output evaluation/results/lahaina_replay_one_to_one.json
```

The initial exploratory parameters are:

- within-frame clustering distance: 2 km;
- between-frame event-association distance: 10 km;
- maximum event time gap: 13 hours.

The 13-hour gap accommodates the observed NOAA-20 acquisition gaps of about
11 hours and 12.5 hours. It is not a validated universal threshold.

| Frame (UTC) | New detections | Clusters | Baseline events | One-to-one events |
| --- | ---: | ---: | ---: | ---: |
| 2023-08-09 12:15 | 49 | 1 | 1 | 1 |
| 2023-08-09 23:26 | 4 | 1 | 1 | 1 |
| 2023-08-10 11:56 | 3 | 2 | 1 | 2 |

Each frame contains only information available up to its timestamp. A test
verifies that an earlier frame does not gain detections from a later frame.

The third frame exposes the baseline's many-to-one behavior: two clusters from
the same timestamp both update event 1. Its result therefore remains one
candidate event containing all 56 detections.

The alternative greedily sorts all valid event-cluster pairs by distance and
accepts a pair only when neither side has already been used in that frame.
The nearest third-frame cluster updates event 1; the unmatched cluster creates
event 2. The result is two candidate events containing 55 and 1 detections.
This removes order-dependent duplicate updates to one event during a frame.
It does not prove that the second candidate is a separate real wildfire.

The two JSON reports record the chosen method, parameters, frame summaries,
event centroids, durations, and the thermal-anomaly/ground-truth limitation.
The comparison is reproducible, but the three-frame subset is too small to
claim real-world tracking accuracy.
