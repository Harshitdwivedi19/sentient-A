"""
tests/test_context.py

Unit tests for Context Construction Engine:
- Zero boundary leakage between dialogues (Risk #21)
- Window length boundary constraints (k=0, 1, 3, 5)
- Standardized speaker tag protocol (Risk #43)
- Left-preservation of target message
"""

import pandas as pd
import pytest
from src.context import build_context_representations, format_turn


@pytest.fixture
def sample_dialogues():
    return pd.DataFrame([
        # Dialogue 0 (3 turns)
        {"dialogue_id": 0, "turn_id": 0, "speaker": "Chandler", "text": "I won the lottery!"},
        {"dialogue_id": 0, "turn_id": 1, "speaker": "Joey", "text": "No way!"},
        {"dialogue_id": 0, "turn_id": 2, "speaker": "Chandler", "text": "I am serious!"},
        # Dialogue 1 (2 turns) - MUST NOT inherit Dialogue 0
        {"dialogue_id": 1, "turn_id": 0, "speaker": "Monica", "text": "Who cleaned the kitchen?"},
        {"dialogue_id": 1, "turn_id": 1, "speaker": "Ross", "text": "It was not me."},
    ])


def test_zero_boundary_leakage(sample_dialogues):
    """Verify Dialogue 1 Turn 0 NEVER inherits Dialogue 0 turns."""
    df_ctx = build_context_representations(sample_dialogues, window_size=3, sep_token=" </s> ")

    # Dialogue 0, Turn 0
    assert df_ctx.loc[0, "context_text"] == "Chandler: I won the lottery!"

    # Dialogue 1, Turn 0 (CRITICAL: must NOT contain Chandler or Joey)
    diag1_turn0 = df_ctx.loc[3, "context_text"]
    assert diag1_turn0 == "Monica: Who cleaned the kitchen?"
    assert "Chandler" not in diag1_turn0
    assert "Joey" not in diag1_turn0
    assert "lottery" not in diag1_turn0


def test_window_length_respect(sample_dialogues):
    # k=1 (immediate preceding turn only)
    df_k1 = build_context_representations(sample_dialogues, window_size=1, sep_token=" </s> ")
    turn2_k1 = df_k1.loc[2, "context_text"]
    assert "Joey: No way!" in turn2_k1
    assert "lottery" not in turn2_k1  # Older turn excluded

    # k=2 (both preceding turns included)
    df_k2 = build_context_representations(sample_dialogues, window_size=2, sep_token=" </s> ")
    turn2_k2 = df_k2.loc[2, "context_text"]
    assert "Chandler: I won the lottery!" in turn2_k2
    assert "Joey: No way!" in turn2_k2
    assert "Chandler: I am serious!" in turn2_k2


def test_k0_returns_isolated_turns(sample_dialogues):
    df_k0 = build_context_representations(sample_dialogues, window_size=0, sep_token=" </s> ")
    for idx, row in df_k0.iterrows():
        assert "</s>" not in row["context_text"]
        assert row["context_text"] == f"{row['speaker']}: {row['text']}"
