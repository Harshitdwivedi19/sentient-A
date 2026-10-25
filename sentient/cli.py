"""
sentient/cli.py

Unified command-line interface for the Sentient-A package.
Commands:
  - sentient analyze <file_path_or_text>
  - sentient gui
  - sentient api [--port PORT] [--host HOST]
  - sentient version
"""

import argparse
import sys
import os
import json
from pathlib import Path

# Ensure UTF-8 output on Windows terminals
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from sentient import __version__


def cmd_analyze(args):
    """Analyze a conversation text string or exported file."""
    from sentient import ConversationSentimentAnalyzer
    input_target = args.input
    analyzer = ConversationSentimentAnalyzer(default_model=args.model)

    p = Path(input_target)
    if p.exists() and p.is_file():
        suffix = p.suffix.lower()
        if suffix in [".txt", ".chat"]:
            input_type = "whatsapp"
        elif suffix == ".csv":
            input_type = "csv"
        else:
            input_type = "text"
            with open(p, "r", encoding="utf-8", errors="ignore") as f:
                input_target = f.read()
    else:
        input_type = "text"
        input_target = input_target.replace("\\n", "\n")

    res = analyzer.analyze_conversation(
        input_data=input_target,
        input_type=input_type,
        model_type=args.model,
        context_window=args.context_window,
    )

    if not res.get("success", False):
        print(f"Error: {res.get('error', 'Analysis failed')}", file=sys.stderr)
        sys.exit(1)

    if args.json:
        # Output structured JSON
        out_data = {
            "version": __version__,
            "model_used": res.get("model_used"),
            "detected_language": res.get("detected_language"),
            "trajectory_stats": res.get("trajectory_stats"),
            "summary_and_results": res.get("summary_and_results"),
            "turns": res.get("predictions_df").to_dict(orient="records") if "predictions_df" in res else []
        }
        print(json.dumps(out_data, indent=2, default=str))
    else:
        # Natural, human-centered console report
        sum_data = res.get("summary_and_results", {})
        exec_sum = sum_data.get("executive_summary", {})
        analysis_res = sum_data.get("analysis_results", {})
        stats = res.get("trajectory_stats", {})

        print("\n" + "=" * 64)
        print(f" SENTIENT CONVERSATION ANALYSIS REPORT (v{__version__})")
        print("=" * 64)
        print(f"Detected Language: {res.get('detected_language', 'unknown').upper()}")
        print(f"Engine Used:       {res.get('model_used')}")
        print(f"Total Turns:       {stats.get('num_turns', 0)}")
        print(f"Average Tone:      {stats.get('mean_polarity', 0.0):+.2f}")
        print(f"Net Tone Drift:    {stats.get('net_change', 0.0):+.2f}")
        print(f"Atmosphere Health: {analysis_res.get('health_status', 'N/A')}")
        print("-" * 64)
        print("EXECUTIVE SUMMARY:")
        print(f"  {exec_sum.get('story', 'N/A')}")
        print()
        print("PARTICIPANT DYNAMICS:")
        print(f"  {exec_sum.get('dynamics', 'N/A')}")
        print("-" * 64)
        print("KEY RESULTS & TAKEAWAY:")
        tb = analysis_res.get("tone_breakdown", {})
        print(f"  • Sentiment Breakdown: {tb.get('positive', 0)}% Pos | {tb.get('neutral', 0)}% Neu | {tb.get('negative', 0)}% Neg")
        print(f"  • {analysis_res.get('decisive_moment', 'N/A')}")
        print(f"  • Takeaway: {analysis_res.get('key_takeaway', 'N/A')}")
        print("=" * 64 + "\n")


def cmd_gui(args):
    """Launch the Windows Desktop Studio."""
    import tkinter as tk
    from src.desktop_app import SentimentTrajectoryDesktopApp

    root = tk.Tk()
    app = SentimentTrajectoryDesktopApp(root)
    root.mainloop()


def cmd_api(args):
    """Launch the FastAPI REST service."""
    import uvicorn
    from src.api import app

    print(f"Starting Sentient REST API server on http://{args.host}:{args.port}...")
    uvicorn.run(app, host=args.host, port=args.port)


def main():
    parser = argparse.ArgumentParser(
        prog="sentient",
        description="Sentient-A: Context-Aware Conversation Sentiment & Trajectory Studio"
    )
    parser.add_argument("--version", "-v", action="version", version=f"sentient-a {__version__}")

    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # Command: analyze
    p_ana = subparsers.add_parser("analyze", help="Analyze conversation text or exported chat file")
    p_ana.add_argument("input", type=str, help="Chat text string or file path (.txt, .csv)")
    p_ana.add_argument("--model", type=str, default="auto", choices=["auto", "baseline", "hindi_baseline", "roberta_context"], help="Model architecture")
    p_ana.add_argument("--context-window", "-k", type=int, default=3, help="Preceding turn context window")
    p_ana.add_argument("--json", action="store_true", help="Output machine-readable JSON")
    p_ana.set_defaults(func=cmd_analyze)

    # Command: gui
    p_gui = subparsers.add_parser("gui", help="Launch the Desktop GUI application")
    p_gui.set_defaults(func=cmd_gui)

    # Command: api
    p_api = subparsers.add_parser("api", help="Start the FastAPI REST backend")
    p_api.add_argument("--host", type=str, default="127.0.0.1", help="Host interface")
    p_api.add_argument("--port", type=int, default=8000, help="Port number")
    p_api.set_defaults(func=cmd_api)

    args = parser.parse_args()

    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(0)

    args.func(args)


if __name__ == "__main__":
    main()
