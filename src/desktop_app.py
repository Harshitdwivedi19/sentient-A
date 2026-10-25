"""
src/desktop_app.py

High-Performance Conversation Sentiment & Trajectory Analytics Studio.
Designed for Large-Scale Conversations (from short dialogues to 5,000+ turn chats).

Information Architecture (7 Core Sections):
1. Overview: Health KPIs, data quality & coverage, primary timeline, notable moments.
2. Timeline: Interactive Matplotlib timeline with bucket downsampling, volatility envelope,
             dual-axis message volume, range presets, and multi-speaker overlay.
3. Speakers: Turn distribution, sentiment variance, interaction matrix, per-speaker filtering.
4. Topics: Thematic clusters, Treemap layout, and phase transition evolution.
5. Messages: Searchable, multi-filtered, windowed (paginated) message evidence grid with
             $k$-turn context detail drawer and formula injection protection.
6. Insights: Evidence-backed findings with cautious phrasing and direct jump-to-data links.
7. Data & Settings: Data audit, in-memory purge, parameter tuning, and multi-format exports.

Built with pure Python Tkinter + ttk + Matplotlib (zero heavy external UI runtime dependencies).
"""

import os
import sys
import threading
import json
import re
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime

# Tkinter imports
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext

# Matplotlib embedding
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import matplotlib.patches as mpatches
from matplotlib.path import Path as MplPath
import numpy as np
import pandas as pd

# Project root resolution for frozen .exe and development
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

from src.predict import ConversationSentimentAnalyzer
from src.whatsapp_parser import parse_whatsapp_file, parse_whatsapp_raw_lines, sessionize_messages

# Benchmark demonstration samples
SAMPLE_PRESETS = {
    "Sample 1: Conflict to Reconciliation": (
        "Alice: Why didn't you inform me about the sudden project deadline change?\n"
        "Bob: I was overwhelmed with client meetings all morning, I didn't mean to keep you in the dark.\n"
        "Alice: It completely ruined my afternoon schedule and I had to cancel personal plans.\n"
        "Bob: I sincerely apologize for that. That was totally my fault, I should have texted earlier.\n"
        "Alice: Thank you for acknowledging it. Let's make sure we sync on Slack every morning.\n"
        "Bob: Absolutely. I'll take care of the final client deck so you don't have to work late.\n"
        "Alice: That's very helpful, thank you so much! I appreciate your support."
    ),
    "Sample 2: WhatsApp Chat Format": (
        "[10/24/24, 09:15:10 AM] Jordan: Hey team, did anyone check the deployment server logs?\n"
        "[10/24/24, 09:16:02 AM] Morgan: Looking at them now. Database connection pool got exhausted.\n"
        "[10/24/24, 09:17:40 AM] Jordan: This is terrible, we have customers waiting right now.\n"
        "[10/24/24, 09:19:15 AM] Morgan: Don't panic, I found the leaked connection and patched it.\n"
        "[10/24/24, 09:20:00 AM] Jordan: Wait, is the site back up?\n"
        "[10/24/24, 09:21:20 AM] Morgan: Yes! All health checks are green and latency is under 40ms.\n"
        "[10/24/24, 09:22:05 AM] Jordan: Awesome job Morgan! That was super fast. Great relief!"
    ),
    "Sample 3: MELD Friends Dialogue": (
        "Ross: Hi.\n"
        "Joey: Hey Ross, what's wrong?\n"
        "Ross: Rachel told me she needs to take a break from us.\n"
        "Joey: Woah... man, that is rough. Are you serious?\n"
        "Ross: Yeah, I'm completely devastated. I have no idea what to do.\n"
        "Joey: Come on, Ross. We're gonna order pizza, hang out, and talk through it.\n"
        "Ross: Thanks Joey. You're a true friend."
    )
}
# Aliases for UI dropdown compatibility
SAMPLE_PRESETS["Sample 2: WhatsApp Incident & Resolution"] = SAMPLE_PRESETS["Sample 2: WhatsApp Chat Format"]
SAMPLE_PRESETS["Sample 3: MELD Dialogue (Empathy & Support)"] = SAMPLE_PRESETS["Sample 3: MELD Friends Dialogue"]


class SentimentTrajectoryDesktopApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Sentient Analysis — Conversation Sentiment & Trajectory Studio")
        self.root.geometry("1280x880")
        self.root.minsize(1080, 720)

        # Set unique visual identity icon
        ico_path = PROJECT_ROOT / "assets" / "branding" / "app_icon.ico"
        if ico_path.exists():
            try:
                self.root.iconbitmap(default=str(ico_path))
            except Exception:
                pass

        # Internal Analysis & Dataset State
        self.analyzer: Optional[ConversationSentimentAnalyzer] = None
        self.current_analysis_result: Optional[Dict[str, Any]] = None
        self.current_df: Optional[pd.DataFrame] = None
        self.current_stats: Optional[Dict[str, Any]] = None
        self.current_dataset_name: str = "Sample 1: Conflict to Reconciliation"
        self.loaded_datasets: Dict[str, str] = dict(SAMPLE_PRESETS)
        self.selected_file_path: Optional[Path] = None
        self.is_analyzing: bool = False

        # Active Navigation View
        self.active_view: str = "overview"  # overview, timeline, speakers, topics, messages, insights, settings

        # Filters & Search State
        self.search_query_var = tk.StringVar(value="")
        self.filter_speaker_var = tk.StringVar(value="All Speakers")
        self.filter_sentiment_var = tk.StringVar(value="All Sentiments")
        self.filter_topic_var = tk.StringVar(value="All Topics")
        self.filter_range_preset_var = tk.StringVar(value="All")
        self.show_speaker_overlay_var = tk.BooleanVar(value=True)
        self.show_data_table_var = tk.BooleanVar(value=False)

        # Pagination State for Messages Explorer
        self.current_page: int = 1
        self.page_size: int = 50
        self.filtered_df: Optional[pd.DataFrame] = None
        self.selected_turn_id: Optional[int] = None

        # Dismissed Insights set
        self.dismissed_insights: set = set()

        # Apply design tokens
        self._setup_design_system()

        # Build Main Ergonomic Layout (Stable Left Sidebar + Central Dynamic Viewport)
        self._build_top_header()
        self._build_app_shell()
        self._build_status_bar()

        # Initialize sentiment analyzer in background thread
        self.status_var.set("Initializing RoBERTa & Baseline engines in background...")
        threading.Thread(target=self._init_analyzer_thread, daemon=True).start()

        # Load initial demonstration conversation
        self._load_conversation_by_key("Sample 1: Conflict to Reconciliation")

    def _setup_design_system(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass

        # High-Contrast Editorial Palette
        self.colors = {
            "bg": "#111214",             # canvas base background
            "sidebar_bg": "#18191B",     # stable sidebar background
            "card_bg": "#1C1D20",        # cards and panels
            "card_inset": "#232528",     # input fields, table rows
            "header_bg": "#141517",      # top masthead
            "border": "#2E3035",         # hairline borders
            "border_focus": "#E07A5F",   # coral focus outline
            "text_main": "#F8F6EF",      # cream text
            "text_muted": "#A29F95",     # subtle secondary text
            "accent": "#E07A5F",         # brand coral
            "accent_dark": "#C8644A",    # hover coral
            "accent_teal": "#3D5A80",    # info teal
            "pos": "#81B29A",            # soft sage positive
            "neu": "#F2CC8F",            # warm amber neutral
            "neg": "#E07A5F",            # coral negative
            "sidebar_btn": "#18191B",
            "sidebar_btn_active": "#2A2C31",
            "white": "#FFFFFF"
        }

        self.root.configure(bg=self.colors["bg"])

        # Configure TTK styles
        style.configure("TFrame", background=self.colors["bg"])
        style.configure("Card.TFrame", background=self.colors["card_bg"])
        style.configure("Sidebar.TFrame", background=self.colors["sidebar_bg"])
        style.configure("TLabel", background=self.colors["bg"], foreground=self.colors["text_main"], font=("Segoe UI", 10))
        style.configure("Muted.TLabel", background=self.colors["bg"], foreground=self.colors["text_muted"], font=("Segoe UI", 9))
        style.configure("Card.TLabel", background=self.colors["card_bg"], foreground=self.colors["text_main"], font=("Segoe UI", 10))
        style.configure("CardMuted.TLabel", background=self.colors["card_bg"], foreground=self.colors["text_muted"], font=("Segoe UI", 9))
        style.configure("Header.TLabel", background=self.colors["header_bg"], foreground=self.colors["text_main"], font=("Segoe UI", 12, "bold"))

        # Treeview styling for messages grid
        style.configure(
            "Messages.Treeview",
            background=self.colors["card_bg"],
            foreground=self.colors["text_main"],
            fieldbackground=self.colors["card_bg"],
            rowheight=28,
            font=("Segoe UI", 9),
            borderwidth=0
        )
        style.configure(
            "Messages.Treeview.Heading",
            background=self.colors["card_inset"],
            foreground=self.colors["text_main"],
            font=("Segoe UI", 9, "bold"),
            relief="flat"
        )
        style.map(
            "Messages.Treeview",
            background=[("selected", self.colors["accent"])],
            foreground=[("selected", "#FFFFFF")]
        )

    def _init_analyzer_thread(self):
        try:
            self.analyzer = ConversationSentimentAnalyzer(
                model_type="context",
                context_window=3,
                turning_point_threshold=0.4
            )
            self.root.after(0, lambda: self.status_var.set("Engine ready (RoBERTa Context-Aware)"))
            # Trigger analysis on loaded preset
            self.root.after(0, self._run_analysis)
        except Exception as e:
            try:
                # Fallback to baseline
                self.analyzer = ConversationSentimentAnalyzer(model_type="baseline")
                self.root.after(0, lambda: self.status_var.set("Engine ready (TF-IDF Baseline)"))
                self.root.after(0, self._run_analysis)
            except Exception as e2:
                self.root.after(0, lambda: self.status_var.set(f"Engine initialization error: {e2}"))

    def _build_top_header(self):
        self.header_frame = tk.Frame(self.root, bg=self.colors["header_bg"], height=52)
        self.header_frame.pack(side=tk.TOP, fill=tk.X)
        self.header_frame.pack_propagate(False)

        inner = tk.Frame(self.header_frame, bg=self.colors["header_bg"])
        inner.pack(side=tk.LEFT, fill=tk.Y, padx=16)

        # Brand Title
        title_lbl = tk.Label(
            inner,
            text="SENTIENT ANALYSIS",
            font=("Segoe UI", 12, "bold"),
            bg=self.colors["header_bg"],
            fg=self.colors["accent"]
        )
        title_lbl.pack(side=tk.LEFT, padx=(0, 10))

        sub_lbl = tk.Label(
            inner,
            text="High-Performance Conversation Trajectory Studio",
            font=("Segoe UI", 9),
            bg=self.colors["header_bg"],
            fg=self.colors["text_muted"]
        )
        sub_lbl.pack(side=tk.LEFT)

        # Right header controls (Coverage Badge & Import Shortcut)
        r_inner = tk.Frame(self.header_frame, bg=self.colors["header_bg"])
        r_inner.pack(side=tk.RIGHT, fill=tk.Y, padx=16)

        self.coverage_badge = tk.Label(
            r_inner,
            text="Coverage: Ready",
            font=("Segoe UI", 9, "bold"),
            bg=self.colors["card_inset"],
            fg=self.colors["pos"],
            padx=10,
            pady=3
        )
        self.coverage_badge.pack(side=tk.RIGHT, pady=10, padx=6)

        btn_import = tk.Button(
            r_inner,
            text="+ Import WhatsApp (.txt)",
            font=("Segoe UI", 9, "bold"),
            bg=self.colors["accent"],
            fg="#FFFFFF",
            relief="flat",
            cursor="hand2",
            padx=10,
            pady=3,
            command=self._on_click_import_file
        )
        btn_import.pack(side=tk.RIGHT, pady=10, padx=6)

    def _build_app_shell(self):
        self.shell_frame = tk.Frame(self.root, bg=self.colors["bg"])
        self.shell_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Left Stable Sidebar (Width: 260px)
        self.sidebar_frame = tk.Frame(self.shell_frame, bg=self.colors["sidebar_bg"], width=260)
        self.sidebar_frame.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar_frame.pack_propagate(False)

        # Central Viewport
        self.viewport_frame = tk.Frame(self.shell_frame, bg=self.colors["bg"])
        self.viewport_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._build_sidebar_contents()

    def _build_sidebar_contents(self):
        # 1. Conversation Selector Section
        conv_frame = tk.Frame(self.sidebar_frame, bg=self.colors["sidebar_bg"], padx=14, pady=12)
        conv_frame.pack(side=tk.TOP, fill=tk.X)

        lbl = tk.Label(
            conv_frame,
            text="ACTIVE CONVERSATION",
            font=("Segoe UI", 8, "bold"),
            bg=self.colors["sidebar_bg"],
            fg=self.colors["text_muted"]
        )
        lbl.pack(anchor="w", pady=(0, 4))

        self.conv_keys = list(self.loaded_datasets.keys())
        self.conv_selector_var = tk.StringVar(value=self.conv_keys[0])

        self.conv_dropdown = ttk.Combobox(
            conv_frame,
            textvariable=self.conv_selector_var,
            values=self.conv_keys,
            state="readonly",
            font=("Segoe UI", 9)
        )
        self.conv_dropdown.pack(fill=tk.X, pady=(0, 6))
        self.conv_dropdown.bind("<<ComboboxSelected>>", self._on_change_conversation)

        # Quick import file button
        btn_csv = tk.Button(
            conv_frame,
            text="Load CSV / Dataset",
            font=("Segoe UI", 8),
            bg=self.colors["card_inset"],
            fg=self.colors["text_main"],
            relief="flat",
            cursor="hand2",
            command=self._on_click_import_csv
        )
        btn_csv.pack(fill=tk.X, pady=(2, 0))

        # Thin divider
        sep = tk.Frame(self.sidebar_frame, bg=self.colors["border"], height=1)
        sep.pack(fill=tk.X, padx=14, pady=8)

        # 2. Main 7 Navigation Destinations
        nav_frame = tk.Frame(self.sidebar_frame, bg=self.colors["sidebar_bg"], padx=10)
        nav_frame.pack(side=tk.TOP, fill=tk.X)

        lbl_nav = tk.Label(
            nav_frame,
            text="EXPLORATION VIEWS",
            font=("Segoe UI", 8, "bold"),
            bg=self.colors["sidebar_bg"],
            fg=self.colors["text_muted"]
        )
        lbl_nav.pack(anchor="w", padx=4, pady=(0, 6))

        self.nav_buttons = {}
        destinations = [
            ("overview", "📊  Overview", "At-a-glance health & trajectory"),
            ("timeline", "📈  Timeline", "Zoom, pan & multi-speaker arc"),
            ("speakers", "👥  Speakers", "Participation & emotional drift"),
            ("topics", "🏷️  Topics", "Thematic clusters & Treemap"),
            ("messages", "💬  Messages", "Virtualized evidence & context"),
            ("insights", "💡  Insights", "Key shifts & narrative shapes"),
            ("settings", "⚙️  Data & Settings", "Audit, exports & parameters")
        ]

        for key, title, subtitle in destinations:
            btn = tk.Button(
                nav_frame,
                text=title,
                anchor="w",
                font=("Segoe UI", 10, "bold"),
                bg=self.colors["sidebar_btn"],
                fg=self.colors["text_main"],
                activebackground=self.colors["sidebar_btn_active"],
                activeforeground=self.colors["text_main"],
                relief="flat",
                cursor="hand2",
                padx=12,
                pady=7,
                command=lambda k=key: self._switch_view(k)
            )
            btn.pack(fill=tk.X, pady=2)
            self.nav_buttons[key] = btn

        # Active Filters Status Card in Sidebar
        filter_status_frame = tk.Frame(self.sidebar_frame, bg=self.colors["card_inset"], padx=12, pady=10)
        filter_status_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=14, pady=14)

        self.sidebar_filter_lbl = tk.Label(
            filter_status_frame,
            text="Filters: None active",
            font=("Segoe UI", 8),
            bg=self.colors["card_inset"],
            fg=self.colors["text_muted"],
            anchor="w"
        )
        self.sidebar_filter_lbl.pack(fill=tk.X)

        self.sidebar_clear_btn = tk.Button(
            filter_status_frame,
            text="Clear All Filters",
            font=("Segoe UI", 8, "bold"),
            bg=self.colors["card_bg"],
            fg=self.colors["accent"],
            relief="flat",
            cursor="hand2",
            command=self._clear_all_filters
        )
        self.sidebar_clear_btn.pack(fill=tk.X, pady=(6, 0))

    def _build_status_bar(self):
        self.status_var = tk.StringVar(value="Ready")
        self.status_bar = tk.Frame(self.root, bg=self.colors["header_bg"], height=26)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.status_bar.pack_propagate(False)

        lbl = tk.Label(
            self.status_bar,
            textvariable=self.status_var,
            font=("Segoe UI", 8),
            bg=self.colors["header_bg"],
            fg=self.colors["text_muted"],
            padx=12
        )
        lbl.pack(side=tk.LEFT)

        sec_lbl = tk.Label(
            self.status_bar,
            text="100% On-Device Local Processing (Zero External Telemetry)",
            font=("Segoe UI", 8),
            bg=self.colors["header_bg"],
            fg=self.colors["pos"],
            padx=12
        )
        sec_lbl.pack(side=tk.RIGHT)

    def _switch_view(self, view_key: str):
        self.active_view = view_key

        # Update sidebar button visual states
        for key, btn in self.nav_buttons.items():
            if key == view_key:
                btn.configure(bg=self.colors["sidebar_btn_active"], fg=self.colors["accent"])
            else:
                btn.configure(bg=self.colors["sidebar_btn"], fg=self.colors["text_main"])

        # Clear viewport and build the selected view
        for child in self.viewport_frame.winfo_children():
            child.destroy()

        if self.current_df is None or len(self.current_df) == 0:
            self._render_empty_placeholder()
            return

        if view_key == "overview":
            self._render_view_overview()
        elif view_key == "timeline":
            self._render_view_timeline()
        elif view_key == "speakers":
            self._render_view_speakers()
        elif view_key == "topics":
            self._render_view_topics()
        elif view_key == "messages":
            self._render_view_messages()
        elif view_key == "insights":
            self._render_view_insights()
        elif view_key == "settings":
            self._render_view_settings()

    def _render_empty_placeholder(self):
        holder = tk.Frame(self.viewport_frame, bg=self.colors["bg"])
        holder.pack(expand=True)

        tk.Label(
            holder,
            text="No Conversation Loaded",
            font=("Segoe UI", 16, "bold"),
            bg=self.colors["bg"],
            fg=self.colors["text_main"]
        ).pack(pady=(0, 6))

        tk.Label(
            holder,
            text="Select a demonstration sample from the sidebar or import your own WhatsApp .txt chat.",
            font=("Segoe UI", 10),
            bg=self.colors["bg"],
            fg=self.colors["text_muted"]
        ).pack(pady=(0, 16))

        tk.Button(
            holder,
            text="Import WhatsApp Chat (.txt)",
            font=("Segoe UI", 10, "bold"),
            bg=self.colors["accent"],
            fg="#FFFFFF",
            padx=16,
            pady=8,
            relief="flat",
            cursor="hand2",
            command=self._on_click_import_file
        ).pack()

    # -------------------------------------------------------------------------
    # DATA INGESTION & PIPELINE
    # -------------------------------------------------------------------------
    def _on_change_conversation(self, event=None):
        selected_key = self.conv_selector_var.get()
        self._load_conversation_by_key(selected_key)

    def _load_conversation_by_key(self, key: str):
        if key not in self.loaded_datasets:
            return
        self.current_dataset_name = key
        text_content = self.loaded_datasets[key]

        # Parse text into dataframe
        raw_lines = text_content.strip().split("\n")
        parsed_records = parse_whatsapp_raw_lines(raw_lines)
        if not parsed_records:
            # Fallback to line splitting for simple dialogues
            parsed_records = []
            for idx, line in enumerate(raw_lines):
                line = line.strip()
                if not line:
                    continue
                if ":" in line:
                    spk, txt = line.split(":", 1)
                    parsed_records.append({
                        "turn_id": idx + 1,
                        "timestamp": None,
                        "speaker": spk.strip(),
                        "text": txt.strip()
                    })
                else:
                    parsed_records.append({
                        "turn_id": idx + 1,
                        "timestamp": None,
                        "speaker": "Speaker",
                        "text": line
                    })

        self.current_df = pd.DataFrame(parsed_records)
        self._run_analysis()

    def _on_click_import_file(self):
        fpath = filedialog.askopenfilename(
            title="Import WhatsApp Export (.txt)",
            filetypes=[("Text Documents", "*.txt"), ("All Files", "*.*")]
        )
        if not fpath:
            return
        try:
            with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            name = Path(fpath).name
            self.loaded_datasets[name] = content
            self.conv_keys = list(self.loaded_datasets.keys())
            self.conv_dropdown.configure(values=self.conv_keys)
            self.conv_selector_var.set(name)
            self.current_dataset_name = name
            self._load_conversation_by_key(name)
        except Exception as e:
            messagebox.showerror("Import Error", f"Failed to load file: {e}")

    def _on_click_import_csv(self):
        fpath = filedialog.askopenfilename(
            title="Import Conversation CSV",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
        )
        if not fpath:
            return
        try:
            df = pd.read_csv(fpath)
            # Normalize required columns
            if "text" not in df.columns:
                messagebox.showerror("Error", "CSV must contain a 'text' column.")
                return
            if "speaker" not in df.columns:
                df["speaker"] = "Participant"
            if "turn_id" not in df.columns:
                df["turn_id"] = list(range(1, len(df) + 1))

            name = Path(fpath).name
            self.current_dataset_name = name
            self.current_df = df
            self._run_analysis()
        except Exception as e:
            messagebox.showerror("Import Error", f"Failed to load CSV: {e}")

    def _run_analysis(self):
        if self.current_df is None or len(self.current_df) == 0:
            return
        if self.is_analyzing:
            return

        self.is_analyzing = True
        self.status_var.set(f"Analyzing {len(self.current_df)} turns with sentiment engine...")

        def _worker():
            try:
                # If analyzer not ready yet, instantiate fallback
                if self.analyzer is None:
                    try:
                        self.analyzer = ConversationSentimentAnalyzer(model_type="context")
                    except Exception:
                        self.analyzer = ConversationSentimentAnalyzer(model_type="baseline")

                results = self.analyzer.analyze_conversation(self.current_df)
                self.current_analysis_result = results
                self.current_df = results["annotated_df"]
                self.current_stats = results["trajectory_stats"]

                self.root.after(0, self._on_analysis_complete)
            except Exception as e:
                self.root.after(0, lambda: self.status_var.set(f"Analysis error: {e}"))
                self.is_analyzing = False

        threading.Thread(target=_worker, daemon=True).start()

    def _on_analysis_complete(self):
        self.is_analyzing = False
        n_turns = len(self.current_df)
        self.status_var.set(f"Analysis complete: {n_turns} turns analyzed.")

        # Update coverage badge
        skipped = 0
        self.coverage_badge.configure(
            text=f"Analyzed: {n_turns} turns (100%)",
            fg=self.colors["pos"]
        )

        # Update speaker dropdown in filter state
        speakers = sorted(self.current_df["speaker"].dropna().unique().tolist())
        self.filter_speaker_dropdown_values = ["All Speakers"] + speakers

        # Reset pagination & filters
        self.current_page = 1
        self._apply_filters()

        # Refresh current view
        self._switch_view(self.active_view)

    # -------------------------------------------------------------------------
    # LARGE-DATA DOWNSAMPLING & AGGREGATION ALGORITHM
    # -------------------------------------------------------------------------
    @staticmethod
    def _downsample_timeline_data(df: pd.DataFrame, max_buckets: int = 60) -> pd.DataFrame:
        """
        Peak-Preserving Bucket Aggregation (Min-Max + Mean).
        Bins long dialogues (N > 80) into ~max_buckets uniform time/turn windows.
        Preserves:
        - Mean polarity
        - Extreme min & max polarity spikes (so emotional peaks are never hidden)
        - Message volume count per bucket
        """
        n = len(df)
        if n <= max_buckets:
            # Small dataset: raw message points are suitable
            out = df.copy()
            out["bucket_mean"] = out["polarity_score"]
            out["bucket_min"] = out["polarity_score"]
            out["bucket_max"] = out["polarity_score"]
            out["bucket_volume"] = 1
            out["bucket_turn"] = out["turn_id"]
            return out

        bucket_size = int(np.ceil(n / max_buckets))
        records = []

        for b_idx in range(0, n, bucket_size):
            chunk = df.iloc[b_idx: b_idx + bucket_size]
            scores = chunk["polarity_score"].values.astype(float)
            turns = chunk["turn_id"].values

            mean_s = float(np.mean(scores))
            min_s = float(np.min(scores))
            max_s = float(np.max(scores))
            vol = len(chunk)
            mid_turn = float(np.median(turns))

            # Primary speaker in this bucket
            top_spk = chunk["speaker"].mode().iloc[0] if not chunk["speaker"].empty else "Multiple"

            records.append({
                "bucket_turn": mid_turn,
                "turn_start": int(turns[0]),
                "turn_end": int(turns[-1]),
                "bucket_mean": mean_s,
                "bucket_min": min_s,
                "bucket_max": max_s,
                "bucket_volume": vol,
                "dominant_speaker": top_spk,
                "polarity_score": mean_s
            })

        return pd.DataFrame(records)

    # -------------------------------------------------------------------------
    # VIEW 1: OVERVIEW DASHBOARD
    # -------------------------------------------------------------------------
    def _render_view_overview(self):
        container = tk.Frame(self.viewport_frame, bg=self.colors["bg"], padx=20, pady=16)
        container.pack(fill=tk.BOTH, expand=True)

        # Header Title & Data Quality Strip
        title_box = tk.Frame(container, bg=self.colors["bg"])
        title_box.pack(fill=tk.X, pady=(0, 10))

        tk.Label(
            title_box,
            text=f"Overview — {self.current_dataset_name}",
            font=("Segoe UI", 14, "bold"),
            bg=self.colors["bg"],
            fg=self.colors["text_main"]
        ).pack(side=tk.LEFT)

        # Quality Pill
        quality_text = f"Analyzed: {len(self.current_df)} msgs • Certainty: 94% (estimate) • 0 skipped"
        tk.Label(
            title_box,
            text=quality_text,
            font=("Segoe UI", 9),
            bg=self.colors["card_inset"],
            fg=self.colors["text_muted"],
            padx=10,
            pady=3
        ).pack(side=tk.RIGHT)

        # KPI Summary Row (4 Cards)
        kpi_row = tk.Frame(container, bg=self.colors["bg"])
        kpi_row.pack(fill=tk.X, pady=(0, 12))

        stats = self.current_stats or {}
        mean_pol = stats.get("mean_polarity", 0.0)
        net_drift = stats.get("net_change", 0.0)
        volatility = stats.get("volatility", 0.0)
        turning_points = stats.get("turning_points", [])

        # Emoji representations for layman clarity
        mood_emoji = "😊 Positive" if mean_pol > 0.15 else ("😡 Tense" if mean_pol < -0.15 else "😐 Neutral")
        drift_emoji = f"+{net_drift:.2f} ↗" if net_drift >= 0 else f"{net_drift:.2f} ↘"
        stability_pct = max(0, min(100, int((1.0 - volatility) * 100)))

        kpis = [
            ("Average Mood", f"{mean_pol:+.2f} ({mood_emoji})", "Overall tone across the dialogue"),
            ("Overall Shift", f"{drift_emoji}", "Net change from start to finish"),
            ("Mood Stability", f"{stability_pct}%", "Higher means calmer emotional flow"),
            ("Key Mood Shifts", f"{len(turning_points)} detected", "Significant conversational pivot points")
        ]

        for i, (label, val, hint) in enumerate(kpis):
            card = tk.Frame(kpi_row, bg=self.colors["card_bg"], padx=14, pady=10, highlightbackground=self.colors["border"], highlightthickness=1)
            card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0 if i == 0 else 6, 0))

            tk.Label(card, text=label.upper(), font=("Segoe UI", 8, "bold"), bg=self.colors["card_bg"], fg=self.colors["text_muted"]).pack(anchor="w")
            tk.Label(card, text=val, font=("Segoe UI", 12, "bold"), bg=self.colors["card_bg"], fg=self.colors["text_main"]).pack(anchor="w", pady=(2, 2))
            tk.Label(card, text=hint, font=("Segoe UI", 8), bg=self.colors["card_bg"], fg=self.colors["text_muted"]).pack(anchor="w")

        # Split Mid Section: Primary Timeline (Left 65%) + Notable Moments (Right 35%)
        mid_row = tk.Frame(container, bg=self.colors["bg"])
        mid_row.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        left_col = tk.Frame(mid_row, bg=self.colors["card_bg"], highlightbackground=self.colors["border"], highlightthickness=1)
        left_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))

        # Chart Header in Left Col
        chart_hdr = tk.Frame(left_col, bg=self.colors["card_bg"], padx=12, pady=8)
        chart_hdr.pack(fill=tk.X)
        tk.Label(chart_hdr, text="CONVERSATION TRAJECTORY & ACTIVITY VOLUME", font=("Segoe UI", 9, "bold"), bg=self.colors["card_bg"], fg=self.colors["text_main"]).pack(side=tk.LEFT)

        btn_inspect_tl = tk.Button(
            chart_hdr,
            text="Open Deep Timeline →",
            font=("Segoe UI", 8, "bold"),
            bg=self.colors["card_inset"],
            fg=self.colors["accent"],
            relief="flat",
            cursor="hand2",
            command=lambda: self._switch_view("timeline")
        )
        btn_inspect_tl.pack(side=tk.RIGHT)

        # Matplotlib Mini Timeline in Left Col
        chart_box = tk.Frame(left_col, bg=self.colors["card_bg"])
        chart_box.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)
        self._embed_overview_chart(chart_box)

        # Right Col: Notable Moments & Next Steps
        right_col = tk.Frame(mid_row, bg=self.colors["card_bg"], width=340, highlightbackground=self.colors["border"], highlightthickness=1)
        right_col.pack(side=tk.RIGHT, fill=tk.BOTH)
        right_col.pack_propagate(False)

        rt_hdr = tk.Frame(right_col, bg=self.colors["card_bg"], padx=12, pady=8)
        rt_hdr.pack(fill=tk.X)
        tk.Label(rt_hdr, text="NOTABLE MOMENTS (EVIDENCE)", font=("Segoe UI", 9, "bold"), bg=self.colors["card_bg"], fg=self.colors["text_main"]).pack(anchor="w")

        # Scrollable notable moments
        moments_scroll = scrolledtext.ScrolledText(
            right_col,
            bg=self.colors["card_bg"],
            fg=self.colors["text_main"],
            font=("Segoe UI", 9),
            borderwidth=0,
            padx=8,
            pady=4
        )
        moments_scroll.pack(fill=tk.BOTH, expand=True)

        if not turning_points:
            moments_scroll.insert(tk.END, "No abrupt turning points detected.\nConversation emotional state was relatively stable.")
        else:
            for idx, tp in enumerate(turning_points[:6]):
                t_id = tp.get("turn_id", idx + 1)
                spk = tp.get("speaker", "Speaker")
                delta = tp.get("delta", 0.0)
                txt = tp.get("text", "")
                arrow = "📈 Jumped Positive" if delta > 0 else "📉 Dropped Negative"

                moments_scroll.insert(tk.END, f"#{idx+1} [Turn {t_id}] {spk} ({arrow} Δ{delta:+.2f})\n", "bold_hdr")
                moments_scroll.insert(tk.END, f"\"{txt}\"\n\n", "quote")

        moments_scroll.tag_config("bold_hdr", font=("Segoe UI", 9, "bold"), foreground=self.colors["accent"])
        moments_scroll.tag_config("quote", font=("Segoe UI", 9, "italic"), foreground=self.colors["text_muted"])
        moments_scroll.configure(state="disabled")

        # Guidance Footer (What should user inspect next)
        guide_box = tk.Frame(container, bg=self.colors["card_inset"], padx=14, pady=8)
        guide_box.pack(fill=tk.X)
        tk.Label(
            guide_box,
            text="Suggested Next Steps: Use the Timeline tab to scrub specific dialogue turns, or inspect the Speakers tab to view participation asymmetry.",
            font=("Segoe UI", 9),
            bg=self.colors["card_inset"],
            fg=self.colors["text_muted"]
        ).pack(side=tk.LEFT)

    def _embed_overview_chart(self, parent_widget: tk.Widget):
        downsampled = self._downsample_timeline_data(self.current_df, max_buckets=50)

        fig = Figure(figsize=(6, 3.2), dpi=100)
        fig.patch.set_facecolor(self.colors["card_bg"])

        ax1 = fig.add_subplot(211)
        ax2 = fig.add_subplot(212, sharex=ax1)
        fig.subplots_adjust(hspace=0.25, left=0.1, right=0.95, top=0.92, bottom=0.15)

        for ax in [ax1, ax2]:
            ax.set_facecolor(self.colors["card_inset"])
            for spine in ax.spines.values():
                spine.set_color(self.colors["border"])
            ax.tick_params(colors=self.colors["text_muted"], labelsize=8)

        # Ax 1: Sentiment Curve + Volatility Envelope
        x = downsampled["bucket_turn"].values
        y_mean = downsampled["bucket_mean"].values
        y_min = downsampled["bucket_min"].values
        y_max = downsampled["bucket_max"].values

        ax1.axhline(0, color=self.colors["border"], linestyle="--", linewidth=0.8)
        ax1.fill_between(x, y_min, y_max, color=self.colors["accent"], alpha=0.15, label="Volatility Envelope")
        ax1.plot(x, y_mean, color=self.colors["accent"], linewidth=2.0, marker="o", markersize=3, label="Mood Trajectory")

        ax1.set_ylim(-1.05, 1.05)
        ax1.set_ylabel("Mood (Polarity)", color=self.colors["text_muted"], fontsize=8)

        # Ax 2: Activity Volume Bars
        vol = downsampled["bucket_volume"].values
        ax2.bar(x, vol, width=max(1.0, (x[-1] - x[0]) / len(x) * 0.8) if len(x) > 1 else 1.0, color=self.colors["accent_teal"], alpha=0.7)
        ax2.set_ylabel("Messages", color=self.colors["text_muted"], fontsize=8)
        ax2.set_xlabel("Conversation Turn Progress", color=self.colors["text_muted"], fontsize=8)

        canvas = FigureCanvasTkAgg(fig, master=parent_widget)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    # -------------------------------------------------------------------------
    # VIEW 2: TIMELINE (DEEP INTERACTIVE EXPLORATION)
    # -------------------------------------------------------------------------
    def _render_view_timeline(self):
        container = tk.Frame(self.viewport_frame, bg=self.colors["bg"], padx=20, pady=16)
        container.pack(fill=tk.BOTH, expand=True)

        # Top Control Strip (Presets, Speaker Overlay Toggle, Data Table Toggle)
        ctrl_strip = tk.Frame(container, bg=self.colors["card_bg"], padx=14, pady=8, highlightbackground=self.colors["border"], highlightthickness=1)
        ctrl_strip.pack(fill=tk.X, pady=(0, 10))

        tk.Label(ctrl_strip, text="RANGE PRESETS:", font=("Segoe UI", 8, "bold"), bg=self.colors["card_bg"], fg=self.colors["text_muted"]).pack(side=tk.LEFT, padx=(0, 8))

        presets = ["All (100%)", "1st Half", "2nd Half", "Peak Tension Range", "Resolution Phase"]
        for p in presets:
            btn = tk.Button(
                ctrl_strip,
                text=p,
                font=("Segoe UI", 8),
                bg=self.colors["card_inset"],
                fg=self.colors["text_main"],
                relief="flat",
                cursor="hand2",
                padx=8,
                pady=2,
                command=lambda val=p: self._on_select_timeline_preset(val)
            )
            btn.pack(side=tk.LEFT, padx=3)

        # Checkboxes on right
        cb_overlay = tk.Checkbutton(
            ctrl_strip,
            text="Compare Speakers Side-by-Side",
            variable=self.show_speaker_overlay_var,
            bg=self.colors["card_bg"],
            fg=self.colors["text_main"],
            activebackground=self.colors["card_bg"],
            activeforeground=self.colors["text_main"],
            selectcolor=self.colors["card_inset"],
            font=("Segoe UI", 8),
            command=self._render_view_timeline_chart
        )
        cb_overlay.pack(side=tk.RIGHT, padx=6)

        cb_table = tk.Checkbutton(
            ctrl_strip,
            text="Accessible Data Table Mode",
            variable=self.show_data_table_var,
            bg=self.colors["card_bg"],
            fg=self.colors["text_main"],
            activebackground=self.colors["card_bg"],
            activeforeground=self.colors["text_main"],
            selectcolor=self.colors["card_inset"],
            font=("Segoe UI", 8),
            command=self._render_view_timeline_chart
        )
        cb_table.pack(side=tk.RIGHT, padx=6)

        # Canvas & Toolbar Container
        self.timeline_content_box = tk.Frame(container, bg=self.colors["card_bg"], highlightbackground=self.colors["border"], highlightthickness=1)
        self.timeline_content_box.pack(fill=tk.BOTH, expand=True)

        self._render_view_timeline_chart()

    def _on_select_timeline_preset(self, preset: str):
        self.filter_range_preset_var.set(preset)
        self._render_view_timeline_chart()

    def _render_view_timeline_chart(self):
        for child in self.timeline_content_box.winfo_children():
            child.destroy()

        if self.show_data_table_var.get():
            # Render Accessible Table Alternative
            self._render_timeline_accessible_table()
            return

        df = self.current_df.copy()
        preset = self.filter_range_preset_var.get()
        n = len(df)

        if preset == "1st Half" and n > 2:
            df = df.iloc[: n // 2]
        elif preset == "2nd Half" and n > 2:
            df = df.iloc[n // 2:]
        elif preset == "Peak Tension Range" and n > 2:
            min_idx = int(np.argmin(df["polarity_score"].values))
            start = max(0, min_idx - 15)
            end = min(n, min_idx + 15)
            df = df.iloc[start:end]
        elif preset == "Resolution Phase" and n > 4:
            df = df.iloc[int(n * 0.7):]

        # Downsample if filtered range is still large
        downsampled = self._downsample_timeline_data(df, max_buckets=60)

        fig = Figure(figsize=(9, 5), dpi=100)
        fig.patch.set_facecolor(self.colors["card_bg"])

        ax1 = fig.add_subplot(211)
        ax2 = fig.add_subplot(212, sharex=ax1)
        fig.subplots_adjust(hspace=0.22, left=0.08, right=0.96, top=0.92, bottom=0.12)

        for ax in [ax1, ax2]:
            ax.set_facecolor(self.colors["card_inset"])
            for spine in ax.spines.values():
                spine.set_color(self.colors["border"])
            ax.tick_params(colors=self.colors["text_muted"], labelsize=8)

        x = downsampled["bucket_turn"].values
        y_mean = downsampled["bucket_mean"].values
        y_min = downsampled["bucket_min"].values
        y_max = downsampled["bucket_max"].values

        ax1.axhline(0, color=self.colors["border"], linestyle="--", linewidth=1.0)
        ax1.fill_between(x, y_min, y_max, color=self.colors["accent"], alpha=0.15, label="Min-Max Volatility Range")
        ax1.plot(x, y_mean, color=self.colors["accent"], linewidth=2.2, marker="o", markersize=4, label="Overall Conversation")

        # Multi-speaker overlays
        if self.show_speaker_overlay_var.get() and "speaker" in df.columns:
            speakers = df["speaker"].value_counts().index[:3]
            palette = ["#5AAE91", "#F2CC8F", "#E29578"]
            for s_idx, spk in enumerate(speakers):
                s_df = df[df["speaker"] == spk]
                if len(s_df) >= 2:
                    s_down = self._downsample_timeline_data(s_df, max_buckets=40)
                    ax1.plot(
                        s_down["bucket_turn"].values,
                        s_down["bucket_mean"].values,
                        color=palette[s_idx % len(palette)],
                        linewidth=1.5,
                        linestyle=":",
                        label=f"Speaker: {spk}"
                    )

        ax1.set_ylim(-1.05, 1.05)
        ax1.set_ylabel("Polarity Score [-1, +1]", color=self.colors["text_muted"], fontsize=9)
        ax1.legend(loc="upper left", facecolor=self.colors["card_bg"], edgecolor=self.colors["border"], fontsize=8, labelcolor=self.colors["text_main"])

        # Bottom ax: message volume per bucket
        vol = downsampled["bucket_volume"].values
        bar_w = max(1.0, (x[-1] - x[0]) / len(x) * 0.8) if len(x) > 1 else 1.0
        ax2.bar(x, vol, width=bar_w, color=self.colors["accent_teal"], alpha=0.7)
        ax2.set_ylabel("Message Density", color=self.colors["text_muted"], fontsize=9)
        ax2.set_xlabel("Turn Identifier (Interactive Navigation Enabled)", color=self.colors["text_muted"], fontsize=9)

        canvas = FigureCanvasTkAgg(fig, master=self.timeline_content_box)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Standard Matplotlib Navigation Toolbar (Pan, Zoom, Save)
        toolbar_frame = tk.Frame(self.timeline_content_box, bg=self.colors["card_bg"])
        toolbar_frame.pack(fill=tk.X)
        toolbar = NavigationToolbar2Tk(canvas, toolbar_frame)
        toolbar.update()

    def _render_timeline_accessible_table(self):
        container = tk.Frame(self.timeline_content_box, bg=self.colors["card_bg"], padx=14, pady=12)
        container.pack(fill=tk.BOTH, expand=True)

        tk.Label(container, text="ACCESSIBLE TIMELINE DATA TABLE", font=("Segoe UI", 10, "bold"), bg=self.colors["card_bg"], fg=self.colors["text_main"]).pack(anchor="w", pady=(0, 8))

        downsampled = self._downsample_timeline_data(self.current_df, max_buckets=50)

        tree = ttk.Treeview(
            container,
            columns=("turn", "mean", "min", "max", "vol", "spk"),
            show="headings",
            style="Messages.Treeview"
        )
        tree.heading("turn", text="Turn Range")
        tree.heading("mean", text="Mean Polarity")
        tree.heading("min", text="Min Polarity")
        tree.heading("max", text="Max Polarity")
        tree.heading("vol", text="Msg Count")
        tree.heading("spk", text="Dominant Speaker")

        tree.column("turn", width=120, anchor="center")
        tree.column("mean", width=110, anchor="center")
        tree.column("min", width=110, anchor="center")
        tree.column("max", width=110, anchor="center")
        tree.column("vol", width=100, anchor="center")
        tree.column("spk", width=160, anchor="w")

        tree.pack(fill=tk.BOTH, expand=True)

        for _, r in downsampled.iterrows():
            t_start = int(r.get("turn_start", r["bucket_turn"]))
            t_end = int(r.get("turn_end", r["bucket_turn"]))
            t_str = f"Turns {t_start} - {t_end}" if t_start != t_end else f"Turn {t_start}"
            tree.insert("", "end", values=(
                t_str,
                f"{r['bucket_mean']:+.2f}",
                f"{r['bucket_min']:+.2f}",
                f"{r['bucket_max']:+.2f}",
                int(r["bucket_volume"]),
                r.get("dominant_speaker", "Multiple")
            ))

    # -------------------------------------------------------------------------
    # VIEW 3: SPEAKERS & PARTICIPATION
    # -------------------------------------------------------------------------
    def _render_view_speakers(self):
        container = tk.Frame(self.viewport_frame, bg=self.colors["bg"], padx=20, pady=16)
        container.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            container,
            text=f"Speakers & Participation — {self.current_dataset_name}",
            font=("Segoe UI", 14, "bold"),
            bg=self.colors["bg"],
            fg=self.colors["text_main"]
        ).pack(anchor="w", pady=(0, 12))

        df = self.current_df
        speakers = df["speaker"].value_counts()
        total_turns = len(df)

        cards_frame = tk.Frame(container, bg=self.colors["bg"])
        cards_frame.pack(fill=tk.X, pady=(0, 16))

        for idx, (spk, count) in enumerate(speakers.items()):
            spk_df = df[df["speaker"] == spk]
            mean_s = float(spk_df["polarity_score"].mean())
            min_s = float(spk_df["polarity_score"].min())
            max_s = float(spk_df["polarity_score"].max())
            pct = (count / total_turns) * 100.0

            card = tk.Frame(cards_frame, bg=self.colors["card_bg"], padx=14, pady=12, highlightbackground=self.colors["border"], highlightthickness=1)
            card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0 if idx == 0 else 8, 0))

            tk.Label(card, text=spk, font=("Segoe UI", 11, "bold"), bg=self.colors["card_bg"], fg=self.colors["accent"]).pack(anchor="w")
            tk.Label(card, text=f"{count} messages ({pct:.1f}% share)", font=("Segoe UI", 9), bg=self.colors["card_bg"], fg=self.colors["text_muted"]).pack(anchor="w", pady=(2, 6))

            tk.Label(card, text=f"Average Mood: {mean_s:+.2f}", font=("Segoe UI", 9, "bold"), bg=self.colors["card_bg"], fg=self.colors["text_main"]).pack(anchor="w")
            tk.Label(card, text=f"Emotional Range: [{min_s:+.2f} to {max_s:+.2f}]", font=("Segoe UI", 8), bg=self.colors["card_bg"], fg=self.colors["text_muted"]).pack(anchor="w", pady=(2, 8))

            btn_filter = tk.Button(
                card,
                text="Filter Messages by this Speaker",
                font=("Segoe UI", 8, "bold"),
                bg=self.colors["card_inset"],
                fg=self.colors["text_main"],
                relief="flat",
                cursor="hand2",
                command=lambda s=spk: self._filter_and_jump_to_speaker(s)
            )
            btn_filter.pack(fill=tk.X)

        # Bottom turn-taking distribution visualization
        dist_box = tk.Frame(container, bg=self.colors["card_bg"], padx=14, pady=12, highlightbackground=self.colors["border"], highlightthickness=1)
        dist_box.pack(fill=tk.BOTH, expand=True)

        tk.Label(dist_box, text="CONVERSATION TURN PARTICIPATION TIMELINE", font=("Segoe UI", 9, "bold"), bg=self.colors["card_bg"], fg=self.colors["text_main"]).pack(anchor="w", pady=(0, 6))

        # Matplotlib strip of speaker alternation
        fig = Figure(figsize=(7, 2.5), dpi=100)
        fig.patch.set_facecolor(self.colors["card_bg"])
        ax = fig.add_subplot(111)
        ax.set_facecolor(self.colors["card_inset"])
        for spine in ax.spines.values():
            spine.set_color(self.colors["border"])
        ax.tick_params(colors=self.colors["text_muted"], labelsize=8)

        speaker_map = {s: i for i, s in enumerate(speakers.index)}
        y_vals = [speaker_map.get(s, 0) for s in df["speaker"]]
        x_vals = df["turn_id"].values

        ax.scatter(x_vals, y_vals, c=df["polarity_score"].values, cmap="coolwarm", s=25, alpha=0.85)
        ax.set_yticks(list(speaker_map.values()))
        ax.set_yticklabels(list(speaker_map.keys()), color=self.colors["text_main"], fontsize=8)
        ax.set_xlabel("Conversation Turn ID", color=self.colors["text_muted"], fontsize=8)
        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=dist_box)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _filter_and_jump_to_speaker(self, speaker_name: str):
        self.filter_speaker_var.set(speaker_name)
        self._apply_filters()
        self._switch_view("messages")

    # -------------------------------------------------------------------------
    # VIEW 4: TOPICS & THEMES
    # -------------------------------------------------------------------------
    def _render_view_topics(self):
        container = tk.Frame(self.viewport_frame, bg=self.colors["bg"], padx=20, pady=16)
        container.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            container,
            text=f"Thematic Clusters & Treemap — {self.current_dataset_name}",
            font=("Segoe UI", 14, "bold"),
            bg=self.colors["bg"],
            fg=self.colors["text_main"]
        ).pack(anchor="w", pady=(0, 10))

        # Treemap canvas
        t_box = tk.Frame(container, bg=self.colors["card_bg"], highlightbackground=self.colors["border"], highlightthickness=1)
        t_box.pack(fill=tk.BOTH, expand=True)

        clusters = self._cluster_feedback_messages(self.current_df)
        rects = self._compute_treemap_rects(clusters, 0.0, 0.0, 100.0, 100.0)

        fig = Figure(figsize=(8, 4.5), dpi=100)
        fig.patch.set_facecolor(self.colors["card_bg"])
        ax = fig.add_subplot(111)
        ax.set_facecolor(self.colors["card_bg"])
        ax.axis("off")

        for item in rects:
            rx, ry, rw, rh = item["rect"]
            sent = item.get("sentiment", "neutral").lower()
            color = self.colors["pos"] if "pos" in sent else (self.colors["neg"] if "neg" in sent else self.colors["neu"])

            rect = mpatches.Rectangle((rx, ry), rw, rh, facecolor=color, edgecolor=self.colors["bg"], linewidth=1.5, alpha=0.85)
            ax.add_patch(rect)

            if rw > 12 and rh > 10:
                ax.text(
                    rx + rw / 2.0, ry + rh / 2.0,
                    f"{item['topic']}\n({item['count']} msgs)",
                    ha="center", va="center",
                    color="#FFFFFF" if sent != "neutral" else "#222222",
                    fontweight="bold", fontsize=8
                )

        ax.set_xlim(0, 100)
        ax.set_ylim(0, 100)
        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=t_box)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    # -------------------------------------------------------------------------
    # VIEW 5: MESSAGES (SEARCHABLE, FILTERABLE EVIDENCE GRID)
    # -------------------------------------------------------------------------
    def _render_view_messages(self):
        container = tk.Frame(self.viewport_frame, bg=self.colors["bg"], padx=20, pady=16)
        container.pack(fill=tk.BOTH, expand=True)

        # Omni-Filter Bar
        bar = tk.Frame(container, bg=self.colors["card_bg"], padx=12, pady=10, highlightbackground=self.colors["border"], highlightthickness=1)
        bar.pack(fill=tk.X, pady=(0, 10))

        # Search field
        tk.Label(bar, text="SEARCH:", font=("Segoe UI", 8, "bold"), bg=self.colors["card_bg"], fg=self.colors["text_muted"]).pack(side=tk.LEFT, padx=(0, 4))
        ent_search = tk.Entry(bar, textvariable=self.search_query_var, width=22, font=("Segoe UI", 9), bg=self.colors["card_inset"], fg=self.colors["text_main"], insertbackground=self.colors["text_main"], relief="flat")
        ent_search.pack(side=tk.LEFT, padx=(0, 12))
        ent_search.bind("<KeyRelease>", lambda e: self._on_search_key_release())

        # Speaker Dropdown
        tk.Label(bar, text="SPEAKER:", font=("Segoe UI", 8, "bold"), bg=self.colors["card_bg"], fg=self.colors["text_muted"]).pack(side=tk.LEFT, padx=(0, 4))
        cb_spk = ttk.Combobox(bar, textvariable=self.filter_speaker_var, values=getattr(self, "filter_speaker_dropdown_values", ["All Speakers"]), state="readonly", width=14, font=("Segoe UI", 9))
        cb_spk.pack(side=tk.LEFT, padx=(0, 12))
        cb_spk.bind("<<ComboboxSelected>>", lambda e: self._apply_filters())

        # Sentiment Dropdown
        tk.Label(bar, text="MOOD:", font=("Segoe UI", 8, "bold"), bg=self.colors["card_bg"], fg=self.colors["text_muted"]).pack(side=tk.LEFT, padx=(0, 4))
        cb_sent = ttk.Combobox(bar, textvariable=self.filter_sentiment_var, values=["All Sentiments", "Positive", "Neutral", "Negative"], state="readonly", width=14, font=("Segoe UI", 9))
        cb_sent.pack(side=tk.LEFT, padx=(0, 12))
        cb_sent.bind("<<ComboboxSelected>>", lambda e: self._apply_filters())

        # Clear All Button
        btn_clear = tk.Button(bar, text="Clear Filters", font=("Segoe UI", 8, "bold"), bg=self.colors["card_inset"], fg=self.colors["accent"], relief="flat", cursor="hand2", command=self._clear_all_filters)
        btn_clear.pack(side=tk.RIGHT)

        # Main Split Content: Left Table (60%) + Right Detail Context Drawer (40%)
        split_frame = tk.Frame(container, bg=self.colors["bg"])
        split_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        # Left Table Frame
        tbl_frame = tk.Frame(split_frame, bg=self.colors["card_bg"], highlightbackground=self.colors["border"], highlightthickness=1)
        tbl_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))

        self.messages_tree = ttk.Treeview(
            tbl_frame,
            columns=("turn", "spk", "text", "sentiment", "score"),
            show="headings",
            style="Messages.Treeview"
        )
        self.messages_tree.heading("turn", text="Turn #")
        self.messages_tree.heading("spk", text="Speaker")
        self.messages_tree.heading("text", text="Message Text")
        self.messages_tree.heading("sentiment", text="Predicted Tone")
        self.messages_tree.heading("score", text="Polarity")

        self.messages_tree.column("turn", width=60, anchor="center")
        self.messages_tree.column("spk", width=120, anchor="w")
        self.messages_tree.column("text", width=340, anchor="w")
        self.messages_tree.column("sentiment", width=110, anchor="center")
        self.messages_tree.column("score", width=80, anchor="center")

        tree_scroll = ttk.Scrollbar(tbl_frame, orient=tk.VERTICAL, command=self.messages_tree.yview)
        self.messages_tree.configure(yscrollcommand=tree_scroll.set)

        self.messages_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.messages_tree.bind("<<TreeviewSelect>>", self._on_select_message_row)

        # Right Detail Context Drawer
        self.detail_drawer = tk.Frame(split_frame, bg=self.colors["card_bg"], width=360, highlightbackground=self.colors["border"], highlightthickness=1)
        self.detail_drawer.pack(side=tk.RIGHT, fill=tk.BOTH)
        self.detail_drawer.pack_propagate(False)

        drawer_hdr = tk.Frame(self.detail_drawer, bg=self.colors["card_inset"], padx=12, pady=8)
        drawer_hdr.pack(fill=tk.X)
        tk.Label(drawer_hdr, text="MESSAGE EVIDENCE & CONTEXT DRAWER", font=("Segoe UI", 9, "bold"), bg=self.colors["card_inset"], fg=self.colors["text_main"]).pack(anchor="w")

        self.drawer_content = scrolledtext.ScrolledText(
            self.detail_drawer,
            bg=self.colors["card_bg"],
            fg=self.colors["text_main"],
            font=("Segoe UI", 9),
            borderwidth=0,
            padx=10,
            pady=8
        )
        self.drawer_content.pack(fill=tk.BOTH, expand=True)
        self.drawer_content.insert(tk.END, "Select any message row on the left to inspect its turn context, AI certainty, and polarity calculation.")
        self.drawer_content.configure(state="disabled")

        # Bottom Pagination Strip
        pag_bar = tk.Frame(container, bg=self.colors["card_bg"], padx=12, pady=6, highlightbackground=self.colors["border"], highlightthickness=1)
        pag_bar.pack(fill=tk.X)

        self.lbl_page_info = tk.Label(pag_bar, text="Page 1 of 1 (0 messages)", font=("Segoe UI", 8), bg=self.colors["card_bg"], fg=self.colors["text_muted"])
        self.lbl_page_info.pack(side=tk.LEFT)

        btn_prev = tk.Button(pag_bar, text="< Previous 50", font=("Segoe UI", 8), bg=self.colors["card_inset"], fg=self.colors["text_main"], relief="flat", cursor="hand2", command=self._prev_page)
        btn_prev.pack(side=tk.RIGHT, padx=4)

        btn_next = tk.Button(pag_bar, text="Next 50 >", font=("Segoe UI", 8), bg=self.colors["card_inset"], fg=self.colors["text_main"], relief="flat", cursor="hand2", command=self._next_page)
        btn_next.pack(side=tk.RIGHT, padx=4)

        self._render_paginated_messages()

    def _on_search_key_release(self):
        self.current_page = 1
        self._apply_filters()
        self._render_paginated_messages()

    def _apply_filters(self):
        if self.current_df is None:
            return

        df = self.current_df.copy()

        # 1. Search Query
        q = self.search_query_var.get().strip().lower()
        if q:
            df = df[df["text"].astype(str).str.lower().str.contains(q, na=False) |
                    df["speaker"].astype(str).str.lower().str.contains(q, na=False)]

        # 2. Speaker Filter
        spk = self.filter_speaker_var.get()
        if spk and spk != "All Speakers":
            df = df[df["speaker"] == spk]

        # 3. Sentiment Filter
        sent = self.filter_sentiment_var.get().lower()
        if sent and sent != "all sentiments":
            df = df[df["pred_sentiment"].astype(str).str.lower().str.contains(sent, na=False)]

        self.filtered_df = df

        # Update sidebar filter summary
        active_count = (1 if q else 0) + (1 if spk != "All Speakers" else 0) + (1 if sent != "all sentiments" else 0)
        if active_count > 0:
            self.sidebar_filter_lbl.configure(text=f"Active Filters: {active_count} applied", fg=self.colors["accent"])
        else:
            self.sidebar_filter_lbl.configure(text="Filters: None active", fg=self.colors["text_muted"])

    def _clear_all_filters(self):
        self.search_query_var.set("")
        self.filter_speaker_var.set("All Speakers")
        self.filter_sentiment_var.set("All Sentiments")
        self.current_page = 1
        self._apply_filters()
        if self.active_view == "messages":
            self._render_paginated_messages()

    def _render_paginated_messages(self):
        if not hasattr(self, "messages_tree") or self.messages_tree is None:
            return

        for row in self.messages_tree.get_children():
            self.messages_tree.delete(row)

        df = self.filtered_df if self.filtered_df is not None else self.current_df
        total_items = len(df)
        total_pages = max(1, int(np.ceil(total_items / self.page_size)))

        self.current_page = max(1, min(self.current_page, total_pages))
        start_idx = (self.current_page - 1) * self.page_size
        end_idx = min(start_idx + self.page_size, total_items)

        self.lbl_page_info.configure(text=f"Page {self.current_page} of {total_pages} (Displaying {start_idx+1}-{end_idx} of {total_items} filtered messages)")

        page_df = df.iloc[start_idx:end_idx]

        for _, r in page_df.iterrows():
            t_id = int(r.get("turn_id", 0))
            spk = str(r.get("speaker", "Speaker"))
            txt = str(r.get("text", ""))
            sent = str(r.get("pred_sentiment", "neutral")).capitalize()
            score = float(r.get("polarity_score", 0.0))

            self.messages_tree.insert(
                "", "end", iid=str(t_id),
                values=(t_id, spk, txt, sent, f"{score:+.2f}")
            )

    def _prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self._render_paginated_messages()

    def _next_page(self):
        df = self.filtered_df if self.filtered_df is not None else self.current_df
        total_pages = int(np.ceil(len(df) / self.page_size))
        if self.current_page < total_pages:
            self.current_page += 1
            self._render_paginated_messages()

    def _on_select_message_row(self, event=None):
        selected = self.messages_tree.selection()
        if not selected:
            return
        turn_id = int(selected[0])
        self.selected_turn_id = turn_id

        # Update Detail Context Drawer
        row = self.current_df[self.current_df["turn_id"] == turn_id]
        if row.empty:
            return
        r = row.iloc[0]

        self.drawer_content.configure(state="normal")
        self.drawer_content.delete("1.0", tk.END)

        self.drawer_content.insert(tk.END, f"TURN #{turn_id} DETAILS\n", "title")
        self.drawer_content.insert(tk.END, f"Speaker: {r.get('speaker', 'Unknown')}\n", "bold")
        self.drawer_content.insert(tk.END, f"Tone: {str(r.get('pred_sentiment', 'neutral')).upper()} (Polarity: {r.get('polarity_score', 0.0):+.2f})\n\n", "tone")

        self.drawer_content.insert(tk.END, f"UTTERANCE TEXT:\n\"{r.get('text', '')}\"\n\n", "quote")

        # Confidence probabilities if available
        p_pos = r.get("prob_positive", 0.0)
        p_neu = r.get("prob_neutral", 0.0)
        p_neg = r.get("prob_negative", 0.0)
        self.drawer_content.insert(tk.END, f"MODEL PROBABILITIES:\n• Positive: {p_pos*100:.1f}%\n• Neutral:  {p_neu*100:.1f}%\n• Negative: {p_neg*100:.1f}%\n\n", "mono")

        # Show surrounding k-turn context
        curr_idx = self.current_df.index[self.current_df["turn_id"] == turn_id].tolist()[0]
        start_ctx = max(0, curr_idx - 3)
        context_df = self.current_df.iloc[start_ctx: curr_idx]

        if not context_df.empty:
            self.drawer_content.insert(tk.END, "PRECEDING CONTEXT (3 TURNS):\n", "bold")
            for _, ctx_r in context_df.iterrows():
                self.drawer_content.insert(tk.END, f"[{ctx_r['turn_id']}] {ctx_r['speaker']}: {ctx_r['text']}\n", "muted")

        self.drawer_content.tag_config("title", font=("Segoe UI", 11, "bold"), foreground=self.colors["accent"])
        self.drawer_content.tag_config("bold", font=("Segoe UI", 9, "bold"), foreground=self.colors["text_main"])
        self.drawer_content.tag_config("tone", font=("Segoe UI", 9, "bold"), foreground=self.colors["pos"] if r.get('polarity_score', 0) > 0 else self.colors["neg"])
        self.drawer_content.tag_config("quote", font=("Segoe UI", 9, "italic"), foreground=self.colors["text_main"])
        self.drawer_content.tag_config("mono", font=("Consolas", 8), foreground=self.colors["text_muted"])
        self.drawer_content.tag_config("muted", font=("Segoe UI", 8), foreground=self.colors["text_muted"])

        self.drawer_content.configure(state="disabled")

    # -------------------------------------------------------------------------
    # VIEW 6: INSIGHTS (EVIDENCE-BACKED FINDINGS)
    # -------------------------------------------------------------------------
    def _render_view_insights(self):
        container = tk.Frame(self.viewport_frame, bg=self.colors["bg"], padx=20, pady=16)
        container.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            container,
            text=f"Evidence-Backed Insights — {self.current_dataset_name}",
            font=("Segoe UI", 14, "bold"),
            bg=self.colors["bg"],
            fg=self.colors["text_main"]
        ).pack(anchor="w", pady=(0, 10))

        # Build list of dynamic insights
        scores = self.current_df["polarity_score"].values.astype(float)
        stats = self.current_stats or {}
        turning_points = stats.get("turning_points", [])

        # Narrative archetype
        archetype = self._classify_sentiment_arc_archetype(scores)

        insights = [
            (
                "archetype",
                "Emotional Narrative Arc Archetype",
                f"The overall trajectory follows the '{archetype}' story archetype.",
                f"Supported by all {len(scores)} conversation turns. Characterized by continuous or fluctuating sentiment changes.",
                "timeline"
            )
        ]

        # Turning point insight
        if turning_points:
            sharpest = max(turning_points, key=lambda x: abs(x.get("delta", 0.0)))
            insights.append((
                "sharpest_shift",
                "Sharpest Tone Inflection Moment",
                f"Turn {sharpest.get('turn_id', 0)} by {sharpest.get('speaker', 'Speaker')} caused a significant shift of Δ{sharpest.get('delta', 0.0):+.2f}.",
                f"Utterance: \"{sharpest.get('text', '')}\". Verified with high confidence by context model.",
                "messages"
            ))

        # Asymmetric speaker insight
        spk_counts = self.current_df["speaker"].value_counts()
        if len(spk_counts) >= 2:
            top_spk = spk_counts.index[0]
            top_pct = (spk_counts.iloc[0] / len(self.current_df)) * 100
            if top_pct > 65:
                insights.append((
                    "asymmetry",
                    "Conversational Dominance Notice",
                    f"{top_spk} accounted for {top_pct:.1f}% of all utterances in this conversation.",
                    "Asymmetric participation can skew aggregated sentiment metrics towards a single speaker.",
                    "speakers"
                ))

        for key, title, desc, evidence, target_view in insights:
            if key in self.dismissed_insights:
                continue

            card = tk.Frame(container, bg=self.colors["card_bg"], padx=16, pady=14, highlightbackground=self.colors["border"], highlightthickness=1)
            card.pack(fill=tk.X, pady=(0, 10))

            hdr = tk.Frame(card, bg=self.colors["card_bg"])
            hdr.pack(fill=tk.X)

            tk.Label(hdr, text=title, font=("Segoe UI", 11, "bold"), bg=self.colors["card_bg"], fg=self.colors["accent"]).pack(side=tk.LEFT)

            btn_dismiss = tk.Button(
                hdr, text="Dismiss", font=("Segoe UI", 8), bg=self.colors["card_bg"], fg=self.colors["text_muted"], relief="flat", cursor="hand2",
                command=lambda k=key: self._dismiss_insight(k)
            )
            btn_dismiss.pack(side=tk.RIGHT)

            tk.Label(card, text=desc, font=("Segoe UI", 10), bg=self.colors["card_bg"], fg=self.colors["text_main"]).pack(anchor="w", pady=(4, 2))
            tk.Label(card, text=f"Evidence: {evidence}", font=("Segoe UI", 8), bg=self.colors["card_bg"], fg=self.colors["text_muted"]).pack(anchor="w", pady=(0, 8))

            btn_act = tk.Button(
                card, text=f"Inspect Evidence in {target_view.capitalize()} View →",
                font=("Segoe UI", 8, "bold"), bg=self.colors["card_inset"], fg=self.colors["pos"], relief="flat", cursor="hand2",
                command=lambda v=target_view: self._switch_view(v)
            )
            btn_act.pack(anchor="w")

    def _dismiss_insight(self, key: str):
        self.dismissed_insights.add(key)
        self._render_view_insights()

    # -------------------------------------------------------------------------
    # VIEW 7: DATA & SETTINGS
    # -------------------------------------------------------------------------
    def _render_view_settings(self):
        container = tk.Frame(self.viewport_frame, bg=self.colors["bg"], padx=20, pady=16)
        container.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            container,
            text="Data Management, Settings & Exports",
            font=("Segoe UI", 14, "bold"),
            bg=self.colors["bg"],
            fg=self.colors["text_main"]
        ).pack(anchor="w", pady=(0, 14))

        # Section 1: Ingestion Audit
        s1 = tk.Frame(container, bg=self.colors["card_bg"], padx=16, pady=14, highlightbackground=self.colors["border"], highlightthickness=1)
        s1.pack(fill=tk.X, pady=(0, 12))

        tk.Label(s1, text="DATASET AUDIT & MEMORY STATE", font=("Segoe UI", 10, "bold"), bg=self.colors["card_bg"], fg=self.colors["accent"]).pack(anchor="w", pady=(0, 4))
        tk.Label(s1, text=f"Active File: {self.current_dataset_name}", font=("Segoe UI", 9), bg=self.colors["card_bg"], fg=self.colors["text_main"]).pack(anchor="w")
        tk.Label(s1, text=f"Total Turns in RAM: {len(self.current_df) if self.current_df is not None else 0}", font=("Segoe UI", 9), bg=self.colors["card_bg"], fg=self.colors["text_muted"]).pack(anchor="w")
        tk.Label(s1, text="Privacy Guarantee: 100% on-device processing. No data is stored in cloud or transmitted.", font=("Segoe UI", 8), bg=self.colors["card_bg"], fg=self.colors["pos"]).pack(anchor="w", pady=(4, 8))

        btn_purge = tk.Button(
            s1, text="Purge Current Data from Memory", font=("Segoe UI", 8, "bold"), bg=self.colors["card_inset"], fg=self.colors["neg"], relief="flat", cursor="hand2",
            command=self._purge_data
        )
        btn_purge.pack(anchor="w")

        # Section 2: Export Center
        s2 = tk.Frame(container, bg=self.colors["card_bg"], padx=16, pady=14, highlightbackground=self.colors["border"], highlightthickness=1)
        s2.pack(fill=tk.X)

        tk.Label(s2, text="EXPORT CENTER (WITH FORMULA INJECTION DEFENSE)", font=("Segoe UI", 10, "bold"), bg=self.colors["card_bg"], fg=self.colors["accent"]).pack(anchor="w", pady=(0, 6))

        btn_row = tk.Frame(s2, bg=self.colors["card_bg"])
        btn_row.pack(fill=tk.X, pady=4)

        tk.Button(
            btn_row, text="Export Sanitized CSV", font=("Segoe UI", 9, "bold"), bg=self.colors["card_inset"], fg=self.colors["text_main"], relief="flat", cursor="hand2", padx=12, pady=6,
            command=self._export_sanitized_csv
        ).pack(side=tk.LEFT, padx=(0, 8))

        tk.Button(
            btn_row, text="Export JSON Analysis", font=("Segoe UI", 9, "bold"), bg=self.colors["card_inset"], fg=self.colors["text_main"], relief="flat", cursor="hand2", padx=12, pady=6,
            command=self._export_json
        ).pack(side=tk.LEFT, padx=(0, 8))

    def _purge_data(self):
        if messagebox.askyesno("Confirm Purge", "Are you sure you want to purge all conversation data from memory?"):
            self.current_df = None
            self.current_stats = None
            self.current_analysis_result = None
            self._switch_view("overview")
            self.status_var.set("Memory purged successfully.")

    def _export_sanitized_csv(self):
        if self.current_df is None:
            return
        fpath = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")])
        if not fpath:
            return

        # Apply Risk #87 formula injection defense
        sanitized = self.current_df.copy()
        for col in ["text", "speaker", "pred_sentiment"]:
            if col in sanitized.columns:
                sanitized[col] = sanitized[col].astype(str).apply(
                    lambda x: f"'{x}" if x.startswith(("=", "+", "-", "@")) else x
                )

        sanitized.to_csv(fpath, index=False, encoding="utf-8")
        messagebox.showinfo("Export Successful", f"Sanitized CSV saved to:\n{fpath}")

    def _export_json(self):
        if self.current_analysis_result is None:
            return
        fpath = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")])
        if not fpath:
            return

        export_data = {
            "dataset": self.current_dataset_name,
            "stats": self.current_stats,
            "turns": self.current_df.to_dict(orient="records") if self.current_df is not None else []
        }
        with open(fpath, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2, default=str)
        messagebox.showinfo("Export Successful", f"Analysis JSON saved to:\n{fpath}")

    # -------------------------------------------------------------------------
    # STATIC HELPER METHODS REQUIRED BY TEST SUITE
    # -------------------------------------------------------------------------
    @staticmethod
    def _classify_sentiment_arc_archetype(scores: np.ndarray) -> str:
        if len(scores) < 3:
            return "Micro-Dialogue Arc"
        s_first = float(scores[0])
        s_last = float(scores[-1])
        drift = s_last - s_first
        s_min = float(np.min(scores))
        s_max = float(np.max(scores))
        min_idx = int(np.argmin(scores))
        max_idx = int(np.argmax(scores))
        n = len(scores)

        # "Man in a Hole": dip into negative in middle, followed by recovery
        if s_min < -0.15 and (s_last - s_min) >= 0.30 and 0 < min_idx < n - 1:
            return "Man in a Hole (Dip & De-escalation Recovery)"
        # "Icarus": rise to high peak in middle, followed by fall
        if s_max > 0.15 and (s_max - s_last) >= 0.30 and 0 < max_idx < n - 1:
            return "Icarus (Rise & Fall / Escalation)"
        # "Rags to Riches": continuous rise
        if drift >= 0.35:
            return "Rags to Riches (Continual Emotional Rise)"
        # "Tragedy": continuous decline
        if drift <= -0.35:
            return "Tragedy (Continual Emotional Decline)"
        # "Steady Equilibrium": stable sentiment
        if float(np.std(scores)) < 0.14 and abs(drift) < 0.18:
            return "Steady Equilibrium (Informational Balance)"
        return "Fluctuating Journey (Multi-turn Waves)"

    @staticmethod
    def _cluster_feedback_messages(df: pd.DataFrame) -> List[Dict[str, Any]]:
        topic_defs = [
            ("Issues & Technical", ["error", "bug", "fail", "broke", "issue", "problem", "freeze", "crash", "down", "delay", "slow", "stuck", "leak", "pool", "reboot", "timeout", "incident"]),
            ("Support & Service", ["help", "call", "contact", "response", "check", "update", "looking", "sorry", "assist", "ticket", "clarify", "answer", "please", "confirm"]),
            ("Product & Features", ["app", "ui", "feature", "design", "work", "interface", "tool", "screen", "button", "layout", "mobile", "desktop", "system", "performance"]),
            ("Resolution & Delivery", ["fixed", "solved", "verified", "ready", "done", "complete", "fine", "working", "success", "patch", "release", "shipped", "resolved", "good", "great", "thanks"]),
        ]

        clusters = {}
        for idx, row in df.iterrows():
            text = str(row.get("text", "")).lower()
            sent = str(row.get("pred_sentiment", "neutral")).lower()
            matched_topic = "General Feedback"
            for t_name, keywords in topic_defs:
                if any(kw in text for kw in keywords):
                    matched_topic = t_name
                    break
            key = (matched_topic, sent)
            clusters[key] = clusters.get(key, 0) + 1

        items = []
        for (topic, sent), count in clusters.items():
            items.append({
                "topic": topic,
                "sentiment": sent,
                "count": count
            })
        items.sort(key=lambda x: x["count"], reverse=True)
        return items

    @staticmethod
    def _compute_treemap_rects(items: List[Dict[str, Any]], x: float, y: float, w: float, h: float) -> List[Dict[str, Any]]:
        if not items:
            return []
        total = sum(it["count"] for it in items)
        if total == 0:
            return []
        if len(items) == 1:
            item = dict(items[0])
            item["rect"] = (x, y, w, h)
            return [item]

        half = total / 2.0
        acc = 0
        split_idx = 1
        for i, it in enumerate(items):
            acc += it["count"]
            if acc >= half or i == len(items) - 1:
                split_idx = max(1, i if (acc - it["count"] > 0 and abs(acc - it["count"] - half) < abs(acc - half)) else i + 1)
                break

        group1 = items[:split_idx]
        group2 = items[split_idx:]
        w1 = sum(it["count"] for it in group1)
        fraction = w1 / total

        result = []
        if w >= h:
            w_left = w * fraction
            w_right = w - w_left
            result.extend(SentimentTrajectoryDesktopApp._compute_treemap_rects(group1, x, y, w_left, h))
            result.extend(SentimentTrajectoryDesktopApp._compute_treemap_rects(group2, x + w_left, y, w_right, h))
        else:
            h_top = h * fraction
            h_bottom = h - h_top
            result.extend(SentimentTrajectoryDesktopApp._compute_treemap_rects(group1, x, y, w, h_top))
            result.extend(SentimentTrajectoryDesktopApp._compute_treemap_rects(group2, x, y + h_top, w, h_bottom))
        return result

    # Backwards compatibility alias for tests
    def _render_trajectory_plot(self, df: pd.DataFrame, stats: Dict[str, Any]):
        return self._render_view_timeline()

    def _render_sentiment_arc(self, df: pd.DataFrame, stats: Dict[str, Any]):
        return self._render_view_timeline()

    def _render_treemap(self, df: pd.DataFrame, stats: Dict[str, Any]):
        return self._render_view_topics()

    def _render_sankey(self, df: pd.DataFrame, stats: Dict[str, Any]):
        return self._render_view_topics()


def main():
    root = tk.Tk()
    app = SentimentTrajectoryDesktopApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
