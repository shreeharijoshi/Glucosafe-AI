# External-Validation Dataset Audit

Read-only structural audit for the finalized GlucoSafeAI Model A XGBoost input contract. No datasets, code, existing reports, or evaluation outputs were modified. No model was trained, no split was created, and no new performance metrics were calculated.

## Dataset availability

| Dataset | Local location | Relevant files |
|---|---|---|
| Manchester / T1D-UOM | `Datasets/ManchesterCSCoordinatedDiabetesStudy-V1.0.1/sharpic-ManchesterCSCoordinatedDiabetesStudy-a9e8025` | `Glucose Data/UoMGlucose*.csv`, `Nutrition Data/UoMNutrition*.csv`, insulin/activity/sleep folders, local `README.md` |
| OhioT1DM | `Datasets/OhioT1DM/OhioT1DM` | `2018/{train,test}/*.xml`, `2020/{train,test}/*.xml` |
| HUPA-UCM | `Datasets/HUPA-UCM Diabetes Dataset/HUPA-UCM Diabetes Dataset` | `Preprocessed/HUPA####P.csv`, raw per-participant device folders |

Archives are also present under `Datasets/` for all three datasets.

## Structure and data quality

| Dataset | Participants / files | Glucose data and units | Sampling/timestamps | Missingness and quality |
|---|---:|---|---|---|
| Manchester / T1D-UOM | 17 glucose files; 17 participant IDs | 356,146 rows; `bg_ts,value`; documentation states mmol/L | Nominally 5 minutes; CSV timestamps are day-first-looking `DD/MM/YYYY HH:MM`, while README documents `MM/DD/YYYY HH:MM:SS`; timestamps are timezone-naive | No missing glucose cells or invalid timestamps in the audit; 15,915 duplicate timestamps and 66,446 intervals over 10 minutes. Nutrition: 15 files, 4,351 rows, 1,290 missing cells and 4 invalid timestamps. |
| OhioT1DM | 12 distinct participant IDs across 24 XML files | 166,533 `<glucose_level><event>` rows; values are mg/dL-compatible and XML has no separate unit field | Nominally 5 minutes; timestamps include seconds, e.g. `19-05-2027 11:36:29`; timestamps are timezone-naive | No missing/duplicate glucose timestamps observed; 1,027 non-5-minute intervals and 511 intervals over 10 minutes. |
| HUPA-UCM | 25 preprocessed participant CSVs | 309,392 rows; semicolon schema includes `time;glucose;...`; values are numerically mg/dL-compatible, but local unit/provenance confirmation is unresolved | Regular 5-minute ISO-like timestamps, timezone-naive/unspecified | No missing cells in the 25 preprocessed files and no intervals over 10 minutes. Zero values and possible carry-forward/preprocessing provenance remain unresolved. |

### Partitions

- **Manchester:** no official `train`/`test` directories or participant-independent split were found in the extracted dataset. The README reports 16 individuals, while the extracted glucose tree contains 17 participant files/IDs; this discrepancy requires resolution.
- **OhioT1DM:** has `2018/train`, `2018/test`, `2020/train`, and `2020/test`, six XML files per partition. The same participant IDs occur in train and test within each year, so this is not participant-independent.
- **HUPA-UCM:** no official train/test partition was found. The preprocessed data is organized by participant file.

## Compatibility with the finalized Model A contract

Required features:

`current_glucose_mg_dl`, `current_glucose_age_minutes`, `glucose_5min_before_mg_dl`, `glucose_10min_before_mg_dl`, `glucose_15min_before_mg_dl`, `glucose_change_5min_mg_dl`, `glucose_change_10min_mg_dl`, `glucose_change_15min_mg_dl`.

Target: a valid glucose value below 70 mg/dL in the strict future interval `(t, t + 30 minutes]`, with the established coverage and gap rules.

| Dataset | Feature compatibility | Target compatibility | Assessment |
|---|---|---|---|
| Manchester / T1D-UOM | **Conditional.** All required historical timestamps exist, but mmol/L must be converted to mg/dL using the documented conversion and timestamp interpretation must be resolved. | **Conditional.** Future windows can be constructed, but duplicate timestamps, long gaps, and ambiguous timestamp parsing require explicit rules; do not label across disallowed gaps. | Suitable for external testing only after unit conversion and timestamp/duplicate policy are locked. |
| OhioT1DM | **Yes, with gap filtering.** XML glucose events provide current and 5/10/15-minute historical observations; exact offsets must use the existing tolerance/age rules. | **Yes, with gap filtering.** Values support the `<70 mg/dL` threshold and strict 30-minute future interval. Explicit `hypo_event` annotations are a separate signal, not a substitute for the threshold target. | Technically suitable for independent testing only after regrouping all records by participant. |
| HUPA-UCM | **Conditional.** Regular 5-minute data supports all eight features if the glucose unit is confirmed and the preprocessed values are accepted as valid observations. | **Conditional.** Dense timestamps support the strict future target, but unit and preprocessing provenance must be confirmed first. | Promising for external testing after unit/provenance confirmation; no official split is available. |

No dataset should be passed directly to the saved model without applying the same unit normalization, timestamp partitioning, gap handling, and missing-feature rejection used by the finalized Model A pipeline.

## Suitability for independent/external testing

- **Manchester / T1D-UOM:** suitable as the primary external dataset after resolving documented timestamp-format and participant/file-count inconsistencies, converting mmol/L to mg/dL, and applying duplicate/gap-aware target construction. No official participant-independent split was identified.
- **OhioT1DM:** suitable for external testing after creating a future, documented participant-level split. The distributed train/test folders must not be used as evidence of unseen-participant generalization.
- **HUPA-UCM:** potentially suitable for external testing because participant files are naturally separable and the preprocessed grid is regular, but unit and preprocessing provenance are unresolved. No official split was identified.

## Relevant documentation

- Manchester: `Datasets/ManchesterCSCoordinatedDiabetesStudy-V1.0.1/.../README.md`
- Existing cross-dataset audit: `Prac/dataset_audit_report.md`
- Existing feasibility audit: `Prac/dataset_feasibility_report.md`
- Project dataset assessment: `ML/docs/DATASET_ASSESSMENT.md`
- Manchester timestamp/specification notes: `ML/docs/MANCHESTER_TIMESTAMP_AND_ID_VALIDATION.md` and `ML/docs/MANCHESTER_TRAINING_DATA_SPEC.md`
- Ohio inspection scripts: `Prac/OhioT1DM_prac/inspect_OhioT1DM.py`, `check_data_quality.py`, and `build_training_data.py`
- HUPA and Ohio source papers are in `Papers/`; no standalone documentation file was found inside their extracted dataset roots.

## Recommended next steps

1. Lock dataset-specific unit and timestamp normalization rules before inference.
2. Resolve Manchester’s timestamp-format and participant/file-count discrepancies with source documentation.
3. Confirm HUPA-UCM glucose units and whether zero/carry-forward values represent measurements or preprocessing artifacts.
4. Implement a read-only, participant-aware adapter that emits exactly the eight Model A features and rejects unresolved rows.
5. Create a new participant-level split only as a separate, documented testing step; do not reuse Ohio’s supplied train/test folders for unseen-person claims.
6. Keep threshold-derived targets separate from Ohio’s explicit `hypo_event` annotations.
