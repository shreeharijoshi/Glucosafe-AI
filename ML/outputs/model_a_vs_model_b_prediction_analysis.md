# Paired Model A vs Model B Prediction Analysis

Analysis-only results from the saved paired out-of-fold predictions; no retraining was performed.

- Rows: 11344; participants/folds: 11
- Model B uses recorded meal timestamps as a carbohydrate proxy; actual consumption timing and timezone semantics are unresolved.
- Rows come from overlapping prediction windows and are not independent observations.
- Results are exploratory and not clinical validation or evidence of safety.

## Probability differences

- Signed difference is Model B minus Model A. Mean: `-0.000113`; median: `-0.000000`; minimum: `-0.046650`; maximum: `0.051059`.
- Mean absolute difference: `0.000777`; median absolute difference: `0.000015`.

| Quantile | Absolute probability difference |
|---:|---:|
| 0% | 0.000000 |
| 25% | 0.000000 |
| 50% | 0.000015 |
| 75% | 0.000252 |
| 90% | 0.001889 |
| 95% | 0.004158 |
| 99% | 0.013365 |
| 100% | 0.051059 |

## Threshold disagreements

- Different predictions at threshold 0.5: `6` of `11344` rows (0.053%).
- Among disagreements: `5` positive targets and `1` negative targets.
- Direction: Model B positive while Model A negative: `3`; Model A positive while Model B negative: `3`.

## Exploratory glucose/trend concentration check

- The saved paired prediction CSV does not contain current glucose, glucose-history, or trend feature columns. Concentration of probability differences by glucose/trend range cannot be tested from the permitted artifact and is not inferred here.

## Per-participant differences

| Participant | Rows | Positive | Negative | Mean signed diff | Mean abs diff | Threshold disagreements | AP diff | ROC-AUC diff |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2301 | 2029 | 12 | 2017 | -0.000010 | 0.000023 | 0 | -0.000131 | -0.000331 |
| 2304 | 1937 | 38 | 1899 | -0.000113 | 0.000814 | 1 | 0.001248 | -0.000499 |
| 2306 | 1 | 0 | 1 | -0.000009 | 0.000009 | 0 | N/A | N/A |
| 2307 | 776 | 5 | 771 | 0.000024 | 0.000037 | 0 | -0.000037 | -0.000519 |
| 2308 | 1400 | 138 | 1262 | -0.001102 | 0.001347 | 1 | 0.002883 | 0.000666 |
| 2309 | 1012 | 29 | 983 | -0.000033 | 0.000057 | 0 | 0.001916 | 0.000018 |
| 2313 | 1337 | 48 | 1289 | 0.001918 | 0.002100 | 3 | -0.002650 | 0.000129 |
| 2314 | 22 | 0 | 22 | -0.000310 | 0.000369 | 0 | N/A | N/A |
| 2320 | 2721 | 162 | 2559 | -0.000762 | 0.000766 | 1 | 0.000193 | 0.000024 |
| 2401 | 104 | 31 | 73 | 0.000309 | 0.003038 | 0 | -0.002024 | -0.000884 |
| 2405 | 5 | 0 | 5 | -0.000001 | 0.000001 | 0 | N/A | N/A |

## Participant-aware uncertainty

- Pooled Average Precision: Model A `0.620856`, Model B `0.617917`, difference `-0.002940`.
- Pooled ROC-AUC: Model A `0.934960`, Model B `0.934732`, difference `-0.000228`.
- A 5,000-resample bootstrap resampled the 11 participants as clusters and included all rows within each selected participant. It yielded `5000` valid resamples.
- 95% percentile interval for Average Precision difference: `[-0.006645, 0.002729]`; median bootstrap difference `-0.002285`.
- 95% percentile interval for ROC-AUC difference: `[-0.000584, 0.000076]`; median bootstrap difference `-0.000184`.
- These intervals reflect participant-level resampling, not independent timestamp-row uncertainty. With only 11 participants and uneven support, they are unstable exploratory summaries and do not establish statistical significance.

## Limitations

- Only 11 participants contribute to the paired population, with highly uneven positive/negative support.
- Prediction windows overlap, creating temporal dependence within participants.
- Meal timestamps are not confirmed actual consumption times.
- No threshold tuning or clinical interpretation was performed.
