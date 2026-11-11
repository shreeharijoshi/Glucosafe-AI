"""Build the combined glucose-only Model A dataset."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from src.data.manchester import ManchesterDataset
from src.features.glucose import build_glucose_features
from src.targets.builder import build_glucose_targets


MODEL_A_FEATURE_COLUMNS = (
    "current_glucose_mg_dl",
    "current_glucose_age_minutes",
    "glucose_5min_before_mg_dl",
    "glucose_10min_before_mg_dl",
    "glucose_15min_before_mg_dl",
    "glucose_change_5min_mg_dl",
    "glucose_change_10min_mg_dl",
    "glucose_change_15min_mg_dl",
)
JOIN_KEYS = ("participant_id", "prediction_timestamp", "source_file")


@dataclass(frozen=True)
class ModelADataset:
    """Combined Model A rows and an auditable summary."""

    data: pd.DataFrame
    summary: dict[str, object]

    def save(self, output_dir: str | Path) -> tuple[Path, Path]:
        directory = Path(output_dir)
        directory.mkdir(parents=True, exist_ok=True)
        data_path = directory / "model_a_dataset.csv"
        report_path = directory / "model_a_dataset_report.md"
        self.data.to_csv(data_path, index=False)
        report_path.write_text(_render_report(self.summary), encoding="utf-8")
        return data_path, report_path


def _key_duplicates(frame: pd.DataFrame) -> int:
    return int(frame.duplicated(list(JOIN_KEYS), keep=False).sum())


def _render_report(summary: dict[str, object]) -> str:
    lines = ["# Model A Dataset Report", ""]
    for key, value in summary.items():
        lines.append(f"- **{key.replace('_', ' ').title()}**: {value}")
    lines.append("")
    return "\n".join(lines)


def build_model_a_dataset(dataset: ManchesterDataset) -> ModelADataset:
    """Integrate loader rows, targets, and glucose-only features.

    The target and feature builders are applied independently within each
    participant and source-file partition. All audit columns are retained;
    ``MODEL_A_FEATURE_COLUMNS`` is the explicit model-input allowlist.
    """

    combined_frames: list[pd.DataFrame] = []
    input_rows = 0
    target_rows = 0
    feature_rows = 0
    warnings: list[str] = []

    for participant_id in sorted(dataset.glucose):
        glucose = dataset.glucose[participant_id].copy()
        input_rows += len(glucose)
        targets = build_glucose_targets(glucose)
        features = build_glucose_features(glucose, targets)
        target_rows += len(targets)
        feature_rows += len(features)

        if _key_duplicates(targets):
            raise ValueError(f"duplicate target keys for participant {participant_id}")
        if _key_duplicates(features):
            raise ValueError(f"duplicate feature keys for participant {participant_id}")

        merged = targets.merge(
            features,
            on=list(JOIN_KEYS),
            how="outer",
            indicator=True,
            validate="one_to_one",
            suffixes=("", "_feature"),
        )
        unmatched = merged["_merge"] != "both"
        if unmatched.any():
            warnings.append(
                f"{participant_id}: {int(unmatched.sum())} unmatched target/feature rows"
            )
        merged = merged.loc[~unmatched].drop(columns="_merge")
        combined_frames.append(merged)

    columns = [
        "participant_id",
        "prediction_timestamp",
        "source_file",
        "target",
        "status",
        "reason",
        *MODEL_A_FEATURE_COLUMNS,
    ]
    data = (
        pd.concat(combined_frames, ignore_index=True)
        if combined_frames
        else pd.DataFrame(columns=columns)
    )
    if not data.empty:
        data = data.sort_values(list(JOIN_KEYS), kind="mergesort").reset_index(
            drop=True
        )
        data = data[columns]

    unknown = data["target"].isna()
    summary: dict[str, object] = {
        "input_glucose_rows": input_rows,
        "loader_quarantined_rows": len(dataset.quarantined),
        "loader_issue_count": len(dataset.issues),
        "participants_with_glucose": len(dataset.glucose),
        "participants_with_both_modalities": sum(
            participant.has_both_modalities for participant in dataset.participants
        ),
        "target_rows": target_rows,
        "feature_rows": feature_rows,
        "combined_prediction_rows": len(data),
        "positive_targets": int((data["target"] == 1).sum()),
        "negative_targets": int((data["target"] == 0).sum()),
        "unknown_targets": int(unknown.sum()),
        "duplicate_prediction_keys": _key_duplicates(data),
        "unmatched_target_feature_rows": sum(
            int(warning.split(": ", 1)[1].split(" ", 1)[0])
            for warning in warnings
        ),
        "feature_missingness": {
            column: int(data[column].isna().sum())
            for column in MODEL_A_FEATURE_COLUMNS
        },
        "unknown_target_reasons": data.loc[unknown, "reason"]
        .value_counts()
        .to_dict(),
        "warnings": warnings,
    }
    return ModelADataset(data=data, summary=summary)
