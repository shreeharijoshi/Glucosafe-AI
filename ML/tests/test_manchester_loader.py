from pathlib import Path

import pandas as pd
import pytest

from src.data.manchester import MMOL_TO_MGDL, load_manchester


def write_dataset(root: Path) -> None:
    (root / "Glucose Data").mkdir()
    (root / "Nutrition Data").mkdir()
    (root / "Glucose Data" / "UoMGlucose2301.csv").write_text(
        "bg_ts,value\n"
        "13/10/2023 00:00,7.5\n"
        "13/10/2023 00:05,8\n"
        "13/10/2023 00:05,8.1\n"
        "22/04/2204 11:45,7\n",
        encoding="utf-8",
    )
    (root / "Nutrition Data" / "UoMNutrition2301.csv").write_text(
        "meal_ts,meal_type,meal_tag,carbs_g,prot_g,fat_g,fibre_g\n"
        "13/10/2023 12:00,Lunch,Meal,42,10,5,2\n"
        "13/10/2023 13:00,Lunch,Missing,,10,5,2\n"
        "22/04/2204 11:45,Lunch,Anomaly,37,10,14,0\n",
        encoding="utf-8",
    )


def test_loader_parses_day_first_and_converts_glucose(tmp_path: Path) -> None:
    write_dataset(tmp_path)

    result = load_manchester(tmp_path)
    glucose = result.glucose["2301"]

    assert glucose.loc[0, "timestamp"] == pd.Timestamp("2023-10-13 00:00")
    assert glucose.loc[0, "glucose_mg_dl"] == pytest.approx(7.5 * MMOL_TO_MGDL)
    assert glucose.loc[0, "timestamp_raw"] == "13/10/2023 00:00"


def test_loader_preserves_missing_carbohydrates(tmp_path: Path) -> None:
    write_dataset(tmp_path)

    nutrition = load_manchester(tmp_path).nutrition["2301"]

    assert pd.isna(nutrition.loc[1, "carbs_g"])


def test_loader_pairs_participants_and_reports_duplicates(tmp_path: Path) -> None:
    write_dataset(tmp_path)
    (tmp_path / "Glucose Data" / "UoMGlucose9999.csv").write_text(
        "bg_ts,value\n13/10/2023 00:00,7\n", encoding="utf-8"
    )

    result = load_manchester(tmp_path)
    participant = next(p for p in result.participants if p.participant_id == "2301")
    glucose_only = next(p for p in result.participants if p.participant_id == "9999")

    assert participant.has_both_modalities
    assert not glucose_only.has_both_modalities
    assert any(issue.category == "duplicate_timestamp" for issue in result.issues)
    assert any(issue.category == "conflicting_duplicate" for issue in result.issues)


def test_loader_quarantines_suspicious_year_without_correction(tmp_path: Path) -> None:
    write_dataset(tmp_path)

    result = load_manchester(tmp_path)

    assert "22/04/2204 11:45" in result.quarantined["timestamp_raw"].tolist()
    assert "22/04/2204 11:45" not in result.nutrition["2301"]["timestamp_raw"].tolist()


def test_loader_quarantines_malformed_timestamp_with_original_row(tmp_path: Path) -> None:
    write_dataset(tmp_path)
    with (tmp_path / "Nutrition Data" / "UoMNutrition2301.csv").open(
        "a", encoding="utf-8"
    ) as file:
        file.write("not-a-timestamp,Dinner,Malformed,20,10,5,2\n")

    result = load_manchester(tmp_path)

    assert "not-a-timestamp" in result.quarantined["timestamp_raw"].tolist()
    assert any(
        issue.category == "timestamp"
        and issue.message == "invalid timestamp"
        for issue in result.issues
    )
