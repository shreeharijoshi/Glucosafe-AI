# Proposed Methodology

## 1. Load and validate

Read source files from `../Datasets/` without modifying them. Validate file integrity, participant identifiers, schemas, timestamp parseability, units, duplicates, missingness, and event semantics.

## 2. Normalize timestamps and units

Parse each dataset using its documented format and retain parsing failures. Normalize verified glucose values to mg/dL. Do not silently choose between ambiguous formats or repair malformed records.

## 3. Handle duplicates and missingness

Report duplicate timestamps and conflicting values before selecting a deterministic policy. Do not impute missing glucose or carbohydrate values in the audit. Missing carbohydrate is not equivalent to zero.

## 4. Define prediction-row eligibility and target

For a prediction time `t`, the target window is exactly:

```text
current_time < future_observation_time <= current_time + 30 minutes
```

Positive means at least one valid glucose value is strictly below 70 mg/dL. Negative means adequate future coverage is established and no qualifying value occurs. Unknown means coverage is insufficient or invalid. The future-coverage rule is provisional and must be tested; a late reading may help assess continuity but must never determine a label from a time beyond the horizon.

## 5. Historical features

Use only observations at or before `t`: current glucose, recent history, and trends with explicitly verified coverage. Never interpolate across long gaps or use future glucose.

## 6. Current-meal carbohydrates

Model B uses only the carbohydrate estimate for the current meal. It must not accumulate previous meal calculations. The application must decide whether this is a planned pre-meal input or a post-meal recorded input before selecting training examples.

## 7. Splitting and evaluation

Assign complete participants to one partition. Keep recording periods and dataset boundaries explicit. Use the same participants, timestamps, target labels, and eligibility policy for Models A and B.

## 8. Training and comparison

After validation, train simple baselines with fixed reproducible settings and compare them using imbalance-aware metrics. This workspace setup does not implement or run training.
