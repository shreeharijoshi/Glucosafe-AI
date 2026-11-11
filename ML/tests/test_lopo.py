import pandas as pd

from src.evaluation import build_lopo_manifest


def test_lopo_manifest_is_deterministic_and_preserves_sparse_participants():
    dataset = pd.DataFrame(
        {
            "participant_id": ["2302", "2301", "2302", "2303", "2303"],
            "target": [0, 1, 1, pd.NA, 0],
            "current_glucose_mg_dl": [100, 100, 90, 100, 80],
            "current_glucose_age_minutes": [0, 0, 0, 0, 0],
            "glucose_5min_before_mg_dl": [95, 95, 85, 95, 75],
            "glucose_10min_before_mg_dl": [90, 90, 80, 90, 70],
            "glucose_15min_before_mg_dl": [85, 85, 75, 85, 65],
            "glucose_change_5min_mg_dl": [5, 5, 5, 5, 5],
            "glucose_change_10min_mg_dl": [10, 10, 10, 10, 10],
            "glucose_change_15min_mg_dl": [15, 15, 15, 15, 15],
        }
    )
    dataset.loc[4, "glucose_10min_before_mg_dl"] = pd.NA

    manifest = build_lopo_manifest(dataset)

    assert manifest["held_out_participant_id"].tolist() == ["2301", "2302"]
    assert len(manifest) == 2
    assert manifest.loc[0, "held_out_rows"] == 1
    assert manifest.loc[0, "held_out_positive"] == 1
    assert manifest.loc[1, "held_out_rows"] == 2
    assert manifest.loc[1, "held_out_positive"] == 1
    assert manifest.loc[0, "training_participant_ids"] == "2302"
    assert manifest.loc[1, "training_participant_ids"] == "2301"
