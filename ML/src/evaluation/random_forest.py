"""Random Forest LOPO evaluation for the existing Model A dataset."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from sklearn.ensemble import RandomForestClassifier

from src.evaluation.baseline import (
    _classification_metrics,
    _eligible,
    _metric_row,
)
from src.integration.model_a import MODEL_A_FEATURE_COLUMNS


FOLD_COUNT = 16
THRESHOLD = 0.5
MODEL_NAME = "random_forest"
RANDOM_STATE = 42


def evaluate_random_forest_model_a(
    dataset_path: str | Path,
    manifest_path: str | Path,
    output_dir: str | Path,
) -> tuple[Path, Path]:
    """Run the fixed-parameter Random Forest Model A LOPO evaluation."""

    dataset = _eligible(pd.read_csv(dataset_path))
    manifest = pd.read_csv(manifest_path, dtype={"held_out_participant_id": str})
    if len(manifest) != FOLD_COUNT:
        raise ValueError(f"expected {FOLD_COUNT} LOPO folds, found {len(manifest)}")

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    prediction_rows: list[pd.DataFrame] = []
    fold_metrics: list[dict[str, object]] = []

    for fold, manifest_row in manifest.reset_index(drop=True).iterrows():
        held_out = str(manifest_row["held_out_participant_id"])
        train_ids = [
            participant
            for participant in str(manifest_row["training_participant_ids"]).split(",")
            if participant
        ]
        train = dataset[dataset["participant_id"].isin(train_ids)]
        test = dataset[dataset["participant_id"] == held_out]
        if set(train["participant_id"]) & set(test["participant_id"]):
            raise ValueError(f"participant overlap in fold {fold + 1}")
        if test.empty:
            raise ValueError(f"held-out participant has no eligible rows: {held_out}")
        if train["target"].nunique() < 2:
            raise ValueError(f"training fold {fold + 1} has fewer than two classes")

        model = RandomForestClassifier(
            n_estimators=300,
            class_weight="balanced",
            random_state=RANDOM_STATE,
            n_jobs=-1,
        )
        model.fit(train[list(MODEL_A_FEATURE_COLUMNS)], train["target"])
        score = model.predict_proba(test[list(MODEL_A_FEATURE_COLUMNS)])[:, 1]

        fold_predictions = test[
            [
                column
                for column in (
                    "participant_id",
                    "prediction_timestamp",
                    "source_file",
                )
                if column in test
            ]
        ].copy()
        fold_predictions["fold"] = fold + 1
        fold_predictions["target"] = test["target"].to_numpy()
        fold_predictions["random_forest_probability"] = score
        fold_predictions["random_forest_prediction"] = (
            pd.Series(score, index=test.index) >= THRESHOLD
        ).astype(int).to_numpy()
        fold_metrics.append(
            _metric_row(
                fold + 1,
                held_out,
                MODEL_NAME,
                test["target"],
                pd.Series(score, index=test.index),
            )
        )
        prediction_rows.append(fold_predictions.reset_index(drop=True))

    predictions = pd.concat(prediction_rows, ignore_index=True)
    predictions_path = output_path / "model_a_random_forest_lopo_predictions.csv"
    predictions.to_csv(predictions_path, index=False)

    fold_metric_frame = pd.DataFrame(fold_metrics)
    pooled_metric = _metric_row(
        0,
        "pooled",
        MODEL_NAME,
        predictions["target"],
        predictions["random_forest_probability"],
    )
    report_path = output_path / "model_a_random_forest_lopo_metrics.md"
    report_path.write_text(
        _render_report(
            fold_metric_frame,
            pd.DataFrame([pooled_metric]),
            len(predictions),
        ),
        encoding="utf-8",
    )
    return predictions_path, report_path


def _render_report(
    participant_metrics: pd.DataFrame,
    pooled_metrics: pd.DataFrame,
    prediction_count: int,
) -> str:
    lines = [
        "# Model A Random Forest LOPO Evaluation",
        "",
        "Exploratory research results only; not clinical validation.",
        "",
        f"- Folds: {FOLD_COUNT}",
        f"- Eligible out-of-fold predictions: {prediction_count}",
        f"- Threshold: {THRESHOLD}",
        "- Model: RandomForestClassifier(n_estimators=300, class_weight='balanced', random_state=42)",
        "- Features and eligibility: identical to the existing Model A Logistic Regression evaluation",
        "- Unknown targets: excluded before fitting and evaluation",
        "",
        "## Pooled out-of-fold metrics",
        "",
        pooled_metrics.to_string(index=False),
        "",
        "## Participant-level metrics",
        "",
        participant_metrics.to_string(index=False),
        "",
        "Metrics are reported as N/A (`None`) when class or prediction support is insufficient.",
        "Rows from overlapping prediction windows are temporally dependent.",
        "",
    ]
    return "\n".join(lines)
