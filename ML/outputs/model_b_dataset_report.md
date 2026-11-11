# Model B Dataset Audit

Exploratory recorded-time carbohydrate proxy; not clinical validation.

- Rolling window: inclusive `[t - 30 minutes, t]`.
- Input Model A rows: 340231
- Model B eligible rows: 11344
- Excluded rows: 328887
- Eligible participants: 11
- Positive targets: 463
- Negative targets: 10881
- Exclusion reasons: {'no_carbohydrate_record_in_window': 167541, 'model_a_not_eligible': 96987, 'no_nutrition_records': 64263, 'conflicting_nutrition_duplicate': 54, 'missing_or_invalid_carbohydrate': 42}
- Ambiguous recording-partition exclusions: 0
- Per-participant eligible counts:
  - 2301: 2029 rows, 12 positive, 2017 negative
  - 2304: 1937 rows, 38 positive, 1899 negative
  - 2306: 1 rows, 0 positive, 1 negative
  - 2307: 776 rows, 5 positive, 771 negative
  - 2308: 1400 rows, 138 positive, 1262 negative
  - 2309: 1012 rows, 29 positive, 983 negative
  - 2313: 1337 rows, 48 positive, 1289 negative
  - 2314: 22 rows, 0 positive, 22 negative
  - 2320: 2721 rows, 162 positive, 2559 negative
  - 2401: 104 rows, 31 positive, 73 negative
  - 2405: 5 rows, 0 positive, 5 negative
- Exact duplicate nutrition rows are counted once; conflicting duplicates are excluded.
- Missing, invalid, or negative carbohydrates are never converted to zero.
- Empty carbohydrate windows are unavailable, not zero.
- `meal_ts` remains a recorded-time proxy; consumption time and timezone alignment are unresolved.
- The intersection dataset equals the Model B dataset because Model B eligibility requires complete known Model A rows.
