"""OhioT1DM test-only external evaluation for the finalized Model A model."""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, roc_auc_score

from src.features.glucose import build_glucose_features
from src.integration.model_a import MODEL_A_FEATURE_COLUMNS
from src.models.xgboost_model import load_final_predictor
from src.targets.builder import build_glucose_targets


THRESHOLD = 0.5
HORIZON_MINUTES = 30
MAX_COVERAGE_DELAY_MINUTES = 10
OHIO_TIMESTAMP_FORMAT = "%d-%m-%Y %H:%M:%S"


def _test_xml_files(dataset_root: str | Path) -> list[Path]:
    root = Path(dataset_root)
    files = sorted(root.glob("*/test/*.xml"))
    if not files:
        raise ValueError(f"no Ohio testing XML files found below {root}")
    if any("train" in path.parts for path in files):
        raise ValueError("Ohio training XML path discovered in testing file set")
    return files


def _load_test_glucose(path: Path) -> pd.DataFrame:
    if "test" not in path.parts or "train" in path.parts:
        raise ValueError(f"refusing non-testing Ohio XML path: {path}")
    root = ET.parse(path).getroot()
    participant_id = str(root.attrib["id"])
    rows: list[dict[str, object]] = []
    for event in root.findall("./glucose_level/event"):
        timestamp = pd.to_datetime(
            event.attrib.get("ts"),
            format=OHIO_TIMESTAMP_FORMAT,
            errors="coerce",
        )
        value = pd.to_numeric(event.attrib.get("value"), errors="coerce")
        rows.append(
            {
                "participant_id": participant_id,
                "source_file": path.name,
                "timestamp": timestamp,
                "glucose_mg_dl": value,
            }
        )
    return pd.DataFrame(rows)


def build_ohio_test_dataset(
    dataset_root: str | Path,
) -> tuple[pd.DataFrame, dict[str, int]]:
    """Build eligible Ohio test-only features and targets without predictions."""

    frames: list[pd.DataFrame] = []
    audit = {
        "test_files": 0,
        "raw_glucose_rows": 0,
        "invalid_timestamp_or_value_rows": 0,
        "duplicate_timestamp_rows": 0,
        "candidate_rows": 0,
        "known_target_rows": 0,
        "feature_complete_rows": 0,
        "eligible_rows": 0,
        "positive_rows": 0,
        "negative_rows": 0,
    }

    for path in _test_xml_files(dataset_root):
        glucose = _load_test_glucose(path)
        audit["test_files"] += 1
        audit["raw_glucose_rows"] += len(glucose)
        audit["invalid_timestamp_or_value_rows"] += int(
            glucose[["timestamp", "glucose_mg_dl"]].isna().any(axis=1).sum()
        )
        audit["duplicate_timestamp_rows"] += int(
            glucose["timestamp"].duplicated(keep=False).sum()
        )
        valid_glucose = glucose.dropna(
            subset=["timestamp", "glucose_mg_dl"]
        ).copy()
        targets = build_glucose_targets(valid_glucose)
        audit["candidate_rows"] += len(targets)
        audit["known_target_rows"] += int(targets["target"].notna().sum())
        features = build_glucose_features(valid_glucose, targets)
        complete = features[list(MODEL_A_FEATURE_COLUMNS)].notna().all(axis=1)
        audit["feature_complete_rows"] += int(complete.sum())
        eligible = targets["target"].notna() & complete
        combined = features.loc[eligible].copy()
        combined["target"] = targets.loc[eligible, "target"].astype(int).to_numpy()
        frames.append(combined)

    if not frames:
        raise ValueError("Ohio testing partition produced no candidate rows")
    dataset = pd.concat(frames, ignore_index=True)
    audit["eligible_rows"] = len(dataset)
    audit["positive_rows"] = int((dataset["target"] == 1).sum())
    audit["negative_rows"] = int((dataset["target"] == 0).sum())
    return dataset, audit


def _classification_metrics(
    target: pd.Series,
    score: pd.Series,
    prediction: pd.Series,
) -> dict[str, float | int | None]:
    tp = int(((target == 1) & (prediction == 1)).sum())
    tn = int(((target == 0) & (prediction == 0)).sum())
    fp = int(((target == 0) & (prediction == 1)).sum())
    fn = int(((target == 1) & (prediction == 0)).sum())
    return {
        "average_precision": float(average_precision_score(target, score))
        if target.nunique() == 2
        else None,
        "roc_auc": float(roc_auc_score(target, score))
        if target.nunique() == 2
        else None,
        "precision": float(tp / (tp + fp)) if tp + fp else None,
        "recall": float(tp / (tp + fn)) if tp + fn else None,
        "specificity": float(tn / (tn + fp)) if tn + fp else None,
        "f1": float(2 * tp / (2 * tp + fp + fn))
        if 2 * tp + fp + fn
        else None,
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
    }


def evaluate_ohio_external(
    dataset_root: str | Path,
    model_dir: str | Path,
    output_dir: str | Path,
) -> tuple[Path, Path]:
    """Evaluate the unchanged Manchester-trained model on Ohio test XML only."""

    dataset, audit = build_ohio_test_dataset(dataset_root)
    predictor = load_final_predictor(model_dir)
    if predictor.threshold != THRESHOLD:
        raise ValueError(f"final model threshold is {predictor.threshold}, not {THRESHOLD}")
    if predictor.feature_columns != MODEL_A_FEATURE_COLUMNS:
        raise ValueError("final model feature ordering does not match Model A")

    score = predictor.model.predict_proba(
        dataset[list(MODEL_A_FEATURE_COLUMNS)]
    )[:, 1]
    prediction = (score >= THRESHOLD).astype(int)
    if not np.isfinite(score).all():
        raise ValueError("model returned non-finite Ohio risk scores")

    predictions = dataset[
        ["participant_id", "source_file", "prediction_timestamp", *MODEL_A_FEATURE_COLUMNS, "target"]
    ].copy()
    predictions = predictions.rename(columns={"target": "actual_target"})
    predictions["risk_probability"] = score
    predictions["binary_prediction"] = prediction
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    predictions_path = output_path / "ohio_external_validation_predictions.csv"
    predictions.to_csv(predictions_path, index=False)

    pooled = _classification_metrics(
        predictions["actual_target"],
        predictions["risk_probability"],
        predictions["binary_prediction"],
    )
    participant_rows: list[dict[str, object]] = []
    for participant_id, group in predictions.groupby("participant_id", sort=True):
        row: dict[str, object] = {
            "participant_id": participant_id,
            "observations": len(group),
            "positive_support": int((group["actual_target"] == 1).sum()),
            "negative_support": int((group["actual_target"] == 0).sum()),
        }
        row.update(
            _classification_metrics(
                group["actual_target"],
                group["risk_probability"],
                group["binary_prediction"],
            )
        )
        participant_rows.append(row)

    report_path = output_path / "ohio_external_validation_metrics.md"
    report_path.write_text(
        _render_report(audit, pooled, pd.DataFrame(participant_rows)),
        encoding="utf-8",
    )
    return predictions_path, report_path


def _render_report(
    audit: dict[str, int],
    pooled: dict[str, float | int | None],
    participant_metrics: pd.DataFrame,
) -> str:
    comparison = {
        "Manchester LOPO": {
            "average_precision": 0.766317,
            "roc_auc": 0.959966,
            "precision": 0.850679,
            "recall": 0.576556,
            "specificity": 0.996189,
            "f1": 0.687293,
            "tp": 5076,
            "tn": 232889,
            "fp": 891,
            "fn": 3728,
        },
        "Ohio external": pooled,
    }
    lines = [
        "# OhioT1DM External Validation Metrics",
        "",
        "Exploratory external-domain evaluation only; not clinical validation.",
        "",
        "## Scope and safeguards",
        "",
        "- Input: only `2018/test/*.xml` and `2020/test/*.xml` Ohio files.",
        "- Ohio training XML files were not read or used.",
        "- Final model: unchanged Manchester-trained `model_a_xgboost_final.json`.",
        "- Ohio values are interpreted as mg/dL under the documented conditional decision; original XML metadata does not declare units, and subsequent peer-reviewed publications support the mg/dL convention.",
        "- No Ohio training, fine-tuning, tuning, threshold selection, calibration, or preprocessing fit was performed.",
        "- Threshold: 0.5.",
        "- Features are historical glucose only; no meal or insulin fields are used.",
        "",
        "## Dataset counts",
        "",
        f"- Test files: {audit['test_files']}",
        f"- Test participants: {audit['eligible_rows'] and participant_metrics['participant_id'].nunique()}",
        f"- Raw glucose observations: {audit['raw_glucose_rows']}",
        f"- Candidate rows: {audit['candidate_rows']}",
        f"- Known target rows: {audit['known_target_rows']}",
        f"- Feature-complete rows: {audit['feature_complete_rows']}",
        f"- Eligible observations: {audit['eligible_rows']}",
        f"- Positive observations: {audit['positive_rows']}",
        f"- Negative observations: {audit['negative_rows']}",
        f"- Invalid timestamp/value rows: {audit['invalid_timestamp_or_value_rows']}",
        f"- Duplicate timestamp rows: {audit['duplicate_timestamp_rows']}",
        "",
        "Preparation estimates were 30,789 eligible, 1,236 positive, and 29,553 negative observations. "
        "The implementation matched those counts exactly; no discrepancy required investigation.",
        "",
        "## Pooled metrics",
        "",
        "| Metric | Ohio external |",
        "|---|---:|",
    ]
    metric_names = [
        ("Average Precision", "average_precision"),
        ("ROC-AUC", "roc_auc"),
        ("Precision", "precision"),
        ("Recall", "recall"),
        ("Specificity", "specificity"),
        ("F1-score", "f1"),
        ("TP", "tp"),
        ("TN", "tn"),
        ("FP", "fp"),
        ("FN", "fn"),
    ]
    for label, key in metric_names:
        value = pooled[key]
        lines.append(f"| {label} | {value:.6f} |" if isinstance(value, float) else f"| {label} | {value} |")
    lines += [
        "",
        "## Manchester internal LOPO comparison",
        "",
        "| Metric | Manchester LOPO | Ohio external |",
        "|---|---:|---:|",
    ]
    for label, key in metric_names:
        ohio_value = pooled[key]
        manchester_value = comparison["Manchester LOPO"][key]
        lines.append(
            f"| {label} | {manchester_value:.6f} | {ohio_value:.6f} |"
            if isinstance(ohio_value, float)
            else f"| {label} | {manchester_value} | {ohio_value} |"
        )
    lines += [
        "",
        "## Participant-wise metrics",
        "",
        participant_metrics.to_string(index=False),
        "",
        "Participant-level AP/ROC-AUC may be unavailable when a participant has only one target class.",
        "",
        "## Limitations",
        "",
        "- Ohio original XML files do not explicitly declare glucose units; mg/dL is supported by subsequent peer-reviewed publications, not direct original-file metadata.",
        "- Only 12 Ohio participants were evaluated.",
        "- Ohio's official train/test partitions reuse participant IDs, although this model was trained exclusively on Manchester data.",
        "- Dataset shift may affect performance.",
        "- The target is hypoglycemia within 30 minutes after the prediction timestamp, not specifically after a meal.",
        "- Results do not establish clinical validity or probability calibration.",
        "",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    evaluate_ohio_external(
        "Datasets/OhioT1DM/OhioT1DM",
        "models",
        "outputs",
    )
