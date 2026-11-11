"""Conservative Model B dataset integration for recorded carbohydrates."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.integration.model_a import MODEL_A_FEATURE_COLUMNS, JOIN_KEYS


MODEL_B_FEATURE_COLUMNS = (*MODEL_A_FEATURE_COLUMNS, "carbs_30min_g")
WINDOW = pd.Timedelta(minutes=30)


def _prepare_nutrition(
    nutrition: pd.DataFrame,
) -> tuple[pd.DataFrame, set[pd.Timestamp]]:
    frame = nutrition.copy()
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], errors="coerce")
    frame["carbs_g"] = pd.to_numeric(frame["carbs_g"], errors="coerce")
    relevant = [
        "timestamp", "carbs_g", "meal_type", "meal_tag",
        "prot_g", "fat_g", "fibre_g",
    ]
    frame["_row_signature"] = (
        frame[relevant].astype(object).fillna("<missing>").astype(str).agg("|".join, axis=1)
    )
    conflicts = {
        timestamp
        for timestamp, group in frame.groupby("timestamp", dropna=False, sort=True)
        if not pd.isna(timestamp) and group["_row_signature"].nunique() > 1
    }
    return frame, conflicts


def build_model_b_dataset(
    model_a: pd.DataFrame,
    nutrition_by_participant: dict[str, pd.DataFrame],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return eligible Model B rows and explicit exclusion audit rows.

    A row is eligible only when Model A is known/complete and at least one
    valid carbohydrate record exists in the inclusive preceding 30-minute
    window. Missing, invalid, negative, or conflicting records in that window
    make the row ineligible; empty windows are not treated as zero.
    """

    required = {
        *JOIN_KEYS,
        "target",
        *MODEL_A_FEATURE_COLUMNS,
    }
    missing = required - set(model_a.columns)
    if missing:
        raise ValueError(f"missing required Model A columns: {sorted(missing)}")

    rows: list[dict[str, object]] = []
    audit: list[dict[str, object]] = []
    for participant_id, group in model_a.groupby("participant_id", sort=True):
        participant_id = str(participant_id)
        nutrition = nutrition_by_participant.get(participant_id)
        if nutrition is None or nutrition.empty:
            for index in group.index:
                audit.append({"participant_id": participant_id, "prediction_timestamp": group.loc[index, "prediction_timestamp"], "reason": "no_nutrition_records"})
            continue
        glucose_sources = set(group["source_file"].astype(str))
        nutrition_sources = set(nutrition["source_file"].astype(str))
        if len(glucose_sources) > 1 or len(nutrition_sources) > 1:
            for index in group.index:
                audit.append({"participant_id": participant_id, "prediction_timestamp": group.loc[index, "prediction_timestamp"], "reason": "ambiguous_recording_partitions"})
            continue
        nutrition, conflict_timestamps = _prepare_nutrition(nutrition)
        valid_rows = nutrition[nutrition["timestamp"].notna()].copy()
        valid_rows = valid_rows.drop_duplicates(subset=["timestamp", "_row_signature"])
        for index, prediction in group.iterrows():
            timestamp = pd.to_datetime(prediction["prediction_timestamp"], errors="coerce")
            reason = None
            if pd.isna(prediction["target"]) or prediction[list(MODEL_A_FEATURE_COLUMNS)].isna().any():
                reason = "model_a_not_eligible"
            elif pd.isna(timestamp):
                reason = "invalid_prediction_timestamp"
            else:
                window = valid_rows[
                    valid_rows["timestamp"].between(
                        timestamp - WINDOW, timestamp, inclusive="both"
                    )
                ]
                if window.empty:
                    reason = "no_carbohydrate_record_in_window"
                elif any(ts in conflict_timestamps for ts in window["timestamp"]):
                    reason = "conflicting_nutrition_duplicate"
                elif window["carbs_g"].isna().any():
                    reason = "missing_or_invalid_carbohydrate"
                elif (window["carbs_g"] < 0).any():
                    reason = "negative_carbohydrate"
                else:
                    row = prediction.to_dict()
                    row["carbs_30min_g"] = float(window["carbs_g"].sum())
                    row["nutrition_source_files"] = ",".join(sorted(window["source_file"].astype(str).unique()))
                    rows.append(row)
            if reason is not None:
                audit.append(
                    {
                        "participant_id": participant_id,
                        "prediction_timestamp": prediction["prediction_timestamp"],
                        "reason": reason,
                    }
                )

    output_columns = [
        "participant_id", "prediction_timestamp", "source_file", "target",
        "status", "reason", *MODEL_B_FEATURE_COLUMNS, "nutrition_source_files",
    ]
    eligible = pd.DataFrame(rows)
    if eligible.empty:
        eligible = pd.DataFrame(columns=output_columns)
    else:
        duplicate_keys = eligible.duplicated(list(JOIN_KEYS), keep=False)
        if duplicate_keys.any():
            raise ValueError("Model B integration produced duplicate prediction keys")
        eligible = eligible[output_columns].sort_values(list(JOIN_KEYS), kind="mergesort").reset_index(drop=True)
    return eligible, pd.DataFrame(audit)


def save_model_b_outputs(
    model_a_path: str | Path,
    nutrition_by_participant: dict[str, pd.DataFrame],
    output_dir: str | Path,
) -> tuple[Path, Path, Path]:
    """Create Model B, fair-intersection, and audit report outputs."""

    model_a = pd.read_csv(model_a_path)
    model_b, audit = build_model_b_dataset(model_a, nutrition_by_participant)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    model_b_path = output / "model_b_dataset.csv"
    intersection_path = output / "model_b_intersection.csv"
    report_path = output / "model_b_dataset_report.md"
    model_b.to_csv(model_b_path, index=False)
    model_b.to_csv(intersection_path, index=False)
    report = [
        "# Model B Dataset Audit",
        "",
        "Exploratory recorded-time carbohydrate proxy; not clinical validation.",
        "",
        "- Rolling window: inclusive `[t - 30 minutes, t]`.",
        f"- Input Model A rows: {len(model_a)}",
        f"- Model B eligible rows: {len(model_b)}",
        f"- Excluded rows: {len(audit)}",
        f"- Eligible participants: {model_b['participant_id'].nunique() if not model_b.empty else 0}",
        f"- Positive targets: {int((model_b['target'] == 1).sum()) if not model_b.empty else 0}",
        f"- Negative targets: {int((model_b['target'] == 0).sum()) if not model_b.empty else 0}",
        f"- Exclusion reasons: {audit['reason'].value_counts().to_dict() if not audit.empty else {}}",
        f"- Ambiguous recording-partition exclusions: {int((audit['reason'] == 'ambiguous_recording_partitions').sum()) if not audit.empty else 0}",
        "- Per-participant eligible counts:",
    ]
    if model_b.empty:
        report.append("- None")
    else:
        participant_counts = (
            model_b.assign(
                positive=model_b["target"].eq(1),
                negative=model_b["target"].eq(0),
            )
            .groupby("participant_id", sort=True)
            .agg(
                eligible_rows=("target", "size"),
                positive_targets=("positive", "sum"),
                negative_targets=("negative", "sum"),
            )
        )
        report.extend(
            f"  - {participant_id}: {int(values.eligible_rows)} rows, "
            f"{int(values.positive_targets)} positive, "
            f"{int(values.negative_targets)} negative"
            for participant_id, values in participant_counts.iterrows()
        )
    report.extend([
        "- Exact duplicate nutrition rows are counted once; conflicting duplicates are excluded.",
        "- Missing, invalid, or negative carbohydrates are never converted to zero.",
        "- Empty carbohydrate windows are unavailable, not zero.",
        "- `meal_ts` remains a recorded-time proxy; consumption time and timezone alignment are unresolved.",
        "- The intersection dataset equals the Model B dataset because Model B eligibility requires complete known Model A rows.",
        "",
    ])
    report_path.write_text("\n".join(report), encoding="utf-8")
    audit_path = output / "model_b_exclusion_audit.csv"
    audit.to_csv(audit_path, index=False)
    return model_b_path, intersection_path, report_path
