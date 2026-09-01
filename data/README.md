# Sample data

`raw/viirs_noaa20_nrt_sample.csv` is a fixed, manually curated subset of five
rows displayed by NASA's official FIRMS API tutorial:

https://firms.modaps.eosdis.nasa.gov/content/academy/data_api/firms_api_use.html

- Dataset: `VIIRS_NOAA20_NRT`
- Acquisition date in the selected rows: 2025-06-06
- Accessed: 2026-08-28
- Source columns retained: all 14 columns shown in the tutorial

The small fixed subset avoids requiring a FIRMS API key during early learning
and makes v0.0 reproducible. It is near-real-time active-fire detection data,
not confirmed wildfire data and not ground truth.

NASA describes VIIRS active-fire products as detections based on nominal
375-metre-resolution observations. Product information is available at:

https://www.earthdata.nasa.gov/data/catalog/lancemodis-vj114img-nrt-2

## Historical replay data

`raw/viirs_noaa20_sp_lahaina_2023-08-08_2023-08-12.csv` is a bounded FIRMS
Area API response used by the in-progress v0.3 historical replay.

- Source: `VIIRS_NOAA20_SP` (NOAA-20 Standard Processing)
- Query date: `2023-08-08`
- Query range: 5 days
- Bounding box: `-156.75,20.80,-156.55,20.98`
- Downloaded: 2026-09-01
- Rows: 56
- Acquisition timestamps present: 2023-08-09 12:15 UTC (49 rows),
  2023-08-09 23:26 UTC (4 rows), and 2023-08-10 11:56 UTC (3 rows)

The file contains active-fire/thermal-anomaly detections, not confirmed
wildfire labels or a reference fire perimeter. Its purpose is to exercise the
chronological replay pipeline on a small reproducible historical subset.
