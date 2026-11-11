import pandas as pd

from src.evaluation.baseline import evaluate_model_a
from src.integration.model_a import MODEL_A_FEATURE_COLUMNS


def test_baseline_evaluation_writes_predictions_and_report(tmp_path):
    rows = []
    for participant, offset in (("2301", 0.0), ("2302", 1.0)):
        for index in range(4):
            rows.append(
                {
                    "participant_id": participant,
                    "prediction_timestamp": f"2023-10-13 12:{index:02d}",
                    "target": int((index + (participant == "2302")) % 2),
                    **{column: 1.0 + offset + index for column in MODEL_A_FEATURE_COLUMNS},
                }
            )
    dataset_path = tmp_path / "dataset.csv"
    manifest_path = tmp_path / "manifest.csv"
    pd.DataFrame(rows).to_csv(dataset_path, index=False)
    pd.DataFrame(
        {
            "held_out_participant_id": ["2301", "2302"],
            "training_participant_ids": ["2302", "2301"],
        }
    ).to_csv(manifest_path, index=False)

    predictions_path, report_path = evaluate_model_a(
        dataset_path, manifest_path, tmp_path / "outputs"
    )

    predictions = pd.read_csv(predictions_path)
    assert len(predictions) == len(rows)
    assert predictions["participant_id"].nunique() == 2
    assert report_path.read_text(encoding="utf-8").startswith(
        "# Model A LOPO Baseline Evaluation"
    )
