"""Deterministic loading and validation for Manchester/T1D-UOM CSV files."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

import pandas as pd


TIMESTAMP_FORMAT = "%d/%m/%Y %H:%M"
MMOL_TO_MGDL = 18.0182
SUSPICIOUS_YEARS = frozenset({2033, 2204})

GLUCOSE_COLUMNS = frozenset({"bg_ts", "value"})
NUTRITION_COLUMNS = frozenset(
    {"meal_ts", "meal_type", "meal_tag", "carbs_g", "prot_g", "fat_g", "fibre_g"}
)


@dataclass(frozen=True)
class DataIssue:
    """A row-level or file-level validation issue."""

    category: str
    source_file: str
    message: str
    row_number: int | None = None


@dataclass(frozen=True)
class ParticipantFiles:
    """The files discovered for one participant."""

    participant_id: str
    glucose_files: tuple[Path, ...]
    nutrition_files: tuple[Path, ...]

    @property
    def has_both_modalities(self) -> bool:
        return bool(self.glucose_files and self.nutrition_files)


@dataclass
class ManchesterDataset:
    """Validated rows, quarantined rows, and explicit data-quality issues."""

    participants: tuple[ParticipantFiles, ...]
    glucose: dict[str, pd.DataFrame]
    nutrition: dict[str, pd.DataFrame]
    quarantined: pd.DataFrame
    issues: tuple[DataIssue, ...]


def _participant_id(path: Path, prefix: str) -> str:
    match = re.fullmatch(rf"{re.escape(prefix)}(?P<id>[^.]+)\.csv", path.name)
    if match is None or not match.group("id"):
        raise ValueError(f"Unexpected Manchester filename: {path.name}")
    return match.group("id")


def _record_duplicate_conflicts(
    frame: pd.DataFrame,
    timestamp_column: str,
    value_columns: tuple[str, ...],
    source_file: str,
    issues: list[DataIssue],
) -> None:
    duplicate_groups = frame[frame[timestamp_column].duplicated(keep=False)].groupby(
        timestamp_column, dropna=False
    )
    for timestamp, group in duplicate_groups:
        if group[list(value_columns)].drop_duplicates().shape[0] <= 1:
            continue
        for index in group.index:
            issues.append(
                DataIssue(
                    category="conflicting_duplicate",
                    source_file=source_file,
                    message=f"conflicting values at timestamp {timestamp}",
                    row_number=int(index) + 2 if isinstance(index, int) else None,
                )
            )


def _record_cross_file_duplicates(
    frame: pd.DataFrame,
    value_columns: tuple[str, ...],
    issues: list[DataIssue],
) -> None:
    duplicate_groups = frame[frame["timestamp"].duplicated(keep=False)].groupby(
        "timestamp", dropna=False
    )
    for timestamp, group in duplicate_groups:
        if group["source_file"].nunique() <= 1:
            continue
        conflicting = group[list(value_columns)].drop_duplicates().shape[0] > 1
        for index, row in group.iterrows():
            issues.append(
                DataIssue(
                    category=(
                        "conflicting_duplicate" if conflicting else "duplicate_timestamp"
                    ),
                    source_file=str(row["source_file"]),
                    message=(
                        f"conflicting values at timestamp {timestamp}"
                        if conflicting
                        else f"duplicate timestamp across files: {timestamp}"
                    ),
                    row_number=None,
                )
            )


def _discover_files(root: Path) -> tuple[ParticipantFiles, ...]:
    glucose_by_id: dict[str, list[Path]] = {}
    nutrition_by_id: dict[str, list[Path]] = {}

    for path in sorted((root / "Glucose Data").glob("*.csv")):
        glucose_by_id.setdefault(_participant_id(path, "UoMGlucose"), []).append(path)
    for path in sorted((root / "Nutrition Data").glob("*.csv")):
        nutrition_by_id.setdefault(
            _participant_id(path, "UoMNutrition"), []
        ).append(path)

    participant_ids = sorted(glucose_by_id.keys() | nutrition_by_id.keys())
    return tuple(
        ParticipantFiles(
            participant_id=participant_id,
            glucose_files=tuple(glucose_by_id.get(participant_id, [])),
            nutrition_files=tuple(nutrition_by_id.get(participant_id, [])),
        )
        for participant_id in participant_ids
    )


def _read_csv(
    path: Path,
    timestamp_column: str,
    required_columns: frozenset[str],
    participant_id: str,
    issues: list[DataIssue],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    frame = pd.read_csv(path, dtype=str, keep_default_na=True)
    missing_columns = required_columns - set(frame.columns)
    if missing_columns:
        raise ValueError(
            f"{path.name} is missing required columns: {sorted(missing_columns)}"
        )

    frame = frame.copy()
    frame.insert(0, "participant_id", participant_id)
    frame.insert(1, "source_file", path.name)
    frame["timestamp_raw"] = frame[timestamp_column]
    parsed = pd.to_datetime(
        frame[timestamp_column],
        format=TIMESTAMP_FORMAT,
        errors="coerce",
    )

    quarantined_rows: list[dict[str, object]] = []
    invalid_timestamp = parsed.isna()
    suspicious_year = parsed.dt.year.isin(SUSPICIOUS_YEARS)
    for index in frame.index[invalid_timestamp | suspicious_year]:
        reason = (
            "invalid timestamp"
            if invalid_timestamp.loc[index]
            else "suspicious timestamp year"
        )
        row = frame.loc[index].to_dict()
        row["quarantine_reason"] = reason
        quarantined_rows.append(row)
        issues.append(
            DataIssue(
                category="timestamp",
                source_file=path.name,
                message=reason,
                row_number=int(index) + 2,
            )
        )

    valid = frame.loc[~(invalid_timestamp | suspicious_year)].copy()
    valid["timestamp"] = parsed.loc[valid.index]

    missing_required = valid[timestamp_column].isna()
    for index in valid.index[missing_required]:
        issues.append(
            DataIssue(
                category="missing_value",
                source_file=path.name,
                message=f"missing {timestamp_column}",
                row_number=int(index) + 2,
            )
        )

    if timestamp_column == "bg_ts":
        raw_glucose = valid["value"].copy()
        valid["glucose_mmol_l"] = pd.to_numeric(valid["value"], errors="coerce")
        for index in valid.index[raw_glucose.isna()]:
            issues.append(
                DataIssue(
                    category="missing_value",
                    source_file=path.name,
                    message="missing glucose value",
                    row_number=int(index) + 2,
                )
            )
        invalid_glucose = raw_glucose.notna() & valid["glucose_mmol_l"].isna()
        for index in valid.index[invalid_glucose]:
            issues.append(
                DataIssue(
                    category="invalid_value",
                    source_file=path.name,
                    message="non-numeric glucose value",
                    row_number=int(index) + 2,
                )
            )
        valid["glucose_mg_dl"] = valid["glucose_mmol_l"] * MMOL_TO_MGDL
    else:
        raw_carbs = valid["carbs_g"].copy()
        valid["carbs_g"] = pd.to_numeric(valid["carbs_g"], errors="coerce")
        for index in valid.index[raw_carbs.isna()]:
            issues.append(
                DataIssue(
                    category="missing_carbohydrate",
                    source_file=path.name,
                    message="missing carbohydrate preserved as missing",
                    row_number=int(index) + 2,
                )
            )
        invalid_carbs = raw_carbs.notna() & valid["carbs_g"].isna()
        for index in valid.index[invalid_carbs]:
            issues.append(
                DataIssue(
                    category="invalid_value",
                    source_file=path.name,
                    message="non-numeric carbohydrate value",
                    row_number=int(index) + 2,
                )
            )

    duplicate_mask = valid["timestamp"].duplicated(keep=False)
    for index in valid.index[duplicate_mask]:
        issues.append(
            DataIssue(
                category="duplicate_timestamp",
                source_file=path.name,
                message="duplicate timestamp retained for explicit resolution",
                row_number=int(index) + 2,
            )
        )
    conflict_columns = (
        ("glucose_mmol_l",)
        if timestamp_column == "bg_ts"
        else ("carbs_g", "meal_type", "meal_tag", "prot_g", "fat_g", "fibre_g")
    )
    _record_duplicate_conflicts(
        valid,
        "timestamp",
        conflict_columns,
        path.name,
        issues,
    )

    return valid.reset_index(drop=True), pd.DataFrame(quarantined_rows)


def load_manchester(root: str | Path) -> ManchesterDataset:
    """Load Manchester CSVs without labels, joins, interpolation, or imputation."""

    root_path = Path(root)
    participants = _discover_files(root_path)
    issues: list[DataIssue] = []
    glucose: dict[str, pd.DataFrame] = {}
    nutrition: dict[str, pd.DataFrame] = {}
    quarantined_frames: list[pd.DataFrame] = []

    for participant in participants:
        if participant.glucose_files:
            frames = []
            for path in participant.glucose_files:
                valid, quarantined = _read_csv(
                    path, "bg_ts", GLUCOSE_COLUMNS, participant.participant_id, issues
                )
                frames.append(valid)
                if not quarantined.empty:
                    quarantined_frames.append(quarantined)
            glucose[participant.participant_id] = pd.concat(
                frames, ignore_index=True
            )
            _record_cross_file_duplicates(
                glucose[participant.participant_id],
                ("glucose_mmol_l",),
                issues,
            )
        if participant.nutrition_files:
            frames = []
            for path in participant.nutrition_files:
                valid, quarantined = _read_csv(
                    path,
                    "meal_ts",
                    NUTRITION_COLUMNS,
                    participant.participant_id,
                    issues,
                )
                frames.append(valid)
                if not quarantined.empty:
                    quarantined_frames.append(quarantined)
            nutrition[participant.participant_id] = pd.concat(
                frames, ignore_index=True
            )
            _record_cross_file_duplicates(
                nutrition[participant.participant_id],
                ("carbs_g", "meal_type", "meal_tag", "prot_g", "fat_g", "fibre_g"),
                issues,
            )

    quarantined = (
        pd.concat(quarantined_frames, ignore_index=True)
        if quarantined_frames
        else pd.DataFrame()
    )
    return ManchesterDataset(
        participants=participants,
        glucose=glucose,
        nutrition=nutrition,
        quarantined=quarantined,
        issues=tuple(issues),
    )
