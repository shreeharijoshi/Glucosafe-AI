# Model B Exclusion Mechanism

Targeted analysis of the saved Model B exclusion audit. Only rows eligible for Model A evaluation were counted as Model B retention failures. No datasets, predictions, or existing reports were modified.

## Scope and linkage

- Model A-eligible denominator: **242,584** rows.
- Audit rows with `model_a_not_eligible` (excluded from this analysis): **96,987**.
- Audit rows matched to Model A-eligible participant/timestamp keys and analyzed: **231,240**.
- The exclusion audit does not contain `source_file`; linkage therefore uses participant ID and prediction timestamp. This is adequate for the saved participant-level artifacts but cannot independently verify source-partition identity.

## Exclusion reasons among Model A-eligible rows

| Reason | Rows | Percent of Model A-eligible rows |
|---|---:|---:|
| no_carbohydrate_record_in_window | 167,541 | 69.065% |
| no_nutrition_records | 63,603 | 26.219% |
| missing_or_invalid_carbohydrate | 42 | 0.017% |
| conflicting_nutrition_duplicate | 54 | 0.022% |
| Other documented reasons | 0 | 0.000% |

- Total excluded after Model A eligibility: **231,240**.
- Model B retained from the Model A-eligible denominator: **11,344**.
- No Model A-eligible row was assigned a zero carbohydrate value by this audit; the reasons reflect unavailable, invalid, or conflicting nutrition evidence under the implementation policy.

## Participant-level pattern

| Participant | Model A eligible | Excluded | Retained | Exclusion rate | No window | No nutrition | Missing/invalid | Conflicting duplicate |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2301 | 35,984.0 | 33,955.0 | 2,029.0 | 94.36% | 33,907.0 | 0.0 | 0.0 | 48.0 |
| 2303 | 13,793.0 | 13,793.0 | 0.0 | 100.00% | 0.0 | 13,793.0 | 0.0 | 0.0 |
| 2304 | 30,706.0 | 28,769.0 | 1,937.0 | 93.69% | 28,769.0 | 0.0 | 0.0 | 0.0 |
| 2305 | 7.0 | 7.0 | 0.0 | 100.00% | 7.0 | 0.0 | 0.0 | 0.0 |
| 2306 | 4.0 | 3.0 | 1.0 | 75.00% | 3.0 | 0.0 | 0.0 | 0.0 |
| 2307 | 8,313.0 | 7,537.0 | 776.0 | 90.67% | 7,537.0 | 0.0 | 0.0 | 0.0 |
| 2308 | 28,472.0 | 27,072.0 | 1,400.0 | 95.08% | 27,065.0 | 0.0 | 7.0 | 0.0 |
| 2309 | 20,489.0 | 19,477.0 | 1,012.0 | 95.06% | 19,465.0 | 0.0 | 12.0 | 0.0 |
| 2310 | 49,810.0 | 49,810.0 | 0.0 | 100.00% | 0.0 | 49,810.0 | 0.0 | 0.0 |
| 2313 | 30,681.0 | 29,344.0 | 1,337.0 | 95.64% | 29,321.0 | 0.0 | 23.0 | 0.0 |
| 2314 | 64.0 | 42.0 | 22.0 | 65.62% | 42.0 | 0.0 | 0.0 | 0.0 |
| 2320 | 23,676.0 | 20,955.0 | 2,721.0 | 88.51% | 20,949.0 | 0.0 | 0.0 | 6.0 |
| 2401 | 443.0 | 339.0 | 104.0 | 76.52% | 339.0 | 0.0 | 0.0 | 0.0 |
| 2403 | 115.0 | 115.0 | 0.0 | 100.00% | 115.0 | 0.0 | 0.0 | 0.0 |
| 2404 | 1.0 | 1.0 | 0.0 | 100.00% | 1.0 | 0.0 | 0.0 | 0.0 |
| 2405 | 26.0 | 21.0 | 5.0 | 80.77% | 21.0 | 0.0 | 0.0 | 0.0 |

## Calendar-month distribution

The audit timestamps support a descriptive month breakdown; this does not establish a causal recording or eating pattern.

| Month | No window | No nutrition | Missing/invalid | Conflicting duplicate | Total |
|---|---:|---:|---:|---:|---:|
| 2023-10 | 20975 | 10578 | 0 | 6 | 31559 |
| 2023-11 | 27914 | 15529 | 9 | 13 | 43465 |
| 2023-12 | 35686 | 8745 | 14 | 17 | 44462 |
| 2024-01 | 41101 | 8696 | 0 | 18 | 49815 |
| 2024-02 | 24522 | 8155 | 13 | 0 | 32690 |
| 2024-03 | 9906 | 8680 | 6 | 0 | 18592 |
| 2024-04 | 7134 | 3220 | 0 | 0 | 10354 |
| 2024-05 | 175 | 0 | 0 | 0 | 175 |
| 2024-06 | 119 | 0 | 0 | 0 | 119 |
| 2024-07 | 6 | 0 | 0 | 0 | 6 |
| 2024-08 | 3 | 0 | 0 | 0 | 3 |

## Policy consistency and limits

- `no_carbohydrate_record_in_window` is consistent with the inclusive `[t - 30 minutes, t]` policy when no qualifying record is available; it must not be interpreted as evidence that no carbohydrates were eaten.
- `no_nutrition_records` is consistent with participants or records lacking nutrition data.
- `missing_or_invalid_carbohydrate` and `conflicting_nutrition_duplicate` are consistent with conservative exclusion rather than silently imputing or selecting values.
- The saved audit cannot distinguish an unrecorded meal from no meal, delayed logging, out-of-window logging, or timestamp misalignment.
- The audit cannot establish actual consumption time, timezone alignment, daylight-saving behavior, or the reason participants with no retained rows lack eligible nutrition windows.
- Counts are descriptive and do not establish selection bias, causality, or statistical significance.

## Recommended next step

**Preserve this exclusion stratification in any future paired analysis and, if stronger generalization is needed, obtain or create a validated nutrition-availability/timestamp provenance field before interpreting carbohydrate eligibility as meal exposure.**
