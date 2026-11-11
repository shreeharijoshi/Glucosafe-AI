"""Paired exploratory LOPO evaluation of Model A and Model B."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.preprocessing import StandardScaler

from src.evaluation.baseline import THRESHOLD
from src.integration.model_a import JOIN_KEYS, MODEL_A_FEATURE_COLUMNS
from src.integration.model_b import MODEL_B_FEATURE_COLUMNS


MODEL_NAMES = ("model_a", "model_b")


def _eligible(frame: pd.DataFrame) -> pd.DataFrame:
    required = {
        *JOIN_KEYS,
        "target",
        "status",
        "reason",
        *MODEL_B_FEATURE_COLUMNS,
    }
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"missing paired-evaluation columns: {sorted(missing)}")
    result = frame.loc[
        frame["target"].notna()
        & frame[list(MODEL_B_FEATURE_COLUMNS)].notna().all(axis=1)
    ].copy()
    result["participant_id"] = result["participant_id"].astype(str)
    result["target"] = pd.to_numeric(result["target"], errors="raise").astype(int)
    if result.duplicated(list(JOIN_KEYS)).any():
        raise ValueError("paired evaluation contains duplicate prediction keys")
    return result


def _metrics(y_true: pd.Series, score: pd.Series) -> dict[str, object]:
    predicted = (score >= THRESHOLD).astype(int)
    tp = int(((y_true == 1) & (predicted == 1)).sum())
    tn = int(((y_true == 0) & (predicted == 0)).sum())
    fp = int(((y_true == 0) & (predicted == 1)).sum())
    fn = int(((y_true == 1) & (predicted == 0)).sum())
    return {
        "average_precision": float(average_precision_score(y_true, score))
        if y_true.nunique() == 2 else None,
        "roc_auc": float(roc_auc_score(y_true, score))
        if y_true.nunique() == 2 else None,
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
        "precision": float(tp / (tp + fp)) if tp + fp else None,
        "recall": float(tp / (tp + fn)) if tp + fn else None,
        "specificity": float(tn / (tn + fp)) if tn + fp else None,
        "f1": float(2 * tp / (2 * tp + fp + fn))
        if 2 * tp + fp + fn else None,
    }


def _metric_frame(predictions: pd.DataFrame, group_column: str) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    groups = [("pooled", predictions)] if group_column == "pooled" else predictions.groupby(
        group_column, sort=True
    )
    for group_name, group in groups:
        for model_name in MODEL_NAMES:
            values = _metrics(
                group["target"],
                group[f"{model_name}_probability"],
            )
            rows.append(
                {
                    "group": group_name,
                    "model": model_name,
                    "positive_support": int((group["target"] == 1).sum()),
                    "negative_support": int((group["target"] == 0).sum()),
                    **values,
                }
            )
    return pd.DataFrame(rows)


def _render_report(
    predictions: pd.DataFrame,
    pooled: pd.DataFrame,
    participant: pd.DataFrame,
    fold_count: int,
) -> str:
    pooled_by_model = pooled.set_index("model")
    differences = []
    for metric in ("average_precision", "roc_auc", "precision", "recall", "specificity", "f1"):
        a = pooled_by_model.loc["model_a", metric]
        b = pooled_by_model.loc["model_b", metric]
        differences.append(
            {"metric": metric, "model_b_minus_model_a": b - a}
        )
    lines = [
        "# Paired Model A vs Model B LOPO Evaluation",
        "",
        "Exploratory observational research only; not clinical validation or evidence of safety.",
        "",
        f"- Shared eligible rows: {len(predictions)}",
        f"- Participants and folds: {predictions['held_out_participant_id'].nunique()}",
        f"- Fixed threshold: {THRESHOLD} (descriptive experimental threshold, not medically validated)",
        "- StandardScaler and regularized logistic regression were fitted separately on training participants per fold.",
        "- Both models used identical rows, targets, participant-held-out folds, and no imputation or threshold tuning.",
        "- Meal timestamps are recorded-time proxies, not confirmed consumption times; participant support is uneven and prediction windows overlap.",
        "- Results are exploratory and do not establish clinical validity or safety.",
        "",
        "## Pooled out-of-fold metrics",
        "",
        pooled.to_string(index=False),
        "",
        "## Pooled Model B minus Model A",
        "",
        pd.DataFrame(differences).to_string(index=False),
        "",
        "## Per-participant metrics",
        "",
        participant.to_string(index=False),
        "",
        "Metrics are N/A when class support is insufficient.",
        "",
    ]
    return "\n".join(lines)


def evaluate_paired(
    intersection_path: str | Path,
    output_dir: str | Path,
) -> tuple[Path, Path]:
    """Evaluate both models on one deterministic shared-population LOPO split."""

    data = _eligible(pd.read_csv(intersection_path))
    participants = sorted(data["participant_id"].unique())
    prediction_rows: list[pd.DataFrame] = []
    for fold, held_out in enumerate(participants, start=1):
        train = data[data["participant_id"] != held_out]
        test = data[data["participant_id"] == held_out].copy()
        if set(train["participant_id"]) & {held_out}:
            raise ValueError(f"participant overlap in fold {fold}")
        scores: dict[str, object] = {}
        for model_name, columns in (
            ("model_a", MODEL_A_FEATURE_COLUMNS),
            ("model_b", MODEL_B_FEATURE_COLUMNS),
        ):
            scaler = StandardScaler()
            x_train = scaler.fit_transform(train[list(columns)])
            x_test = scaler.transform(test[list(columns)])
            model = LogisticRegression(max_iter=1000, solver="lbfgs")
            model.fit(x_train, train["target"])
            scores[model_name] = model.predict_proba(x_test)[:, 1]
        rows = test[list(JOIN_KEYS) + ["target", "status", "reason"]].copy()
        rows["fold"] = fold
        rows["held_out_participant_id"] = held_out
        for model_name in MODEL_NAMES:
            rows[f"{model_name}_probability"] = scores[model_name]
            rows[f"{model_name}_prediction"] = (
                pd.Series(scores[model_name], index=test.index) >= THRESHOLD
            ).astype(int).to_numpy()
        prediction_rows.append(rows)

    predictions = pd.concat(prediction_rows, ignore_index=True)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    prediction_path = output / "model_a_vs_model_b_paired_predictions.csv"
    report_path = output / "model_a_vs_model_b_paired_report.md"
    predictions.to_csv(prediction_path, index=False)
    pooled = _metric_frame(predictions, "pooled")
    participant = _metric_frame(predictions, "held_out_participant_id")
    report_path.write_text(
        _render_report(predictions, pooled, participant, len(participants)),
        encoding="utf-8",
    )
    return prediction_path, report_path
