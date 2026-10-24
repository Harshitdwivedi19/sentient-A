"""
src/explain.py

Evidence-Grounded Written Explanation Engine.
Generates structured, auditable analytical reports adhering to:
- Risk #80: Non-causal language ("coincided with", "followed turn X").
- Risk #82: Verbatim excerpts indexing existing records.
- Risk #85: Strict prohibition against inferring psychological states or intent.
"""

from typing import Dict, Any, List
import numpy as np
import pandas as pd


def determine_macro_pattern(net_change: float, volatility: float, num_turning_points: int, mean_polarity: float) -> str:
    """Classify overall conversational sentiment trajectory based on documented thresholds."""
    if net_change >= 0.35 and mean_polarity >= 0.1:
        return "Markedly Improving"
    elif net_change >= 0.15:
        return "Modestly Improving"
    elif net_change <= -0.35 and mean_polarity <= -0.1:
        return "Markedly Deteriorating"
    elif net_change <= -0.15:
        return "Modestly Deteriorating"
    elif volatility >= 0.35 or num_turning_points >= 2:
        return "Volatile / Highly Fluctuating"
    elif volatility <= 0.15 and abs(mean_polarity) <= 0.2:
        return "Stable / Neutral Baseline"
    else:
        return "Fluctuating with Stable Baseline"


def generate_conversation_explanation(
    df: pd.DataFrame,
    stats: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate an auditable, evidence-linked trajectory report.
    Returns structured dictionary and formatted Markdown string.
    """
    num_turns = stats["num_turns"]
    if num_turns == 0:
        return {
            "summary_pattern": "Empty Dialogue",
            "markdown_report": "No utterances to analyze.",
            "sections": {}
        }

    mean_pol = stats["mean_polarity"]
    net_change = stats["net_change"]
    volatility = stats["volatility"]
    turning_points = stats["turning_points"]
    init_score = stats["initial_polarity"]
    final_score = stats["final_polarity"]

    pattern = determine_macro_pattern(net_change, volatility, len(turning_points), mean_pol)

    # 1. Overall Trajectory
    sec_overall = (
        f"The conversation displays a **{pattern}** linguistic sentiment pattern across {num_turns} conversational turns. "
        f"The average estimated sentiment polarity is **{mean_pol:+.2f}** (on a standardized scale from -1.00 to +1.00), "
        f"with a turn-to-turn volatility score of **{volatility:.2f}**."
    )

    # 2. Beginning vs. Ending Comparison
    sec_endpoints = (
        f"The conversation commenced at an estimated polarity of **{init_score:+.2f}** (Turn 0: *{df.iloc[0]['speaker']}*) "
        f"and concluded at **{final_score:+.2f}** (Turn {num_turns-1}: *{df.iloc[-1]['speaker']}*), representing a net directional drift of "
        f"**{net_change:+.2f}**. Note that endpoint differences summarize net direction but do not capture intermediate fluctuations."
    )

    # 3. Conversation Phases (Tri-partition)
    if num_turns >= 3:
        third = num_turns // 3
        p1_scores = df["polarity_score"].iloc[:third]
        p2_scores = df["polarity_score"].iloc[third: 2 * third]
        p3_scores = df["polarity_score"].iloc[2 * third:]
        sec_phases = (
            f"- **Opening Phase (Turns 0–{third-1})**: Average polarity **{p1_scores.mean():+.2f}**\n"
            f"- **Middle Phase (Turns {third}–{2*third-1})**: Average polarity **{p2_scores.mean():+.2f}**\n"
            f"- **Closing Phase (Turns {2*third}–{num_turns-1})**: Average polarity **{p3_scores.mean():+.2f}**"
        )
    else:
        sec_phases = "Dialogue contains fewer than 3 turns; phase segmentation is omitted."

    # 4. Turning Points Analysis
    sec_shifts = []
    if len(turning_points) > 0:
        for idx, tp in enumerate(turning_points, 1):
            direction = "positive upward" if tp["delta"] > 0 else "negative downward"
            context_snippet = ""
            if tp["preceding_context"]:
                context_snippet = f"\n  *Preceding Context*: {' | '.join(tp['preceding_context'])}"
            
            shift_entry = (
                f"{idx}. **Turn {tp['turn_id']} ({tp['speaker']})**: Shifted **{direction}** by **{tp['delta']:+.2f}** "
                f"(from {tp['score_before']:+.2f} to {tp['score_after']:+.2f}).\n"
                f"  *Utterance Excerpt*: \"{tp['text']}\"{context_snippet}"
            )
            sec_shifts.append(shift_entry)
        sec_shifts_text = "\n\n".join(sec_shifts)
    else:
        sec_shifts_text = "No large turn-to-turn shifts exceeded the sensitivity threshold."

    # 5. Scientific Limitations & Epistemic Boundaries
    sec_limitations = (
        "1. **Linguistic Proxy vs. Emotional State**: The model estimates expressed textual sentiment polarity, "
        "not ground-truth psychological states, neurochemical emotions, or sincerity.\n"
        "2. **Ambiguity & Sarcasm**: Terse utterances ('Yeah right', 'Whatever') rely heavily on vocal prosody "
        "and cultural context that text-only representations may misjudge.\n"
        "3. **Non-Causal Attribution**: Observed polarity shifts coincide with specific messages but do not establish "
        "that the cited text was the sole psychological cause of the conversational tone change."
    )

    # Compile Markdown Document
    md_lines = [
        f"### Conversation Trajectory Report: {pattern}\n",
        "#### A. Overall Trajectory Pattern",
        sec_overall,
        "\n#### B. Beginning vs. Ending Comparison",
        sec_endpoints,
        "\n#### C. Conversation Phase Dynamics",
        sec_phases,
        "\n#### D. Notable Sentiment Shifts & Context",
        sec_shifts_text,
        "\n#### E. Epistemic Limitations & Uncertainty",
        sec_limitations
    ]
    full_markdown = "\n".join(md_lines)

    return {
        "summary_pattern": pattern,
        "markdown_report": full_markdown,
        "sections": {
            "overall": sec_overall,
            "endpoints": sec_endpoints,
            "phases": sec_phases,
            "shifts": sec_shifts_text,
            "limitations": sec_limitations,
        }
    }
