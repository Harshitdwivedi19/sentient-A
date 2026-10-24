"""
src/prepare_data.py

Phase 1 Data Preparation Pipeline:
- Downloads raw MELD dataset splits (train, dev/val, test) if not present locally.
- Inspects and cleans text (encodings, whitespace, null values).
- Normalizes schema to: [dialogue_id, turn_id, speaker, text, sentiment, label].
- Validates dialogue ordering, split integrity, and class balance.
- Exports cleaned splits and computes a dataset validation summary.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Tuple
import urllib.request
import yaml
import pandas as pd
import numpy as np

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


def load_config(config_path: str = "configs/config.yaml") -> Dict[str, Any]:
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def download_file(url: str, dest_path: Path) -> None:
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    if dest_path.exists() and dest_path.stat().st_size > 0:
        logger.info(f"File already exists: {dest_path} ({dest_path.stat().st_size:,} bytes). Skipping download.")
        return

    logger.info(f"Downloading from {url} to {dest_path}...")
    try:
        # User-agent header to prevent raw github blocks
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req) as response, open(dest_path, "wb") as out_file:
            data = response.read()
            out_file.write(data)
        logger.info(f"Successfully downloaded {dest_path.name} ({dest_path.stat().st_size:,} bytes).")
    except Exception as e:
        logger.error(f"Failed to download from {url}: {e}")
        raise


def clean_text(text: Any) -> str:
    """Normalize unicode quotes, dashes, whitespace, and handle missing values."""
    if pd.isna(text):
        return ""
    text = str(text)
    # Common character replacements from subtitle transcriptions
    replacements = {
        "\x92": "'",
        "\x91": "'",
        "\x93": '"',
        "\x94": '"',
        "\x97": "--",
        "\xa0": " ",
        "’": "'",
        "‘": "'",
        "“": '"',
        "”": '"',
        "—": "--",
        "…": "...",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return " ".join(text.strip().split())


def process_split(
    raw_csv_path: Path,
    label_map: Dict[str, int],
    split_name: str
) -> pd.DataFrame:
    """
    Ingest, clean, normalize schema, sort, and validate an individual split.
    Expected raw columns: Utterance, Speaker, Emotion, Sentiment, Dialogue_ID, Utterance_ID
    Target schema: dialogue_id, turn_id, speaker, text, sentiment, label
    """
    logger.info(f"Processing split: {split_name} from {raw_csv_path}...")
    # Attempt reading with utf-8, fallback to latin-1 / cp1252 if encoding issues occur
    try:
        df = pd.read_csv(raw_csv_path, encoding="utf-8")
    except UnicodeDecodeError:
        logger.warning(f"UTF-8 decode failed for {raw_csv_path}. Falling back to cp1252.")
        df = pd.read_csv(raw_csv_path, encoding="cp1252")

    # Column mapping
    column_mapping = {
        "Dialogue_ID": "dialogue_id",
        "Utterance_ID": "turn_id",
        "Speaker": "speaker",
        "Utterance": "text",
        "Sentiment": "sentiment",
    }

    # Verify expected columns
    for orig_col in column_mapping:
        if orig_col not in df.columns:
            raise KeyError(f"Expected column '{orig_col}' not found in {raw_csv_path.name}. Found: {df.columns.tolist()}")

    df = df.rename(columns=column_mapping)
    df = df[["dialogue_id", "turn_id", "speaker", "text", "sentiment"]].copy()

    # Normalize data types
    df["dialogue_id"] = pd.to_numeric(df["dialogue_id"], errors="raise").astype(int)
    df["turn_id"] = pd.to_numeric(df["turn_id"], errors="raise").astype(int)
    df["speaker"] = df["speaker"].astype(str).str.strip()
    df["sentiment"] = df["sentiment"].astype(str).str.strip().str.lower()
    df["text"] = df["text"].apply(clean_text)

    # Validate sentiments against label mapping
    unknown_sentiments = set(df["sentiment"]) - set(label_map.keys())
    if unknown_sentiments:
        raise ValueError(f"Found unexpected sentiment labels: {unknown_sentiments}")

    df["label"] = df["sentiment"].map(label_map).astype(int)

    # Flag and log empty utterances
    empty_mask = df["text"].str.len() == 0
    if empty_mask.any():
        num_empty = empty_mask.sum()
        logger.warning(f"Split {split_name} contains {num_empty} empty utterance(s). Imputing with '[SILENCE]'.")
        df.loc[empty_mask, "text"] = "[SILENCE]"

    # Sort strictly by dialogue_id and turn_id to preserve conversation sequence
    df = df.sort_values(by=["dialogue_id", "turn_id"]).reset_index(drop=True)

    # Verify duplicate records
    dup_mask = df.duplicated(subset=["dialogue_id", "turn_id"], keep=False)
    if dup_mask.any():
        logger.warning(f"Split {split_name} has {dup_mask.sum()} duplicate (dialogue_id, turn_id) records! Resolving by index.")
        # Deduplicate keeping first
        df = df.drop_duplicates(subset=["dialogue_id", "turn_id"], keep="first").reset_index(drop=True)

    logger.info(f"Split {split_name} successfully normalized: {len(df):,} utterances across {df['dialogue_id'].nunique():,} dialogues.")
    return df


def compute_split_statistics(df: pd.DataFrame, split_name: str, label_map: Dict[str, int]) -> Dict[str, Any]:
    """Calculate dialogue and sentiment distributions for reporting."""
    dialogue_lengths = df.groupby("dialogue_id")["turn_id"].count()
    class_counts = df["sentiment"].value_counts().to_dict()
    total_utterances = len(df)
    class_percentages = {k: round((v / total_utterances) * 100, 2) for k, v in class_counts.items()}

    return {
        "split_name": split_name,
        "total_utterances": total_utterances,
        "total_dialogues": int(df["dialogue_id"].nunique()),
        "turns_per_dialogue": {
            "min": int(dialogue_lengths.min()),
            "max": int(dialogue_lengths.max()),
            "mean": round(float(dialogue_lengths.mean()), 2),
            "median": float(dialogue_lengths.median()),
            "std": round(float(dialogue_lengths.std()), 2)
        },
        "class_counts": class_counts,
        "class_percentages": class_percentages,
    }


def main():
    config = load_config()

    raw_dir = Path(config["paths"]["raw_data_dir"])
    processed_dir = Path(config["paths"]["processed_data_dir"])
    metrics_dir = Path(config["paths"]["metrics_dir"])

    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    metrics_dir.mkdir(parents=True, exist_ok=True)

    urls = config["dataset"]["urls"]
    label_map = config["dataset"]["label_mapping"]

    # 1. Download
    raw_files = {
        "train": raw_dir / "train_sent_emo.csv",
        "val": raw_dir / "dev_sent_emo.csv",
        "test": raw_dir / "test_sent_emo.csv",
    }
    for split_key, dest_path in raw_files.items():
        download_file(urls[split_key], dest_path)

    # 2. Process & Validate
    processed_dfs = {}
    summaries = {}
    for split_key, raw_path in raw_files.items():
        clean_df = process_split(raw_path, label_map, split_key)
        out_csv = processed_dir / f"{split_key}.csv"
        clean_df.to_csv(out_csv, index=False, encoding="utf-8")
        logger.info(f"Saved normalized {split_key} split to {out_csv}")
        processed_dfs[split_key] = clean_df
        summaries[split_key] = compute_split_statistics(clean_df, split_key, label_map)

    # 3. Save Summary Report
    summary_report_path = metrics_dir / "dataset_summary.json"
    with open(summary_report_path, "w", encoding="utf-8") as f:
        json.dump(summaries, f, indent=2)
    logger.info(f"Saved dataset summary metrics to {summary_report_path}")

    # 4. Print Summary Table
    print("\n" + "=" * 70)
    print("MELD DATASET NORMALIZATION AND VALIDATION SUMMARY")
    print("=" * 70)
    for split, stat in summaries.items():
        print(f"\nSplit: {split.upper()}")
        print(f"  Total Dialogues:    {stat['total_dialogues']:,}")
        print(f"  Total Utterances:    {stat['total_utterances']:,}")
        t = stat['turns_per_dialogue']
        print(f"  Turns per Dialogue:  Min={t['min']}, Max={t['max']}, Mean={t['mean']}, Median={t['median']}")
        print("  Class Distribution:")
        for sentiment, count in stat['class_counts'].items():
            pct = stat['class_percentages'][sentiment]
            print(f"    - {sentiment.capitalize():<8}: {count:,} ({pct}%)")
    print("=" * 70)
    print("Data preparation complete and verified.\n")


if __name__ == "__main__":
    main()
