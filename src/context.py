"""
src/context.py

Context Construction Engine for:
- MELD Benchmark Dialogues
- Exported WhatsApp Chat Logs

Enforces:
1. Zero Dialogue Boundary Leakage (Risk #21): Turn 0 has empty history; never bleeds across dialogue_id.
2. Target Utterance Preservation (Risk #22): Left-truncation of historical turns ensures target message is never cut off.
3. Standardized Speaker Tag Protocol (Risk #43): Uniform formatting: "Speaker: message </s>".
"""

import logging
from typing import List, Optional
import pandas as pd

logger = logging.getLogger(__name__)


def format_turn(speaker: str, text: str, include_speaker: bool = True) -> str:
    """Format an individual turn with optional speaker prefix."""
    speaker_clean = str(speaker).strip()
    text_clean = str(text).strip()
    if include_speaker and speaker_clean:
        return f"{speaker_clean}: {text_clean}"
    return text_clean


def build_context_representations(
    df: pd.DataFrame,
    window_size: int = 3,
    sep_token: str = " </s> ",
    include_speaker: bool = True,
    target_column_name: str = "context_text"
) -> pd.DataFrame:
    """
    Construct context-aware input strings for every utterance in a conversation.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Must contain ['dialogue_id', 'turn_id', 'speaker', 'text'].
    window_size : int
        Number of preceding turns to prepend (k >= 0).
    sep_token : str
        Delimiter token separating conversational turns.
    include_speaker : bool
        Whether to prefix utterances with "Speaker: ".
    target_column_name : str
        Name of the generated context column.

    Returns:
    --------
    pd.DataFrame with added target_column_name containing context-formatted text.
    """
    required_cols = ["dialogue_id", "turn_id", "speaker", "text"]
    for col in required_cols:
        if col not in df.columns:
            raise KeyError(f"Expected column '{col}' missing from DataFrame.")

    # Ensure chronological sort order
    df_sorted = df.sort_values(by=["dialogue_id", "turn_id"]).copy()

    context_strings: List[str] = []

    # Group strictly by dialogue_id to eliminate cross-conversation boundary leakage
    for diag_id, group in df_sorted.groupby("dialogue_id", sort=False):
        turns = group[["speaker", "text"]].values.tolist()
        num_turns = len(turns)

        for i in range(num_turns):
            curr_speaker, curr_text = turns[i]
            curr_turn_str = format_turn(curr_speaker, curr_text, include_speaker=include_speaker)

            if window_size == 0 or i == 0:
                # Independent turn / First turn of conversation: zero history
                context_strings.append(curr_turn_str)
            else:
                # Preceding turns strictly bounded within the current dialogue
                start_idx = max(0, i - window_size)
                preceding_turns = turns[start_idx:i]

                history_parts = [
                    format_turn(spk, txt, include_speaker=include_speaker)
                    for spk, txt in preceding_turns
                ]

                # Format: "PrevSpk1: txt </s> PrevSpk2: txt </s> CurrSpk: target_txt"
                full_context_str = sep_token.join(history_parts) + sep_token + curr_turn_str
                context_strings.append(full_context_str)

    df_sorted[target_column_name] = context_strings
    return df_sorted
