# Meal Data Semantics Audit

## 1. Executive summary

The current product scope is a **recently consumed meal**, not a planned meal. Model B is intended to receive carbohydrates for one current meal only; it must not receive accumulated carbohydrates, meal-calculation history, protein, or fat.

**Primary candidate: Manchester / T1D-UOM.** It has explicit meal timestamps, `carbs_g`, meal type, and meal tags, and 15 participant IDs with both glucose and nutrition files. Its limitations are substantial: timestamp-format ambiguity, missing/malformed nutrition records, duplicate glucose timestamps, long glucose gaps, and no proof that a recorded meal timestamp equals consumption time.

**Backup: OhioT1DM.** It has explicit XML meal events with timestamps, type, and carbohydrate values, and comparatively clear glucose timestamps. It has only 12 distinct participants, because its 24 XML files are train/test recordings for the same 12 people. Its supplied split is therefore not participant-independent.

**Not suitable as the primary recent-meal dataset: HUPA-UCM.** Its `carb_input` is attached to a synchronized five-minute grid, but local evidence does not establish that it is an individual consumed-meal event, its units, or whether a nonzero value is entered before or after eating.

No model was trained and no source file was modified.

## 2. Scope and evidence

Inspected:

- `Prac/dataset_audit_report.md`
- `Prac/dataset_feasibility_report.md`
- `Prac/dataset_feasibility_summary.csv`
- `ML/docs/DATASET_ASSESSMENT.md`
- `ML/docs/DATA_DICTIONARY.md`
- `ML/docs/METHODOLOGY.md`
- Extracted dataset trees under `Datasets/`
- Manchester `README.md` and `CITATION.cff`
- Existing scripts under `Prac/`

The analysis below distinguishes **verified file facts**, **assumptions used for exploratory counts**, and **unresolved semantics**.

## 3. Meal-record schemas and samples

### HUPA-UCM

Location:

`Datasets/HUPA-UCM Diabetes Dataset/HUPA-UCM Diabetes Dataset/Preprocessed/`

Schema:

```text
time;glucose;calories;heart_rate;steps;basal_rate;bolus_volume_delivered;carb_input
```

Representative record from `Preprocessed/HUPA0001P.csv`:

```text
2018-06-13T18:40:00;332.0;6.3595;82.3228;34.0;0.0916667;0.0;0.0
```

Verified facts:

- 25 participant files and 309,392 synchronized rows.
- 2,646 rows have nonzero `carb_input`; 22 of the 25 files contain at least one nonzero value.
- There is no separate meal timestamp, meal type, meal tag, or event identifier.
- Separate protein, fat, and fibre fields are absent.

Interpretation is unresolved. `carb_input` may be a time-aligned input signal, but local evidence does not establish that each nonzero value is one consumed meal, that its unit is grams, or that zero means confirmed absence of carbohydrate. It may also reflect an announced, recorded, carried-forward, or otherwise transformed input.

### Manchester / T1D-UOM

Location:

`Datasets/ManchesterCSCoordinatedDiabetesStudy-V1.0.1/sharpic-ManchesterCSCoordinatedDiabetesStudy-a9e8025/Nutrition Data/`

Schema:

```text
meal_ts,meal_type,meal_tag,carbs_g,prot_g,fat_g,fibre_g
```

Representative records from `UoMNutrition2301.csv` and `UoMNutrition2302.csv`:

```text
meal_ts              meal_type  meal_tag          carbs_g  prot_g  fat_g  fibre_g
22/10/2023 10:00     Breakfast  Coffee             0        0       1      0
22/10/2023 12:00     Lunch      Huel+Peanutbutter  19       50      32     10
22/10/2023 17:15     Dinner                        10       [missing] [missing] [missing]
01/10/2023 10:30     Breakfast  Kwark              13       20      0      [missing]
01/10/2023 17:30     Snack      Paneer + Rice      36       47      20     [missing]
01/10/2023 18:15     Dinner     Beer + Hotdog      63       19      14     4
09/10/2023 12:33     Lunch      Jacket_Bean_cheese 118      25      12     15
09/10/2023 18:38     Dinner     TofuRice+crisps    43       43      29     1
09/10/2023 17:18     Snack      chubachub          11       0       0      0
```

Verified facts from the local files/audits:

- 4,351 nutrition rows in 15 files.
- 15 participants have both nutrition and glucose files.
- Carbohydrates are documented as grams in the local README.
- 42 carbohydrate fields are missing in the prior audit; 4,309 were nonempty there.
- Protein, fat, and fibre are present but are not required by the current Model B.
- Five nutrition timestamps were reported invalid in the prior audit; one local parser accepted one additional ambiguous timestamp, producing a count of 4,347 valid rather than 4,346. This discrepancy must be resolved by a single approved parser.
- The prior audit reported 18 duplicate nutrition timestamps.
- The README describes a month-first format, while records such as `22/10/2023` require day-first parsing. This is unresolved.

The field name `meal_ts` establishes a recorded meal timestamp, not necessarily the time food was consumed. No local evidence proves whether records were entered before eating, after eating, or retrospectively.

### OhioT1DM

Location example:

`Datasets/OhioT1DM/OhioT1DM/2018/train/559-ws-training.xml`

Schema:

```xml
<meal>
  <event ts="07-12-2021 15:25:00" type="Snack" carbs="18"/>
</meal>
```

Representative records:

```text
participant  timestamp              type       carbs
559           18-01-2022 05:45:00   Breakfast  46
559           18-01-2022 10:50:00   Lunch      30
563           29-10-2021 05:50:00   Breakfast  15
563           29-10-2021 20:20:00   Dinner     63
```

Verified facts:

- 2,168 meal events across 24 XML files.
- 24 XML files correspond to 12 distinct participant IDs; each person has a train and test file.
- 23 of 24 files contain usable carbohydrate records according to the local audit.
- Meal timestamps use the XML day-month-year format.
- Meal records contain timestamp, type, and carbohydrates only; protein, fat, and fibre are absent.
- The XML does not establish whether `ts` is consumption time or entry/logging time.

## 4. Missingness and quality

| Dataset | Meal/nutrition records | Timestamp issues | Carbohydrate issues | Participant coverage |
|---|---:|---|---|---|
| HUPA-UCM | 309,392 synchronized rows; 2,646 nonzero carb signals | No meal-event timestamp exists | Unit and zero semantics unresolved | 22 files have nonzero signals; 25 have synchronized glucose |
| Manchester | 4,351 rows | 5 invalid timestamps in prior audit; 18 duplicate nutrition timestamps; parser disagreement | 42 missing carbohydrate fields in prior audit; do not treat as zero | 15 participants with glucose and nutrition files |
| OhioT1DM | 2,168 meal events | XML timestamps parse consistently in inspected files | 23/24 files have usable carbohydrate records; no protein/fat/fibre | 12 distinct participants; 24 recording files |

Missing carbohydrates are not evidence of zero intake. They should be excluded, treated as unknown, or handled by a predeclared common-policy analysis.

## 5. Meal-to-glucose alignment

### Compatible time bases

- HUPA glucose and `carb_input` share the synchronized grid, but that makes alignment easy without proving meal semantics.
- Manchester glucose uses `bg_ts`; nutrition uses `meal_ts`. Both are human-readable timestamps, but format interpretation is unresolved and the glucose stream has duplicate timestamps and long gaps.
- Ohio glucose and meal events use the same XML timestamp convention within each file.

### Recorded meal versus consumed meal

None of the three datasets proves that its meal timestamp is the actual time of consumption. Therefore, a recorded-meal window is only an exploratory proxy for “recently consumed.” It cannot validate the product’s time-since-eating assumption without a separate consumption-time field or documentation.

### Multiple meals

Multiple meal events can occur close together, especially in Manchester and Ohio. A prediction timestamp can therefore have multiple eligible prior meals. The audit must not silently sum carbohydrates across them. A future experiment needs a declared policy, such as selecting the most recent valid event, restricting to timestamps with exactly one eligible event, or representing ambiguity as missing.

### Leakage

For a recently consumed meal workflow, the meal event and its carbohydrate value must have been available by prediction time. Using a meal record that was entered after consumption is only valid if the application also receives it at that time. Future meal events must not be used.

## 6. Exploratory recorded-meal windows

These counts use **recorded timestamps**, not verified consumption times. They are exploratory only. The association rule is: a glucose prediction timestamp `t` is eligible if at least one valid meal timestamp lies in `[t - window, t]`. Multiple eligible meals are counted as ambiguity, not summed. Target counts use the provisional corrected 30-minute policy: values determining the target must satisfy `t < glucose_time <= t + 30 minutes`; coverage tolerance is not a product decision.

### Manchester

Across the 17 glucose files:

| Prior recorded-meal window | Prediction timestamps with ≥1 meal | Positive | Negative | Unknown | Timestamps with multiple eligible meals | Participants |
|---:|---:|---:|---:|---:|---:|---:|
| 30 min | 20,193 | 58 | 582 | 19,553 | 301 | 15 |
| 60 min | 36,894 | 540 | 11,669 | 24,685 | 1,275 | 15 |
| 120 min | 67,091 | 1,356 | 32,393 | 33,342 | 5,975 | 15 |

An alternative meal-centric calculation found 3,998 of 4,346 parsed meal records had at least one later glucose reading within 30 minutes, 4,005 within 60 minutes, and 4,022 within 120 minutes. These are different denominators and must not be confused with prediction-timestamp counts.

### OhioT1DM

Across the 24 recording files:

| Prior recorded-meal window | Prediction timestamps with ≥1 meal | Positive | Negative | Unknown | Timestamps with multiple eligible meals | Distinct participants |
|---:|---:|---:|---:|---:|---:|---:|
| 30 min | 11,504 | 56 | 115 | 11,333 | 119 | 12 |
| 60 min | 22,834 | 1,044 | 10,521 | 11,269 | 480 | 12 |
| 120 min | 44,163 | 1,927 | 31,812 | 10,424 | 2,467 | 12 |

The meal-centric audit found 1,972 of 2,168 meal records had a later glucose reading within 30 minutes, 1,988 within 60 minutes, and 2,018 within 120 minutes. These are verified exploratory counts, but they do not establish actual time since eating.

These prediction-timestamp counts are exploratory and are calculated within each XML recording file. They should not be interpreted as 12 independent participant samples until the participant-level split and train/test recording policy are finalized.

### HUPA-UCM

Recorded-meal windows cannot be calculated defensibly. `carb_input` has no documented event timestamp or event semantics. Counting nonzero grid rows as meals would create an unsupported assumption.

## 7. Target-label methodology review

The existing implementation in `Prac/validate_dataset_feasibility.py`, function `target_counts()`, correctly excludes the current observation and includes a reading exactly at `t + 30 minutes`. However, it uses the first reading at or after the endpoint to assess coverage and includes that reading in the future-value slice even if it is 1–10 minutes late.

That can allow a low reading after the exact horizon to determine a label. The target protocol must be corrected so that:

```text
t < glucose_time <= t + 30 minutes
```

is used for target values. A late reading may be used only for an explicitly documented continuity policy, never as a target-determining value. Existing counts must not be copied as final labels until this is fixed and tested.

## 8. Comparison

| Criterion | HUPA-UCM | Manchester / T1D-UOM | OhioT1DM |
|---|---|---|---|
| Individual meal events | Not established | Yes, nutrition rows | Yes, XML events |
| Recorded meal timestamp | No separate field | `meal_ts` | `meal/@ts` |
| Carbohydrate quantity | `carb_input`, semantics unresolved | `carbs_g`, documented grams | `carbs`, unit convention should be confirmed |
| Glucose alignment | Easy grid alignment, weak meal semantics | Possible after timestamp cleaning | Possible within XML file |
| Recent-meal support | Not defensible currently | Best candidate | Good backup |
| Glucose continuity | Strong regular grid | Duplicate/gap problems | Regular with gaps |
| Participant-independent evaluation | 25 participants | 15 meal+glucose participants; 17 glucose IDs | 12 distinct participants |
| Main risk | Signal is not a documented meal event | Timestamp and logging-time ambiguity | Small participant count and train/test overlap |

## 9. Recommendation

### Primary: Manchester / T1D-UOM

Use Manchester for the first recently-consumed-meal carbohydrate investigation because it has the clearest event-level carbohydrate field and the largest usable meal-plus-glucose participant coverage among the event-based candidates.

This is a **research recommendation**, not a clinical endorsement. Before modeling, resolve timestamp parsing, duplicate policies, missing carbohydrate handling, participant mapping, and the maximum allowed interval since a recorded meal.

### Backup: OhioT1DM

Use OhioT1DM as the backup or as a simpler carbohydrate-event prototype. Its event structure is clearer, but its 12 distinct participants and overlapping supplied train/test IDs limit unseen-participant evaluation.

### HUPA-UCM

Retain HUPA-UCM for a glucose-only regular-grid baseline or a later experiment after its unit, preprocessing provenance, and `carb_input` semantics are verified. Do not treat nonzero grid values as consumed meals without evidence.

## 10. Fair Model A versus Model B comparison

1. Use the same participant partitions.
2. Use the same prediction timestamps and corrected target labels wherever possible.
3. Restrict Model B to timestamps with a valid, available current-meal carbohydrate input, then evaluate Model A on that identical subset.
4. Alternatively, define a predeclared missing-input policy, but do not silently encode missing carbohydrates as zero.
5. Keep all future glucose and future meal records out of features.
6. Avoid random row-level splitting because adjacent 30-minute windows overlap and are statistically dependent.
7. Keep Ohio train/test files together by participant for unseen-person evaluation.

## 11. Unresolved questions and next steps

1. Does the application receive the carbohydrate input immediately after eating, and what maximum recorded-meal age is allowed?
2. Does each dataset's meal timestamp represent consumption time, entry time, or retrospective logging?
3. Which Manchester timestamp parser and participant mapping will be approved?
4. How will duplicate or conflicting meal and glucose timestamps be handled?
5. How will missing carbohydrate values be treated without assuming zero?
6. Which coverage policy will define known versus unknown target labels?
7. Should multiple eligible meals make a timestamp ambiguous/excluded, or should the most recent meal be selected?
8. Can HUPA units, preprocessing provenance, and `carb_input` semantics be verified?
9. Can Ohio's 12 participants support a sufficiently balanced participant-independent evaluation?

## Status

This is an audit only. No model, feature pipeline, or training/evaluation code was implemented. No source dataset or existing audit file was changed.
