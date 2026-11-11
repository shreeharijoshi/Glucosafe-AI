# GlucoSafeAI ML Viva Preparation

## 1. Project in simple words

GlucoSafeAI estimates whether a person with Type 1 diabetes may have a hypoglycemia event soon. The first model uses recent glucose information only. It predicts whether a valid glucose value below 70 mg/dL will occur in the next 30 minutes.

This is a research prototype. It is not a clinical device and does not recommend insulin doses.

## 2. Problem statement and objective

Continuous glucose monitoring produces a time series. A single current glucose value may not show whether glucose is falling quickly. The ML objective is to use the current value, recent history, and glucose trends to estimate near-term hypoglycemia risk.

Model A answers:

> Given valid glucose history up to time `t`, is there a glucose value below 70 mg/dL in `(t, t + 30 minutes]`?

## 3. Dataset selection

### Training and internal evaluation

The model was trained using Manchester/T1D-UOM data because it was the primary project dataset and supported the documented Model A feature and target pipeline.

The final training data contained:

- 242,584 eligible observations.
- 16 participants.
- 8,804 positive targets.
- 233,780 negative targets.

### External evaluation

OhioT1DM was used for external testing. Only its official testing XML files were used. Ohio training files were not used for training, history, or evaluation.

Ohio external evaluation contained:

- 12 participants.
- 30,789 eligible observations.
- 1,236 positive observations.
- 29,553 negative observations.

The Ohio XML files do not directly declare glucose units. The evaluation treated values as mg/dL under a conditional decision supported by later publications.

## 4. Preprocessing and feature engineering

The final XGBoost model uses no scaling, imputation, or other preprocessing.

The feature builder:

- Uses only readings at or before prediction time `t`.
- Uses the latest valid reading available for each lookup.
- Uses a five-minute maximum age for the 5-, 10-, and 15-minute historical lookups.
- Does not interpolate across gaps.
- Does not fill missing values with zero.
- Rejects rows without complete model features.

The change features are calculated as:

```text
current glucose - historical glucose
```

## 5. Hypoglycemia target

The target is positive if at least one valid future glucose reading is strictly below 70 mg/dL.

The future interval is exactly:

```text
(t, t + 30 minutes]
```

Therefore:

- A reading exactly at `t` is excluded.
- A reading exactly at `t + 30 minutes` is included.
- A reading after `t + 30 minutes` cannot create the label.
- Insufficient future coverage produces an unknown target, not a negative target.
- Adjacent gaps over 10 minutes invalidate the target.

## 6. Model A input features

The model requires exactly these eight features, in this order:

1. `current_glucose_mg_dl` — current glucose in mg/dL.
2. `current_glucose_age_minutes` — age of the current glucose reading in minutes.
3. `glucose_5min_before_mg_dl` — historical glucose near five minutes before `t`.
4. `glucose_10min_before_mg_dl` — historical glucose near ten minutes before `t`.
5. `glucose_15min_before_mg_dl` — historical glucose near fifteen minutes before `t`.
6. `glucose_change_5min_mg_dl` — current glucose minus the five-minute value.
7. `glucose_change_10min_mg_dl` — current glucose minus the ten-minute value.
8. `glucose_change_15min_mg_dl` — current glucose minus the fifteen-minute value.

Model A does not use meal carbohydrates, protein, fat, or insulin dose.

## 7. Model comparison

All three models used the same eligible observations, target labels, features, threshold, and 16-fold LOPO protocol.

| Model | AP | ROC-AUC | Precision | Recall | Specificity | F1 |
|---|---:|---:|---:|---:|---:|---:|
| Logistic Regression | 0.690458 | 0.949951 | 0.750000 | 0.544752 | 0.994148 | 0.631168 |
| Random Forest | 0.643901 | 0.938373 | 0.373745 | 0.761245 | 0.951963 | 0.501346 |
| XGBoost | 0.766317 | 0.959966 | 0.850679 | 0.576556 | 0.996189 | 0.687293 |

## 8. Why XGBoost was selected

XGBoost had the best Average Precision, which was the primary selection metric. It also had the best ROC-AUC, precision, specificity, and F1-score.

Random Forest had higher recall than XGBoost, but it produced many more false positives and had lower precision and AP. Logistic Regression was a useful simpler baseline, but XGBoost ranked risk scores better overall.

The selection was based on measured results, not because XGBoost is newer.

## 9. LOPO cross-validation

LOPO means Leave-One-Participant-Out validation.

There were 16 participants and 16 folds. In each fold:

- One participant was held out for testing.
- All other participants were used for training.
- No participant appeared in both training and test data.

This is important because time-series rows from the same person are related. A random row split could place very similar observations from one participant in both sets and produce data leakage.

The final internal XGBoost results were:

- AP: 0.766317
- ROC-AUC: 0.959966
- Precision: 0.850679
- Recall: 0.576556
- Specificity: 0.996189
- F1-score: 0.687293

## 10. OhioT1DM external validation

The Manchester-trained final model was tested without retraining on OhioT1DM official test files.

Ohio results:

- AP: 0.875424
- ROC-AUC: 0.991105
- Precision: 0.863992
- Recall: 0.714401
- Specificity: 0.995297
- F1-score: 0.782108
- TP: 883
- TN: 29,414
- FP: 139
- FN: 353

These results show performance on this external sample. They do not prove clinical validity. The Ohio unit interpretation remains conditional because the original XML metadata does not explicitly declare units.

## 11. Metrics and interpretation

- **Average Precision (AP):** Summarizes precision-recall performance across thresholds. It is useful for imbalanced data.
- **ROC-AUC:** Measures how well positive cases are ranked above negative cases across thresholds.
- **Precision:** Of predicted positive cases, the fraction that was actually positive.
- **Recall:** Of actual positive cases, the fraction detected.
- **Specificity:** Of actual negative cases, the fraction correctly identified as negative.
- **F1-score:** Harmonic mean of precision and recall.
- **TP:** Correct positive predictions.
- **TN:** Correct negative predictions.
- **FP:** Negative cases incorrectly predicted as positive.
- **FN:** Positive cases missed by the model.

Accuracy was not used as the main metric because the negative class is much larger.

## 12. Inference and integration

The final artifact is:

```text
ML/models/model_a_xgboost_final.json
```

Its metadata is:

```text
ML/models/model_a_xgboost_final_metadata.json
```

The existing interface is:

```python
from src.models.xgboost_model import load_final_predictor

predictor = load_final_predictor("models")
result = predictor.predict({
    "current_glucose_mg_dl": 112.0,
    "current_glucose_age_minutes": 0.0,
    "glucose_5min_before_mg_dl": 118.0,
    "glucose_10min_before_mg_dl": 124.0,
    "glucose_15min_before_mg_dl": 129.0,
    "glucose_change_5min_mg_dl": -6.0,
    "glucose_change_10min_mg_dl": -12.0,
    "glucose_change_15min_mg_dl": -17.0,
})
```

The result contains:

```python
{
    "status": "success",
    "risk_probability": 0.0,
    "prediction": 0,
    "threshold": 0.5,
}
```

The predictor rejects missing keys, unexpected keys, non-numeric values, and non-finite values. It does not invent missing history.

## 13. Limitations and safety

- The dataset is observational.
- Rows are temporally dependent.
- Participant differences and dataset shift can affect results.
- Ohio has only 12 external participants.
- Ohio glucose units are supported by indirect published evidence, not direct XML metadata.
- The output is not demonstrated to be clinically calibrated.
- The target is not specifically meal-related.
- Model A does not use meal or insulin information.
- The model does not diagnose hypoglycemia.
- The model must not recommend insulin doses.
- The result is not a substitute for medical advice.

## 14. Two-minute ML pipeline explanation

> GlucoSafeAI uses machine learning to estimate near-term hypoglycemia risk for people with Type 1 diabetes. We selected Manchester/T1D-UOM as the training dataset and defined a positive target when a valid glucose reading below 70 mg/dL occurs strictly after the prediction time and up to 30 minutes later. Model A uses eight glucose-only features: the current glucose, its age, glucose values near 5, 10, and 15 minutes earlier, and the three changes from those historical values. We use only information available at or before the prediction time, and we do not interpolate or replace missing history with zero.
>
> We compared Logistic Regression, Random Forest, and XGBoost using the same data and a 16-fold Leave-One-Participant-Out protocol. LOPO holds out one complete participant in each fold, which prevents participant leakage. XGBoost was selected because it had the best Average Precision, 0.766317, and also the best ROC-AUC, precision, specificity, and F1-score in internal evaluation. We then tested the unchanged Manchester-trained model on only OhioT1DM official test files. The Ohio Average Precision was 0.875424, but this is external research evaluation, not clinical validation. During inference, the backend constructs the eight features, loads the saved model, and receives a probability and a thresholded prediction at 0.5. Invalid or incomplete inputs are rejected. The output must be treated as a research risk estimate, not a diagnosis or insulin-dosing recommendation.

## 15. Likely viva questions and answers

### 1. What is the main objective?

To estimate whether hypoglycemia may occur within the next 30 minutes using recent glucose history.

### 2. What does hypoglycemia mean in this project?

A valid glucose value strictly below 70 mg/dL.

### 3. Why is the interval written `(t, t + 30]`?

It excludes a reading exactly at the prediction time and includes a reading exactly at the 30-minute endpoint.

### 4. Why use glucose history instead of only current glucose?

The direction and speed of glucose change can indicate increasing risk.

### 5. What is Model A?

The glucose-only model. It uses eight current, historical, age, and change features.

### 6. Does Model A use carbohydrates?

No. Carbohydrates belong to the separate Model B design.

### 7. What preprocessing does the final model use?

None. The saved XGBoost model receives the eight numeric features directly.

### 8. What happens when historical data is missing?

The row is not eligible for the evaluated dataset. At inference, missing required features are rejected.

### 9. Why not replace missing values with zero?

Zero is not a valid general glucose-history value and would create false information.

### 10. Why is AP important?

The data is imbalanced, so AP focuses on the precision-recall trade-off for positive cases.

### 11. What does recall measure?

Recall measures how many actual positive cases the model detects.

### 12. What does specificity measure?

Specificity measures how many actual negative cases the model correctly rejects.

### 13. Why use LOPO instead of a random split?

Rows from one participant are related. LOPO tests whether the model generalizes to a participant not used for training in that fold.

### 14. How many LOPO folds were used?

Sixteen folds, one for each participant.

### 15. What was the best internal model?

XGBoost, with AP 0.766317.

### 16. Why was Random Forest not selected?

It had higher recall, but lower AP, precision, specificity, ROC-AUC, and F1-score than XGBoost.

### 17. Was XGBoost tuned extensively?

No. A fixed, sensible baseline configuration was used.

### 18. What is the prediction threshold?

0.5. A probability greater than or equal to 0.5 produces prediction `1`.

### 19. What did Ohio external validation test?

It tested the unchanged Manchester-trained model on only OhioT1DM official testing files.

### 20. Was Ohio data used for training?

No. Ohio data was not used for training, tuning, calibration, or threshold selection.

### 21. What does the prediction probability mean?

It is the model's estimated risk score. It is not proven to be a clinically calibrated probability.

### 22. What does the predictor return?

It returns status, risk probability, binary prediction, and threshold.

### 23. What errors can the predictor raise?

It can reject a non-mapping input, missing features, extra features, non-numeric values, or non-finite values.

### 24. Can this model recommend insulin?

No. It is not designed or approved for treatment recommendations.

### 25. What must the backend do?

The backend must collect valid glucose history, construct the eight features without future information, validate the input, call the predictor, and display the result with appropriate safety disclaimers.

## 16. Five challenging examiner questions

### Challenge 1: Could the high performance be caused by leakage?

The evaluation reduced participant leakage by using LOPO. Each held-out participant was excluded from that fold's training data. Historical features used only data at or before prediction time. However, overlapping time windows are still temporally dependent, so results must not be interpreted as fully independent row-level experiments.

### Challenge 2: Why can a late future reading help coverage but not determine the label?

A late reading can show that the recording continues and help assess whether a gap is acceptable. But a reading after the exact 30-minute endpoint must not create a positive label, because that would change the defined prediction horizon.

### Challenge 3: Why can external performance be higher than internal performance?

The Ohio sample may have different participant patterns, class balance, data quality, or recording characteristics. A higher external score does not prove that the model is universally better. It may also reflect sampling variation and dataset differences.

### Challenge 4: Is an Average Precision of 0.766 a 76.6% chance of hypoglycemia?

No. AP is a ranking and precision-recall summary across thresholds. It is not a calibration statement. The individual XGBoost risk output has not been demonstrated to be clinically calibrated.

### Challenge 5: What would be required before clinical use?

Independent validation on larger and representative populations, verified units and data quality, calibration analysis, prospective evaluation, safety review, clinical oversight, and regulatory assessment would be required. The current research prototype is not sufficient.
