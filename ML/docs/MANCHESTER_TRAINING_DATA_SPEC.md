# Manchester Training-Example Construction Specification

## 1. Executive summary

This specification defines a leakage-safe, participant-grouped construction of training examples for the provisional Manchester/T1D-UOM Model B experiment. Model B uses:

- current glucose;
- a small history of glucose observations and trends; and
- carbohydrates in grams from one eligible, recently recorded meal.

Model A uses the same glucose features and is evaluated on the same examples as Model B. No model is trained by this specification.

The construction is intentionally conservative. It treats `meal_ts` as a **recorded nutrition timestamp**, not as proven food-consumption time. It does not use missing carbohydrates as zero, sum multiple meals, use future events, or convert unknown target coverage into a negative label.

Implementation is blocked until the project approves one timestamp parser, confirms participant/file mapping, and defines how recorded meal time is intended to approximate the application's “recently consumed” input. The rules below are the proposed implementation contract once those decisions are approved.

## 2. Confirmed data facts versus assumptions

### Confirmed from local files and reports

- Manchester has glucose files with schema `bg_ts,value`; the README documents glucose values in mmol/L.
- Manchester nutrition files have schema `meal_ts,meal_type,meal_tag,carbs_g,prot_g,fat_g,fibre_g`; the README documents `carbs_g` in grams.
- The extracted tree contains 17 glucose files and 15 nutrition files. Existing audits identify 15 participants with both modalities, but the README and citation metadata disagree about the total population.
- The prior audit counted 356,146 glucose rows, 15,915 duplicate glucose timestamps, and 66,446 within-file gaps longer than 10 minutes.
- The prior audit counted 4,351 nutrition rows, 42 missing carbohydrate values, 5 invalid nutrition timestamps under its parser, and 18 duplicate nutrition timestamps.
- The README documents month-first timestamp formats, while source records such as `22/10/2023` require day-first parsing. This conflict is unresolved.
- The target policy in the project documentation is a threshold-derived label: any valid glucose value strictly below 70 mg/dL in `(t, t + 30 minutes]`.

### Proposed assumptions/design choices, not dataset facts

- A recorded `meal_ts` with valid `carbs_g` is an observable meal-input proxy. It is not evidence that consumption happened at exactly that timestamp.
- A meal is eligible for Model B only when its timestamp and carbohydrate value pass validation and its availability is compatible with the declared application scenario.
- The initial glucose history is a 15-minute, observation-based history with current glucose plus approximately 5-minute and 15-minute changes. This is a practical starting design, not an established project requirement.
- A candidate meal recency window is evaluated from 30, 60, and 120 minutes before `t`. No final window is selected until the required feasibility counts are produced.
- Prediction examples with multiple eligible meals are excluded initially rather than silently choosing one or summing them.

## 3. Participant and timestamp handling

### 3.1 Participant identity and file pairing

Use the participant identifier encoded by the documented filename convention:

```text
UoM + data category + ParticipantID.csv
```

Extract and normalize the suffix after the category prefix using the actual filenames. Pair a glucose file and nutrition file only when their normalized participant IDs match exactly. Do not pair files because their names merely look similar.

Before implementation, produce a pairing manifest containing:

- participant ID;
- glucose file path(s);
- nutrition file path(s);
- whether each modality is present;
- recording start/end after approved timestamp parsing;
- overlapping recording intervals;
- duplicate and invalid-row counts.

Unmatched glucose-only participants remain eligible for Model A-only descriptive accounting but cannot contribute to the common Model A/Model B evaluation set. Unmatched nutrition-only participants are excluded from this experiment. If one participant has multiple files or overlapping recordings, retain a recording/file identifier and do not concatenate them until overlap and provenance are resolved. Overlapping files must not duplicate the same recording period.

The existing count of 15 participants with both modalities is a planning fact from the audit, not a substitute for this manifest. The README's 16-person statement, citation's 17-person statement, and extracted file counts must be reconciled.

### 3.2 Timestamp parsing

Do not silently choose between month-first and day-first parsing. The implementation must:

1. retain the original timestamp string;
2. parse using the project-approved format policy;
3. record the parser/version and failures;
4. reject impossible or implausible resulting dates;
5. exclude unresolved ambiguous timestamps from temporal joins.

The current evidence requires a project decision because the README describes `MM/DD/YYYY`, while values containing days above 12 cannot use that interpretation. A parser that accepts both formats without a documented disambiguation rule is not sufficient for final data construction.

Glucose and nutrition timestamps must be normalized to one timezone/naive-time convention only after the dataset's timezone assumption is documented. Do not infer timezone alignment from matching clock times alone.

### 3.3 Duplicate records and invalid rows

For glucose:

- Group duplicate timestamps within the legitimate participant/recording segment.
- Preserve all raw rows and record duplicate counts and value conflicts.
- Do not select the first or last duplicate silently.
- If duplicate values agree, a deterministic deduplication may be approved; if values conflict, the timestamp is excluded from feature and target construction unless a project policy resolves it.

For nutrition:

- Treat exact duplicate rows as one recorded row only after counting and documenting the duplicates.
- Treat same-timestamp rows with different meal metadata or carbohydrate values as ambiguous; exclude prediction examples for which that ambiguity affects meal association.
- Do not sum same-timestamp rows unless a source-level rule proves they are separate foods in one meal and the task explicitly defines summation.

Reject rows with invalid timestamps, nonnumeric glucose/carbohydrate values, or missing required identifiers. Retain rejection reasons in exclusion accounting.

## 4. Glucose-feature construction

### 4.1 Units and values

Convert glucose from mmol/L to mg/dL using the project-approved factor `18.0182` only after confirming the README's mmol/L unit and the timestamp/participant mapping. Preserve the original value and converted value.

Do not silently discard physiologically unusual values. First record nonnumeric, missing, negative, and implausible readings. A value should be excluded from modeling only under a declared quality rule that is applied before feature and target construction. A low glucose value below 70 mg/dL is not automatically invalid or a clinically adjudicated hypoglycemia event.

### 4.2 History and current glucose

For every legitimate recording segment, sort cleaned glucose observations by timestamp and construct features before applying meal eligibility:

- `current_glucose`: the valid glucose observation at prediction time `t`;
- `glucose_5min_change`: current glucose minus the immediately preceding valid observation only when its elapsed time is within an approved approximately 5-minute tolerance;
- `glucose_15min_change`: current glucose minus the observation approximately 15 minutes earlier only when the elapsed span and every intervening gap satisfy the approved coverage rule.

The first implementation should use a 15-minute history window and no interpolation. It should require current glucose, a valid approximately 5-minute predecessor, and a valid approximately 15-minute predecessor with no adjacent gap over 10 minutes. This is an explicit design choice that can be revised after feature-availability counts.

Features may use observations with timestamps `<= t` only. Do not use future glucose, target-window observations, or future meal records. Do not fill missing history by interpolation or carry-forward across an unapproved gap.

Prediction timestamps are observation timestamps, not arbitrary points generated by resampling. If duplicate or conflicting current timestamps remain unresolved, no example is created at that time.

## 5. Target and coverage rules

Construct labels from each complete cleaned glucose series **before** filtering prediction times by meal eligibility.

For prediction time `t`, define:

```text
target_window = (t, t + 30 minutes]
```

- `positive (1)`: at least one valid glucose observation with timestamp strictly greater than `t` and less than or equal to `t + 30 minutes`, whose converted value is strictly below 70 mg/dL.
- `negative (0)`: the target window contains no qualifying value and future coverage is sufficient under the rule below.
- `unknown`: future coverage is absent, too late, crosses an invalid/ambiguous recording boundary, or includes a disallowed gap.

An observation exactly at `t` is excluded. An observation exactly at `t + 30 minutes` is included in the label. An observation after `t + 30 minutes` may establish whether the recording continues, but its glucose value cannot create a positive label.

### 5.1 Provisional coverage policy

Retain the project's provisional policy:

- Find the first valid glucose observation at or after `t + 30 minutes`.
- It may be up to 10 minutes late.
- Reject the label as unknown if no such reading exists within that tolerance.
- Reject the label as unknown if any adjacent valid-glucose gap from `t` through the coverage observation is greater than 10 minutes.
- Do not cross a legitimate recording/file boundary when seeking coverage.

The observations in `(t, t + 30 minutes]` determine the label. The first observation at or after the endpoint and the intervening path are used only to establish continuity. A late coverage reading beyond the endpoint must never determine the label.

This policy is consistent with the existing methodology and feasibility reports, but remains provisional. Its final implementation must include boundary tests for `t`, `t + 30 minutes`, `t + 30 minutes + 10 minutes`, and a gap exactly over 10 minutes.

## 6. Meal association and candidate recency windows

### 6.1 Eligible meal record

For a prediction timestamp `t`, a meal record is eligible only if:

1. it belongs to the same participant and legitimate recording context;
2. its approved `meal_ts` is valid and satisfies `meal_ts <= t`;
3. `carbs_g` is present, numeric, and nonnegative;
4. the `carbs_g` unit is confirmed as grams by the approved schema documentation;
5. the record is not a duplicate or unresolved same-time conflict;
6. it falls within the selected candidate recency window before `t`.

Do not infer consumption time from `meal_ts`. The experiment must state that this is a recorded-meal-time proxy and must not describe the resulting feature as observed consumption timing.

### 6.2 Candidate windows

Evaluate these candidate windows independently:

```text
30 minutes:  t - 30 minutes <= meal_ts <= t
60 minutes:  t - 60 minutes <= meal_ts <= t
120 minutes: t - 120 minutes <= meal_ts <= t
```

The endpoints are inclusive for recorded timestamps. A meal at exactly `t` is permitted as an available recorded input only if the application scenario says it is available at prediction time. If the intended workflow is post-consumption input, this must be stated explicitly; if it is pre-meal, the recorded meal may not be available at `t`.

For each window, report:

- valid meal-linked prediction examples;
- unique participants represented;
- examples per participant;
- positive and negative labels;
- unknown labels;
- multiple-meal ambiguities;
- missing/invalid carbohydrate exclusions;
- meal age distribution;
- participants with no eligible examples.

Do not choose a window because it produces the most positive examples. Prefer the shortest window that provides adequate participant representation, enough positive and negative examples per participant, low ambiguity, and acceptable timestamp/data quality. If no window meets those criteria, report Model B as infeasible for this dataset rather than expanding the window until it appears feasible. The final window is a project decision after these counts, not a fact established by this document.

### 6.3 Multiple and missing meals

Do not sum carbohydrates across multiple eligible meal records. Initially exclude a prediction timestamp when more than one distinct eligible meal remains in the selected window, including unresolved duplicate/same-time records. Record the count so a later sensitivity analysis can compare this conservative policy with an approved “most recent meal” rule.

Exclude missing, invalid, or ambiguous carbohydrate values from Model B eligibility. Never encode them as zero. A zero value is retained only when it is an explicit, valid `carbs_g` value and its meal-row meaning is accepted by the schema policy; it is not evidence that no other meal occurred.

## 7. Common Model A/Model B example construction

The construction order is fixed:

1. Parse and validate participant identities, file pairings, and timestamps.
2. Resolve legitimate recording segments and preserve raw-row audit metadata.
3. Clean, order, and deduplicate glucose observations under the approved policy.
4. Construct glucose-history features from observations available at each `t`.
5. Construct target labels and future-coverage status from the complete cleaned glucose series.
6. Keep timestamps with valid features and known labels.
7. Apply the selected meal-association rule.
8. Define the common eligible set as timestamps with valid glucose features, known target labels, and one valid eligible meal.
9. Use that same common set for both models in the primary comparison.
10. Assign complete participants to evaluation partitions before fitting any preprocessing.

Model A is not evaluated on every glucose-only timestamp in the primary comparison. It is evaluated on the same meal-eligible common set as Model B so any difference is attributable to the carbohydrate feature rather than a different population. A separate Model A-only availability analysis may report all valid glucose examples, but it must not replace the matched comparison.

Model A feature columns are the glucose features in Section 4. Model B contains exactly those columns plus the selected single-meal `carbs_g` value. Do not include meal type, meal tag, protein, fat, fibre, insulin, future glucose, future meals, or accumulated carbohydrates.

## 8. Participant-grouped evaluation plan

Assign every participant to exactly one of training, validation, or held-out test. Never split rows randomly. Adjacent windows from one participant may overlap and must remain in the same participant partition.

Because only 15 participants currently have both nutrition and glucose files and the total participant count is inconsistent across documentation, a single split may be unstable. Prefer repeated participant-grouped cross-validation or leave-one-participant-out evaluation for the primary research comparison, with a final participant-held-out test only if the project can predeclare a sufficiently represented test set. The exact strategy must be selected before training.

All preprocessing, scaling, imputation policy (if later approved), and threshold selection must be fitted using training participants only. The same participant assignments, target labels, timestamps, and evaluation policy must be used for Model A and Model B.

Report pooled and per-participant results. Record participant-level variability and class support; do not make a participant-independent claim if a split has no meaningful positive or negative support.

## 9. Exclusion accounting and feasibility checks

Before training, produce an auditable table with counts by participant and split for:

- raw glucose rows;
- invalid, missing, implausible, duplicate, and conflicting glucose rows;
- valid glucose prediction timestamps;
- examples lacking the required 5-minute or 15-minute history;
- positive, negative, and unknown target labels;
- examples rejected for missing future coverage, late coverage, long gaps, or recording boundaries;
- raw nutrition rows;
- invalid, duplicate, conflicting, and missing-carbohydrate meal rows;
- valid meal-linked examples for each 30/60/120-minute candidate window;
- examples with multiple eligible meals;
- common Model A/Model B examples;
- positive and negative examples per participant and per evaluation split.

Existing totals are planning evidence, not final training counts. In particular, the prior target counts were generated before this meal-eligibility construction and the timestamp parser discrepancy is unresolved. Recalculate counts only after the parser, pairing, duplicate, and coverage policies are approved.

Do not declare feasibility from total row count. The experiment is feasible only if the common set has sufficient valid examples, participant representation, and class support in every intended evaluation partition without relying on unknown labels or participant leakage.

## 10. Unresolved questions and decisions required before implementation

1. Which timestamp interpretation is authoritative when the README's month-first format conflicts with day-first source values such as `22/10/2023`?
2. What timezone convention applies, and are glucose and nutrition timestamps aligned in that convention?
3. What exact filename-to-participant mapping is approved, and how should the README/citation/file-count disagreement be recorded?
4. How should duplicate glucose timestamps with conflicting values be handled?
5. Are multiple files for one participant separate recordings, overlapping exports, or duplicate periods?
6. Does the application receive carbohydrate input before eating, after eating, or after delayed logging?
7. Which of the 30-, 60-, or 120-minute windows will be selected after the required participant/class/quality counts?
8. Should multiple eligible meals remain excluded, or may a predeclared most-recent-meal rule be used in a sensitivity analysis?
9. Is the 10-minute future-coverage tolerance final for Manchester, and what constitutes a legitimate recording boundary?
10. Which participant-grouped evaluation strategy will be approved given the small meal-plus-glucose population?

Until these decisions are recorded, Manchester is a promising provisional Model B dataset, not a validated training source.
