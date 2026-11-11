"""Final Model A XGBoost artifact training and inference."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping

import numpy as np
import pandas as pd
from xgboost import XGBClassifier

from src.evaluation.baseline import _eligible
from src.integration.model_a import MODEL_A_FEATURE_COLUMNS


THRESHOLD = 0.5
RANDOM_STATE = 42
MODEL_FILENAME = "model_a_xgboost_final.json"
METADATA_FILENAME = "model_a_xgboost_final_metadata.json"
MODEL_PARAMETERS = {
    "objective": "binary:logistic",
    "n_estimators": 200,
    "max_depth": 4,
    "learning_rate": 0.05,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "eval_metric": "logloss",
    "random_state": RANDOM_STATE,
    "n_jobs": -1,
}


def train_final_model(
    dataset_path: str | Path,
    artifact_dir: str | Path,
) -> tuple[Path, Path]:
    """Train and save the final Model A XGBoost model on eligible rows."""

    dataset = _eligible(pd.read_csv(dataset_path))
    if dataset.empty:
        raise ValueError("Model A dataset has no eligible observations")
    if dataset["target"].nunique() < 2:
        raise ValueError("eligible Model A data must contain both target classes")

    artifact_path = Path(artifact_dir)
    artifact_path.mkdir(parents=True, exist_ok=True)
    model = XGBClassifier(**MODEL_PARAMETERS)
    model.fit(dataset[list(MODEL_A_FEATURE_COLUMNS)], dataset["target"])

    model_path = artifact_path / MODEL_FILENAME
    metadata_path = artifact_path / METADATA_FILENAME
    model.save_model(model_path)
    metadata = {
        "model_type": "XGBClassifier",
        "xgboost_version": _xgboost_version(),
        "feature_columns": list(MODEL_A_FEATURE_COLUMNS),
        "threshold": THRESHOLD,
        "preprocessing": "none",
        "missing_value_handling": {
            "training": "Rows missing target or any model feature are excluded.",
            "inference": "Missing, non-numeric, and non-finite feature values are rejected.",
        },
        "target_definition": {
            "threshold_mg_dl": 70,
            "horizon_minutes": 30,
            "interval": "(t, t + 30 minutes]",
        },
        "training": {
            "eligible_observations": len(dataset),
            "participants": int(dataset["participant_id"].nunique()),
            "positive_targets": int((dataset["target"] == 1).sum()),
            "negative_targets": int((dataset["target"] == 0).sum()),
        },
        "model_parameters": MODEL_PARAMETERS,
    }
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return model_path, metadata_path


class XGBoostPredictor:
    """Strict single-observation predictor for the saved Model A artifact."""

    def __init__(self, model_path: str | Path, metadata_path: str | Path) -> None:
        self.model_path = Path(model_path)
        self.metadata_path = Path(metadata_path)
        self.metadata = json.loads(self.metadata_path.read_text(encoding="utf-8"))
        self.feature_columns = tuple(self.metadata["feature_columns"])
        self.threshold = float(self.metadata["threshold"])
        self.model = XGBClassifier()
        self.model.load_model(self.model_path)

    def predict(self, features: Mapping[str, object]) -> dict[str, object]:
        """Return risk probability and thresholded prediction for one observation."""

        if not isinstance(features, Mapping):
            raise TypeError("features must be a mapping of Model A feature names to values")
        supplied = set(features)
        required = set(self.feature_columns)
        missing = sorted(required - supplied)
        extra = sorted(supplied - required)
        if missing:
            raise ValueError(f"missing required Model A features: {missing}")
        if extra:
            raise ValueError(f"unexpected Model A features: {extra}")

        frame = pd.DataFrame(
            [[features[column] for column in self.feature_columns]],
            columns=self.feature_columns,
        )
        numeric = frame.apply(pd.to_numeric, errors="coerce")
        values = numeric.to_numpy(dtype=float)
        if not np.isfinite(values).all():
            raise ValueError("Model A features must be finite numeric values")

        probability = float(self.model.predict_proba(numeric)[:, 1][0])
        return {
            "status": "success",
            "risk_probability": probability,
            "prediction": int(probability >= self.threshold),
            "threshold": self.threshold,
        }


def load_final_predictor(artifact_dir: str | Path) -> XGBoostPredictor:
    """Load the final Model A XGBoost artifact and its metadata."""

    directory = Path(artifact_dir)
    return XGBoostPredictor(
        directory / MODEL_FILENAME,
        directory / METADATA_FILENAME,
    )


def _xgboost_version() -> str:
    import xgboost

    return xgboost.__version__
