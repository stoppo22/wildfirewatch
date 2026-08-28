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
