"""
src/trajectory.py

Core Trajectory Dynamics & Turning-Point Detection Engine.
Calculates:
- Continuous sentiment polarity score: s_t = P_t(positive) - P_t(negative) in [-1, +1]
- Turn-to-turn changes: delta_s_t = s_t - s_{t-1}
- Conversation-level statistics: mean, net change, volatility (std dev of deltas)
- Duration of sustained positive / negative sentiment states
- Candidate turning points based on threshold tau and sign transitions
"""

from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd


def compute_trajectory_statistics(
    df: pd.DataFrame,
    turning_point_threshold: float = 0.4,
    smoothing_window: Optional[int] = None
) -> Dict[str, Any]:
    """
    Compute comprehensive conversation trajectory dynamics.
    
    Expected DataFrame columns:
    ['dialogue_id', 'turn_id', 'speaker', 'text', 'prob_negative', 'prob_neutral', 'prob_positive', 'polarity_score']
    """
    if len(df) == 0:
        return {
            "num_turns": 0,
            "mean_polarity": 0.0,
            "initial_polarity": 0.0,
            "final_polarity": 0.0,
            "net_change": 0.0,
            "volatility": 0.0,
            "max_positive_turn": None,
            "max_negative_turn": None,
            "sustained_positive_turns": 0,
            "sustained_negative_turns": 0,
            "turning_points": [],
            "scores": [],
            "deltas": [],
        }

    scores = df["polarity_score"].values.astype(float)
    num_turns = len(scores)

    # Optional rolling smoothing for noisy probabilities
    if smoothing_window and smoothing_window > 1 and num_turns >= smoothing_window:
        smoothed_scores = pd.Series(scores).rolling(window=smoothing_window, min_periods=1, center=True).mean().values
    else:
        smoothed_scores = scores

    # Turn-to-turn differences
    deltas = np.zeros(num_turns)
    if num_turns > 1:
        deltas[1:] = scores[1:] - scores[:-1]

    mean_polarity = float(np.mean(scores))
    initial_polarity = float(scores[0])
    final_polarity = float(scores[-1])
    net_change = float(scores[-1] - scores[0])
    volatility = float(np.std(deltas[1:])) if num_turns > 1 else 0.0

    # Extrema
    max_pos_idx = int(np.argmax(scores))
    max_neg_idx = int(np.argmin(scores))

    max_positive_turn = {
        "turn_id": int(df.iloc[max_pos_idx]["turn_id"]),
        "speaker": str(df.iloc[max_pos_idx]["speaker"]),
        "text": str(df.iloc[max_pos_idx]["text"]),
        "polarity_score": round(float(scores[max_pos_idx]), 4),
    }

    max_negative_turn = {
        "turn_id": int(df.iloc[max_neg_idx]["turn_id"]),
        "speaker": str(df.iloc[max_neg_idx]["speaker"]),
        "text": str(df.iloc[max_neg_idx]["text"]),
        "polarity_score": round(float(scores[max_neg_idx]), 4),
    }

    # Sustained sentiment runs (continuous runs > +0.1 or < -0.1)
    sustained_pos = 0
    sustained_neg = 0
    curr_pos = 0
    curr_neg = 0

    for s in scores:
        if s > 0.1:
            curr_pos += 1
            curr_neg = 0
            sustained_pos = max(sustained_pos, curr_pos)
        elif s < -0.1:
            curr_neg += 1
            curr_pos = 0
            sustained_neg = max(sustained_neg, curr_neg)
        else:
            curr_pos = 0
            curr_neg = 0

    # Turning points detection: |delta| >= threshold or significant sign reversal
    turning_points = []
    if num_turns > 1:
        for t in range(1, num_turns):
            delta = deltas[t]
            is_threshold_shift = abs(delta) >= turning_point_threshold
            is_sign_flip = (scores[t-1] < -0.15 and scores[t] > 0.15) or (scores[t-1] > 0.15 and scores[t] < -0.15)

            if is_threshold_shift or is_sign_flip:
                shift_type = "positive_shift" if delta > 0 else "negative_shift"
                
                # Extract preceding context text (up to 2 previous turns)
                prev_context = []
                for p_idx in range(max(0, t - 2), t):
                    prev_context.append(f"{df.iloc[p_idx]['speaker']}: \"{df.iloc[p_idx]['text']}\"")

                turning_points.append({
                    "turn_index": t,
                    "turn_id": int(df.iloc[t]["turn_id"]),
                    "speaker": str(df.iloc[t]["speaker"]),
                    "text": str(df.iloc[t]["text"]),
                    "score_before": round(float(scores[t-1]), 4),
                    "score_after": round(float(scores[t]), 4),
                    "delta": round(float(delta), 4),
                    "shift_type": shift_type,
                    "preceding_context": prev_context,
                })

    return {
        "num_turns": num_turns,
        "mean_polarity": round(mean_polarity, 4),
        "initial_polarity": round(initial_polarity, 4),
        "final_polarity": round(final_polarity, 4),
        "net_change": round(net_change, 4),
        "volatility": round(volatility, 4),
        "max_positive_turn": max_positive_turn,
        "max_negative_turn": max_negative_turn,
        "sustained_positive_turns": sustained_pos,
        "sustained_negative_turns": sustained_neg,
        "turning_points": turning_points,
        "scores": [round(float(s), 4) for s in scores],
        "smoothed_scores": [round(float(s), 4) for s in smoothed_scores],
        "deltas": [round(float(d), 4) for d in deltas],
    }
