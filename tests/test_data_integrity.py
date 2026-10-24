"""
tests/test_data_integrity.py

Automated unit tests to verify:
1. File existence and schema adherence.
2. Label integrity and alignment with specified numerical mapping (0: neg, 1: neu, 2: pos).
3. Monotonic turn order within every dialogue (no cross-contamination).
4. No empty text, missing values, or unhandled nulls.
"""

from pathlib import Path
import pandas as pd
import pytest
import yaml

PROCESSED_DIR = Path("data/processed")
CONFIG_PATH = Path("configs/config.yaml")


@pytest.fixture(scope="module")
def config():
    assert CONFIG_PATH.exists(), f"Configuration file not found: {CONFIG_PATH}"
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="module")
def splits(config):
    splits_dict = {}
    for split in ["train", "val", "test"]:
        file_path = PROCESSED_DIR / f"{split}.csv"
        assert file_path.exists(), f"Processed split missing: {file_path}. Run src/prepare_data.py first."
        df = pd.read_csv(file_path)
        splits_dict[split] = df
    return splits_dict


def test_schema_adherence(splits):
    expected_columns = ["dialogue_id", "turn_id", "speaker", "text", "sentiment", "label"]
    for split_name, df in splits.items():
        assert list(df.columns) == expected_columns, (
            f"Split '{split_name}' columns {list(df.columns)} do not match expected schema {expected_columns}"
        )


def test_no_null_or_empty_values(splits):
    for split_name, df in splits.items():
        assert df["dialogue_id"].isna().sum() == 0, f"Null dialogue_id found in {split_name}"
        assert df["turn_id"].isna().sum() == 0, f"Null turn_id found in {split_name}"
        assert df["speaker"].isna().sum() == 0, f"Null speaker found in {split_name}"
        assert df["text"].isna().sum() == 0, f"Null text found in {split_name}"
        assert (df["text"].str.strip() == "").sum() == 0, f"Empty string text found in {split_name}"
        assert df["sentiment"].isna().sum() == 0, f"Null sentiment found in {split_name}"
        assert df["label"].isna().sum() == 0, f"Null label found in {split_name}"


def test_label_mapping_consistency(splits, config):
    label_map = config["dataset"]["label_mapping"]
    expected_labels = set(label_map.values())

    for split_name, df in splits.items():
        unique_labels = set(df["label"].unique())
        assert unique_labels == expected_labels, (
            f"Split '{split_name}' has labels {unique_labels}, expected {expected_labels}"
        )
        # Check mapping correctness
        for sentiment, expected_idx in label_map.items():
            subset = df[df["sentiment"] == sentiment]
            if len(subset) > 0:
                assert (subset["label"] == expected_idx).all(), (
                    f"Label mismatch in {split_name} for sentiment '{sentiment}'"
                )


def test_monotonic_turn_ordering(splits):
    """Ensure turns within each dialogue are strictly monotonic and sorted."""
    for split_name, df in splits.items():
        for diag_id, group in df.groupby("dialogue_id"):
            turn_ids = group["turn_id"].tolist()
            assert turn_ids == sorted(turn_ids), (
                f"Dialogue {diag_id} in {split_name} is not sorted chronologically: {turn_ids}"
            )
            # Ensure unique turn IDs per dialogue
            assert len(turn_ids) == len(set(turn_ids)), (
                f"Dialogue {diag_id} in {split_name} has duplicate turn_ids!"
            )


def test_dialogue_counts_and_sizes(splits):
    """Sanity checks on dataset size based on MELD publications."""
    assert len(splits["train"]) > 9000, f"Train split unexpectedly small: {len(splits['train'])}"
    assert len(splits["val"]) > 1000, f"Val split unexpectedly small: {len(splits['val'])}"
    assert len(splits["test"]) > 2000, f"Test split unexpectedly small: {len(splits['test'])}"
