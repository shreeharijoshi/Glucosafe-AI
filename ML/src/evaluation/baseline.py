"""Exploratory LOPO baseline evaluation for Model A."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.preprocessing import StandardScaler

from src.integration.model_a import MODEL_A_FEATURE_COLUMNS


THRESHOLD = 0.5
MODEL_NAMES = ("logistic", "always_negative", "training_prevalence")


def _eligible(dataset: pd.DataFrame) -> pd.DataFrame:
    required = {"participant_id", "target", *MODEL_A_FEATURE_COLUMNS}
    missing = required - set(dataset.columns)
    if missing:
        raise ValueError(f"missing required Model A columns: {sorted(missing)}")
    result = dataset.loc[
        dataset["target"].notna()
        & dataset[list(MODEL_A_FEATURE_COLUMNS)].notna().all(axis=1)
    ].copy()
    result["participant_id"] = result["participant_id"].astype(str)
    result["target"] = pd.to_numeric(result["target"], errors="raise").astype(int)
    return result


def _classification_metrics(y_true: pd.Series, score: pd.Series) -> dict[str, object]:
    y_pred = (score >= THRESHOLD).astype(int)
    tp = int(((y_true == 1) & (y_pred == 1)).sum())
    tn = int(((y_true == 0) & (y_pred == 0)).sum())
    fp = int(((y_true == 0) & (y_pred == 1)).sum())
    fn = int(((y_true == 1) & (y_pred == 0)).sum())
    metrics: dict[str, object] = {
        "average_precision": (
            float(average_precision_score(y_true, score))
            if y_true.sum() and (y_true == 0).sum()
            else None
        ),
        "roc_auc": (
            float(roc_auc_score(y_true, score))
            if y_true.nunique() == 2
            else None
        ),
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
        "precision": float(tp / (tp + fp)) if tp + fp else None,
        "recall": float(tp / (tp + fn)) if tp + fn else None,
        "specificity": float(tn / (tn + fp)) if tn + fp else None,
        "f1": (
            float(2 * tp / (2 * tp + fp + fn))
            if 2 * tp + fp + fn
            else None
        ),
    }
    return metrics


def _metric_row(
    fold: int, participant_id: str, model: str, y_true: pd.Series, score: pd.Series
) -> dict[str, object]:
    row = {"fold": fold, "held_out_participant_id": participant_id, "model": model}
    row.update(_classification_metrics(y_true, score))
    row["positive_support"] = int((y_true == 1).sum())
    row["negative_support"] = int((y_true == 0).sum())
    return row


def evaluate_model_a(
    dataset_path: str | Path,
    manifest_path: str | Path,
    output_dir: str | Path,
) -> tuple[Path, Path]:
    """Run fixed-threshold logistic and reference LOPO evaluation."""

    dataset = _eligible(pd.read_csv(dataset_path))
    manifest = pd.read_csv(manifest_path, dtype={"held_out_participant_id": str})
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

        scaler = StandardScaler()
        x_train = scaler.fit_transform(train[list(MODEL_A_FEATURE_COLUMNS)])
        x_test = scaler.transform(test[list(MODEL_A_FEATURE_COLUMNS)])
        model = LogisticRegression(max_iter=1000, solver="lbfgs")
        model.fit(x_train, train["target"])
        logistic_score = model.predict_proba(x_test)[:, 1]
        prevalence = float(train["target"].mean())
        scores = {
            "logistic": logistic_score,
            "always_negative": [0.0] * len(test),
            "training_prevalence": [prevalence] * len(test),
        }
        fold_predictions = test[
            [column for column in ("participant_id", "prediction_timestamp", "source_file") if column in test]
        ].copy()
        fold_predictions["fold"] = fold + 1
        fold_predictions["target"] = test["target"].to_numpy()
        for model_name, score in scores.items():
            fold_predictions[f"{model_name}_probability"] = score
            fold_predictions[f"{model_name}_prediction"] = (
                pd.Series(score, index=test.index) >= THRESHOLD
            ).astype(int).to_numpy()
            fold_metrics.append(
                _metric_row(
                    fold + 1,
                    held_out,
                    model_name,
                    test["target"],
                    pd.Series(score, index=test.index),
                )
            )
        prediction_rows.append(fold_predictions.reset_index(drop=True))

    predictions = pd.concat(prediction_rows, ignore_index=True)
    predictions_path = output_path / "model_a_lopo_predictions.csv"
    predictions.to_csv(predictions_path, index=False)

    metrics = pd.DataFrame(fold_metrics)
    pooled_rows = []
    for model_name in MODEL_NAMES:
        score = predictions[f"{model_name}_probability"]
        pooled = _metric_row(
            0,
            "pooled",
            model_name,
            predictions["target"],
            score,
        )
        pooled_rows.append(pooled)
    report_path = output_path / "model_a_lopo_metrics.md"
    report_path.write_text(
        _render_report(metrics, pd.DataFrame(pooled_rows), len(manifest)),
        encoding="utf-8",
    )
    return predictions_path, report_path


def _render_report(
    fold_metrics: pd.DataFrame, pooled_metrics: pd.DataFrame, fold_count: int
) -> str:
    lines = [
        "# Model A LOPO Baseline Evaluation",
        "",
        "Exploratory research results only; not clinical validation.",
        "",
        f"- Folds: {fold_count}",
        f"- Threshold: {THRESHOLD} (arbitrary fixed baseline)",
        "- Preprocessing: StandardScaler fitted separately on training participants",
        "- Unknown targets: excluded before fitting and evaluation",
        "",
        "## Pooled out-of-fold metrics",
        "",
        pooled_metrics.to_string(index=False),
        "",
        "## Fold metrics",
        "",
        fold_metrics.to_string(index=False),
        "",
        "Metrics are reported as N/A (`None`) when class or prediction support is insufficient.",
        "Rows from overlapping prediction windows are temporally dependent.",
        "",
    ]
    return "\n".join(lines)
