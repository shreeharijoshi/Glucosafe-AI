# GlucoSafeAI Model A Backend Integration Handoff

## 1. Model information

### Final model

- **Name:** GlucoSafeAI Model A final XGBoost classifier.
- **Model type:** `XGBClassifier`.
- **Artifact:** [`../models/model_a_xgboost_final.json`](../models/model_a_xgboost_final.json)
- **Metadata:** [`../models/model_a_xgboost_final_metadata.json`](../models/model_a_xgboost_final_metadata.json)
- **XGBoost version:** `3.4.1`
- **Preprocessing:** None.
- **Decision threshold:** `0.5`.

The model was trained on the eligible Manchester/T1D-UOM Model A dataset:

- 242,584 eligible observations.
- 16 participants.
- 8,804 positive targets.
- 233,780 negative targets.

The training configuration was fixed. It used binary logistic loss, 200 estimators, maximum depth 4, learning rate 0.05, 0.8 row subsampling, 0.8 column subsampling, and random state 42.

### Internal evaluation

The 16-fold participant-level LOPO evaluation produced:

| Metric | Result |
|---|---:|
| Average Precision | 0.766317 |
| ROC-AUC | 0.959966 |
| Precision | 0.850679 |
| Recall | 0.576556 |
| Specificity | 0.996189 |
| F1-score | 0.687293 |

### OhioT1DM external evaluation

The external evaluation used only the 12 official OhioT1DM testing participants:

- 30,789 eligible observations.
- 1,236 positive observations.
- 29,553 negative observations.

| Metric | Result |
|---|---:|
| Average Precision | 0.875424 |
| ROC-AUC | 0.991105 |
| Precision | 0.863992 |
| Recall | 0.714401 |
| Specificity | 0.995297 |
| F1-score | 0.782108 |

Ohio glucose values were interpreted as mg/dL under a conditional evidence decision. The original XML files do not declare units directly.

## 2. Exact input contract

The predictor requires exactly these eight keys, in this order:

| Order | Feature | Unit | Meaning |
|---:|---|---|---|
| 1 | `current_glucose_mg_dl` | mg/dL | The latest valid glucose value available at or before prediction time `t`. |
| 2 | `current_glucose_age_minutes` | minutes | The age of that current glucose observation at prediction time. |
| 3 | `glucose_5min_before_mg_dl` | mg/dL | The latest valid glucose observation for the 5-minute historical lookup. |
| 4 | `glucose_10min_before_mg_dl` | mg/dL | The latest valid glucose observation for the 10-minute historical lookup. |
| 5 | `glucose_15min_before_mg_dl` | mg/dL | The latest valid glucose observation for the 15-minute historical lookup. |
| 6 | `glucose_change_5min_mg_dl` | mg/dL | Current glucose minus the 5-minute historical glucose. |
| 7 | `glucose_change_10min_mg_dl` | mg/dL | Current glucose minus the 10-minute historical glucose. |
| 8 | `glucose_change_15min_mg_dl` | mg/dL | Current glucose minus the 15-minute historical glucose. |

Historical lookups use only observations available at or before `t`. The 5-, 10-, and 15-minute lookups use the existing five-minute maximum-age tolerance. The feature builder does not interpolate, average, zero-fill, or use future glucose.

The backend or upstream feature service must construct these features with the same rules. The predictor accepts features only. It does not construct glucose history.

The target used during evaluation was whether any valid glucose reading was strictly below 70 mg/dL in the interval:

```text
(t, t + 30 minutes]
```

The target definition is not an inference-time input.

## 3. Python prediction interface

The existing implementation is in [`../src/models/xgboost_model.py`](../src/models/xgboost_model.py).

Import and load the predictor with:

```python
from src.models.xgboost_model import load_final_predictor

predictor = load_final_predictor("models")
```

When running from the `ML` directory, `"models"` resolves to the existing model artifact directory.

### Minimal example

```python
from src.models.xgboost_model import load_final_predictor

predictor = load_final_predictor("models")

features = {
    "current_glucose_mg_dl": 112.0,
    "current_glucose_age_minutes": 0.0,
    "glucose_5min_before_mg_dl": 118.0,
    "glucose_10min_before_mg_dl": 124.0,
    "glucose_15min_before_mg_dl": 129.0,
    "glucose_change_5min_mg_dl": -6.0,
    "glucose_change_10min_mg_dl": -12.0,
    "glucose_change_15min_mg_dl": -17.0,
}

result = predictor.predict(features)
print(result)
```

The example values are only a shape example. They must be replaced with valid, measured, or correctly derived values. Do not use fabricated history in production.

## 4. Input validation and error handling

`load_final_predictor(artifact_dir)` loads both the JSON model artifact and its metadata. Loading errors are raised by the underlying file or model loader and must be surfaced by the backend.

`predict(features)` requires a mapping.

The predictor raises:

- `TypeError` if `features` is not a mapping.
- `ValueError` if a required feature is missing.
- `ValueError` if an unexpected feature is supplied.
- `ValueError` if a feature is non-numeric or non-finite.
- The underlying model exception if prediction cannot be performed.

The predictor performs no imputation. Missing history must be handled before calling the predictor. If the required historical features cannot be constructed, the backend must return an explicit validation or insufficient-history response. It must not substitute zero, a default, an interpolated value, or a fabricated reading.

## 5. Prediction output

For valid input, the predictor returns:

```python
{
    "status": "success",
    "risk_probability": 0.0,  # float in the model's probability output range
    "prediction": 0,           # 0 or 1 using probability >= 0.5
    "threshold": 0.5,
}
```

The binary prediction is `1` when the risk probability is greater than or equal to `0.5`. Otherwise it is `0`.

The output is a research risk estimate. It is not a diagnosis.

## 6. Limitations and medical disclaimer

- Model A uses glucose-derived features only.
- Meal carbohydrates, protein, fat, and insulin dose are not model inputs.
- The prediction concerns hypoglycemia within the next 30 minutes after prediction time. It is not specifically a post-meal prediction.
- XGBoost output has not been demonstrated to be clinically calibrated.
- Internal and external evaluation results do not establish clinical validity.
- The Ohio unit interpretation is supported by subsequent publications, not direct original XML unit metadata.
- Dataset shift can affect performance.
- The Ohio external evaluation used only 12 participants.
- This model is not a substitute for medical advice.
- This model must not be used to recommend insulin doses or other treatment.

## 7. Backend integration guidance

### ML component responsibilities

The ML component should:

1. Load the unchanged model and metadata.
2. Enforce the exact feature names and order.
3. Reject missing, unexpected, non-numeric, and non-finite values.
4. Return the risk probability, thresholded prediction, threshold, and success status.
5. Keep model loading and prediction separate from API routing.

### Backend responsibilities

The backend should:

1. Obtain the user's authorized glucose history.
2. Validate timestamps, units, participant context, and data quality.
3. Construct the eight features using the documented historical lookup rules.
4. Reject requests with insufficient history or invalid feature construction.
5. Pass exactly the eight feature keys to `predictor.predict`.
6. Handle predictor exceptions without converting them into successful predictions.
7. Record model version and prediction time for application traceability.
8. Apply authentication, authorization, request validation, and operational logging.
9. Avoid sending meal or insulin fields to this Model A predictor as model inputs.

### Inputs the backend must obtain or calculate

The backend must obtain or calculate:

- Current glucose in mg/dL.
- The timestamp age of the current glucose.
- Valid historical glucose values for the 5-, 10-, and 15-minute lookups.
- The three current-minus-historical glucose changes.
- A prediction timestamp and the source-data context needed to verify that no future value was used.

If any required value is unavailable, the backend must return an explicit inability-to-predict response.

### Frontend information

The frontend may display:

- A risk probability labeled as a model estimate.
- The thresholded risk status.
- The prediction timestamp.
- The model or evaluation disclaimer.
- An insufficient-history or invalid-data status when prediction is unavailable.

The frontend should not display the result as a diagnosis, guarantee, or insulin-dosing instruction.

No FastAPI endpoint is implemented by this handoff. API routing remains a backend responsibility.
