"""
src/predict.py

Unified Inference Engine.
Loads trained models (TF-IDF Baseline, RoBERTa Independent, RoBERTa Context-Aware)
and runs end-to-end conversation sentiment, trajectory, and explanation analysis
on raw text inputs, WhatsApp exported chats (.txt), or CSV files.
"""

import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
import joblib
import numpy as np
import pandas as pd
import torch
import yaml
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# Ensure project root is in sys.path
def get_project_root() -> Path:
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        if (exe_dir / "configs").exists() or (exe_dir / "models").exists():
            return exe_dir
        if hasattr(sys, "_MEIPASS"):
            return Path(sys._MEIPASS)
        return exe_dir
    return Path(__file__).resolve().parent.parent

PROJECT_ROOT = get_project_root()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.context import build_context_representations
from src.trajectory import compute_trajectory_statistics
from src.explain import generate_conversation_explanation
from src.whatsapp_parser import parse_whatsapp_file, parse_whatsapp_raw_lines, sessionize_messages

logger = logging.getLogger(__name__)


def load_config(config_path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
    if config_path is None:
        cfg = PROJECT_ROOT / "configs" / "config.yaml"
    else:
        cfg = Path(config_path)
        if not cfg.is_absolute():
            cfg = PROJECT_ROOT / cfg
    with open(cfg, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


class ConversationSentimentAnalyzer:
    """Unified analyzer for running sentiment, trajectory, and explanation pipelines."""

    def __init__(self, config_path: str = "configs/config.yaml", default_model: str = "baseline"):
        self.config = load_config(config_path)
        self.target_names = self.config["dataset"]["target_names"]
        self.active_model_type = default_model
        self.loaded_models: Dict[str, Any] = {}
        self._load_model(default_model)

    def _load_model(self, model_type: str):
        """Lazy loader for model checkpoints."""
        if model_type in self.loaded_models:
            self.active_model_type = model_type
            return

        raw_models_path = Path(self.config["paths"]["models_dir"])
        models_base = raw_models_path if raw_models_path.is_absolute() else PROJECT_ROOT / raw_models_path

        if model_type == "baseline":
            model_dir = models_base / "baseline_tfidf"
            vec_path = model_dir / "tfidf_vectorizer.joblib"
            clf_path = model_dir / "logistic_regression.joblib"
            if not vec_path.exists() or not clf_path.exists():
                raise FileNotFoundError(f"Baseline TF-IDF artifacts missing at {model_dir}. Train baseline first.")
            vectorizer = joblib.load(vec_path)
            classifier = joblib.load(clf_path)
            self.loaded_models["baseline"] = {"vectorizer": vectorizer, "classifier": classifier}

        elif model_type in ["roberta_independent", "roberta_context"]:
            model_dir = models_base / model_type
            if not model_dir.exists() or not (model_dir / "model.safetensors").exists():
                raise FileNotFoundError(f"RoBERTa artifacts missing at {model_dir}. Train model first.")
            tokenizer = AutoTokenizer.from_pretrained(str(model_dir))
            model = AutoModelForSequenceClassification.from_pretrained(str(model_dir))
            model.eval()
            self.loaded_models[model_type] = {"tokenizer": tokenizer, "model": model}

        else:
            raise ValueError(f"Unknown model type: {model_type}. Choose from ['baseline', 'roberta_independent', 'roberta_context'].")

        self.active_model_type = model_type
        logger.info(f"Loaded model architecture: '{model_type}'")

    def parse_raw_text_input(self, raw_text: str) -> pd.DataFrame:
        """Parse multi-line conversation text into a structured DataFrame."""
        lines = [line.strip() for line in raw_text.strip().split("\n") if line.strip()]
        rows = []
        for idx, line in enumerate(lines):
            # Check for "Speaker: Message" pattern
            if ":" in line:
                parts = line.split(":", 1)
                speaker = parts[0].strip()
                text = parts[1].strip()
            else:
                speaker = f"Speaker_{idx % 2 + 1}"
                text = line

            rows.append({
                "dialogue_id": 0,
                "turn_id": idx,
                "speaker": speaker,
                "text": text
            })
        return pd.DataFrame(rows)

    def predict_dataframe(
        self,
        df: pd.DataFrame,
        model_type: Optional[str] = None,
        context_window: int = 3
    ) -> pd.DataFrame:
        """Run batch sentiment inference on a DataFrame."""
        model_to_use = model_type or self.active_model_type
        self._load_model(model_to_use)

        df_out = df.copy()
        if "dialogue_id" not in df_out.columns:
            df_out["dialogue_id"] = 0
        if "turn_id" not in df_out.columns:
            df_out["turn_id"] = np.arange(len(df_out))

        if model_to_use == "baseline":
            vectorizer = self.loaded_models["baseline"]["vectorizer"]
            clf = self.loaded_models["baseline"]["classifier"]
            X = vectorizer.transform(df_out["text"])
            probs = clf.predict_proba(X)

        elif model_to_use == "roberta_independent":
            tokenizer = self.loaded_models["roberta_independent"]["tokenizer"]
            model = self.loaded_models["roberta_independent"]["model"]
            encodings = tokenizer(df_out["text"].tolist(), padding=True, truncation=True, max_length=64, return_tensors="pt")
            with torch.no_grad():
                logits = model(**encodings).logits
                probs = torch.softmax(logits, dim=-1).numpy()

        elif model_to_use == "roberta_context":
            tokenizer = self.loaded_models["roberta_context"]["tokenizer"]
            model = self.loaded_models["roberta_context"]["model"]
            df_ctx = build_context_representations(df_out, window_size=context_window)
            encodings = tokenizer(df_ctx["context_text"].tolist(), padding=True, truncation=True, max_length=128, return_tensors="pt")
            with torch.no_grad():
                logits = model(**encodings).logits
                probs = torch.softmax(logits, dim=-1).numpy()

        preds = np.argmax(probs, axis=1)

        df_out["pred_label"] = preds
        df_out["pred_sentiment"] = [self.target_names[p] for p in preds]
        df_out["prob_negative"] = np.round(probs[:, 0], 4)
        df_out["prob_neutral"] = np.round(probs[:, 1], 4)
        df_out["prob_positive"] = np.round(probs[:, 2], 4)
        df_out["polarity_score"] = np.round(probs[:, 2] - probs[:, 0], 4)

        return df_out

    def analyze_conversation(
        self,
        input_data: Union[str, Path, pd.DataFrame],
        input_type: str = "text",
        model_type: Optional[str] = None,
        context_window: int = 3,
        turning_point_threshold: float = 0.4,
        whatsapp_gap_minutes: int = 120
    ) -> Dict[str, Any]:
        """
        End-to-end conversation analysis.
        Input types: 'text' (raw string), 'csv' (file path), 'whatsapp' (file path or raw lines), 'dataframe'.
        """
        if input_type == "text":
            df = self.parse_raw_text_input(str(input_data))
        elif input_type == "csv":
            df = pd.read_csv(Path(input_data))
        elif input_type == "whatsapp":
            if isinstance(input_data, (str, Path)) and Path(input_data).exists():
                df = parse_whatsapp_file(Path(input_data), inactivity_gap_minutes=whatsapp_gap_minutes)
            else:
                raw_lines = str(input_data).split("\n")
                records = parse_whatsapp_raw_lines(raw_lines)
                df = sessionize_messages(records, inactivity_gap_minutes=whatsapp_gap_minutes)
        elif input_type == "dataframe":
            df = input_data.copy()
        else:
            raise ValueError(f"Unsupported input_type: '{input_type}'")

        if len(df) == 0:
            return {
                "success": False,
                "error": "Input conversation contains zero valid utterances.",
                "predictions_df": pd.DataFrame(),
                "trajectory_stats": {},
                "explanation": {}
            }

        preds_df = self.predict_dataframe(df, model_type=model_type, context_window=context_window)
        trajectory_stats = compute_trajectory_statistics(preds_df, turning_point_threshold=turning_point_threshold)
        explanation = generate_conversation_explanation(preds_df, trajectory_stats)

        return {
            "success": True,
            "model_used": model_type or self.active_model_type,
            "predictions_df": preds_df,
            "trajectory_stats": trajectory_stats,
            "explanation": explanation
        }
