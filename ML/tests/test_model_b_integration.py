import pandas as pd

from src.integration.model_a import MODEL_A_FEATURE_COLUMNS
from src.integration.model_b import build_model_b_dataset


def test_model_b_window_boundaries_sum_and_exclude_future():
    start = pd.Timestamp("2023-10-13 12:00")
    model_a = pd.DataFrame([{
        "participant_id": "2301", "prediction_timestamp": start,
        "source_file": "UoMGlucose2301.csv", "target": 0, "status": "known", "reason": "ok",
        **{column: 100.0 for column in MODEL_A_FEATURE_COLUMNS},
    }])
    nutrition = pd.DataFrame({
        "timestamp": [start - pd.Timedelta(minutes=30), start - pd.Timedelta(minutes=15), start + pd.Timedelta(minutes=1)],
        "carbs_g": [60, 25, 99], "meal_type": ["a", "b", "c"], "meal_tag": ["x"] * 3,
        "prot_g": [1] * 3, "fat_g": [1] * 3, "fibre_g": [1] * 3,
        "source_file": ["UoMNutrition2301.csv"] * 3,
    })
    result, audit = build_model_b_dataset(model_a, {"2301": nutrition})
    assert result.iloc[0]["carbs_30min_g"] == 85
    assert audit.empty


def test_model_b_rejects_bad_values_conflicts_and_preserves_participants():
    start = pd.Timestamp("2023-10-13 12:00")
    model_a = pd.DataFrame([
        {"participant_id": participant, "prediction_timestamp": start, "source_file": f"{participant}.csv",
         "target": 0, "status": "known", "reason": "ok",
         **{column: 100.0 for column in MODEL_A_FEATURE_COLUMNS}}
        for participant in ("2301", "2302")
    ])
    nutrition = pd.DataFrame({
        "timestamp": [start - pd.Timedelta(minutes=5), start - pd.Timedelta(minutes=5)],
        "carbs_g": [pd.NA, 20], "meal_type": ["a", "a"], "meal_tag": ["x", "x"],
        "prot_g": [1, 1], "fat_g": [1, 1], "fibre_g": [1, 1],
        "source_file": ["n.csv", "n.csv"],
    })
    result, audit = build_model_b_dataset(model_a, {"2301": nutrition})
    assert result.empty
    assert set(audit["participant_id"]) == {"2301", "2302"}
    assert "no_nutrition_records" in set(audit["reason"])


def test_model_b_counts_exact_duplicates_once_and_rejects_negative_values():
    start = pd.Timestamp("2023-10-13 12:00")
    model_a = pd.DataFrame([{
        "participant_id": "2301", "prediction_timestamp": start,
        "source_file": "UoMGlucose2301.csv", "target": 0, "status": "known", "reason": "ok",
        **{column: 100.0 for column in MODEL_A_FEATURE_COLUMNS},
    }])
    nutrition = pd.DataFrame({
        "timestamp": [start - pd.Timedelta(minutes=5), start - pd.Timedelta(minutes=5)],
        "carbs_g": [20, 20], "meal_type": ["a", "a"], "meal_tag": ["x", "x"],
        "prot_g": [1, 1], "fat_g": [1, 1], "fibre_g": [1, 1],
        "source_file": ["n.csv", "n.csv"],
    })
    result, audit = build_model_b_dataset(model_a, {"2301": nutrition})
    assert result.iloc[0]["carbs_30min_g"] == 20
    assert audit.empty

    negative_nutrition = nutrition.iloc[[0]].copy()
    negative_nutrition.loc[:, "carbs_g"] = -1
    result, audit = build_model_b_dataset(model_a, {"2301": negative_nutrition})
    assert result.empty
    assert "negative_carbohydrate" in set(audit["reason"])
