# HUPA-UCM Model B Feasibility

## 1. Executive conclusion

HUPA-UCM is a reasonable candidate for glucose-only Model A, but the local evidence does not currently establish a defensible recent-meal carbohydrate feature for Model B.

The preprocessed files contain a sparse, synchronized `carb_input` column on the same five-minute grid as glucose. In the representative files inspected, nonzero values occur at isolated timestamps and are followed by zero at the adjacent grid points. This is compatible with an instantaneous logged input, but it does not prove that each nonzero value is one meal, that its unit is grams, or that its timestamp is consumption time.

The raw HUPA-UCM export contains a Spanish `Hidratos de Carbono` field and meal-context labels such as `Antes Desayuno`, `Despues Comida`, and `Antes Cena`. This provides evidence that carbohydrate-related meal records exist, but the local extracted dataset does not include documentation that defines the field's unit or explains how those records were transformed into the preprocessed `carb_input` series. Therefore, HUPA should not be used for the main Model B experiment until those points are confirmed.

**Recommendation:** **Potentially suitable, pending specific clarification.** HUPA is suitable for Model A now subject to the glucose-unit/provenance caveats below. Manchester/T1D-UOM remains the stronger current candidate for Model B because its nutrition files expose an explicit meal timestamp and `carbs_g` field, even though its timestamps and data quality still require validation.

## 2. Documented meaning and units of `carb_input`

### Documented locally

- The preprocessed HUPA schema is:
  `time;glucose;calories;heart_rate;steps;basal_rate;bolus_volume_delivered;carb_input`.
- The preprocessed representation is a synchronized time series, not a separate meal-event table.
- The raw pump/glucometer export includes the field `Hidratos de Carbono` (“carbohydrates”) and meal-context text in `Hito`.
- Raw glucose rows inspected in the pump export explicitly label glucose as `mg/dL`.
- The existing audit found 25 preprocessed participant files and a regular five-minute pattern.

### Not documented or not established locally

- No local HUPA documentation inspected defines the unit of `carb_input` or `Hidratos de Carbono`. The values must not be called grams based only on the field name or their numeric ranges.
- The local files do not define whether `carb_input` is a meal carbohydrate amount, an insulin-calculator input, a normalized value, or another derived signal.
- The local files do not state whether zero means no carbohydrate event, missing/unrecorded carbohydrate, or a preprocessing fill value. Missing carbohydrate cannot safely be treated as zero.
- The local files do not document whether preprocessed values are measured, copied forward, interpolated, aggregated, or otherwise transformed.
- The local files do not establish whether an event timestamp is consumption time, logging time, bolus-calculation time, or another device timestamp.

The existing `ML/docs/DATA_DICTIONARY.md` and `ML/docs/DATASET_ASSESSMENT.md` correctly treat these points as unresolved.

## 3. Evidence from representative records inspected

Only two preprocessed participant files and one raw participant export were inspected:

- `Datasets/HUPA-UCM Diabetes Dataset/HUPA-UCM Diabetes Dataset/Preprocessed/HUPA0001P.csv`
- `Datasets/HUPA-UCM Diabetes Dataset/HUPA-UCM Diabetes Dataset/Preprocessed/HUPA0002P.csv`
- `Datasets/HUPA-UCM Diabetes Dataset/HUPA-UCM Diabetes Dataset/Raw_Data/HUPA0002P/roche_insulin_pump/HUPA0002P_roche_insulin_pump_glucometer_2018-06-11_2018-06-28.csv`

### Preprocessed HUPA0001P

- 4,096 five-minute rows were read.
- 40 rows had nonzero `carb_input`.
- The first inspected nonzero records were `4` at `2018-06-13T21:50:00`, `3` at `2018-06-14T10:10:00`, and `4` at `2018-06-14T14:40:00`.
- No inspected nonzero record had a nonzero value on the immediately preceding or following five-minute row.
- Values in this file ranged from `0.5` to `4.0` among the nonzero records.

### Preprocessed HUPA0002P

- 3,181 five-minute rows were read.
- 12 rows had nonzero `carb_input`.
- The first inspected nonzero records included `90` at `2018-06-14T13:55:00`, `45` at `2018-06-14T22:55:00`, and `79` at `2018-06-15T13:55:00`.
- No inspected nonzero record had a nonzero value on the immediately preceding or following five-minute row.
- Values in this file ranged from `5` to `103` among the nonzero records.

These files support only the narrower observation that `carb_input` is sparse and non-persistent in the inspected examples. The large difference in value ranges between the two participants is another reason not to infer units or semantics from the values.

### Raw HUPA0002P export

The raw header contains `Hidratos de Carbono`, but no unit is included in that header. Representative rows include:

- `28/06/2018 09:21`, `Antes Desayuno`, glucose `201 mg/dL`, carbohydrate field `10`.
- `27/06/2018 17:33`, `Despues Comida`, glucose `161 mg/dL`, carbohydrate field `120`.
- `26/06/2018 22:58`, `Despues Cena`, glucose `134 mg/dL`, carbohydrate field `80`.

These rows show that the raw export can associate a carbohydrate entry with a recorded meal-context label. They do not establish that the entry is a consumed-meal amount, that it is in grams, or that it maps one-to-one to the preprocessed `carb_input` value.

## 4. Meal-event and timestamp limitations

The preprocessed HUPA files do not expose a meal ID, meal type, event category, or separate meal table. A nonzero `carb_input` timestamp could be used as a recorded input timestamp only after its provenance and availability semantics are confirmed.

The raw export is more informative than the preprocessed column because it includes meal-context labels and a carbohydrate field. However:

1. `Antes` and `Despues` indicate a recorded context around a named meal; they do not prove the exact food-consumption time.
2. The raw carbohydrate field has no unit in the inspected header.
3. The transformation from raw records to the five-minute synchronized `carb_input` signal is undocumented locally.
4. Without a documented zero/missing policy, zero-valued grid points cannot distinguish “no meal” from “no recorded carbohydrate.”
5. An isolated nonzero grid value avoids obvious repeated counting in the two samples, but this is not enough to define a general event extraction rule or to prove that separate meals are always distinguishable.

Consequently, a Model B feature based on “carbohydrates from a recently consumed meal” would currently require undocumented assumptions about unit, event identity, timing, and missingness.

## 5. Suitability for Model A

HUPA remains a reasonable Model A candidate:

- The existing audit found 25 participant-level preprocessed CSV files.
- The preprocessed data uses a synchronized five-minute pattern and had no missing cells in the audited files.
- Participant files provide a natural basis for participant-grouped splits.
- The dense grid is useful for constructing a 30-minute future window, subject to the declared coverage policy.

Important limitations remain:

- Local raw records label glucose as `mg/dL`, but the unit and preprocessing provenance of every preprocessed glucose value are not fully confirmed.
- The local evidence does not establish whether all preprocessed glucose values are measured or whether any are interpolated or carried forward.
- A regular grid does not by itself prove measurement continuity or clinical validity.

Model A should therefore use the preprocessed glucose data only with explicit provenance and unit validation, participant-level splitting, and the existing leakage-safe target rules.

## 6. Comparison with Manchester for Model B

Manchester/T1D-UOM is currently the stronger candidate for a current-meal carbohydrate experiment because its nutrition records expose:

- `meal_ts`, an explicit nutrition-record timestamp;
- `carbs_g`, an explicitly named carbohydrate field;
- meal type and meal tag;
- additional protein, fat, and fibre fields.

Those fields still do not prove that `meal_ts` is food-consumption time, and Manchester has substantial known limitations: duplicate glucose timestamps, long gaps, malformed or ambiguous timestamps, missing nutrition fields, and unequal modality coverage. It therefore needs a documented cleaning and alignment policy before training.

The comparison is not a claim that Manchester is ready for production or clinical use. It is only that Manchester currently supplies a more explicit meal-event schema for Model B, while HUPA's preprocessed carbohydrate signal lacks documented unit and event semantics.

## 7. Final recommendation and unresolved questions

**Potentially suitable, pending specific clarification.**

Use HUPA for Model A feasibility work, but do not make HUPA the main Model B dataset yet. Before using HUPA for Model B, obtain evidence that resolves all of the following:

1. What unit is used by the raw `Hidratos de Carbono` field and by preprocessed `carb_input`?
2. Is `carb_input` a single meal/input event, and how is it generated from raw records?
3. Does a nonzero value represent an amount entered once, or can it be repeated/aggregated across synchronized rows?
4. What exactly does zero mean, and is missing/unrecorded carbohydrate distinguishable?
5. Which timestamp represents the feature's availability: consumption, logging, meal context, bolus calculation, or another event?
6. Can each preprocessed nonzero value be linked to one raw meal record and a unique participant-level event?
7. Are preprocessed glucose values measured or transformed, and are their units definitively documented?

Until these questions are answered, HUPA carbohydrate values may be used for a separate data-audit investigation, but not as a defensible “recently consumed meal carbohydrates” feature in the primary Model B comparison.
