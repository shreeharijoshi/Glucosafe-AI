# Model B Product-Feature Alignment Review

## Current training feature

The experimental Model B integration defines `MODEL_B_FEATURE_COLUMNS` as the
eight Model A glucose features plus `carbs_30min_g` in
[`ML/src/integration/model_b.py`](../src/integration/model_b.py).

For each prediction timestamp `t`, `carbs_30min_g` is computed as:

```text
sum(carbs_g for same-participant nutrition records where
    t - 30 minutes <= nutrition timestamp <= t)
```

The implementation therefore:

- includes both 30-minute and prediction-time boundaries;
- excludes nutrition timestamps after `t`;
- sums multiple valid records in the window;
- removes exact duplicate nutrition rows before summing;
- excludes a window containing conflicting duplicate records;
- excludes missing, nonnumeric, or negative carbohydrate values rather than
  converting them to zero;
- treats a window with no qualifying record as unavailable, not zero.

The paired evaluator in
[`ML/src/evaluation/paired.py`](../src/evaluation/paired.py) trains Model B
with this feature alongside the eight Model A features. It does not create a
single-meal identifier or select one meal from the window.

## Intended product feature

The project README describes Model B as using “the carbohydrate quantity for
the meal currently being calculated”; it explicitly says carbohydrates must
not be accumulated across meals. See
[`ML/README.md`](../README.md).

The intended application interaction is:

1. The user enters a recently eaten meal.
2. The nutrition calculator returns that meal's macros.
3. The model receives the carbohydrate amount for that meal currently being
   evaluated.

This is a single user-selected meal value, not a historical rolling sum.
The product description does not, by itself, define whether the relevant
timestamp is the time of eating, calculator submission, or model invocation.

## Alignment assessment

**Assessment: materially different features, not merely a naming difference.**

| Issue | Experimental Model B | Intended product |
|---|---|---|
| Quantity | Sum of all valid records in `[t-30m, t]` | Carbohydrates for one current meal |
| Multiple meals | Multiple records can be summed | Meals must not be accumulated |
| Event time | Dataset `meal_ts`/parsed timestamp proxy | User entry or product-defined meal/input time, not yet specified |
| Missing record | Prediction is ineligible | User may provide a meal directly even if dataset nutrition has no record |
| Window | Inclusive 30-minute lookback | No product recency interval is established here |
| Duplicates | Exact duplicates counted once; conflicts exclude | Product duplicate-submission behavior is not defined |

The experimental feature can match the product only under an additional
assumption: every eligible window contains exactly one valid nutrition record,
that record represents the current meal, and its recorded timestamp is an
acceptable proxy for the product input time. The existing implementation does
not establish those conditions.

## Confirmed behavior versus assumptions

### Confirmed implementation behavior

- Matching is by participant ID.
- The window is inclusive at both endpoints.
- Future nutrition records are excluded.
- Multiple qualifying records are summed.
- Exact duplicate records are not double-counted.
- Conflicting, missing, invalid, or negative records make affected windows
  ineligible.
- The paired evaluation uses the resulting `carbs_30min_g` value without
  retraining on a separately defined product feature.

### Implementation and interpretation assumptions

- A dataset nutrition timestamp can be ordered against a glucose prediction
  timestamp after the loader's timezone-naive parsing.
- A nutrition record in the lookback window is relevant to the prediction.
- The recorded timestamp is sufficiently close to the meal's actual or
  application-available time.

These assumptions are operational research choices, not documented proof that
the dataset records actual meal consumption or immediate user availability.

## Unresolved decisions

Before claiming that the experiment represents the product input, the project
must decide:

1. Is the production feature one explicit meal amount, or is a rolling
   carbohydrate exposure feature intentionally desired?
2. What event starts the feature's recency interval: meal consumption,
   calculator submission, or model invocation?
3. If multiple meals occur close together, should the product reject the
   input, select one explicit meal, or deliberately aggregate them?
4. How should a missing dataset nutrition record be distinguished from a
   user-entered meal that exists only in the application?
5. How are duplicate submissions and edits represented?
6. What timestamp, timezone, and logging-delay policy makes a meal eligible?

The open questions in
[`ML/docs/OPEN_QUESTIONS.md`](../docs/OPEN_QUESTIONS.md) already record the
unresolved maximum interval, multiple-meal handling, and possible logging
delay. Dataset `meal_ts` semantics and timezone alignment also remain
unresolved.

## Recommendation

The smallest defensible next step is to freeze the product contract before
changing the pipeline: define a prediction-time input record containing an
explicit meal identifier, carbohydrate amount, and application event
timestamp, and state whether the model feature is strictly that one meal.

Then perform a small, non-training schema/alignment test showing how one
product meal maps to one prediction row and how multiple, duplicate, missing,
and future records are handled. Do not reinterpret the existing
`carbs_30min_g` results as evidence about the single-meal product feature until
that contract is decided. No fabricated meal timestamps or carbohydrate values
should be introduced.
