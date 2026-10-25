"""
src/train.py

Unified training entrypoint for:
- Traditional ML Baseline (TF-IDF + Logistic Regression) [Phase 2]
- Deep Learning Independent RoBERTa [Phase 3]
- Context-Aware RoBERTa Sequence Classifier [Phase 4]
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from typing import Dict, Any, Tuple, Optional
import joblib
import numpy as np
import pandas as pd
import yaml
import torch
from torch.utils.data import Dataset
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import FeatureUnion
from sklearn.utils.class_weight import compute_class_weight

from transformers import (
    AutoTokenizer,
    AutoConfig,
    AutoModelForSequenceClassification,
    DataCollatorWithPadding,
    Trainer,
    TrainingArguments,
    set_seed,
)

from src.context import build_context_representations
from src.evaluate import evaluate_predictions, plot_and_save_confusion_matrix
from src.hinglish_normalizer import normalize_whatsapp_text

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


def load_config(config_path: str = "configs/config.yaml") -> Dict[str, Any]:
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


class UtteranceDataset(Dataset):
    """PyTorch Dataset with dynamic batch-level padding for sequence classification."""

    def __init__(self, texts: list, labels: list, tokenizer, max_length: int = 64):
        self.encodings = tokenizer(
            texts,
            truncation=True,
            max_length=max_length,
        )
        self.labels = labels

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        item = {key: self.encodings[key][idx] for key in self.encodings}
        item["labels"] = self.labels[idx]
        return item


class WeightedLossTrainer(Trainer):
    """Custom Trainer supporting class-weighted cross-entropy loss."""

    def __init__(self, class_weights: Optional[torch.Tensor] = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.class_weights = class_weights

    def compute_loss(self, model, inputs, return_outputs=False, num_items_in_batch=None):
        labels = inputs.get("labels")
        outputs = model(**inputs)
        logits = outputs.get("logits")
        if self.class_weights is not None:
            weights = self.class_weights.to(model.device)
            loss_fct = torch.nn.CrossEntropyLoss(weight=weights)
        else:
            loss_fct = torch.nn.CrossEntropyLoss()
        loss = loss_fct(logits.view(-1, self.model.config.num_labels), labels.view(-1))
        return (loss, outputs) if return_outputs else loss


def train_tfidf_baseline(config: Dict[str, Any], ngram_mode: str = "both") -> Dict[str, Any]:
    """
    Train and evaluate TF-IDF + Logistic Regression baseline on official validation split.
    Evaluates both unigram (1, 1) and unigram+bigram (1, 2) features as required.
    """
    processed_dir = Path(config["paths"]["processed_data_dir"])
    models_dir = Path(config["paths"]["models_dir"]) / "baseline_tfidf"
    metrics_dir = Path(config["paths"]["metrics_dir"])
    preds_dir = Path(config["paths"]["predictions_dir"])
    figures_dir = Path(config["paths"]["figures_dir"])

    models_dir.mkdir(parents=True, exist_ok=True)
    metrics_dir.mkdir(parents=True, exist_ok=True)
    preds_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    train_path = processed_dir / "train.csv"
    val_path = processed_dir / "val.csv"

    logger.info(f"Loading training data from {train_path}...")
    train_df = pd.read_csv(train_path)
    logger.info(f"Loading validation data from {val_path}...")
    val_df = pd.read_csv(val_path)

    target_names = config["dataset"]["target_names"]
    random_seed = config["project"]["seed"]

    ngram_configs = {
        "unigram": (1, 1),
        "bigram": (1, 2),
    }

    results = {}
    best_macro_f1 = -1.0
    best_model_bundle = None
    best_val_preds_df = None
    best_config_name = "bigram"

    for name, ngram_range in ngram_configs.items():
        logger.info(f"\n--- Training TF-IDF ({name}: n-gram range {ngram_range}) ---")
        vectorizer = TfidfVectorizer(
            ngram_range=ngram_range,
            max_features=config["models"]["baseline_tfidf"]["max_features"],
            sublinear_tf=True,
            strip_accents="unicode",
            lowercase=True
        )

        X_train = vectorizer.fit_transform(train_df["text"])
        y_train = train_df["label"].values

        X_val = vectorizer.transform(val_df["text"])
        y_val = val_df["label"].values

        # Multinomial Logistic Regression with L2 regularization
        clf = LogisticRegression(
            C=config["models"]["baseline_tfidf"]["c_regularization"],
            max_iter=1000,
            class_weight="balanced",
            random_state=random_seed,
            solver="lbfgs"
        )
        clf.fit(X_train, y_train)

        # Validation inference
        val_probs = clf.predict_proba(X_val)
        val_preds = np.argmax(val_probs, axis=1)

        eval_report = evaluate_predictions(
            y_true=y_val,
            y_pred=val_preds,
            y_prob=val_probs,
            target_names=target_names,
            model_name=f"TF-IDF_LogReg_{name}",
            split_name="val"
        )
        results[name] = eval_report
        logger.info(f"Result [{name}]: Accuracy = {eval_report['accuracy']:.4f}, Macro-F1 = {eval_report['macro_f1']:.4f}, Brier = {eval_report['calibration']['brier_score']:.4f}")

        if eval_report["macro_f1"] > best_macro_f1:
            best_macro_f1 = eval_report["macro_f1"]
            best_config_name = name
            best_model_bundle = (vectorizer, clf)

            # Format predictions dataframe
            preds_df = val_df.copy()
            preds_df["pred_label"] = val_preds
            preds_df["pred_sentiment"] = [target_names[p] for p in val_preds]
            preds_df["prob_negative"] = np.round(val_probs[:, 0], 4)
            preds_df["prob_neutral"] = np.round(val_probs[:, 1], 4)
            preds_df["prob_positive"] = np.round(val_probs[:, 2], 4)
            preds_df["polarity_score"] = np.round(val_probs[:, 2] - val_probs[:, 0], 4)
            best_val_preds_df = preds_df

    # Save best model artifacts
    best_vectorizer, best_clf = best_model_bundle
    joblib.dump(best_vectorizer, models_dir / "tfidf_vectorizer.joblib")
    joblib.dump(best_clf, models_dir / "logistic_regression.joblib")
    logger.info(f"Saved best model artifacts ({best_config_name}) to {models_dir}")

    # Save predictions
    preds_out_path = preds_dir / "val_predictions_tfidf.csv"
    best_val_preds_df.to_csv(preds_out_path, index=False)
    logger.info(f"Saved validation predictions to {preds_out_path}")

    # Save metrics report
    metrics_out_path = metrics_dir / "val_metrics_tfidf.json"
    full_report = {
        "best_configuration": best_config_name,
        "configurations": results,
    }
    with open(metrics_out_path, "w", encoding="utf-8") as f:
        json.dump(full_report, f, indent=2)
    logger.info(f"Saved evaluation metrics to {metrics_out_path}")

    # Generate and save confusion matrix figure for best config
    cm = np.array(results[best_config_name]["confusion_matrix"])
    cm_fig_path = figures_dir / "confusion_matrix_tfidf.png"
    plot_and_save_confusion_matrix(
        cm=cm,
        target_names=target_names,
        output_path=cm_fig_path,
        title=f"Confusion Matrix: TF-IDF + LogReg ({best_config_name.capitalize()})"
    )
    logger.info(f"Saved confusion matrix plot to {cm_fig_path}")

    return full_report


def train_hindi_baseline(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Train and evaluate Context-Aware Hybrid (Word + Char n-Gram) TF-IDF + Logistic Regression
    on Devanagari Hindi and Romanized Hindi (Hinglish) conversational datasets.
    """
    processed_dir = Path(config["paths"]["processed_data_dir"])
    models_dir = Path(config["paths"]["models_dir"]) / "hindi_baseline_tfidf"
    metrics_dir = Path(config["paths"]["metrics_dir"])
    preds_dir = Path(config["paths"]["predictions_dir"])
    figures_dir = Path(config["paths"]["figures_dir"])

    models_dir.mkdir(parents=True, exist_ok=True)
    metrics_dir.mkdir(parents=True, exist_ok=True)
    preds_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    train_path = processed_dir / "hindi_train.csv"
    val_path = processed_dir / "hindi_val.csv"

    if not train_path.exists():
        from src.prepare_hindi_data import build_and_save_hindi_datasets
        build_and_save_hindi_datasets(str(processed_dir))

    logger.info(f"Loading Hindi & Hinglish training data from {train_path}...")
    train_df = pd.read_csv(train_path)
    logger.info(f"Loading Hindi & Hinglish validation data from {val_path}...")
    val_df = pd.read_csv(val_path)

    # Normalize elongations and WhatsApp shorthand
    train_df_clean = train_df.copy()
    train_df_clean["text"] = train_df_clean["text"].astype(str).apply(normalize_whatsapp_text)

    val_df_clean = val_df.copy()
    val_df_clean["text"] = val_df_clean["text"].astype(str).apply(normalize_whatsapp_text)

    # Build context representations (window_size=3)
    k = config.get("models", {}).get("context", {}).get("default_window_size", 3)
    train_ctx = build_context_representations(train_df_clean, window_size=k)
    val_ctx = build_context_representations(val_df_clean, window_size=k)

    train_texts = train_ctx["context_text"].tolist()
    y_train = train_df["label"].values

    val_texts = val_ctx["context_text"].tolist()
    y_val = val_df["label"].values

    logger.info(f"Fitting Hybrid Word (1-2) + Char_wb (2-5) TF-IDF Vectorizer on {len(train_texts)} turns...")
    vectorizer = FeatureUnion([
        ("word", TfidfVectorizer(
            analyzer="word",
            ngram_range=(1, 2),
            max_features=6000,
            sublinear_tf=True,
            lowercase=True
        )),
        ("char", TfidfVectorizer(
            analyzer="char_wb",
            ngram_range=(2, 5),
            max_features=12000,
            sublinear_tf=True,
            lowercase=True
        ))
    ])

    X_train = vectorizer.fit_transform(train_texts)
    X_val = vectorizer.transform(val_texts)

    clf = LogisticRegression(
        C=1.0,
        max_iter=1000,
        class_weight="balanced",
        random_state=config["project"]["seed"],
        solver="lbfgs"
    )
    clf.fit(X_train, y_train)

    val_probs = clf.predict_proba(X_val)
    val_preds = np.argmax(val_probs, axis=1)

    target_names = config["dataset"]["target_names"]
    eval_report = evaluate_predictions(
        y_true=y_val,
        y_pred=val_preds,
        y_prob=val_probs,
        target_names=target_names,
        model_name="Hindi_Hinglish_Hybrid_TFIDF",
        split_name="val"
    )

    # Save artifacts
    joblib.dump(vectorizer, models_dir / "tfidf_vectorizer.joblib")
    joblib.dump(clf, models_dir / "logistic_regression.joblib")

    meta = {
        "model_name": "Hindi_Hinglish_Hybrid_TFIDF",
        "context_window_k": k,
        "classes": target_names,
        "features": "word(1,2) + char_wb(2,5)",
        "train_samples": len(train_texts),
        "val_samples": len(val_texts)
    }
    with open(models_dir / "config.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    with open(metrics_dir / "hindi_baseline_metrics.json", "w", encoding="utf-8") as f:
        json.dump(eval_report, f, indent=2)

    val_df_out = val_df.copy()
    val_df_out["pred_label"] = val_preds
    val_df_out["pred_sentiment"] = [target_names[p] for p in val_preds]
    for i, name in enumerate(target_names):
        val_df_out[f"prob_{name}"] = val_probs[:, i]
    val_df_out.to_csv(preds_dir / "hindi_baseline_val_preds.csv", index=False)

    cm = np.array(eval_report["confusion_matrix"])
    plot_and_save_confusion_matrix(
        cm=cm,
        target_names=target_names,
        output_path=figures_dir / "hindi_baseline_val_cm.png",
        title="Confusion Matrix: Hindi & Hinglish Hybrid TF-IDF"
    )

    return eval_report


def train_roberta_independent(config: Dict[str, Any], args) -> Dict[str, Any]:
    """
    Train and evaluate independent RoBERTa sequence classifier on validation split.
    Each utterance is classified without surrounding turns.
    """
    processed_dir = Path(config["paths"]["processed_data_dir"])
    models_dir = Path(config["paths"]["models_dir"]) / "roberta_independent"
    metrics_dir = Path(config["paths"]["metrics_dir"])
    preds_dir = Path(config["paths"]["predictions_dir"])
    figures_dir = Path(config["paths"]["figures_dir"])

    models_dir.mkdir(parents=True, exist_ok=True)
    metrics_dir.mkdir(parents=True, exist_ok=True)
    preds_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    target_names = config["dataset"]["target_names"]
    random_seed = config["project"]["seed"]
    set_seed(random_seed)

    # Load splits
    train_df = pd.read_csv(processed_dir / "train.csv")
    val_df = pd.read_csv(processed_dir / "val.csv")

    # Smoke test or subsample reduction if requested
    if args.smoke_test:
        logger.info("SMOKE TEST MODE: Reducing dataset to 100 train and 50 val samples for fast verification.")
        train_df = train_df.head(100).copy()
        val_df = val_df.head(50).copy()
        num_epochs = 1
        batch_size = 16
    else:
        if args.max_train_samples and args.max_train_samples < len(train_df):
            logger.info(f"Subsampling training set to {args.max_train_samples} samples.")
            train_df = train_df.sample(n=args.max_train_samples, random_state=random_seed).reset_index(drop=True)
        num_epochs = args.epochs or config["models"]["roberta"]["num_train_epochs"]
        batch_size = args.batch_size or config["models"]["roberta"]["batch_size"]

    logger.info(f"Training independent RoBERTa on {len(train_df):,} samples, validating on {len(val_df):,} samples.")

    model_name = config["models"]["roberta"]["pretrained_model_name"]
    max_length = min(64, config["models"]["roberta"]["max_length"])

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    train_dataset = UtteranceDataset(train_df["text"].tolist(), train_df["label"].tolist(), tokenizer, max_length)
    val_dataset = UtteranceDataset(val_df["text"].tolist(), val_df["label"].tolist(), tokenizer, max_length)
    data_collator = DataCollatorWithPadding(tokenizer=tokenizer)

    # Compute balanced class weights to handle MELD neutral class imbalance
    class_weights_np = compute_class_weight(
        class_weight="balanced",
        classes=np.array([0, 1, 2]),
        y=train_df["label"].values
    )
    class_weights = torch.tensor(class_weights_np, dtype=torch.float)
    logger.info(f"Class weights (neg, neu, pos): {class_weights_np.round(3).tolist()}")

    # Model definition
    id2label = {i: name for i, name in enumerate(target_names)}
    label2id = {name: i for i, name in enumerate(target_names)}
    model = AutoModelForSequenceClassification.from_pretrained(
        model_name,
        num_labels=len(target_names),
        id2label=id2label,
        label2id=label2id
    )

    if args.freeze_encoder:
        logger.info("Freezing base RoBERTa encoder weights (training classification head only for CPU efficiency).")
        for param in model.roberta.parameters():
            param.requires_grad = False

    total_steps = max(1, (len(train_dataset) // batch_size) * num_epochs)
    warmup_steps = int(total_steps * config["models"]["roberta"]["warmup_ratio"])

    training_args = TrainingArguments(
        output_dir=str(models_dir / "checkpoints"),
        num_train_epochs=num_epochs,
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=config["models"]["roberta"]["eval_batch_size"],
        learning_rate=config["models"]["roberta"]["learning_rate"] if not args.freeze_encoder else 1e-3,
        weight_decay=config["models"]["roberta"]["weight_decay"],
        warmup_steps=warmup_steps,
        logging_steps=10 if args.smoke_test else 50,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="macro_f1",
        greater_is_better=True,
        save_total_limit=1,
        report_to="none",
        dataloader_pin_memory=False,
        seed=random_seed,
    )

    def compute_metrics(eval_pred):
        logits, labels = eval_pred
        preds = np.argmax(logits, axis=1)
        from sklearn.metrics import f1_score, accuracy_score
        return {
            "accuracy": float(accuracy_score(labels, preds)),
            "macro_f1": float(f1_score(labels, preds, average="macro")),
            "weighted_f1": float(f1_score(labels, preds, average="weighted")),
        }

    trainer = WeightedLossTrainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        data_collator=data_collator,
        processing_class=tokenizer,
        compute_metrics=compute_metrics,
        class_weights=class_weights,
    )

    logger.info("Beginning RoBERTa fine-tuning...")
    trainer.train()

    # Save final best model and tokenizer
    logger.info(f"Saving best RoBERTa model to {models_dir}...")
    trainer.save_model(str(models_dir))
    tokenizer.save_pretrained(str(models_dir))

    # Inference on validation set
    logger.info("Running validation inference with best checkpoint...")
    predictions_output = trainer.predict(val_dataset)
    logits = predictions_output.predictions
    val_probs = torch.softmax(torch.tensor(logits), dim=-1).numpy()
    val_preds = np.argmax(val_probs, axis=1)

    eval_report = evaluate_predictions(
        y_true=val_df["label"].values,
        y_pred=val_preds,
        y_prob=val_probs,
        target_names=target_names,
        model_name="RoBERTa_Independent",
        split_name="val"
    )

    # Save validation predictions with continuous polarity score
    preds_df = val_df.copy()
    preds_df["pred_label"] = val_preds
    preds_df["pred_sentiment"] = [target_names[p] for p in val_preds]
    preds_df["prob_negative"] = np.round(val_probs[:, 0], 4)
    preds_df["prob_neutral"] = np.round(val_probs[:, 1], 4)
    preds_df["prob_positive"] = np.round(val_probs[:, 2], 4)
    preds_df["polarity_score"] = np.round(val_probs[:, 2] - val_probs[:, 0], 4)

    preds_out_path = preds_dir / "val_predictions_roberta_independent.csv"
    preds_df.to_csv(preds_out_path, index=False)
    logger.info(f"Saved validation predictions to {preds_out_path}")

    # Save metrics report
    metrics_out_path = metrics_dir / "val_metrics_roberta_independent.json"
    with open(metrics_out_path, "w", encoding="utf-8") as f:
        json.dump(eval_report, f, indent=2)
    logger.info(f"Saved evaluation metrics to {metrics_out_path}")

    # Plot confusion matrix
    cm = np.array(eval_report["confusion_matrix"])
    cm_fig_path = figures_dir / "confusion_matrix_roberta_independent.png"
    plot_and_save_confusion_matrix(
        cm=cm,
        target_names=target_names,
        output_path=cm_fig_path,
        title="Confusion Matrix: RoBERTa Independent"
    )
    logger.info(f"Saved confusion matrix plot to {cm_fig_path}")

    return eval_report


def train_roberta_context(config: Dict[str, Any], args) -> Dict[str, Any]:
    """
    Train and evaluate Context-Aware RoBERTa sequence classifier on validation split.
    Each utterance is prepended with k preceding turns formatted with speaker markers.
    """
    processed_dir = Path(config["paths"]["processed_data_dir"])
    models_dir = Path(config["paths"]["models_dir"]) / "roberta_context"
    metrics_dir = Path(config["paths"]["metrics_dir"])
    preds_dir = Path(config["paths"]["predictions_dir"])
    figures_dir = Path(config["paths"]["figures_dir"])

    models_dir.mkdir(parents=True, exist_ok=True)
    metrics_dir.mkdir(parents=True, exist_ok=True)
    preds_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    target_names = config["dataset"]["target_names"]
    random_seed = config["project"]["seed"]
    set_seed(random_seed)

    window_size = args.context_window if args.context_window is not None else config["models"]["context"]["default_window_size"]
    sep_token = config["models"]["context"]["separator_token"]
    include_speaker = config["models"]["context"]["include_speaker"]

    logger.info(f"Building context representations with window_size k={window_size}...")

    # Load splits
    raw_train_df = pd.read_csv(processed_dir / "train.csv")
    raw_val_df = pd.read_csv(processed_dir / "val.csv")

    train_df = build_context_representations(
        raw_train_df,
        window_size=window_size,
        sep_token=sep_token,
        include_speaker=include_speaker
    )
    val_df = build_context_representations(
        raw_val_df,
        window_size=window_size,
        sep_token=sep_token,
        include_speaker=include_speaker
    )

    # Smoke test or subsample reduction if requested
    if args.smoke_test:
        logger.info("SMOKE TEST MODE: Reducing dataset to 100 train and 50 val samples for fast verification.")
        train_df = train_df.head(100).copy()
        val_df = val_df.head(50).copy()
        num_epochs = 1
        batch_size = 16
    else:
        if args.max_train_samples and args.max_train_samples < len(train_df):
            logger.info(f"Subsampling training set to {args.max_train_samples} samples.")
            train_df = train_df.sample(n=args.max_train_samples, random_state=random_seed).reset_index(drop=True)
        num_epochs = args.epochs or config["models"]["roberta"]["num_train_epochs"]
        batch_size = args.batch_size or config["models"]["roberta"]["batch_size"]

    logger.info(f"Training context-aware RoBERTa (k={window_size}) on {len(train_df):,} samples, validating on {len(val_df):,} samples.")

    model_name = config["models"]["roberta"]["pretrained_model_name"]
    max_length = config["models"]["roberta"]["max_length"]

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    train_dataset = UtteranceDataset(train_df["context_text"].tolist(), train_df["label"].tolist(), tokenizer, max_length)
    val_dataset = UtteranceDataset(val_df["context_text"].tolist(), val_df["label"].tolist(), tokenizer, max_length)
    data_collator = DataCollatorWithPadding(tokenizer=tokenizer)

    # Compute balanced class weights
    class_weights_np = compute_class_weight(
        class_weight="balanced",
        classes=np.array([0, 1, 2]),
        y=train_df["label"].values
    )
    class_weights = torch.tensor(class_weights_np, dtype=torch.float)
    logger.info(f"Class weights (neg, neu, pos): {class_weights_np.round(3).tolist()}")

    # Model definition
    id2label = {i: name for i, name in enumerate(target_names)}
    label2id = {name: i for i, name in enumerate(target_names)}
    model = AutoModelForSequenceClassification.from_pretrained(
        model_name,
        num_labels=len(target_names),
        id2label=id2label,
        label2id=label2id
    )

    if args.freeze_encoder:
        logger.info("Freezing base RoBERTa encoder weights (training classification head only for CPU efficiency).")
        for param in model.roberta.parameters():
            param.requires_grad = False

    total_steps = max(1, (len(train_dataset) // batch_size) * num_epochs)
    warmup_steps = int(total_steps * config["models"]["roberta"]["warmup_ratio"])

    training_args = TrainingArguments(
        output_dir=str(models_dir / "checkpoints"),
        num_train_epochs=num_epochs,
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=config["models"]["roberta"]["eval_batch_size"],
        learning_rate=config["models"]["roberta"]["learning_rate"] if not args.freeze_encoder else 1e-3,
        weight_decay=config["models"]["roberta"]["weight_decay"],
        warmup_steps=warmup_steps,
        logging_steps=10 if args.smoke_test else 50,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="macro_f1",
        greater_is_better=True,
        save_total_limit=1,
        report_to="none",
        dataloader_pin_memory=False,
        seed=random_seed,
    )

    def compute_metrics(eval_pred):
        logits, labels = eval_pred
        preds = np.argmax(logits, axis=1)
        from sklearn.metrics import f1_score, accuracy_score
        return {
            "accuracy": float(accuracy_score(labels, preds)),
            "macro_f1": float(f1_score(labels, preds, average="macro")),
            "weighted_f1": float(f1_score(labels, preds, average="weighted")),
        }

    trainer = WeightedLossTrainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        data_collator=data_collator,
        processing_class=tokenizer,
        compute_metrics=compute_metrics,
        class_weights=class_weights,
    )

    logger.info("Beginning Context-Aware RoBERTa fine-tuning...")
    trainer.train()

    # Save final best model and tokenizer
    logger.info(f"Saving best context-aware RoBERTa model to {models_dir}...")
    trainer.save_model(str(models_dir))
    tokenizer.save_pretrained(str(models_dir))

    # Inference on validation set
    logger.info("Running validation inference with best context checkpoint...")
    predictions_output = trainer.predict(val_dataset)
    logits = predictions_output.predictions
    val_probs = torch.softmax(torch.tensor(logits), dim=-1).numpy()
    val_preds = np.argmax(val_probs, axis=1)

    eval_report = evaluate_predictions(
        y_true=val_df["label"].values,
        y_pred=val_preds,
        y_prob=val_probs,
        target_names=target_names,
        model_name=f"RoBERTa_Context_k{window_size}",
        split_name="val"
    )
    eval_report["context_window_k"] = window_size

    # Save validation predictions with continuous polarity score
    preds_df = val_df.copy()
    preds_df["pred_label"] = val_preds
    preds_df["pred_sentiment"] = [target_names[p] for p in val_preds]
    preds_df["prob_negative"] = np.round(val_probs[:, 0], 4)
    preds_df["prob_neutral"] = np.round(val_probs[:, 1], 4)
    preds_df["prob_positive"] = np.round(val_probs[:, 2], 4)
    preds_df["polarity_score"] = np.round(val_probs[:, 2] - val_probs[:, 0], 4)

    preds_out_path = preds_dir / "val_predictions_roberta_context.csv"
    preds_df.to_csv(preds_out_path, index=False)
    logger.info(f"Saved validation predictions to {preds_out_path}")

    # Save metrics report
    metrics_out_path = metrics_dir / "val_metrics_roberta_context.json"
    with open(metrics_out_path, "w", encoding="utf-8") as f:
        json.dump(eval_report, f, indent=2)
    logger.info(f"Saved context metrics to {metrics_out_path}")

    # Save confusion matrix plot
    cm = np.array(eval_report["confusion_matrix"])
    cm_fig_path = figures_dir / "confusion_matrix_roberta_context.png"
    plot_and_save_confusion_matrix(
        cm=cm,
        target_names=target_names,
        output_path=cm_fig_path,
        title=f"Confusion Matrix: RoBERTa Context-Aware (k={window_size})"
    )
    logger.info(f"Saved confusion matrix plot to {cm_fig_path}")

    # Generate Unified Comparison Report (Baseline vs Independent vs Context)
    comparison_out_path = metrics_dir / "val_metrics_comparison.json"
    comparison = {}

    tfidf_metrics_file = metrics_dir / "val_metrics_tfidf.json"
    if tfidf_metrics_file.exists():
        with open(tfidf_metrics_file, "r", encoding="utf-8") as f:
            t_data = json.load(f)
            best_cfg = t_data.get("best_configuration", "bigram")
            comparison["TF-IDF_Baseline"] = t_data["configurations"][best_cfg]

    indep_metrics_file = metrics_dir / "val_metrics_roberta_independent.json"
    if indep_metrics_file.exists():
        with open(indep_metrics_file, "r", encoding="utf-8") as f:
            comparison["RoBERTa_Independent"] = json.load(f)

    comparison[f"RoBERTa_Context_k{window_size}"] = eval_report

    with open(comparison_out_path, "w", encoding="utf-8") as f:
        json.dump(comparison, f, indent=2)
    logger.info(f"Saved unified comparison metrics to {comparison_out_path}")

    return eval_report


def main():
    parser = argparse.ArgumentParser(description="Model Training Pipeline")
    parser.add_argument(
        "--model",
        type=str,
        default="tfidf",
        choices=["tfidf", "roberta_independent", "roberta_context", "hindi_baseline"],
        help="Model architecture to train"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="configs/config.yaml",
        help="Path to YAML configuration file"
    )
    parser.add_argument(
        "--context-window",
        type=int,
        default=None,
        help="Number of preceding turns for context-aware model (e.g. 1, 3, 5)"
    )
    parser.add_argument(
        "--smoke-test",
        action="store_true",
        help="Run quick smoke test on 100 samples to verify end-to-end pipeline"
    )
    parser.add_argument(
        "--freeze-encoder",
        action="store_true",
        help="Freeze RoBERTa encoder layers to run fast classification head training on CPU"
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=None,
        help="Override number of training epochs"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=None,
        help="Override batch size"
    )
    parser.add_argument(
        "--max-train-samples",
        type=int,
        default=None,
        help="Optional limit on number of training samples for faster CPU runs"
    )
    args = parser.parse_args()

    config = load_config(args.config)

    if args.model == "tfidf":
        report = train_tfidf_baseline(config)
        print("\n" + "=" * 70)
        print(f"TF-IDF BASELINE VALIDATION COMPLETE (Selected: {report['best_configuration'].upper()})")
        print("=" * 70)
        best_stats = report["configurations"][report["best_configuration"]]
        print(f"  Accuracy:    {best_stats['accuracy']:.4f}")
        print(f"  Macro-F1:    {best_stats['macro_f1']:.4f}")
        print(f"  Weighted-F1: {best_stats['weighted_f1']:.4f}")
        print(f"  Brier Score: {best_stats['calibration']['brier_score']:.4f}")
        print(f"  Expected Calibration Error: {best_stats['calibration']['expected_calibration_error']:.4f}")
        print("\n  Per-Class Breakdown:")
        for sentiment, p_stat in best_stats["per_class"].items():
            print(f"    - {sentiment.capitalize():<8}: Precision={p_stat['precision']:.4f}, Recall={p_stat['recall']:.4f}, F1={p_stat['f1']:.4f} (Support: {p_stat['support']})")
        print("=" * 70 + "\n")
    elif args.model == "roberta_independent":
        report = train_roberta_independent(config, args)
        print("\n" + "=" * 70)
        print("ROBERTA INDEPENDENT VALIDATION COMPLETE")
        print("=" * 70)
        print(f"  Accuracy:    {report['accuracy']:.4f}")
        print(f"  Macro-F1:    {report['macro_f1']:.4f}")
        print(f"  Weighted-F1: {report['weighted_f1']:.4f}")
        print(f"  Brier Score: {report['calibration']['brier_score']:.4f}")
        print(f"  Expected Calibration Error: {report['calibration']['expected_calibration_error']:.4f}")
        print("\n  Per-Class Breakdown:")
        for sentiment, p_stat in report["per_class"].items():
            print(f"    - {sentiment.capitalize():<8}: Precision={p_stat['precision']:.4f}, Recall={p_stat['recall']:.4f}, F1={p_stat['f1']:.4f} (Support: {p_stat['support']})")
        print("=" * 70 + "\n")
    elif args.model == "roberta_context":
        report = train_roberta_context(config, args)
        print("\n" + "=" * 70)
        print(f"ROBERTA CONTEXT-AWARE (k={report.get('context_window_k', 3)}) VALIDATION COMPLETE")
        print("=" * 70)
        print(f"  Accuracy:    {report['accuracy']:.4f}")
        print(f"  Macro-F1:    {report['macro_f1']:.4f}")
        print(f"  Weighted-F1: {report['weighted_f1']:.4f}")
        print(f"  Brier Score: {report['calibration']['brier_score']:.4f}")
        print(f"  Expected Calibration Error: {report['calibration']['expected_calibration_error']:.4f}")
        print("\n  Per-Class Breakdown:")
        for sentiment, p_stat in report["per_class"].items():
            print(f"    - {sentiment.capitalize():<8}: Precision={p_stat['precision']:.4f}, Recall={p_stat['recall']:.4f}, F1={p_stat['f1']:.4f} (Support: {p_stat['support']})")
        print("=" * 70 + "\n")
    elif args.model == "hindi_baseline":
        report = train_hindi_baseline(config)
        print("\n" + "=" * 70)
        print("HINDI & HINGLISH HYBRID TF-IDF BASELINE VALIDATION COMPLETE")
        print("=" * 70)
        print(f"  Accuracy:    {report['accuracy']:.4f}")
        print(f"  Macro-F1:    {report['macro_f1']:.4f}")
        print(f"  Weighted-F1: {report['weighted_f1']:.4f}")
        print(f"  Brier Score: {report['calibration']['brier_score']:.4f}")
        print(f"  Expected Calibration Error: {report['calibration']['expected_calibration_error']:.4f}")
        print("\n  Per-Class Breakdown:")
        for sentiment, p_stat in report["per_class"].items():
            print(f"    - {sentiment.capitalize():<8}: Precision={p_stat['precision']:.4f}, Recall={p_stat['recall']:.4f}, F1={p_stat['f1']:.4f} (Support: {p_stat['support']})")
        print("=" * 70 + "\n")
    else:
        raise NotImplementedError(f"Model architecture '{args.model}' will be implemented in subsequent phases.")


if __name__ == "__main__":
    main()
