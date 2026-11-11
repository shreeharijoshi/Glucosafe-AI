"""Leakage-safe glucose target construction."""

from __future__ import annotations

import pandas as pd


HORIZON = pd.Timedelta(minutes=30)
MAX_COVERAGE_DELAY = pd.Timedelta(minutes=10)
LOW_GLUCOSE_THRESHOLD = 70.0


def _as_partition(frame: pd.DataFrame) -> pd.Series:
    if "participant_id" in frame.columns:
        participants = frame["participant_id"].dropna().unique()
        if len(participants) > 1:
            raise ValueError("target construction requires one participant")
    if "source_file" in frame.columns:
        return frame["source_file"].fillna("<missing-source-file>").astype(str)
    return pd.Series("<single-recording>", index=frame.index, dtype="string")


def _unique_values(group: pd.DataFrame) -> set[float]:
    values = pd.to_numeric(group["glucose_mg_dl"], errors="coerce").dropna()
    return set(values.astype(float).tolist())


def _interval_has_quality_issue(
    frame: pd.DataFrame,
    start: pd.Timestamp,
    end: pd.Timestamp,
    timestamp_column: str,
) -> bool:
    interval = frame[
        frame[timestamp_column].between(start, end, inclusive="both")
    ]
    if interval.empty:
        return False
    return interval["glucose_mg_dl"].isna().any()


def _reasoned_target(
    timestamp: pd.Timestamp,
    segment: pd.DataFrame,
    valid_timestamps: pd.Series,
    invalid_timestamps: pd.Series,
    duplicate_reasons: dict[pd.Timestamp, str],
) -> tuple[int | None, str, str]:
    endpoint = timestamp + HORIZON
    coverage_index = valid_timestamps.searchsorted(endpoint, side="left")
    if coverage_index >= len(valid_timestamps):
        return None, "unknown", "missing_endpoint_coverage"

    coverage_timestamp = valid_timestamps.iloc[coverage_index]
    if coverage_timestamp - endpoint > MAX_COVERAGE_DELAY:
        return None, "unknown", "late_endpoint_coverage"

    start_index = valid_timestamps.searchsorted(timestamp, side="left")
    path_timestamps = valid_timestamps.iloc[start_index : coverage_index + 1]
    if path_timestamps.diff().iloc[1:].gt(pd.Timedelta(minutes=10)).any():
        return None, "unknown", "glucose_gap_over_10_minutes"
    invalid_start = invalid_timestamps.searchsorted(timestamp, side="left")
    invalid_end = invalid_timestamps.searchsorted(coverage_timestamp, side="right")
    if invalid_end > invalid_start:
        return None, "unknown", "invalid_glucose_in_coverage_interval"

    affected = [
        duplicate_timestamp
        for duplicate_timestamp in duplicate_reasons
        if timestamp <= duplicate_timestamp <= coverage_timestamp
    ]
    if affected:
        return None, "unknown", duplicate_reasons[affected[0]]

    target_start = valid_timestamps.searchsorted(timestamp, side="right")
    target_end = valid_timestamps.searchsorted(endpoint, side="right")
    target_values = segment.iloc[target_start:target_end]["glucose_mg_dl"]
    if (target_values < LOW_GLUCOSE_THRESHOLD).any():
        return 1, "known", "below_threshold_in_30_minute_horizon"
    return 0, "known", "no_value_below_threshold_with_coverage"


def build_glucose_targets(glucose: pd.DataFrame) -> pd.DataFrame:
    """Build one 30-minute target for each valid glucose timestamp.

    The input must be one participant's cleaned glucose frame containing
    ``timestamp`` and ``glucose_mg_dl``. Rows from different ``source_file``
    values are treated as separate recording partitions.
    """

    required = {"timestamp", "glucose_mg_dl"}
    missing = required - set(glucose.columns)
    if missing:
        raise ValueError(f"missing required target columns: {sorted(missing)}")

    frame = glucose.copy()
    frame["_partition"] = _as_partition(frame)
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], errors="coerce")
    frame["glucose_mg_dl"] = pd.to_numeric(
        frame["glucose_mg_dl"], errors="coerce"
    )
    frame = frame.dropna(subset=["timestamp"]).sort_values(
        ["timestamp", "_partition"], kind="mergesort"
    )
    if frame.empty:
        return pd.DataFrame(
            columns=["prediction_timestamp", "target", "status", "reason"]
        )

    grouped = frame.groupby(["_partition", "timestamp"], sort=True, dropna=False)
    duplicate_reasons: dict[pd.Timestamp, str] = {}
    for (partition, timestamp), group in grouped:
        if len(group) > 1:
            values = _unique_values(group)
            if len(values) > 1 or group["glucose_mg_dl"].isna().any():
                duplicate_reasons[(partition, timestamp)] = (
                    "conflicting_duplicate_glucose"
                )
    rows: list[dict[str, object]] = []
    for partition, partition_frame in frame.groupby("_partition", sort=True):
        segment = partition_frame.dropna(
            subset=["glucose_mg_dl"]
        ).sort_values("timestamp")
        segment = segment.reset_index(drop=True)
        valid_timestamps = segment["timestamp"].reset_index(drop=True)
        invalid_timestamps = partition_frame.loc[
            partition_frame["glucose_mg_dl"].isna(), "timestamp"
        ].reset_index(drop=True)
        valid_prediction_timestamps = valid_timestamps.drop_duplicates()
        partition_duplicate_reasons = {
            timestamp: reason
            for (duplicate_partition, timestamp), reason in duplicate_reasons.items()
            if duplicate_partition == partition
        }
        for timestamp in valid_prediction_timestamps:
            duplicate_reason = partition_duplicate_reasons.get(timestamp)
            if duplicate_reason:
                target, status, reason = None, "unknown", duplicate_reason
            else:
                segment_values = segment.reset_index(drop=True)
                target, status, reason = _reasoned_target(
                    timestamp,
                    segment,
                    valid_timestamps,
                    invalid_timestamps,
                    partition_duplicate_reasons,
                )
            row = {
                "prediction_timestamp": timestamp,
                "target": target,
                "status": status,
                "reason": reason,
            }
            if "participant_id" in frame.columns:
                row["participant_id"] = partition_frame["participant_id"].iloc[0]
            if "source_file" in frame.columns:
                row["source_file"] = partition
            rows.append(row)

    result = pd.DataFrame(rows).sort_values(
        "prediction_timestamp", kind="mergesort"
    ).reset_index(drop=True)
    result["target"] = result["target"].astype("Int64")
    columns = ["prediction_timestamp", "target", "status", "reason"]
    if "participant_id" in result.columns:
        columns.append("participant_id")
    if "source_file" in result.columns:
        columns.append("source_file")
    return result[columns]
