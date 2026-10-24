"""
scripts/generate_demo_plot.py

Generates a real trajectory plot from model inference for README showcase.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import matplotlib.pyplot as plt
from src.predict import ConversationSentimentAnalyzer

def generate():
    analyzer = ConversationSentimentAnalyzer(default_model="baseline")
    sample = (
        "Alice: Why didn't you inform me about the sudden project deadline change?\n"
        "Bob: I was overwhelmed with client meetings all morning, I didn't mean to keep you in the dark.\n"
        "Alice: It completely ruined my afternoon schedule and I had to cancel personal plans.\n"
        "Bob: I sincerely apologize for that. That was totally my fault, I should have texted earlier.\n"
        "Alice: Thank you for acknowledging it. Let's make sure we sync on Slack every morning.\n"
        "Bob: Absolutely. I'll take care of the final client deck so you don't have to work late.\n"
        "Alice: That's very helpful, thank you so much! I appreciate your support."
    )

    res = analyzer.analyze_conversation(sample, input_type="text", model_type="baseline")
    stats = res["trajectory_stats"]
    df = res["predictions_df"]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 5.5), dpi=150, facecolor="#FFFDF6")
    ax1.set_facecolor("#FFFDF6")
    ax2.set_facecolor("#FFFDF6")

    turns = list(range(len(df)))
    scores = stats["scores"]

    # Shaded zones
    ax1.axhspan(0.15, 1.0, color="#5AAE91", alpha=0.12, label="Positive Zone (> +0.15)")
    ax1.axhspan(-0.15, 0.15, color="#8795A5", alpha=0.08, label="Neutral Zone")
    ax1.axhspan(-1.0, -0.15, color="#D97873", alpha=0.12, label="Negative Zone (< -0.15)")
    ax1.axhline(0, color="#777873", linestyle="--", linewidth=0.9, alpha=0.6)

    # Main trajectory line
    ax1.plot(turns, scores, marker="o", markersize=6, color="#292A2D", linewidth=2.2, label="Polarity Score (s_t)")

    # Turning points
    for tp in stats["turning_points"]:
        t = tp["turn_index"]
        s = tp["score_after"]
        delta = tp["delta"]
        col = "#5AAE91" if delta > 0 else "#D97873"
        ax1.plot(t, s, marker="*", markersize=14, color=col)
        ax1.annotate(
            f"Shift T{t} ({delta:+.2f})",
            (t, s),
            xytext=(t, s + (0.16 if s >= 0 else -0.18)),
            ha="center",
            fontsize=8,
            fontweight="bold",
            color=col,
            bbox=dict(boxstyle="round,pad=0.2", facecolor="#FFFDF6", edgecolor=col, alpha=0.9),
            arrowprops=dict(arrowstyle="->", color=col, lw=1)
        )

    ax1.set_ylim(-1.05, 1.05)
    ax1.set_ylabel("Predicted Polarity (s_t)", fontsize=9, fontweight="bold", color="#292A2D")
    ax1.set_title("Conversation Sentiment Trajectory & Turning-Point Analysis", fontsize=11, fontweight="bold", color="#292A2D")
    ax1.grid(True, linestyle=":", alpha=0.4, color="#E8E4D9")
    ax1.legend(loc="upper left", fontsize=8, facecolor="#FFFDF6", edgecolor="#E8E4D9")

    # Subplot 2: probabilities
    ax2.bar(turns, df["prob_negative"], color="#D97873", label="Negative", width=0.6, alpha=0.85)
    ax2.bar(turns, df["prob_neutral"], bottom=df["prob_negative"], color="#8795A5", label="Neutral", width=0.6, alpha=0.85)
    ax2.bar(turns, df["prob_positive"], bottom=df["prob_negative"] + df["prob_neutral"], color="#5AAE91", label="Positive", width=0.6, alpha=0.85)
    ax2.set_ylim(0, 1.02)
    ax2.set_xlabel("Conversation Turn Index (t)", fontsize=9, fontweight="bold", color="#292A2D")
    ax2.set_ylabel("Class Probability", fontsize=9, fontweight="bold", color="#292A2D")
    ax2.set_xticks(turns)
    ax2.set_xticklabels([f"T{t}" for t in turns], fontsize=8)
    ax2.grid(True, linestyle=":", alpha=0.4, color="#E8E4D9")
    ax2.legend(loc="lower left", fontsize=8, ncol=3, facecolor="#FFFDF6", edgecolor="#E8E4D9")

    fig.tight_layout()
    out_fig = Path("assets/demo_trajectory_plot.png")
    fig.savefig(out_fig, bbox_inches="tight")
    print("Demo plot generated successfully at:", out_fig)

if __name__ == "__main__":
    generate()
