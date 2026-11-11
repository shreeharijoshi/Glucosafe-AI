# Dataset Assessment

This assessment summarizes the existing files under `Prac/` and the extracted source trees. It records preliminary audit facts and unresolved issues; it does not select a final dataset.

## HUPA-UCM

The preprocessed directory contains 25 participant CSV files and a semicolon-delimited synchronized schema with `time`, `glucose`, `calories`, `heart_rate`, `steps`, `basal_rate`, `bolus_volume_delivered`, and `carb_input`. The prior audit measured 309,392 rows with a regular five-minute pattern and no missing cells in those preprocessed files. Raw files contain mg/dL-labelled fields, but the unit and transformation/provenance of every preprocessed glucose value are not fully confirmed locally.

Carbohydrate information is a synchronized `carb_input` signal rather than a clearly documented meal-event table. Its units, event semantics, zero meaning, and before/after-eating timing remain unresolved. Separate protein, fat, and fibre fields are absent.

HUPA is attractive for a glucose-only regular-grid baseline and participant-grouped evaluation, but its target counts remain provisional until units and preprocessing provenance are confirmed.

## Manchester / T1D-UOM

The extracted tree contains 17 glucose files, 15 nutrition files, 14 basal files, and 16 bolus files. Glucose is documented as mmol/L and is nominally sampled every five minutes, but the prior audit found 15,915 duplicate timestamps and 66,446 gaps over ten minutes. Nutrition contains meal timestamps, type/tag, carbohydrates, protein, fat, and fibre, with missing fields and invalid timestamps.

Manchester is the strongest candidate for a current-meal carbohydrate experiment because it exposes meal timestamps and an explicit carbohydrate field. Its timestamp-format discrepancy, participant/file coverage differences, duplicate glucose rows, missing values, and malformed schemas require resolution. The dataset does not establish whether a meal record represents a planned meal or a post-consumption record.

For the current recently-consumed-meal scope, `meal_ts` is evidence of a recorded meal time, not proof of consumption time. A recorded-meal window can be used only as an exploratory proxy, with multiple eligible meals and missing carbohydrates handled explicitly.

## OhioT1DM

OhioT1DM contains 24 XML files but only 12 distinct participant IDs, with train and test files for the same people. It provides five-minute glucose events, meal timestamps/types/carbohydrates, basal, temporary basal, bolus, and explicit `hypo_event` sections. Meals do not provide protein, fat, or fibre.

Ohio is convenient for an event-based carbohydrate experiment and has relatively explicit XML conventions, but the supplied split is not participant-independent. A new split by complete participant ID is required. It is less suitable for claiming broad unseen-person generalization because only 12 people are available.

The XML `meal/@ts` field is also a recorded event timestamp; local documentation does not prove that it is the time food was consumed.

## Selection status

No final dataset has been selected. The decision depends on confirming HUPA units/provenance, resolving Manchester timestamp and alignment rules, deciding whether the application meal is pre-meal or post-meal, and inspecting participant-level target balance under the corrected target definition.
