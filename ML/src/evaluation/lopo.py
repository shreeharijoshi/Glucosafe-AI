"""Participant-grouped Leave-One-Participant-Out manifest generation."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.integration.model_a import MODEL_A_FEATURE_COLUMNS


MANIFEST_COLUMNS = (
    "held_out_participant_id",
    "training_participant_ids",
    "training_rows",
    "training_positive",
    "training_negative",
    "held_out_rows",
    "held_out_positive",
    "held_out_negative",
)


def _eligible_rows(dataset: pd.DataFrame) -> pd.DataFrame:
    required = {"participant_id", "target", *MODEL_A_FEATURE_COLUMNS}
    missing = required - set(dataset.columns)
    if missing:
        raise ValueError(f"missing required Model A columns: {sorted(missing)}")
    eligible = dataset.loc[
        dataset["target"].notna()
        & dataset[list(MODEL_A_FEATURE_COLUMNS)].notna().all(axis=1)
    ].copy()
    eligible["participant_id"] = eligible["participant_id"].astype(str)
    eligible["target"] = pd.to_numeric(eligible["target"], errors="raise").astype(int)
    return eligible


def build_lopo_manifest(dataset: pd.DataFrame) -> pd.DataFrame:
    """Return one deterministic LOPO fold row per eligible participant."""

    eligible = _eligible_rows(dataset)
    participant_ids = sorted(eligible["participant_id"].unique())
    if not participant_ids:
        return pd.DataFrame(columns=MANIFEST_COLUMNS)

    stats = eligible.groupby("participant_id")["target"].agg(
        rows="size", positive="sum"
    )
    stats["negative"] = stats["rows"] - stats["positive"]
    rows: list[dict[str, object]] = []
    for held_out in participant_ids:
        training_ids = [pid for pid in participant_ids if pid != held_out]
        training = stats.loc[training_ids]
        held_out_stats = stats.loc[held_out]
        rows.append(
            {
                "held_out_participant_id": held_out,
                "training_participant_ids": ",".join(training_ids),
                "training_rows": int(training["rows"].sum()),
                "training_positive": int(training["positive"].sum()),
                "training_negative": int(training["negative"].sum()),
                "held_out_rows": int(held_out_stats["rows"]),
                "held_out_positive": int(held_out_stats["positive"]),
                "held_out_negative": int(held_out_stats["negative"]),
            }
        )
    return pd.DataFrame(rows, columns=MANIFEST_COLUMNS)


def save_lopo_manifest(
    dataset: pd.DataFrame, output_path: str | Path
) -> Path:
    """Write a deterministic LOPO manifest without changing the source data."""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    build_lopo_manifest(dataset).to_csv(path, index=False)
    return path
