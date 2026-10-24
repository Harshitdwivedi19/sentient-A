"""
tests/test_baseline.py

Automated unit tests to verify:
1. Existence of saved model artifacts for TF-IDF baseline.
2. Prediction schema and valid probability bounds.
3. Polarity score calculation: s_t = prob_positive - prob_negative in [-1, +1].
4. Metric file adherence and baseline performance bounds.
"""

from pathlib import Path
import json
import numpy as np
import pandas as pd
import pytest

MODELS_DIR = Path("models/baseline_tfidf")
PREDS_PATH = Path("outputs/predictions/val_predictions_tfidf.csv")
METRICS_PATH = Path("outputs/metrics/val_metrics_tfidf.json")


def test_model_artifacts_exist():
    assert (MODELS_DIR / "tfidf_vectorizer.joblib").exists(), "TF-IDF vectorizer artifact missing."
    assert (MODELS_DIR / "logistic_regression.joblib").exists(), "Logistic Regression artifact missing."


def test_predictions_schema_and_integrity():
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


def test_metrics_report_structure():
    assert METRICS_PATH.exists(), f"Metrics JSON missing: {METRICS_PATH}"
    with open(METRICS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "best_configuration" in data
    assert "configurations" in data
    best_config = data["best_configuration"]
    stats = data["configurations"][best_config]

    assert stats["accuracy"] > 0.40, f"Unreasonably low baseline accuracy: {stats['accuracy']}"
    assert stats["macro_f1"] > 0.40, f"Unreasonably low baseline macro-F1: {stats['macro_f1']}"
    assert "calibration" in stats
    assert "brier_score" in stats["calibration"]
    assert "expected_calibration_error" in stats["calibration"]
