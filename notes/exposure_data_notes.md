# Exposure Data Notes

## Source

Data generated from [sparklabnyc/global_tc_2024](https://github.com/sparklabnyc/global_tc_2024).  
File: `exposure_data/global_storm_winds_2017.rds` — 3.65M rows, 11 columns.

## What the data contains

Each row = one ADM2 region x one storm encounter in 2017.

| Column | Description |
|--------|-------------|
| `ADM2_id` | Second-level administrative division (district/county) from geoBoundaries/GHSL |
| `vmax_sust` | Maximum 1-minute sustained wind speed at 10m height (m/s) |
| `vmax_gust` | Maximum 3-second gust wind speed (m/s), ~1.49x sustained |
| `sust_dur` | Total minutes sustained winds exceeded threshold (default 20 m/s) |
| `gust_dur` | Total minutes gust winds exceeded threshold |
| `storm_dist` | Distance from ADM2 centroid to storm track (km) |
| `sid` | IBTrACS storm identifier |
| `storm_id` | Storm name/ID |
| `usa_atcf_id` | ATCF identifier (e.g., AL092017 for Irma) |
| `closest_date` | Datetime of closest approach |
| `date_time_max_wind` | Datetime when max wind occurred at that location |

## Wind model

- Willoughby et al. (2006) parametric vortex model
- Surface reduction: 0.9 over water, 0.72 over land
- Gust factor: 1.49 (3-sec gust / 1-min sustained)
- Input: IBTrACS 6-hour tracks, interpolated to finer intervals

## Key thresholds (Saffir-Simpson, m/s)

- Tropical storm: >= 17.5 m/s (34 kt)
- Cat 1: >= 33 m/s (64 kt)
- Cat 2: >= 43 m/s (83 kt)
- Cat 3: >= 50 m/s (96 kt)
- Cat 4: >= 58 m/s (113 kt)
- Cat 5: >= 70 m/s (137 kt)

## Using as a single county-level impact variable

### Option 1: Max sustained wind (severity)

```python
impact = df.groupby("ADM2_id")["vmax_sust"].max()
```

Best for: capturing peak intensity a county experienced.

### Option 2: Cumulative sustained wind (total exposure)

```python
impact = df.groupby("ADM2_id")["vmax_sust"].sum()
```

Best for: capturing repeated or multi-storm exposure.

### Option 3: Total duration (prolonged impact)

```python
impact = df.groupby("ADM2_id")["sust_dur"].sum()
```

Best for: capturing how long a county was under damaging winds.

### Option 4: Integrated dose (intensity x duration)

```python
df["dose"] = df["vmax_sust"] * df["sust_dur"]
impact = df.groupby("ADM2_id")["dose"].sum()
```

Best for: a composite metric combining both severity and duration.

### Option 5: Person-days of exposure (what the repo uses)

The repo's primary metric. Requires external population data (GHSL at 1km):

> Person-days = population x (days with wind >= threshold)

Integrates who is exposed, not just wind speed. Not directly computable from the .rds file alone.

## Recommendation

For a regression or model without population data, **max sustained wind** (`vmax_sust` max per ADM2) is the simplest and most interpretable. For a richer metric, **integrated dose** (option 4) captures both how strong and how long the winds lasted.
