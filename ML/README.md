# GlucoSafeAI Machine-Learning Contribution

GlucoSafeAI is a student Engineering, Design and Innovation research prototype for near-term hypoglycemia-risk prediction in Type 1 diabetes. This folder is the self-contained ML contribution for review and backend integration.

## Current deliverable

The selected Model A predictor is a Manchester/T1D-UOM-trained XGBoost classifier. It estimates whether a valid glucose observation strictly below **70 mg/dL** occurs in:

```text
(t, t + 30 minutes]
```

The final model uses glucose history only. It does not use meal, insulin, protein, or fat inputs.

Included:

- Validated data loading, unit conversion, feature engineering, and target construction.
- Logistic Regression, Random Forest, and XGBoost evaluation implementations.
- Participant-level LOPO evaluation and OhioT1DM test-only external evaluation code.
- Final XGBoost model and metadata.
- Evaluation reports and prediction results.
- Tests, configuration, dependency requirements, and backend handoff documentation.

The model is a research prototype. It is not clinically validated and must not provide diagnoses or insulin-dosing recommendations.

## Directory guide

| Path | Purpose |
|---|---|
| `src/data/` | Manchester/T1D-UOM data loading and validation |
| `src/features/` | Historical glucose feature construction |
| `src/targets/` | Strict 30-minute target construction |
| `src/integration/` | Model A and Model B dataset integration |
| `src/evaluation/` | Baselines, LOPO, model comparison, and Ohio evaluation |
| `src/models/` | Final XGBoost training and inference interface |
| `models/` | Final model artifact and metadata |
| `outputs/` | Evaluation datasets, predictions, and metric reports |
| `docs/` | Methodology, limitations, viva preparation, and backend handoff |
| `tests/` | Automated unit and integration tests |
| `configs/` | Reproducibility and baseline configuration |

## External datasets

Original datasets are not included in this folder. Keep them read-only at the repository-level location:

```text
EDI\Datasets\
```

Expected dataset roots:

```text
..\Datasets\ManchesterCSCoordinatedDiabetesStudy-V1.0.1\
..\Datasets\OhioT1DM\
..\Datasets\HUPA-UCM Diabetes Dataset\
```

The final Model A artifact and inference interface do not require loading raw data. Evaluation and retraining scripts require the relevant dataset paths as function arguments or the documented working directory.

Do not copy raw datasets into `ML/`. Confirm that redistribution is permitted before sharing any dataset outside its original location.

## Setup

Use Python 3.14 or a compatible supported Python environment. From the repository root:

```powershell
& ".\.venv\Scripts\python.exe" -m pip install -r "ML\requirements.txt"
```

The direct dependencies are pinned in [`requirements.txt`](requirements.txt):

- NumPy
- pandas
- scikit-learn
- matplotlib
- pytest
- XGBoost

## Tests

Run the existing test suite from the `ML` directory:

```powershell
cd ML
& "..\.venv\Scripts\python.exe" -m pytest
```

The tests do not train the final model or regenerate evaluation outputs.

## Inference

The backend should use [`src/models/xgboost_model.py`](src/models/xgboost_model.py) and the existing model artifacts:

```python
from src.models.xgboost_model import load_final_predictor

predictor = load_final_predictor("models")
result = predictor.predict(features)
```

The predictor requires exactly eight finite numeric Model A features. It rejects missing keys, unexpected keys, non-numeric values, and non-finite values. It performs no imputation.

Read [`docs/backend_integration_handoff.md`](docs/backend_integration_handoff.md) for the exact feature contract, output structure, error behavior, limitations, and backend responsibilities.

## Evaluation summary

Internal 16-fold participant-level LOPO evaluation of the final XGBoost model:

- Average Precision: `0.766317`
- ROC-AUC: `0.959966`
- Precision: `0.850679`
- Recall: `0.576556`
- Specificity: `0.996189`
- F1-score: `0.687293`

OhioT1DM official test-only external evaluation:

- Average Precision: `0.875424`
- ROC-AUC: `0.991105`
- Precision: `0.863992`
- Recall: `0.714401`
- Specificity: `0.995297`
- F1-score: `0.782108`

These are research evaluation results. They do not establish clinical validity or probability calibration.

## Reproducibility and integration notes

- Historical features use only observations at or before prediction time.
- No interpolation or fabricated missing values are used.
- The target includes the exact 30-minute endpoint.
- Participant-level separation is required for evaluation.
- Ohio external evaluation uses only official test XML files.
- The final model threshold is `0.5`.
- Model A is not a meal-specific predictor.

For the complete explanation and safety limitations, see:

- [`docs/METHODOLOGY.md`](docs/METHODOLOGY.md)
- [`docs/DATA_LEAKAGE_AND_SPLITTING.md`](docs/DATA_LEAKAGE_AND_SPLITTING.md)
- [`docs/backend_integration_handoff.md`](docs/backend_integration_handoff.md)
- [`docs/ML_viva_prep.md`](docs/ML_viva_prep.md)
