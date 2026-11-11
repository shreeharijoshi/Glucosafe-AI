from datetime import datetime, timedelta

import pandas as pd

from src.targets import build_glucose_targets


def glucose_frame(values, *, participant_id="2301", source_file=None):
    start = datetime(2023, 10, 13, 12, 0)
    rows = [
        {
            "timestamp": start + timedelta(minutes=minutes),
            "glucose_mg_dl": value,
            "participant_id": participant_id,
        }
        for minutes, value in values
    ]
    if source_file is not None:
        for row in rows:
            row["source_file"] = source_file
    return pd.DataFrame(rows)


def target_at(result, minute=0):
    timestamp = pd.Timestamp("2023-10-13 12:00") + pd.Timedelta(minutes=minute)
    return result.loc[
        result["prediction_timestamp"] == timestamp
    ].iloc[0]


def test_below_threshold_in_horizon_is_positive():
    result = build_glucose_targets(
        glucose_frame([(0, 100), (5, 80), (10, 80), (20, 69), (30, 80)])
    )
    assert target_at(result)["target"] == 1


def test_value_at_prediction_time_is_excluded():
    result = build_glucose_targets(
        glucose_frame([(0, 69), (10, 80), (20, 80), (30, 80), (40, 80)])
    )
    assert target_at(result)["target"] == 0


def test_adequate_non_low_values_are_negative_and_70_is_not_low():
    result = build_glucose_targets(
        glucose_frame([(0, 100), (10, 70), (20, 80), (30, 80), (40, 80)])
    )
    assert target_at(result)["target"] == 0


def test_endpoint_is_included_but_late_value_cannot_make_target_positive():
    result = build_glucose_targets(
        glucose_frame([(0, 100), (10, 80), (20, 80), (30, 69), (40, 80)])
    )
    assert target_at(result)["target"] == 1

    result = build_glucose_targets(
        glucose_frame([(0, 100), (10, 80), (20, 80), (30, 80), (40, 69)])
    )
    assert target_at(result)["target"] == 0


def test_missing_coverage_and_long_gap_are_unknown():
    missing = build_glucose_targets(glucose_frame([(0, 100), (20, 80)]))
    assert pd.isna(target_at(missing)["target"])
    assert target_at(missing)["reason"] == "missing_endpoint_coverage"

    gap = build_glucose_targets(
        glucose_frame([(0, 100), (5, 80), (16, 80), (30, 80), (40, 80)])
    )
    assert pd.isna(target_at(gap)["target"])
    assert target_at(gap)["reason"] == "glucose_gap_over_10_minutes"


def test_conflicting_duplicate_is_unknown_and_participants_cannot_mix():
    duplicate = glucose_frame(
        [(0, 100), (0, 90), (10, 80), (20, 80), (30, 80), (40, 80)]
    )
    result = build_glucose_targets(duplicate)
    assert pd.isna(target_at(result)["target"])
    assert target_at(result)["reason"] == "conflicting_duplicate_glucose"

    mixed = pd.concat(
        [
            glucose_frame([(0, 100), (30, 80), (40, 80)], participant_id="2301"),
            glucose_frame([(0, 60), (30, 80), (40, 80)], participant_id="2302"),
        ],
        ignore_index=True,
    )
    try:
        build_glucose_targets(mixed)
    except ValueError as error:
        assert "one participant" in str(error)
    else:
        raise AssertionError("mixed participants must be rejected")


def test_recording_partitions_do_not_supply_each_other_coverage():
    first = glucose_frame(
        [(0, 100), (10, 80)],
        source_file="first.csv",
    )
    second = glucose_frame(
        [(30, 69), (40, 80)],
        source_file="second.csv",
    )

    result = build_glucose_targets(pd.concat([first, second], ignore_index=True))

    first_target = result.loc[
        (result["source_file"] == "first.csv")
        & (result["prediction_timestamp"] == pd.Timestamp("2023-10-13 12:00"))
    ].iloc[0]
    assert pd.isna(first_target["target"])
    assert first_target["reason"] == "missing_endpoint_coverage"
