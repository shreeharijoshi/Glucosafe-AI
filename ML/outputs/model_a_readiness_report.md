# Model A Readiness Report

## Scope and validation

This audit used the saved `model_a_dataset.csv` and the existing Model A
integration summary. The dataset was not rebuilt, and no model was trained.
The optimized glucose feature lookup and its focused tests were inspected.
The implementation uses sorted `searchsorted` lookups at or before each
requested time, and keys feature partitions by participant and `source_file`.
The existing tests cover future-observation exclusion and participant/recording
partition isolation; they were not rerun because pytest is unavailable.

## Saved dataset checks

| Check | Result |
|---|---:|
| Saved rows | 340,231 |
| Positive targets | 9,064 |
| Negative targets | 236,338 |
| Unknown targets | 94,829 |
| Participants represented | 17 |
| Duplicate `(participant_id, prediction_timestamp, source_file)` rows | 0 |
| Required Model A feature columns missing | 0 |
| Audit columns in `MODEL_A_FEATURE_COLUMNS` | 0 |

Unknown-target reasons:

| Reason | Rows |
|---|---:|
| Glucose gap over 10 minutes | 85,411 |
| Late endpoint coverage | 6,956 |
| Conflicting duplicate glucose | 2,387 |
| Missing endpoint coverage | 75 |

## Known-label feature completeness

Among known labels:

- 242,584 rows have every required Model A feature.
  - Positive: 8,804
  - Negative: 233,780
- 2,818 rows have at least one missing feature.

Missing feature counts among known labels, by target class:

| Feature | Positive rows missing | Negative rows missing |
|---|---:|---:|
| `current_glucose_mg_dl` | 0 | 0 |
| `current_glucose_age_minutes` | 0 | 0 |
| `glucose_5min_before_mg_dl` | 179 | 1,490 |
| `glucose_10min_before_mg_dl` | 76 | 923 |
| `glucose_15min_before_mg_dl` | 75 | 1,122 |
| `glucose_change_5min_mg_dl` | 179 | 1,490 |
| `glucose_change_10min_mg_dl` | 76 | 923 |
| `glucose_change_15min_mg_dl` | 75 | 1,122 |

Missing values are retained as missing. No imputation was performed.

## Eligible rows by participant

“Eligible” here means a known target with every required Model A feature
present. Participants are not treated as interchangeable independent rows.

| Participant | Eligible rows | Positive | Negative |
|---|---:|---:|---:|
| 2301 | 35,984 | 589 | 35,395 |
| 2303 | 13,793 | 285 | 13,508 |
| 2304 | 30,706 | 645 | 30,061 |
| 2305 | 7 | 0 | 7 |
| 2306 | 4 | 0 | 4 |
| 2307 | 8,313 | 200 | 8,113 |
| 2308 | 28,472 | 1,969 | 26,503 |
| 2309 | 20,489 | 501 | 19,988 |
| 2310 | 49,810 | 1,222 | 48,588 |
| 2313 | 30,681 | 2,563 | 28,118 |
| 2314 | 64 | 0 | 64 |
| 2320 | 23,676 | 743 | 22,933 |
| 2401 | 443 | 82 | 361 |
| 2403 | 115 | 0 | 115 |
| 2404 | 1 | 0 | 1 |
| 2405 | 26 | 5 | 21 |

Sixteen of the 17 represented participants have at least one eligible row.
Support is highly uneven: several participants have very few rows and no
positive examples.

## Readiness assessment

The saved dataset is structurally ready for the next participant-level split
step: keys are unique, targets and features are joined one-to-one, and audit
metadata remains separate from the explicit Model A feature allowlist.
Historical lookup code does not use future glucose observations and does not
cross participant or recording partitions.

Recommended conservative preprocessing policy:

1. Preserve the saved CSV unchanged as the audit/source artifact.
2. For modeling experiments, use only rows with known targets and all required
   Model A features present; record the exclusion counts.
3. Keep unknown targets excluded from supervised loss and metrics, never
   recode them as negative.
4. Do not impute missing features for the initial experiment.
5. Split complete participants before fitting any preprocessing or selecting
   thresholds.
6. Report pooled and per-participant results, including participants with
   sparse or single-class eligible data.

The next step can be participant-level split design, but model training should
wait until the project accepts the substantial unknown-label rate, duplicate
handling policy, and sparse participant support. These are data-quality and
evaluation constraints, not reasons to alter the saved dataset silently.
