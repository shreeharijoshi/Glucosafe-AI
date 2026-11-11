"""Glucose-only historical features for Model A."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


LOOKBACK_MINUTES = (5, 10, 15)


@dataclass(frozen=True)
class _Partition:
    timestamps: pd.DatetimeIndex
    values: pd.Series
    conflicts: frozenset[pd.Timestamp]


def _build_partition(frame: pd.DataFrame) -> _Partition:
    valid = frame.dropna(subset=["timestamp"]).copy()
    valid["glucose_mg_dl"] = pd.to_numeric(
        valid["glucose_mg_dl"], errors="coerce"
    )
    conflicts: set[pd.Timestamp] = set()
    values: dict[pd.Timestamp, float] = {}
    for timestamp, group in valid.groupby("timestamp", sort=True):
        numeric_values = group["glucose_mg_dl"].dropna().astype(float).unique()
        if group["glucose_mg_dl"].isna().any() or len(numeric_values) > 1:
            conflicts.add(timestamp)
        else:
            values[timestamp] = float(numeric_values[0])
    timestamps = pd.DatetimeIndex(sorted(values.keys() | conflicts))
    return _Partition(
        timestamps=timestamps,
        values=pd.Series(
            [values.get(timestamp, float("nan")) for timestamp in timestamps],
            index=range(len(timestamps)),
            dtype="float64",
        ),
        conflicts=frozenset(conflicts),
    )


def _lookup(
    partition: _Partition,
    requested: pd.Timestamp,
    tolerance: pd.Timedelta | None,
) -> tuple[float | None, float | None]:
    index = partition.timestamps.searchsorted(requested, side="right") - 1
    if index < 0:
        return None, None
    timestamp = partition.timestamps[index]
    if timestamp in partition.conflicts:
        return None, None
    age = requested - timestamp
    if tolerance is not None and age > tolerance:
        return None, None
    return float(partition.values.iloc[index]), age.total_seconds() / 60


def _lookup_many(
    partition: _Partition,
    requested: pd.DatetimeIndex,
    tolerance: pd.Timedelta | None,
) -> tuple[np.ndarray, np.ndarray]:
    values = np.full(len(requested), np.nan)
    ages = np.full(len(requested), np.nan)
    valid_requested = ~requested.isna()
    if not valid_requested.any():
        return values, ages
    indices = partition.timestamps.searchsorted(
        requested[valid_requested], side="right"
    ) - 1
    requested_positions = np.flatnonzero(valid_requested)
    for position, index in zip(requested_positions, indices):
        if index < 0:
            continue
        timestamp = partition.timestamps[index]
        if timestamp in partition.conflicts:
            continue
        age = requested[position] - timestamp
        if tolerance is not None and age > tolerance:
            continue
        values[position] = partition.values.iloc[index]
        ages[position] = age.total_seconds() / 60
    return values, ages


def build_glucose_features(
    glucose: pd.DataFrame,
    predictions: pd.DataFrame | pd.Series,
    *,
    max_lookback_minutes: int = 5,
) -> pd.DataFrame:
    """Build mg/dL glucose-history features without future observations.

    ``glucose`` requires ``timestamp`` and ``glucose_mg_dl``. ``predictions``
    requires ``prediction_timestamp`` (or a timestamp Series). Historical
    values use the latest valid reading at or before each requested time within
    the tolerance. Missing or conflicting values remain missing; no
    interpolation, averaging, or zero-filling is performed.
    """

    if max_lookback_minutes < 0:
        raise ValueError("max_lookback_minutes must be non-negative")
    required = {"timestamp", "glucose_mg_dl"}
    missing = required - set(glucose.columns)
    if missing:
        raise ValueError(f"missing required glucose columns: {sorted(missing)}")

    if isinstance(predictions, pd.Series):
        prediction_frame = pd.DataFrame(
            {"prediction_timestamp": predictions.to_numpy()}
        )
    else:
        if "prediction_timestamp" not in predictions.columns:
            raise ValueError("predictions must contain prediction_timestamp")
        prediction_frame = predictions.copy()

    frame = glucose.copy()
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], errors="coerce")
    frame["glucose_mg_dl"] = pd.to_numeric(
        frame["glucose_mg_dl"], errors="coerce"
    )
    frame["_participant"] = (
        frame["participant_id"].astype(str)
        if "participant_id" in frame
        else ""
    )
    frame["_source"] = (
        frame["source_file"].astype(str)
        if "source_file" in frame
        else ""
    )
    keys = ["_participant", "_source"]
    partitions = {
        key: _build_partition(group)
        for key, group in frame.groupby(keys, sort=False, dropna=False)
    }

    output = prediction_frame.copy()
    output["prediction_timestamp"] = pd.to_datetime(
        output["prediction_timestamp"], errors="coerce"
    )
    if "participant_id" not in output:
        if len({key[0] for key in partitions}) != 1:
            raise ValueError("predictions require participant_id for multiple participants")
        output["participant_id"] = next(iter(partitions))[0]
    if "source_file" not in output:
        sources = {key[1] for key in partitions}
        if len(sources) != 1:
            raise ValueError("predictions require source_file for multiple partitions")
        output["source_file"] = next(iter(sources))

    tolerance = pd.Timedelta(minutes=max_lookback_minutes)
    feature_columns = [
        "current_glucose_mg_dl",
        "current_glucose_age_minutes",
        *[
            name
            for minutes in LOOKBACK_MINUTES
            for name in (
                f"glucose_{minutes}min_before_mg_dl",
                f"glucose_change_{minutes}min_mg_dl",
            )
        ],
    ]
    for column in feature_columns:
        output[column] = np.nan

    for key, prediction_group in output.groupby(
        ["participant_id", "source_file"], sort=False, dropna=False
    ):
        partition = partitions.get((str(key[0]), str(key[1])))
        if partition is None:
            continue
        positions = prediction_group.index.to_numpy()
        timestamps = pd.DatetimeIndex(prediction_group["prediction_timestamp"])
        current, current_age = _lookup_many(partition, timestamps, None)
        output.loc[positions, "current_glucose_mg_dl"] = current
        output.loc[positions, "current_glucose_age_minutes"] = current_age
        for minutes in LOOKBACK_MINUTES:
            historical, _ = _lookup_many(
                partition,
                timestamps - pd.Timedelta(minutes=minutes),
                tolerance,
            )
            output.loc[
                positions, f"glucose_{minutes}min_before_mg_dl"
            ] = historical
            output.loc[
                positions, f"glucose_change_{minutes}min_mg_dl"
            ] = current - historical

    return output[
        ["prediction_timestamp", "participant_id", "source_file", *feature_columns]
    ]
