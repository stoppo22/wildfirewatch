# WildfireWatch — Roadmap

## Goal
WildfireWatch is a learning-first geospatial software engineering project that turns NASA FIRMS active-fire detections into candidate tracked fire events, evaluates how well those events are reconstructed, enriches them with environmental context, ranks them with an interpretable priority score, and eventually exposes them through an interactive map.

Two equal goals:
1. learn real software engineering and algorithms;
2. build a strong, honest portfolio project for internship applications.

A polished v0.3/v0.4 is more valuable than a rushed v1.0.

## v0.0 — Foundation and FIRMS ingestion
Status: completed as v0.0.0.

Build:
- minimal Python project structure;
- load a small NASA FIRMS VIIRS sample;
- parse and normalize only needed fields;
- define a simple `Detection` representation;
- print useful summaries;
- introduce first simple pytest tests;
- introduce one automatic Python formatter after basic formatting conventions
  have been understood manually.

Learn:
- Python modules;
- CSV/files;
- timestamps;
- data modeling;
- ingestion concepts;
- basic error handling;
- first unit tests;
- the difference between formatting, linting and testing, without adding all
  three tool categories prematurely.

Done when:
- a small sample loads reproducibly;
- detections have a clean internal representation;
- malformed/empty inputs are handled reasonably;
- simple tests pass;
- the code can be formatted consistently with one documented command;
- the user can explain every important field and transformation.

## v0.1 — Geographic primitives and clustering baseline
Build:
- calculate real geographic distance between coordinates;
- create a simple threshold-based grouping baseline;
- group nearby detections into candidate clusters;
- calculate basic cluster summaries.

Learn:
- latitude/longitude;
- Haversine distance;
- algorithm design;
- nested loops and complexity;
- testing geographic functions;
- edge cases.

Done when:
- clustering behavior is predictable on controlled examples;
- tests document expected behavior;
- the user can explain the algorithm and its time complexity.

## v0.2 — Spatiotemporal event tracking
Build:
- associate clusters across observation windows into candidate `FireEvent`s;
- track first_seen, last_seen, duration, detection_count, centroid history, FRP history, movement and a simple spatial-growth proxy.

Important:
- do not force every cluster into an existing event;
- later, associations may expose an interpretable confidence score.

Learn:
- state over time;
- temporal windows;
- matching/association;
- data structures;
- decomposition;
- serious testing.

Done when:
- repeated observations can be linked into stable event IDs;
- disappearing/new events are handled;
- tracking tests cover clear matches and non-matches;
- the user can explain why two clusters are considered the same event.

## v0.3 — Evaluation, algorithm comparison and historical replay
This is the first major CV-worthy checkpoint.

Build:
- create a reproducible evaluation framework;
- measure fragmentation/false splits;
- measure incorrect merges;
- measure event continuity;
- measure raw detections -> candidate events reduction;
- measure runtime;
- study sensitivity to spatial/temporal thresholds;
- compare the simple baseline against at least one better method if justified.

Historical fire replay:
- load detections for a selected historical fire/time range;
- sort them chronologically;
- reveal detections incrementally;
- update events using only information available up to that moment;
- visualize how the reconstruction evolves.

Learn:
- benchmarks;
- experimental design;
- metrics;
- parameter sensitivity;
- fair algorithm comparison;
- temporal correctness.

Done when:
- evaluation is reproducible;
- results are measured and stored;
- at least one historical case can be replayed;
- README claims use measured numbers only.

## v0.4 — Persistence and incremental processing
Build:
- SQLite;
- persistent detections/events;
- incremental ingestion;
- update existing events instead of recalculating everything;
- logging;
- repeatable/idempotent processing where possible;
- basic GitHub Actions CI for tests and a formatter check.

Learn:
- relational databases;
- schemas;
- persistence;
- pipeline reliability;
- CI;
- production-style failure handling.

Done when:
- restarting the program preserves event state;
- processing new detections updates stored events;
- tests run automatically in CI.

This is already a very strong stopping point for internship screening if polished well.

## v0.5 — Environmental context
Use Google Earth Engine only after event tracking/evaluation is stable.

Start with one contextual variable:
- vegetation, or
- land cover, or
- historical fire activity.

Learn:
- raster/geospatial datasets;
- external APIs;
- spatial queries;
- caching;
- quotas;
- feature extraction.

Done when:
- one environmental feature is retrieved reliably;
- it is cached/queried efficiently;
- its meaning and limitations are documented.

## v0.6 — Interpretable priority scoring
Build:
- rank candidate events using transparent signals such as persistence, FRP trend, spatial growth and environmental context;
- always explain why a score is high/medium/low.

Important:
- this is an event-ranking heuristic, not a validated danger/emergency-risk model.

Learn:
- feature design;
- normalization;
- rule systems;
- sensitivity analysis;
- explainability.

Done when:
- every score is explainable from input signals;
- weight/threshold sensitivity is evaluated.

## v0.7 — Backend and interactive product
Architecture:
processing pipeline -> SQLite -> backend API -> interactive web map

Possible event view:
- location;
- first/last seen;
- duration;
- detections;
- FRP trend;
- movement;
- spatial evolution;
- environmental context;
- priority and reason;
- event timeline;
- historical replay.

Learn:
- HTTP;
- REST/backend APIs;
- FastAPI or similar;
- frontend/backend boundaries;
- product integration;
- interactive maps.

Done when:
- events are served through an API;
- a user can inspect an event without reading raw data;
- the replay/demo communicates the project in under a minute.

## v1.0 — Polished release
Build:
- clean repository;
- strong README;
- architecture diagram;
- reproducible setup;
- documented benchmark;
- automated tests;
- GitHub Actions;
- demo video/GIF/screenshots;
- release tag;
- clear limitations;
- technical write-up.

The user should be able to explain:
- the real problem;
- why raw detections are not enough;
- the baseline;
- tracking algorithm;
- failures;
- improvements;
- evaluation;
- measured results;
- architecture;
- tradeoffs.

## v1.1 — Optional machine learning
Only if a real prediction task emerges.

Possible example:
> Given the first N hours of a candidate event, predict whether it will still be detected after M hours.

Before ML:
- define the target;
- create a simple baseline;
- avoid temporal leakage;
- define train/test methodology;
- justify why ML adds value.

It is completely acceptable for WildfireWatch to never use ML.

## Priority order if time becomes limited
Cut in this order:
1. optional ML;
2. extra Earth Engine datasets;
3. sophisticated priority scoring;
4. sophisticated frontend features.

Do NOT cut:
- core event logic;
- testing;
- evaluation;
- measured results;
- understanding.

## Portfolio target
The strongest version is not the one with the most technologies. It is the one where the user can truthfully explain the system, algorithm, evaluation, tradeoffs, failures and measured results.

Every number eventually placed on the CV must come from a reproducible measurement.
