# Interpretable priority scoring

WildfireWatch v0.6 ranks persisted candidate fire events for human review. The
score is deliberately a transparent heuristic: it is not a validated danger,
severity, spread, or emergency-risk prediction.

## Signals and normalization

Each signal is converted to a component between 0 and 1:

```text
persistence = clamp(duration hours / full-score hours, 0, 1)
FRP trend   = clamp(mean FRP increase / full-score FRP increase, 0, 1)
growth      = clamp(radius increase / full-score radius increase, 0, 1)
```

Negative FRP or radius changes become zero because the current rule rewards
only increases. Values above their configured full-score thresholds are capped
at one.

The default point weights are:

| Component | Weight |
| --- | ---: |
| Persistence | 40 |
| Mean-FRP trend | 35 |
| Spatial growth | 25 |

The three point contributions sum to a score from 0 to 100. The command prints
every contribution, so a reviewer can see exactly why an event received its
score. Scores below 33 are labeled `low`, scores from 33 up to (but excluding)
67 are `medium`, and scores from 67 through 100 are `high`.

ESA WorldCover is displayed as context but is not assigned points. Adding a
land-cover weight without a defensible interpretation would make the score look
more scientific without supplying evidence.

## Commands

Rank the events in a local SQLite database:

```bash
python scripts/rank_events.py data/wildfirewatch.db
```

Run the sensitivity analysis and write
`evaluation/results/scoring_sensitivity.json`:

```bash
python scripts/run_scoring_sensitivity.py data/wildfirewatch.db
```

The sensitivity command applies the same scoring and deterministic ordering to
six configurations:

| Scenario | Change from default |
| --- | --- |
| `default` | 40/35/25 weights; 24 h, 20 MW and 2 km thresholds |
| `persistence_heavy` | persistence weight raised to 60 |
| `frp_trend_heavy` | FRP-trend weight raised to 60 |
| `spatial_growth_heavy` | spatial-growth weight raised to 55 |
| `lenient_thresholds` | thresholds halved |
| `strict_thresholds` | thresholds doubled |

The JSON records every configuration, rank, total score, priority label, and
component contribution. Equal scores use ascending event ID as a deterministic
tie-breaker.

## Measured Lahaina result

The local historical database contains two candidate events reconstructed from
56 FIRMS detections. Across all six scenarios:

- event 1 remains rank 1 and event 2 remains rank 2;
- event 1 ranges from 19.74 points under strict thresholds to 59.21 when
  persistence receives extra weight;
- event 2 remains at zero;
- mean-FRP trend and spatial-growth contributions are zero for both events.

The stable ordering is therefore caused by the observed persistence difference,
not by agreement among three informative signals. A controlled test separately
checks that emphasizing persistence instead of FRP trend can reverse a ranking.

## Limitations

- The weights and thresholds are explicit engineering choices, not learned or
  scientifically calibrated parameters.
- Two candidate events from one bounded historical replay are too few to
  establish general sensitivity or predictive performance.
- FIRMS thermal anomalies are not confirmed-wildfire ground truth.
- A priority label indicates review order only. It must not be used for public
  warnings, dispatch, evacuation, or safety decisions.
