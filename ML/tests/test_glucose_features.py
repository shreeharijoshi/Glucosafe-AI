from datetime import datetime, timedelta

import pandas as pd

from src.features import build_glucose_features


START = datetime(2023, 10, 13, 12, 0)


def glucose_frame(values, *, participant_id="2301", source_file="glucose.csv"):
    return pd.DataFrame(
        [
            {
                "timestamp": START + timedelta(minutes=minute),
                "glucose_mg_dl": value,
                "participant_id": participant_id,
                "source_file": source_file,
            }
            for minute, value in values
        ]
    )


def predictions(*, participant_id="2301", source_file="glucose.csv"):
    return pd.DataFrame(
        {
            "prediction_timestamp": [pd.Timestamp(START)],
            "participant_id": [participant_id],
            "source_file": [source_file],
        }
    )


def test_exact_and_tolerated_history_and_changes():
    glucose = glucose_frame([(0, 100), (-5, 95), (-10, 90), (-15, 85)])

    result = build_glucose_features(glucose, predictions())
    row = result.iloc[0]

    assert row["current_glucose_mg_dl"] == 100
    assert row["current_glucose_age_minutes"] == 0
    assert row["glucose_5min_before_mg_dl"] == 95
    assert row["glucose_10min_before_mg_dl"] == 90
    assert row["glucose_15min_before_mg_dl"] == 85
    assert row["glucose_change_5min_mg_dl"] == 5


def test_tolerance_and_no_future_leakage():
    glucose = glucose_frame([(0, 100), (-11, 89), (-16, 86), (1, 40)])

    row = build_glucose_features(glucose, predictions()).iloc[0]

    assert pd.isna(row["glucose_5min_before_mg_dl"])
    assert row["glucose_10min_before_mg_dl"] == 89
    assert row["glucose_15min_before_mg_dl"] == 86
    assert row["current_glucose_mg_dl"] == 100


def test_missing_history_and_conflicting_duplicates_remain_missing():
    glucose = glucose_frame(
        [(0, 100), (-10, 90), (-10, 91), (-15, 85)]
    )

    row = build_glucose_features(glucose, predictions()).iloc[0]

    assert pd.isna(row["glucose_10min_before_mg_dl"])
    assert pd.isna(row["glucose_change_10min_mg_dl"])


def test_participant_and_recording_partitions_are_isolated():
    first = glucose_frame([(0, 100), (-5, 95)], source_file="first.csv")
    other_participant = glucose_frame(
        [(-10, 10)], participant_id="2302", source_file="other.csv"
    )
    other_partition = glucose_frame(
        [(-10, 20)], source_file="second.csv"
    )
    glucose = pd.concat([first, other_participant, other_partition], ignore_index=True)

    row = build_glucose_features(
        first, predictions(source_file="first.csv")
    ).iloc[0]
    assert row["glucose_5min_before_mg_dl"] == 95

    isolated = build_glucose_features(
        glucose,
        predictions(source_file="first.csv"),
    ).iloc[0]
    assert pd.isna(isolated["glucose_10min_before_mg_dl"])
