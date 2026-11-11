# Model B Subset Representativeness Audit

Descriptive comparison of the saved Model A-eligible cohort and the shared Model A–Model B cohort. No datasets, models, or existing artifacts were modified.

## Cohort totals

- Model A-eligible rows: **242,584**
- Model B/shared rows: **{len(B):,}**
- Overall retention: **4.68%**
- Model A-eligible positive/negative labels: **8804 / 233780**.
- Model B/shared positive/negative labels: **463 / 10881**.
- Model A prevalence: **3.629%**; Model B/shared prevalence: **4.081%**.

## Participant retention and composition

| Participant | Model A rows | Model B rows | Retained | A positive | B positive | A prevalence | B prevalence |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 2301 | 35,984.0 | 2,029.0 | 5.64% | 589.0 | 12.0 | 1.64% | 0.591% |
| 2303 | 13,793.0 | 0.0 | 0.00% | 285.0 | 0.0 | 2.07% | N/A% |
| 2304 | 30,706.0 | 1,937.0 | 6.31% | 645.0 | 38.0 | 2.10% | 1.962% |
| 2305 | 7.0 | 0.0 | 0.00% | 0.0 | 0.0 | 0.00% | N/A% |
| 2306 | 4.0 | 1.0 | 25.00% | 0.0 | 0.0 | 0.00% | 0.000% |
| 2307 | 8,313.0 | 776.0 | 9.33% | 200.0 | 5.0 | 2.41% | 0.644% |
| 2308 | 28,472.0 | 1,400.0 | 4.92% | 1,969.0 | 138.0 | 6.92% | 9.857% |
| 2309 | 20,489.0 | 1,012.0 | 4.94% | 501.0 | 29.0 | 2.45% | 2.866% |
| 2310 | 49,810.0 | 0.0 | 0.00% | 1,222.0 | 0.0 | 2.45% | N/A% |
| 2313 | 30,681.0 | 1,337.0 | 4.36% | 2,563.0 | 48.0 | 8.35% | 3.590% |
| 2314 | 64.0 | 22.0 | 34.38% | 0.0 | 0.0 | 0.00% | 0.000% |
| 2320 | 23,676.0 | 2,721.0 | 11.49% | 743.0 | 162.0 | 3.14% | 5.954% |
| 2401 | 443.0 | 104.0 | 23.48% | 82.0 | 31.0 | 18.51% | 29.808% |
| 2403 | 115.0 | 0.0 | 0.00% | 0.0 | 0.0 | 0.00% | N/A% |
| 2404 | 1.0 | 0.0 | 0.00% | 0.0 | 0.0 | 0.00% | N/A% |
| 2405 | 26.0 | 5.0 | 19.23% | 5.0 | 0.0 | 19.23% | 0.000% |

- Model A-eligible participants: **16**. Participants represented in Model B: **11**. Participants with no Model B rows: **2303, 2305, 2310, 2403, 2404**.
- Largest Model B contributors by row count: 2320 (2,721), 2301 (2,029), 2304 (1,937), 2308 (1,400), 2313 (1,337).
- Lowest nonzero Model B contributors: 2306 (1), 2405 (5), 2314 (22), 2401 (104), 2307 (776).

## Feature and timestamp comparison

| Measure | Model A eligible | Model B/shared |
|---|---:|---:|
| current_glucose_mg_dl mean | 146.455 | 145.216 |
| current_glucose_mg_dl median | 133.335 | 133.335 |
| current_glucose_age_minutes mean | 0.000 | 0.000 |
| current_glucose_age_minutes median | 0.000 | 0.000 |
| glucose_5min_before_mg_dl mean | 146.441 | 143.663 |
| glucose_5min_before_mg_dl median | 133.335 | 131.533 |
| glucose_10min_before_mg_dl mean | 146.440 | 142.486 |
| glucose_10min_before_mg_dl median | 133.335 | 131.533 |
| glucose_15min_before_mg_dl mean | 146.439 | 141.691 |
| glucose_15min_before_mg_dl median | 133.335 | 129.731 |
| glucose_change_5min_mg_dl mean | 0.015 | 1.553 |
| glucose_change_5min_mg_dl median | 0.000 | 0.000 |
| glucose_change_10min_mg_dl mean | 0.015 | 2.730 |
| glucose_change_10min_mg_dl median | 0.000 | 1.802 |
| glucose_change_15min_mg_dl mean | 0.016 | 3.525 |
| glucose_change_15min_mg_dl median | 0.000 | 1.802 |
| Target prevalence | 3.629% | 4.081% |
| Earliest prediction timestamp | 2023-10-01 00:19:00 | 2023-10-09 12:33:00 |
| Latest prediction timestamp | 2024-08-29 14:00:00 | 2024-08-13 07:08:00 |
| Distinct source files | 16 | 11 |

The saved paired prediction CSV contains probabilities and identifiers but not the eight glucose feature values, so it was not used for feature distribution calculations. The comparison above uses the saved Model A and Model B datasets.

## Interpretation and limitations

- Retention is highly selective descriptively: only about one in five Model A-eligible rows is present in Model B, and five of sixteen participants contribute no paired rows.
- Model B rows are concentrated in a small number of participants, especially the largest contributors shown above. This means pooled paired metrics are weighted toward those participants.
- The shared cohort has a different label prevalence and feature distribution from the wider Model A cohort; these are descriptive cohort differences, not proof of selection bias or causality.
- Timestamp ranges and source-file counts describe coverage only. They do not establish why rows were retained, whether meal logging behavior caused retention, or whether the cohorts differ statistically.
- The saved artifacts do not provide a direct missingness mechanism, meal availability process, or validated consumption-time alignment. Timestamp semantics remain uncertain, and nutrition records may represent recorded-time proxies.
- Overlapping prediction windows create temporal dependence; rows must not be treated as independent evidence. Only 11 participants contribute to paired evaluation.

## Recommended next step

**Use participant-level, paired descriptive reporting as the primary interpretation layer, and before any stronger Model A–Model B claim, document and analyze the eligibility mechanism for missing/no-window carbohydrate records (including retention by participant and time period).** This should remain exploratory and should not involve threshold tuning or clinical claims.
