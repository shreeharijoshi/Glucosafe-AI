import pandas as pd

from src.data.manchester import ManchesterDataset
from src.integration.model_a import MODEL_A_FEATURE_COLUMNS, build_model_a_dataset


def _glucose(participant_id: str, source_file: str, values: list[tuple[int, float]]):
    start = pd.Timestamp("2023-10-13 12:00")
    return pd.DataFrame(
        {
            "participant_id": participant_id,
            "source_file": source_file,
            "timestamp": [start + pd.Timedelta(minutes=m) for m, _ in values],
            "glucose_mg_dl": [value for _, value in values],
        }
    )


def _dataset(glucose: dict[str, pd.DataFrame]) -> ManchesterDataset:
    return ManchesterDataset(
        participants=(),
        glucose=glucose,
        nutrition={},
        quarantined=pd.DataFrame(),
        issues=(),
    )


def test_model_a_join_is_one_to_one_and_preserves_unknowns():
    frame = _glucose(
        "2301",
        "one.csv",
        [(0, 100), (10, 80), (20, 80), (30, 80), (40, 80)],
    )
    result = build_model_a_dataset(_dataset({"2301": frame}))

    assert not result.data.duplicated(
        ["participant_id", "prediction_timestamp", "source_file"]
    ).any()
    assert len(result.data) == result.summary["target_rows"]
    assert result.summary["unknown_targets"] > 0
    assert set(MODEL_A_FEATURE_COLUMNS).issubset(result.data.columns)


def test_model_a_keeps_participants_and_recording_partitions_separate():
    first = _glucose(
        "2301", "first.csv", [(0, 100), (10, 80), (20, 80), (30, 80), (40, 80)]
    )
    second = _glucose(
        "2302", "second.csv", [(0, 60), (10, 80), (20, 80), (30, 80), (40, 80)]
    )
    result = build_model_a_dataset(_dataset({"2301": first, "2302": second}))

    assert set(result.data["participant_id"]) == {"2301", "2302"}
    assert set(result.data["source_file"]) == {"first.csv", "second.csv"}
    assert result.summary["unmatched_target_feature_rows"] == 0
