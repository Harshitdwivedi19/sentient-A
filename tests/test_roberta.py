"""
tests/test_roberta.py

Automated unit tests to verify:
1. Existence of saved model artifacts and tokenizer for RoBERTa independent model.
2. Prediction schema, probability bounds, and polarity score validity.
3. Calibration metrics (Brier score & ECE).
"""

from pathlib import Path
import json
import numpy as np
import pandas as pd
import pytest

ROBERTA_DIR = Path("models/roberta_independent")
PREDS_PATH = Path("outputs/predictions/val_predictions_roberta_independent.csv")
METRICS_PATH = Path("outputs/metrics/val_metrics_roberta_independent.json")


def test_roberta_artifacts_exist():
    assert ROBERTA_DIR.exists(), "RoBERTa model directory missing."
    assert (ROBERTA_DIR / "model.safetensors").exists(), "RoBERTa model.safetensors missing."
    assert (ROBERTA_DIR / "config.json").exists(), "RoBERTa config.json missing."
    assert (ROBERTA_DIR / "tokenizer_config.json").exists(), "Tokenizer config missing."


def test_roberta_predictions_schema_and_probabilities():
    assert PREDS_PATH.exists(), f"Validation predictions missing: {PREDS_PATH}"
    df = pd.read_csv(PREDS_PATH)

    expected_cols = [
        "dialogue_id", "turn_id", "speaker", "text", "sentiment", "label",
        "pred_label", "pred_sentiment", "prob_negative", "prob_neutral",
        "prob_positive", "polarity_score"
    ]
    for col in expected_cols:
        assert col in df.columns, f"Expected column '{col}' missing from predictions."

    # Validate probabilities sum to ~1.0
    prob_sums = df["prob_negative"] + df["prob_neutral"] + df["prob_positive"]
    np.testing.assert_allclose(prob_sums.values, 1.0, atol=1e-3, err_msg="Probabilities do not sum to 1.0")

    # Validate polarity score definition
    calculated_polarity = df["prob_positive"] - df["prob_negative"]
    np.testing.assert_allclose(
        df["polarity_score"].values,
        calculated_polarity.values,
        atol=1e-3,
        err_msg="Polarity score does not match P(positive) - P(negative)"
    )

    # Validate bounds [-1, 1]
    assert (df["polarity_score"] >= -1.0).all(), "Polarity score below -1.0"
    assert (df["polarity_score"] <= 1.0).all(), "Polarity score above +1.0"


def test_roberta_metrics_structure():
    assert METRICS_PATH.exists(), f"Metrics JSON missing: {METRICS_PATH}"
    with open(METRICS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "accuracy" in data
    assert "macro_f1" in data
    assert "per_class" in data
    assert "calibration" in data
    assert "brier_score" in data["calibration"]
    assert "expected_calibration_error" in data["calibration"]
