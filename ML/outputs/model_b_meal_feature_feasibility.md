# Model B Meal-Feature Feasibility

## 1. Executive conclusion

**Not currently supported for a defensible reproduction of the intended
product input.**

The Manchester/T1D-UOM data can provide participant-associated nutrition
records and arithmetic differences between parsed timestamps. However, it does
not establish that a nutrition record represents one specific consumed meal at
the reported time. The existing Model B feature is a rolling sum, not the
carbohydrate amount for one user-selected meal. Reproducing the proposed
product behavior would therefore require unsupported assumptions about meal
identity, consumption time, logging delay, and clock alignment.

This is an exploratory data-feasibility conclusion, not a clinical or safety
claim.

## 2. What the dataset records

The dataset README describes nutrition `meal_ts` as a datetime of observation,
with `carbs_g` documented as carbohydrates eaten in grams. It does not state
whether `meal_ts` is consumption time, entry time, retrospective reporting
time, or another event time. It also does not document timezone, daylight
saving, clock synchronization, or logging-delay conventions.

The existing loader in
[`ML/src/data/manchester.py`](../src/data/manchester.py):

- associates files by filename-derived participant ID;
- parses both glucose and nutrition timestamps with the operational
  day-first format `%d/%m/%Y %H:%M`;
- stores timezone-naive timestamps;
- preserves raw timestamp text;
- quarantines invalid timestamps and suspicious years;
- retains duplicate records for explicit downstream handling.

Day-first parsing is supported by the project's prior empirical audit, but the
README's documented month-first format remains a documentation conflict.

## 3. Intended product input versus available training data

The intended product behavior is one user-entered meal, a calculator-provided
carbohydrate amount for that meal, and a rough user estimate of elapsed time
since eating, limited initially to 30 minutes. The model should receive that
meal's carbohydrates, not a sum of multiple meals.

The existing integration in
[`ML/src/integration/model_b.py`](../src/integration/model_b.py) defines
`carbs_30min_g` as:

```text
sum(carbs_g for same-participant records with
    prediction_time - 30 minutes <= meal_timestamp <= prediction_time)
```

Both boundaries are inclusive. Future records are excluded. Multiple valid
records are summed. Exact duplicate rows are counted once; conflicting
duplicates, missing or invalid carbohydrates, negative values, and empty
windows make a prediction row ineligible rather than assigning zero.

The saved Model B schema contains `carbs_30min_g`, not a meal identifier,
consumption timestamp, user-entered elapsed-time value, or application
submission timestamp.

## 4. Specific blockers and risks

### One specific consumed meal

The data does not provide a documented meal-event identity linking one
prediction to one consumed meal. If multiple records fall in the window, the
current implementation aggregates them. Selecting one as the current meal
would be an unsupported inference.

### Consumption time and elapsed time

Elapsed minutes can be computed numerically from two parsed timestamps, but
the result cannot be called time since eating because `meal_ts` semantics are
unresolved. It may instead measure time since recording or reporting. The
rough user estimate proposed by the product has no corresponding field in the
dataset.

### Missing and invalid records

No nutrition record means the experimental row is unavailable; it does not
mean that no meal occurred or that carbohydrate intake was zero. Missing or
invalid carbohydrate values are conservatively excluded. This differs from a
product user directly entering a meal whose record need not exist in the
dataset.

### Duplicates and partitions

Exact duplicate nutrition rows are deduplicated. Conflicting duplicate
timestamps exclude affected windows. Invalid timestamps are quarantined by
the loader. Multiple source partitions for a participant are treated
conservatively as ambiguous by the Model B integration. These rules prevent
silent fabrication but do not recover meal identity or consumption time.

### Temporal alignment

Arithmetic ordering assumes glucose and nutrition timestamps share a usable
clock basis after timezone-naive parsing. The documentation does not
establish that assumption, nor does it establish that a recorded nutrition
event was available to an application at prediction time.

## 5. Recommended next step

Freeze a product-compatible data contract before changing the pipeline:

- one explicit meal identifier;
- carbohydrate amount for that meal;
- user/application event timestamp;
- a separately recorded elapsed-time estimate or a documented rule for
  deriving it;
- explicit behavior for multiple meals, duplicate edits, missing values, and
  future entries.

Then perform a small non-training alignment test using only records with
documented provenance. Do not convert the current rolling-sum feature into a
single-meal feature by selecting records heuristically, and do not reinterpret
the existing Model B evaluation as evaluation of the proposed product input.

## 6. Relevant project paths

- [`ML/src/data/manchester.py`](../src/data/manchester.py) — timestamp parsing,
  quarantine, participant association, and duplicate handling.
- [`ML/src/integration/model_b.py`](../src/integration/model_b.py) — current
  rolling `carbs_30min_g` integration policy.
- [`ML/outputs/model_b_dataset.csv`](model_b_dataset.csv) — saved experimental
  Model B schema.
- [`ML/outputs/model_b_product_alignment_review.md`](model_b_product_alignment_review.md)
  — prior product-versus-rolling-feature assessment.
- [`ML/docs/OPEN_QUESTIONS.md`](../docs/OPEN_QUESTIONS.md) — unresolved meal
  timing, multiple-meal, and logging-delay questions.
