"""
src/evaluate.py

Evaluation module providing:
- Classification metrics: Accuracy, Macro-F1, Weighted-F1, per-class Precision/Recall/F1.
- Confusion matrix computation and plotting.
- Probability quality: Multiclass Brier Score and Expected Calibration Error (ECE).
- Export of metrics to JSON and figures to PNG.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_recall_fscore_support,
    confusion_matrix,
)


def compute_multiclass_brier_score(y_true: np.ndarray, y_prob: np.ndarray, num_classes: int = 3) -> float:
    """
    Computes multi-class Brier score:
    Brier = (1 / N) * sum_{i=1}^N sum_{k=0}^{K-1} (p_{ik} - y_{ik})^2
    Lower is better (0.0 is perfect calibration, worst is 2.0).
    """
    N = len(y_true)
    if N == 0:
        return 0.0
    # One-hot encode y_true
    y_one_hot = np.zeros((N, num_classes))
    y_one_hot[np.arange(N), y_true] = 1.0
    return float(np.mean(np.sum((y_prob - y_one_hot) ** 2, axis=1)))


def compute_expected_calibration_error(
    y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 10
) -> float:
    """
    Expected Calibration Error (ECE) for multi-class predictions.
    ECE = sum_{m=1}^M (|B_m| / N) * |acc(B_m) - conf(B_m)|
    """
    confidences = np.max(y_prob, axis=1)
    predictions = np.argmax(y_prob, axis=1)
    accuracies = (predictions == y_true)

    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    n_samples = len(y_true)

    for i in range(n_bins):
        bin_lower = bin_boundaries[i]
        bin_upper = bin_boundaries[i + 1]

        # In bin mask
        if i == n_bins - 1:
            in_bin = (confidences >= bin_lower) & (confidences <= bin_upper)
        else:
            in_bin = (confidences >= bin_lower) & (confidences < bin_upper)

        bin_size = np.sum(in_bin)
        if bin_size > 0:
            bin_acc = np.mean(accuracies[in_bin])
            bin_conf = np.mean(confidences[in_bin])
            ece += (bin_size / n_samples) * np.abs(bin_acc - bin_conf)

    return float(ece)


def evaluate_predictions(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_prob: Optional[np.ndarray] = None,
    target_names: Optional[List[str]] = None,
    model_name: str = "model",
    split_name: str = "val"
) -> Dict[str, Any]:
    """
    Compute comprehensive classification, per-class, and probability metrics.
    """
    if target_names is None:
        target_names = ["negative", "neutral", "positive"]

    acc = float(accuracy_score(y_true, y_pred))
    macro_f1 = float(f1_score(y_true, y_pred, average="macro"))
    weighted_f1 = float(f1_score(y_true, y_pred, average="weighted"))

    precision, recall, f1, support = precision_recall_fscore_support(
        y_true, y_pred, labels=list(range(len(target_names))), zero_division=0
    )

    per_class_metrics = {}
    for i, name in enumerate(target_names):
        per_class_metrics[name] = {
            "precision": round(float(precision[i]), 4),
            "recall": round(float(recall[i]), 4),
            "f1": round(float(f1[i]), 4),
            "support": int(support[i]),
        }

    cm = confusion_matrix(y_true, y_pred, labels=list(range(len(target_names))))

    report = {
        "model_name": model_name,
        "split_name": split_name,
        "accuracy": round(acc, 4),
        "macro_f1": round(macro_f1, 4),
        "weighted_f1": round(weighted_f1, 4),
        "per_class": per_class_metrics,
        "confusion_matrix": cm.tolist(),
    }

    if y_prob is not None:
        brier = compute_multiclass_brier_score(y_true, y_prob, num_classes=len(target_names))
        ece = compute_expected_calibration_error(y_true, y_prob)
        report["calibration"] = {
            "brier_score": round(brier, 4),
            "expected_calibration_error": round(ece, 4),
        }

    return report


def plot_and_save_confusion_matrix(
    cm: np.ndarray,
    target_names: List[str],
    output_path: Path,
    title: str = "Confusion Matrix"
) -> None:
    """Save normalized confusion matrix plot."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(6, 5))
    cm_norm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
    sns.heatmap(
        cm_norm,
        annot=True,
        fmt=".2%",
        cmap="Blues",
        xticklabels=target_names,
        yticklabels=target_names,
        cbar=True
    )
    plt.title(title, fontsize=12, pad=12)
    plt.ylabel("True Label", fontsize=10)
    plt.xlabel("Predicted Label", fontsize=10)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
