# OhioT1DM External Validation Preparation

This is a read-only preparation audit for applying the finalized Manchester-trained Model A XGBoost model to OhioT1DM. Only the official Ohio testing XML files were inspected. No Ohio training-partition observations were used for feature construction, target construction, or counts. No model was retrained, no predictions or performance metrics were generated, and no existing files were modified.

## Final recommendation

**CONDITIONALLY READY**

Strong published evidence supports interpreting OhioT1DM glucose values as mg/dL, but the original local XML files remain unitless and the local copy of the original paper could not be text-verified with the available PDF tools. Evaluation may proceed only after the published evidence and unit decision are recorded in the locked external-evaluation specification, and after the test-only adapter is implemented and independently checked. The supplied Ohio train/test arrangement also reuses participant IDs, so the resulting test would be external to Manchester but not an unseen-participant Ohio evaluation.

## Glucose Unit Evidence and Final Compatibility Decision

### Original dataset and local evidence

- The inspected Ohio XML files contain `<glucose_level><event ts="..." value="..."/>` values but no unit attribute or unit declaration.
- `Prac/OhioT1DM_prac/check_data_quality.py`, `check_gap_distribution.py`, and `build_training_data.py` use a `<70 mg/dL` threshold in local exploratory code. This is project-side working convention, not dataset documentation and cannot by itself prove the source unit.
- `Prac/dataset_audit_report.md` describes Ohio values as “mg/dL-compatible” and explicitly says the local files do not establish the unit.
- The project `ML/docs/DATA_DICTIONARY.md` requires glucose to be in mg/dL **after verified conversion**, which is a project requirement rather than Ohio source evidence.
- The local Ohio dataset tree contains no README or XML schema document declaring the glucose unit.
- The local original-paper file is present at `Papers/OhioT1DM-dataset-paper.pdf` (also copied under `Prac/Papers/OhioT1DM-dataset-paper.pdf`), but no local PDF text-extraction tool was available to verify a unit statement from that file directly.

### Subsequent published evidence

- The peer-reviewed open-access article **“Feature Transformation for Efficient Blood Glucose Prediction in Type 1 Diabetes Mellitus”** evaluates the OhioT1DM dataset and reports prediction errors in **mg/dL** and the hypoglycemia boundary as **70 mg/dL**: [PMC9913914](https://pmc.ncbi.nlm.nih.gov/articles/PMC9913914/). This is strong published evidence of the unit convention used for OhioT1DM research, but it is subsequent research rather than the original dataset documentation.
- A subsequent peer-reviewed PLOS ONE study, **“AWD-stacking: An enhanced ensemble learning model for predicting blood glucose levels”**, likewise reports OhioT1DM blood-glucose errors in mg/dL: [PLOS ONE 10.1371/journal.pone.0291594](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0291594).
- The dataset-author citation identified in the literature is Marling and Bunescu, **“The OhioT1DM Dataset for Blood Glucose Level Prediction: Update 2020,”** with the author-maintained dataset page referenced as `http://smarthealth.cs.ohio.edu/OhioT1DM-dataset.html`. That page was not retrievable during this review, so it cannot serve as a directly verified local citation here.

### Final unit decision

The strongest available evidence is the consistent mg/dL convention in multiple peer-reviewed OhioT1DM studies, supported by the local project audit and scripts but not proved by the unitless XML schema. This is sufficient for a **CONDITIONALLY READY** decision and for a documented mg/dL interpretation in a locked external-evaluation protocol; it is not sufficient to claim that the original XML itself explicitly verifies the unit. Do not apply a conversion factor. If the dataset authors or an accessible original documentation copy later states a different unit, stop the evaluation and revise the protocol.

## Dataset structure

Inspected paths:

- `Datasets/OhioT1DM/OhioT1DM/2018/test/*.xml`
- `Datasets/OhioT1DM/OhioT1DM/2020/test/*.xml`

The official testing partition contains 12 XML files: six in each year. It contains 12 distinct participant IDs (`540, 544, 552, 559, 563, 567, 570, 575, 584, 588, 591, 596`) and 31,743 glucose events. Each test XML is treated as an independent participant/year recording boundary. Files are not merged across years, and no corresponding `train` XML is read for feature history or target coverage.

All inspected event sequences were chronologically sorted. Timestamp ranges are file-specific and span 2021–2027 in the local XML values; the directory year is not used as a timestamp. Timestamps include seconds and use the explicit day-month-year form shown in the XML, for example `19-05-2027 11:36:29`. No timezone or offset is present, so timestamps are treated as timezone-naive within each file.

## Units and target semantics

Ohio XML glucose values are integer-valued and are interpreted as mg/dL for the conditional evaluation plan based on the published evidence above. The XML schema itself does not include a unit attribute, so this remains a documented external-evaluation decision rather than a direct XML-level verification.

The target must remain:

- Positive if at least one valid glucose value is `<70 mg/dL` in `(t, t + 30 minutes]`.
- Negative only when the future interval has adequate coverage and contains no such value.
- Unknown/ineligible when endpoint coverage is absent or more than 10 minutes late, or when an adjacent glucose gap exceeds 10 minutes.
- A value exactly at `t` is excluded; a value exactly at `t + 30 minutes` is included.

Ohio's explicit `hypo_event` annotations are not used as the target. They are a separate signal and must not be substituted for the threshold-derived target.

## Feature compatibility and construction

The finalized model requires these features, in this order:

1. `current_glucose_mg_dl`
2. `current_glucose_age_minutes`
3. `glucose_5min_before_mg_dl`
4. `glucose_10min_before_mg_dl`
5. `glucose_15min_before_mg_dl`
6. `glucose_change_5min_mg_dl`
7. `glucose_change_10min_mg_dl`
8. `glucose_change_15min_mg_dl`

The existing Manchester feature builder performs latest-observation lookups at or before each requested time. Historical lookups have a five-minute maximum age. It does not interpolate, average, carry values across a disallowed gap, or zero-fill missing values.

| Feature | Ohio construction using the existing definition | Status |
|---|---|---|
| Current glucose | Use the latest valid Ohio glucose at or before `t`; for Ohio candidate times defined by each glucose event, the exact event has age 0. | Compatible |
| Current glucose age | `t - timestamp_of_latest_valid_reading_at_or_before_t`, expressed in minutes. This lookup has no five-minute age cap in the Manchester implementation; only the historical lookups are capped. | Compatible; expected to be 0 for event-time candidates |
| 5-minute history | Use the latest valid reading at or before `t - 5 minutes`, accepting it only if its age is at most 5 minutes. | Compatible, with eligibility loss for irregular gaps |
| 10-minute history | Same lookup at `t - 10 minutes`, with the same five-minute maximum age. | Compatible, with eligibility loss for irregular gaps |
| 15-minute history | Same lookup at `t - 15 minutes`, with the same five-minute maximum age. | Compatible, with eligibility loss for irregular gaps |
| 5-minute change | `current_glucose - glucose_5min_before`; no separate time normalization is applied. | Compatible |
| 10-minute change | `current_glucose - glucose_10min_before`; no separate time normalization is applied. | Compatible |
| 15-minute change | `current_glucose - glucose_15min_before`; no separate time normalization is applied. | Compatible |

Only glucose events from the same official test XML file may be used. Ohio training files, other participants, other years, future events, interpolation, imputation, and cross-file carry-forward are prohibited.

The model input order is the `MODEL_A_FEATURE_COLUMNS` order: current glucose, current age, the three historical values, then the three changes. The feature builder's internal output arrangement must not be used as an alternative positional order.

## Missingness, duplicates, and gaps

The inspected Ohio test glucose events had no missing timestamps or values and no duplicate timestamps. The data is nominally sampled every five minutes, but 1,027 intervals were not exactly five minutes and 511 intervals exceeded 10 minutes.

The evaluation adapter must:

- Parse and sort timestamps within each test file.
- Preserve and report malformed or nonnumeric events rather than silently repairing them.
- Treat duplicate timestamps as a quality issue. If duplicates conflict, the affected timestamp and dependent rows must be ineligible; no arbitrary selection is allowed.
- Reject historical features when the latest prior reading is more than five minutes old.
- Reject rows whose history crosses an adjacent gap over 10 minutes.
- Never interpolate or impute missing glucose values.
- Keep each XML file/year boundary separate.

## Target coverage and estimated eligibility

The following counts were determined read-only by applying the existing Manchester-style feature and target rules independently within each official test XML file. These are eligibility/count estimates only, not predictions or performance metrics.

| Quantity | Official Ohio test partition |
|---|---:|
| Test XML files | 12 |
| Distinct participant IDs | 12 |
| Glucose events | 31,743 |
| Rows with complete backward-looking feature history | 31,425 |
| Rows with known 30-minute target coverage before feature filtering | 31,107 |
| Eligible rows with all eight features and known target | **30,789** |
| Estimated positive eligible targets (`<70 mg/dL`, unit still unverified) | **1,236** |
| Estimated negative eligible targets | **29,553** |
| Missing endpoint coverage | 72 |
| Endpoint more than 10 minutes late | 443 |
| Future-path gaps over 10 minutes | 121 |
| Duplicate glucose timestamps | 0 observed |

The count audit used only `*/test/*.xml`, kept each file/year boundary isolated, used each event time as a candidate, and counted each event once. Historical lookup used only earlier-or-equal events in the same test file with the Manchester five-minute tolerance. For target coverage it selected the first valid reading at or after `t + 30 minutes`, allowed at most 10 minutes of lateness, rejected any adjacent path gap over 10 minutes, and evaluated positives only over readings strictly after `t` and no later than the exact `t + 30 minutes` endpoint. A late coverage reading was used to establish continuity but was not used to determine the label. These are counts only; no predictions or performance metrics were produced.

These counts must be regenerated by the eventual locked adapter as an audit artifact before inference, with row-level reasons retained. The counts do not use training-partition context.

## Participant and chronological boundaries

The official test partition has six files for 2018 and six for 2020. Participant IDs also occur in Ohio training directories within the same year. Therefore:

- The test-only restriction can be honored by reading only `*/test/*.xml`.
- The evaluation is not participant-independent with respect to the Ohio distributed split.
- A test file must not borrow history from its matching training file.
- A 2018 and 2020 file for an ID must not be merged unless a separately approved data specification establishes that boundary.
- Manchester's 16-fold LOPO result remains internal validation; Ohio test results must be reported separately as external-domain evaluation.

## Differences from Manchester that may affect evaluation

1. Manchester glucose is documented as mmol/L and was converted to mg/dL for model training; Ohio's XML has no explicit unit field, so unit confirmation is a blocker.
2. Ohio timestamps include seconds and show small sampling offsets; exact 5-minute positional indexing must not replace timestamp-based lookups.
3. Ohio is much more regular than Manchester, but still has test-file gaps over 10 minutes.
4. Ohio includes explicit `hypo_event` annotations; these are not equivalent to the threshold-derived Model A target.
5. Ohio's official train/test partitions reuse participant IDs, unlike a true unseen-participant external cohort.
6. Ohio XML files contain event sections beyond glucose, but Model A must remain glucose-only. Meal, insulin, and annotation fields must not enter the feature vector.

## What must happen before external evaluation

1. Record the published mg/dL evidence and conditional unit decision in the locked external-evaluation specification; seek direct dataset-author confirmation if available.
2. Implement a read-only Ohio test-only adapter that emits the exact eight features in the exact order above.
3. Validate that the adapter never reads `train` files and never crosses XML/year boundaries.
4. Preserve row-level exclusion reasons for missing history, late coverage, gaps, malformed values, and duplicates.
5. Run a schema/feature audit against the saved model metadata.
6. Only then load the unchanged Manchester-trained XGBoost artifact and generate external-test predictions and metrics in new, clearly labeled outputs.
