# EDA Summary (Auto-generated)

This document summarizes key insights from the latest dataset used in the AQI Forecasting project. Results below were computed directly from `dataEDA/merged_with_numerical_aqi.csv` at the time of generation.

## Dataset Overview
- Rows: 4013
- Columns: 33
- Time range: 2025-03-04 00:00:00 → 2025-08-28 04:00:00
- Example columns (first 30): `aqi_category`, `co`, `coco`, `day`, `day_of_week`, `day_of_year`, `day_of_year_cos`, `day_of_year_sin`, `dew_point`, `hour`, `is_weekend`, `month`, `nh3`, `no`, `no2`, `o3`, `pm10`, `pm2_5`, `precipitation`, `pressure`, `relative_humidity`, `snow`, `so2`, `temperature`, `timestamp`, `tsun`, `week_cos`, `week_of_year`, `week_sin`, `wind_direction`

## Missing Values (Top 10)
- `tsun`: 4013
- `snow`: 4013
- `wpgt`: 4013
- `precipitation`: 164
- `coco`: 164
- `dew_point`: 108
- `pressure`: 107
- `wind_direction`: 107
- `temperature`: 107
- `wind_speed`: 107

## Target: numerical_aqi (Summary)
- Mean: 120.63
- Std: 37.10
- Min: 29.00
- 25%: 93.00
- 50%: 116.00
- 75%: 152.00
- Max: 359.00

## Correlations with numerical_aqi (Top)
- `numerical_aqi`: 1.000
- `pm2_5`: 0.901
- `aqi_category`: 0.857
- `pm10`: 0.842
- `so2`: 0.623
- `co`: 0.585
- `no2`: 0.551
- `nh3`: 0.403
- `no`: 0.362
- `week_cos`: 0.195
- `day_of_year_cos`: 0.180
- `relative_humidity`: 0.138
- `wind_direction`: 0.087
- `pressure`: 0.084
- `dew_point`: 0.064

Insights:
- Strongest relationships with AQI are particulate matter: `pm2_5`, `pm10`.
- Secondary contributors: `so2`, `co`, `no2`.
- Temporal cosine features show weaker but present seasonality patterns.

## AQI Category Distribution
- 3.0: 1914
- 4.0: 1436
- 5.0: 440
- 2.0: 222
- 4.666629791: 1 (likely an outlier/encoding artifact)

Recommendation: Review and correct the anomalous category value `4.666629791`.

## Hourly Pattern (Mean numerical_aqi)
- Night/Early AM higher: peaks around 6:00–7:00 and 18:00–21:00 (127–130)
- Midday dip: 12:00–14:00 shows lower means (~107–113)

Sample values:
- 06: 129.57
- 07: 118.13
- 13: 107.25 (lower)
- 19–21: ~127–128 (higher)

## Monthly Pattern (Mean numerical_aqi)
- Mar: 156.35 (highest)
- Apr: 87.99 (lowest)
- May–Aug: 113.93–126.22 range

Interpretation:
- Seasonal signal present: elevated AQI in March, improvement in April, moderate in summer months.

## How to Reproduce
From the repository root:

```bash
python - << 'PY'
import pandas as pd, numpy as np, json
from pathlib import Path
p = Path('dataEDA/merged_with_numerical_aqi.csv')
df = pd.read_csv(p, parse_dates=['timestamp'])
num_cols = df.select_dtypes(include=[np.number]).columns
summary = {
  'rows': int(df.shape[0]),
  'cols': int(df.shape[1]),
  'time_start': str(df['timestamp'].min()),
  'time_end': str(df['timestamp'].max()),
  'missing_top10': df.isna().sum().sort_values(ascending=False).head(10).to_dict(),
  'target_desc': df['numerical_aqi'].describe().to_dict(),
  'top_corr': df[num_cols].corr()['numerical_aqi'].dropna().sort_values(ascending=False).head(15).to_dict(),
  'aqi_counts': df['aqi_category'].value_counts().to_dict(),
  'hourly_mean': df.groupby('hour')['numerical_aqi'].mean().to_dict(),
  'monthly_mean': df.groupby('month')['numerical_aqi'].mean().to_dict(),
}
print(json.dumps(summary, indent=2))
PY
```

## Notes
- High missingness in `tsun`, `snow`, `wpgt` suggests either unavailable signals or columns reserved for other datasets; consider dropping or imputing appropriately.
- Address the `aqi_category` anomaly prior to supervised learning.
- Strong PM correlations align with domain expectations; prioritize PM features in modeling and monitoring.

Generated from the latest dataset snapshot on this machine.
