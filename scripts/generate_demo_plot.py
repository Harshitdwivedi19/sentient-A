"""
scripts/generate_demo_plot.py

Generates a real trajectory plot from model inference for README showcase
using a genuine customer dispute and resolution dialogue that exhibits a
pronounced inflection point (T0-T2 negative -> T3 neutral -> T4 positive).
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
        "Customer: This is ridiculous! My order is 5 days late and customer support has been completely useless!\n"
        "Support: I am very sorry for this terrible experience. I understand your frustration.\n"
        "Customer: Sorry doesn't fix it. I want a full refund immediately or I am canceling my subscription.\n"
        "Support: I have processed your full refund right now, and credited $20 to your account for the inconvenience.\n"
        "Customer: Oh wow, thank you so much! That is actually really great customer service, I really appreciate you resolving this quickly."
    )

    res = analyzer.analyze_conversation(sample, model_type="baseline")
    stats = res["trajectory_stats"]
    df = res["predictions_df"]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 5.8), dpi=150, facecolor="#FFFDF6")
    ax1.set_facecolor("#FFFDF6")
    ax2.set_facecolor("#FFFDF6")

    turns = list(range(len(df)))
    scores = stats["scores"]

    # 1. Shaded zones
    ax1.axhspan(0.15, 1.05, color="#5AAE91", alpha=0.14, label="Positive Zone (s > +0.15)")
    ax1.axhspan(-0.15, 0.15, color="#8795A5", alpha=0.10, label="Neutral Zone (-0.15 <= s <= +0.15)")
    ax1.axhspan(-1.05, -0.15, color="#D97873", alpha=0.14, label="Negative Zone (s < -0.15)")
    ax1.axhline(0, color="#777873", linestyle="--", linewidth=0.9, alpha=0.7)

    # 2. Main trajectory line
    ax1.plot(turns, scores, marker="o", markersize=7, color="#292A2D", linewidth=2.4, label="Polarity Score ($s_t = P(pos) - P(neg)$)", zorder=3)

    # Annotate points with speaker & score
    speakers = df["speaker"].tolist()
    for idx, (t, s, spk) in enumerate(zip(turns, scores, speakers)):
        offset_y = 0.12 if s >= 0 else -0.16
        ax1.annotate(
            f"T{t} ({spk}): {s:+.2f}",
            (t, s),
            xytext=(t, s + offset_y),
            ha="center",
            fontsize=8,
            color="#292A2D",
            fontweight="semibold",
            bbox=dict(boxstyle="round,pad=0.2", facecolor="#FFFDF6", edgecolor="#E8E4D9", alpha=0.85)
        )

    # 3. Highlight Turning Points
    for tp in stats["turning_points"]:
        t = tp["turn_index"]
        s = tp["score_after"]
        delta = tp["delta"]
        col = "#10B981" if delta > 0 else "#EF4444"
        ax1.plot(t, s, marker="*", markersize=16, color=col, zorder=5)
        ax1.annotate(
            f"Candidate Pivot T{t} (Delta: {delta:+.2f})",
            (t, s),
            xytext=(t - 0.45, s - 0.22),
            ha="center",
            fontsize=8.5,
            fontweight="bold",
            color=col,
            bbox=dict(boxstyle="round,pad=0.3", facecolor="#FFFDF6", edgecolor=col, alpha=0.95),
            arrowprops=dict(arrowstyle="->", color=col, lw=1.5)
        )

    ax1.set_ylim(-1.15, 1.15)
    ax1.set_ylabel("Predicted Polarity ($s_t$)", fontsize=9, fontweight="bold", color="#292A2D")
    ax1.set_title("Customer Dispute & Resolution: Real Sentiment Trajectory & Inflection Analysis", fontsize=11, fontweight="bold", color="#292A2D", pad=12)
    ax1.grid(True, linestyle=":", alpha=0.45, color="#D5D0C2")
    ax1.legend(loc="lower left", fontsize=8, facecolor="#FFFDF6", edgecolor="#E8E4D9")

    # 4. Subplot 2: Stacked Class Probabilities
    ax2.bar(turns, df["prob_negative"], color="#D97873", label="Negative $P(neg)$", width=0.55, alpha=0.88)
    ax2.bar(turns, df["prob_neutral"], bottom=df["prob_negative"], color="#8795A5", label="Neutral $P(neu)$", width=0.55, alpha=0.88)
    ax2.bar(turns, df["prob_positive"], bottom=df["prob_negative"] + df["prob_neutral"], color="#5AAE91", label="Positive $P(pos)$", width=0.55, alpha=0.88)
    
    ax2.set_ylim(0, 1.05)
    ax2.set_xlabel("Conversation Turn Index (t)", fontsize=9, fontweight="bold", color="#292A2D")
    ax2.set_ylabel("Probability Distribution", fontsize=9, fontweight="bold", color="#292A2D")
    ax2.set_xticks(turns)
    ax2.set_xticklabels([f"T{t}\n({speakers[t]})" for t in turns], fontsize=8.5)
    ax2.grid(True, linestyle=":", alpha=0.45, color="#D5D0C2")
    ax2.legend(loc="lower left", fontsize=8, ncol=3, facecolor="#FFFDF6", edgecolor="#E8E4D9")

    fig.tight_layout()
    out_fig = PROJECT_ROOT / "assets" / "demo_trajectory_plot.png"
    fig.savefig(out_fig, bbox_inches="tight")
    print("Demo plot generated successfully at:", out_fig)

if __name__ == "__main__":
    generate()
