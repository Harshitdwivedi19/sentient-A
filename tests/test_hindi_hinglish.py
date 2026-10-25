"""
tests/test_hindi_hinglish.py

Automated tests for Hindi (Devanagari) & Romanized Hindi (Hinglish)
preprocessing, language routing, and context-aware sentiment analysis.
"""

from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from src.hinglish_normalizer import (
    compress_character_elongations,
    normalize_whatsapp_text,
    detect_language_mode,
    detect_batch_language,
    transliterate_devanagari_to_roman,
)
from src.predict import ConversationSentimentAnalyzer

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_elongation_compression():
    """Verify repeated character elongation compression."""
    assert compress_character_elongations("achhaaaaa") == "achhaa"
    assert compress_character_elongations("booooohot") == "boohot"
    assert compress_character_elongations("mastttttt") == "mastt"
    assert compress_character_elongations("बहादुरी") == "बहादुरी"


def test_shorthand_and_slang_normalization():
    """Verify conversational WhatsApp slang is normalized."""
    norm = normalize_whatsapp_text("bht achhaaaaa kaam kiya yrr")
    assert "bohot" in norm
    assert "achhaa" in norm
    assert "yaar" in norm


def test_script_and_language_detection():
    """Verify automatic classification of Devanagari, Hinglish, and English."""
    # Devanagari Hindi
    assert detect_language_mode("नमस्ते, यह सेवा बहुत अच्छी है") == "hi_deva"
    assert detect_language_mode("मौसम बहुत खराब रहने वाला है") == "hi_deva"

    # Romanized Hindi (Hinglish)
    assert detect_language_mode("bhai order kahan hai mera jaldi batao") == "hi_roman"
    assert detect_language_mode("bohot badhiya service hai aapki, shukriya") == "hi_roman"

    # English
    assert detect_language_mode("Hello, please check the status of my order.") == "en"
    assert detect_language_mode("The deployment server is running smoothly.") == "en"


def test_batch_language_detection():
    """Verify batch-level dialogue detection."""
    hinglish_turns = [
        "Customer: Hello, delivery abhi tak nahi hui",
        "Support: Sir let me check tracking for you",
        "Customer: Bhai bohot delay chal raha hai, bekar service!"
    ]
    assert detect_batch_language(hinglish_turns) == "hi_roman"

    deva_turns = [
        "अमित: क्या रविवार को मिलने का विचार है?",
        "नेहा: हाँ ज़रूर, बहुत दिनों से मिले नहीं हैं"
    ]
    assert detect_batch_language(deva_turns) == "hi_deva"

    en_turns = [
        "Alice: Why was the deadline changed?",
        "Bob: I apologize, client pushed it up."
    ]
    assert detect_batch_language(en_turns) == "en"


def test_transliteration_mapping():
    """Verify Devanagari to Roman transliteration produces intelligible Latin script."""
    roman = transliterate_devanagari_to_roman("नमस्ते धन्यवाद")
    assert "namaste" in roman
    assert "dhanyavad" in roman or "dhanyawad" in roman


def test_hindi_dataset_integrity_and_zero_leakage():
    """Verify processed datasets exist, follow schema, and have zero dialogue leakage."""
    proc_dir = PROJECT_ROOT / "data" / "processed"
    train_path = proc_dir / "hindi_train.csv"
    val_path = proc_dir / "hindi_val.csv"
    test_path = proc_dir / "hindi_test.csv"

    assert train_path.exists(), "hindi_train.csv missing"
    assert val_path.exists(), "hindi_val.csv missing"
    assert test_path.exists(), "hindi_test.csv missing"

    df_train = pd.read_csv(train_path)
    df_val = pd.read_csv(val_path)
    df_test = pd.read_csv(test_path)

    required_cols = {"dialogue_id", "turn_id", "speaker", "text", "sentiment", "label"}
    assert required_cols.issubset(df_train.columns)
    assert required_cols.issubset(df_val.columns)
    assert required_cols.issubset(df_test.columns)

    # Zero dialogue leakage
    d_train = set(df_train["dialogue_id"])
    d_val = set(df_val["dialogue_id"])
    d_test = set(df_test["dialogue_id"])

    assert len(d_train.intersection(d_val)) == 0, "Train-Val dialogue leakage"
    assert len(d_train.intersection(d_test)) == 0, "Train-Test dialogue leakage"
    assert len(d_val.intersection(d_test)) == 0, "Val-Test dialogue leakage"


def test_hindi_model_artifacts_exist():
    """Verify trained model artifacts exist in models/hindi_baseline_tfidf."""
    model_dir = PROJECT_ROOT / "models" / "hindi_baseline_tfidf"
    assert (model_dir / "tfidf_vectorizer.joblib").exists()
    assert (model_dir / "logistic_regression.joblib").exists()
    assert (model_dir / "config.json").exists()


def test_end_to_end_hindi_and_hinglish_analysis():
    """Verify ConversationSentimentAnalyzer auto-routes and predicts Hindi/Hinglish accurately."""
    analyzer = ConversationSentimentAnalyzer(default_model="hindi_baseline")

    # Hinglish Conversation
    hinglish_text = (
        "Customer: Bhai order kahan hai, bohot bekar service hai!\n"
        "Support: Sorry sir, abhi check karke batate hain\n"
        "Customer: Chalo theek hai, bohot bohot shukriya"
    )
    res_hing = analyzer.analyze_conversation(hinglish_text, model_type="auto")
    assert res_hing["success"] is True
    assert res_hing["detected_language"] == "hi_roman"
    df_h = res_hing["predictions_df"]
    assert len(df_h) == 3
    # Turn 0 must be negative
    assert df_h.iloc[0]["pred_sentiment"] == "negative"
    # Polarity formula: prob_positive - prob_negative
    p_diff = df_h.iloc[0]["prob_positive"] - df_h.iloc[0]["prob_negative"]
    assert np.isclose(df_h.iloc[0]["polarity_score"], p_diff, atol=1e-3)

    # Devanagari Conversation
    deva_text = (
        "अमित: यह सेवा बहुत अच्छी और मददगार है!\n"
        "नेहा: आपका बहुत बहुत धन्यवाद!"
    )
    res_deva = analyzer.analyze_conversation(deva_text, model_type="auto")
    assert res_deva["success"] is True
    assert res_deva["detected_language"] == "hi_deva"
    df_d = res_deva["predictions_df"]
    assert len(df_d) == 2
    assert df_d.iloc[0]["pred_sentiment"] == "positive"
