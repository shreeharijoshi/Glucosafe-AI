# Model A Model Comparison

Exploratory research results only; not clinical validation.

## Evaluation scope and comparability

- Participants: 16
- Eligible observations / pooled out-of-fold predictions: 242584
- LOPO folds: 16
- XGBoost version: 3.4.1
- Dataset, target definition, feature allowlist, eligibility rules, threshold, and LOPO manifest were reused unchanged.
- Same keyed observations and targets across all models: yes
- Same fold assignments across all models: yes
- Threshold 0.5 applied consistently: yes
- Participant-level leakage detected in manifest/evaluations: no

## Pooled out-of-fold comparison

| Model | AP | ROC-AUC | Precision | Recall | Specificity | F1-score | TP | TN | FP | FN |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Logistic Regression | 0.702349 | 0.956123 | 0.859681 | 0.478078 | 0.997061 | 0.614453 | 4209 | 233093 | 687 | 4595 |
| Random Forest | 0.643901 | 0.938373 | 0.373745 | 0.761245 | 0.951963 | 0.501346 | 6702 | 222550 | 11230 | 2102 |
| XGBoost | 0.766317 | 0.959966 | 0.850679 | 0.576556 | 0.996189 | 0.687293 | 5076 | 232889 | 891 | 3728 |

## Recommendation

**Recommended model: XGBoost.** It achieved the highest pooled Average Precision (0.766317), the primary metric for this imbalanced target.

- **Logistic Regression** has lower recall (0.478078) but the highest precision among the three (0.859681) and the fewest false positives.
- **Random Forest** has the highest recall (0.761245) but substantially lower precision and specificity, producing many more false positives.
- **XGBoost** provides the best AP, ROC-AUC, and F1-score, while retaining high precision and specificity. Its recall is higher than Logistic Regression and lower than Random Forest.

The recommendation is based on the fixed baseline configurations and this single participant-level evaluation; no hyperparameter tuning was performed.
