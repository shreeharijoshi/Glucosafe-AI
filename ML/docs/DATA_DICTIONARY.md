# Preliminary Data Dictionary

This is a conceptual dictionary, not a claim that the datasets share a schema.

## Standardized conceptual fields

| Field | Meaning | Expected unit | Required |
|---|---|---|---|
| `participant_id` | Person/group identifier used for all splits | Identifier | Required |
| `timestamp` | Time of the glucose observation or event | Dataset-specific timezone/format | Required |
| `glucose` | Glucose observation | mg/dL after verified conversion | Required |
| `current_meal_carbohydrates` | Carbohydrates for one recently consumed meal, if available at prediction time | grams, if verified | Required only for Model B |
| `recent_glucose_history` | Past observations available at prediction time | mg/dL | Model features |
| `glucose_trend` | Trend derived only from past valid observations | mg/dL per time interval | Optional |
| `target_30m` | Any valid glucose below 70 mg/dL in `(t, t + 30 minutes]` | Boolean | Derived |
| `target_status` | Positive, negative, or unknown under the coverage policy | Label status | Derived |

## Dataset-specific raw fields

### HUPA-UCM

`time`, `glucose`, `calories`, `heart_rate`, `steps`, `basal_rate`, `bolus_volume_delivered`, and `carb_input` appear in the preprocessed files. Units and whether values are measured, interpolated, carried forward, or zero-filled are not fully established.

### Manchester / T1D-UOM

Glucose uses `bg_ts,value`. Nutrition uses `meal_ts,meal_type,meal_tag,carbs_g,prot_g,fat_g,fibre_g`. Insulin uses dataset-specific basal and bolus timestamp/dose fields. Timestamp formats and malformed rows require validation.

### OhioT1DM

XML sections include `glucose_level`, `meal`, `basal`, `temp_basal`, `bolus`, and `hypo_event`. Meal events expose `ts`, `type`, and `carbs`; insulin attributes differ by event type.

## Missing values and timestamps

Missing carbohydrates are not zero by default. A recorded meal timestamp must not automatically be treated as consumption time. Invalid timestamps, duplicate timestamps, long gaps, and uncertain units must be retained in audit metadata and handled by a declared policy. No interpolation should invent glucose observations or labels.
