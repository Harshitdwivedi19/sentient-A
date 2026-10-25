"""
src/desktop_app.py

Desktop GUI Application for:
Context-Aware Conversation-Level Sentiment and Emotional Trajectory Analysis.

Redesigned into an Elegant, Intuitive, Explainable AI Experience:
- Section 1: Home / Overview (Introduction, 5-Step Workflow, Quick Demo launcher)
- Section 2: Analyze Conversation (Step 1: Input -> Step 2: Review & Preview -> Step 3: Configure -> Step 4: Run)
- Section 3: Results Dashboard (Summary KPIs, Trajectory Curve with "How to Read", Distribution, Message Explorer, Turning Points, Evidence Report, Exports)
- Section 4: Built-in User Guide & Help (Plain-English manual, concept glossary, mathematical formulas, epistemic boundaries)

Built on Python standard Tkinter + ttk + Matplotlib with zero external heavy UI dependencies.
"""

import os
import sys
import threading
import json
from pathlib import Path
from typing import Optional, Dict, Any, List

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
# Aliases for UI dropdown readability
SAMPLE_PRESETS["Sample 2: WhatsApp Incident & Resolution"] = SAMPLE_PRESETS["Sample 2: WhatsApp Chat Format"]
SAMPLE_PRESETS["Sample 3: MELD Dialogue (Empathy & Support)"] = SAMPLE_PRESETS["Sample 3: MELD Friends Dialogue"]


class SentimentTrajectoryDesktopApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Sentiment Trajectory Analysis — Explainable AI Studio")
        self.root.geometry("1240x860")
        self.root.minsize(1040, 720)

        # Set unique visual identity icon
        ico_path = PROJECT_ROOT / "assets" / "branding" / "app_icon.ico"
        if ico_path.exists():
            try:
                self.root.iconbitmap(default=str(ico_path))
            except Exception:
                pass

        # Internal state
        self.analyzer: Optional[ConversationSentimentAnalyzer] = None
        self.current_analysis_result: Optional[Dict[str, Any]] = None
        self.parsed_preview_df: Optional[pd.DataFrame] = None
        self.selected_file_path: Optional[Path] = None
        self.is_results_stale: bool = False
        self.active_filter: str = "all"
        self.active_chart_mode: str = "arc"

        # Apply styling system
        self._setup_design_system()

        # Build application structure
        self._build_top_header()
        self._build_main_navigation()
        self._build_status_bar()

        # Initialize sentiment engine in background thread
        self.status_var.set("Initializing deep learning engine in background...")
        threading.Thread(target=self._init_analyzer_thread, daemon=True).start()

        # Load initial demonstration conversation
        self._load_preset_conversation("Sample 1: Conflict to Reconciliation")

    def _setup_design_system(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass

        # Professional, accessible design tokens — warm ivory / pale cream premium palette
        self.colors = {
            "bg": "#F8F6EF",             # warm ivory — main window background
            "card_bg": "#FFFDF6",        # soft cream — card backgrounds
            "header_bg": "#292A2D",      # muted charcoal — top header bar
            "header_text": "#F8F6EF",    # ivory on charcoal header
            "border": "#E8E4D9",         # thin warm gray border
            "border_focus": "#C9B96A",   # warm gold focus ring
            "text_main": "#292A2D",      # muted charcoal main text
            "text_muted": "#777873",     # secondary warm gray
            "primary": "#292A2D",        # dark charcoal for primary buttons
            "primary_hover": "#3D3E42",  # slightly lighter charcoal hover
            "accent": "#F3D86A",         # pale gold accent
            "accent_dark": "#C9A94A",    # darker gold for hover states
            "pos": "#5AAE91",            # teal green for positive sentiment
            "pos_bg": "#EBF7F3",         # very light teal background
            "neu": "#8795A5",            # cool slate for neutral
            "neu_bg": "#F0F3F7",         # very light slate background
            "neg": "#D97873",            # coral for negative sentiment
            "neg_bg": "#FCF0EF",         # very light coral background
            "gold": "#C9A94A"            # warm amber for warnings/stale notices
        }

        self.root.configure(bg=self.colors["bg"])

        # TTK Widget Styles
        style.configure("TFrame", background="#F8F6EF")
        style.configure("Card.TFrame", background="#FFFDF6", relief="flat", borderwidth=1)
        style.configure("TLabel", background="#F8F6EF", foreground="#292A2D", font=("Segoe UI", 10))
        style.configure("Card.TLabel", background="#FFFDF6", foreground="#292A2D", font=("Segoe UI", 10))
        style.configure("HeaderTitle.TLabel", font=("Segoe UI", 14, "bold"), foreground="#F8F6EF", background="#292A2D")
        style.configure("HeaderSub.TLabel", font=("Segoe UI", 10), foreground="#B0ADA5", background="#292A2D")

        # Navigation Tabs
        style.configure("TNotebook", background="#F8F6EF", tabmargins=[8, 4, 8, 0])
        style.configure("TNotebook.Tab", font=("Segoe UI", 10, "bold"), padding=[18, 9], background="#E8E4D9", foreground="#777873")
        style.map("TNotebook.Tab",
                  background=[("selected", "#292A2D")],
                  foreground=[("selected", "#F8F6EF")])

        # Buttons
        style.configure("Primary.TButton", font=("Segoe UI", 10, "bold"), background="#292A2D", foreground="#F8F6EF", padding=[14, 7])
        style.map("Primary.TButton", background=[("active", "#3D3E42")])

        style.configure("Secondary.TButton", font=("Segoe UI", 9), background="#FFFDF6", foreground="#292A2D", padding=[11, 5], relief="flat")
        style.configure("FilterActive.TButton", font=("Segoe UI", 9, "bold"), background="#F3D86A", foreground="#292A2D")

        # Treeview
        style.configure("Treeview", font=("Segoe UI", 10), rowheight=26, background="#FFFDF6", fieldbackground="#FFFDF6", foreground="#292A2D")
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"), background="#F0EDE5", foreground="#292A2D")

    def _init_analyzer_thread(self):
        try:
            self.analyzer = ConversationSentimentAnalyzer(default_model="baseline")
            self.root.after(0, lambda: self.status_var.set("Ready. Sentiment models loaded successfully."))
        except Exception as e:
            self.root.after(0, lambda: self.status_var.set(f"Note on models: {e}"))

    def _build_top_header(self):
        header = tk.Frame(self.root, bg=self.colors["header_bg"], height=58, padx=16, pady=8)
        header.pack(side="top", fill="x")

        # Branding & Title
        title_box = tk.Frame(header, bg=self.colors["header_bg"])
        title_box.pack(side="left", fill="y")

        lbl_title = ttk.Label(title_box, text="Sentiment Trajectory Analysis", style="HeaderTitle.TLabel")
        lbl_title.pack(anchor="w")

        lbl_sub = ttk.Label(title_box, text="Understand how model-predicted sentiment changes across a conversation.", style="HeaderSub.TLabel")
        lbl_sub.pack(anchor="w")

        # Top Right Badges: Local Privacy & Status
        badges_box = tk.Frame(header, bg=self.colors["header_bg"])
        badges_box.pack(side="right", fill="y", pady=4)

        priv_lbl = tk.Label(
            badges_box,
            text="🛡️ 100% On-Device / Local Processing",
            font=("Segoe UI", 8, "bold"),
            bg="#3D3E42",
            fg="#F3D86A",
            padx=8,
            pady=3
        )
        priv_lbl.pack(side="right", padx=6)

    def _build_main_navigation(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(side="top", fill="both", expand=True, padx=12, pady=6)

        # Tab 1: Home / Overview
        self.tab_home = ttk.Frame(self.notebook, padding=14)
        self.notebook.add(self.tab_home, text="  🏠 Home / Overview  ")
        self._build_home_view()

        # Tab 2: Analyze Conversation (The Stepped Workspace)
        self.tab_workspace = ttk.Frame(self.notebook, padding=14)
        self.notebook.add(self.tab_workspace, text="  🔬 Analyze Conversation  ")
        self._build_workspace_view()

        # Tab 3: Results Dashboard
        self.tab_results = ttk.Frame(self.notebook, padding=14)
        self.notebook.add(self.tab_results, text="  📊 Results Dashboard  ")
        self._build_results_view()

        # Tab 4: Built-in User Guide & Help
        self.tab_guide = ttk.Frame(self.notebook, padding=14)
        self.notebook.add(self.tab_guide, text="  📖 Guide & Help  ")
        self._build_guide_view()

    # =========================================================================
    # SECTION 1: HOME / OVERVIEW
    # =========================================================================
    def _build_home_view(self):
        scroll_container = scrolledtext.ScrolledText(self.tab_home, wrap="word", bg=self.colors["bg"], relief="flat", font=("Segoe UI", 10))
        scroll_container.pack(fill="both", expand=True)

        content_frame = ttk.Frame(scroll_container, padding=12)
        scroll_container.window_create("1.0", window=content_frame)

        # Welcome Card
        welc_card = ttk.Frame(content_frame, style="Card.TFrame", padding=18)
        welc_card.pack(fill="x", pady=(0, 14))

        ttk.Label(welc_card, text="Welcome to Sentiment Trajectory Analysis", font=("Segoe UI", 15, "bold"), style="Card.TLabel").pack(anchor="w")
        ttk.Label(
            welc_card,
            text=(
                "This tool analyzes the sentiment expressed in conversation messages, visualizes how model-predicted\n"
                "sentiment changes over time, and highlights notable shifts. It provides an evidence-based summary\n"
                "to help users explore conversational patterns."
            ),
            font=("Segoe UI", 10),
            style="Card.TLabel",
            foreground=self.colors["text_muted"],
            justify="left"
        ).pack(anchor="w", pady=(8, 14))

        # Action Buttons
        btn_row = ttk.Frame(welc_card, style="Card.TFrame")
        btn_row.pack(anchor="w")

        ttk.Button(btn_row, text="🚀  Analyze a Conversation", style="Primary.TButton", command=lambda: self.notebook.select(self.tab_workspace)).pack(side="left", padx=(0, 10))
        ttk.Button(btn_row, text="💡  Try Demonstration Dialogue", style="Secondary.TButton", command=self._load_demo_and_open_workspace).pack(side="left", padx=(0, 10))
        ttk.Button(btn_row, text="📖  Read Built-in Guide", style="Secondary.TButton", command=lambda: self.notebook.select(self.tab_guide)).pack(side="left")

        # 5-Step Workflow Overview Card
        flow_card = ttk.Frame(content_frame, style="Card.TFrame", padding=18)
        flow_card.pack(fill="x", pady=(0, 14))

        ttk.Label(flow_card, text="How It Works: 5-Step Workflow", font=("Segoe UI", 12, "bold"), style="Card.TLabel").pack(anchor="w", pady=(0, 10))

        steps = [
            ("1. Provide Conversation", "Paste dialogue, upload an exported WhatsApp chat (.txt), or select a structured CSV file."),
            ("2. Review & Prepare", "Verify parsed turns, speaker attributions, and message boundaries before running inference."),
            ("3. Configure & Run", "Select the model (RoBERTa Context-Aware or Baseline) and initiate sentiment classification."),
            ("4. Explore Trajectory", "Inspect the continuous polarity curve, shaded sentiment zones, and candidate turning points."),
            ("5. Evidence & Export", "Read the grounded narrative report and export predictions safely with formula-injection guards.")
        ]

        for num_title, desc in steps:
            s_box = ttk.Frame(flow_card, style="Card.TFrame", padding=4)
            s_box.pack(fill="x", pady=2)
            ttk.Label(s_box, text=num_title, font=("Segoe UI", 9, "bold"), foreground=self.colors["primary"], style="Card.TLabel").pack(anchor="w")
            ttk.Label(s_box, text=desc, font=("Segoe UI", 9), foreground=self.colors["text_muted"], style="Card.TLabel").pack(anchor="w")

        # Scientific Rigor & Epistemic Boundaries Card
        notice_card = ttk.Frame(content_frame, style="Card.TFrame", padding=14)
        notice_card.pack(fill="x")

        ttk.Label(notice_card, text="⚖️ Epistemic Boundary Notice (Scientific Accuracy)", font=("Segoe UI", 10, "bold"), style="Card.TLabel").pack(anchor="w")
        ttk.Label(
            notice_card,
            text=(
                "• The model predicts sentiment polarity from text (s_t = P(positive) - P(negative)).\n"
                "• Polarity scores are mathematical model indicators, NOT direct measurements of human internal emotions.\n"
                "• A sharp score shift reflects a shift in expressed language, not a proven psychological diagnosis or clinical cause."
            ),
            font=("Segoe UI", 8),
            style="Card.TLabel",
            foreground=self.colors["text_muted"],
            justify="left"
        ).pack(anchor="w", pady=(4, 0))

    def _load_demo_and_open_workspace(self):
        self._load_preset_conversation("Sample 1: Conflict to Reconciliation")
        self.notebook.select(self.tab_workspace)

    # =========================================================================
    # SECTION 2: ANALYZE CONVERSATION (STEPPED WORKSPACE)
    # =========================================================================
    def _build_workspace_view(self):
        # Paned layout: Left = Stepped Input & Settings / Right = Live Message Review & Preview
        paned = ttk.PanedWindow(self.tab_workspace, orient="horizontal")
        paned.pack(fill="both", expand=True)

        left_frame = ttk.Frame(paned, padding=8)
        right_frame = ttk.Frame(paned, padding=8)
        paned.add(left_frame, weight=3)
        paned.add(right_frame, weight=2)

        # -------------------------------------------------------------
        # STEP 1: Provide Your Conversation
        # -------------------------------------------------------------
        s1_card = ttk.Frame(left_frame, style="Card.TFrame", padding=12)
        s1_card.pack(fill="x", pady=(0, 10))

        ttk.Label(s1_card, text="Step 1 — Provide Your Conversation", font=("Segoe UI", 11, "bold"), style="Card.TLabel").pack(anchor="w", pady=(0, 4))
        ttk.Label(
            s1_card,
            text="Enter one message per line. If speaker names are included, use 'Speaker: Message'.",
            font=("Segoe UI", 8),
            style="Card.TLabel",
            foreground=self.colors["text_muted"]
        ).pack(anchor="w", pady=(0, 8))

        # Mode Selector
        self.input_mode_var = tk.StringVar(value="text")
        mode_box = ttk.Frame(s1_card, style="Card.TFrame")
        mode_box.pack(fill="x", pady=(0, 8))

        ttk.Radiobutton(mode_box, text="Paste Text", variable=self.input_mode_var, value="text", command=self._on_input_mode_change).pack(side="left", padx=(0, 12))
        ttk.Radiobutton(mode_box, text="WhatsApp (.txt)", variable=self.input_mode_var, value="whatsapp", command=self._on_input_mode_change).pack(side="left", padx=(0, 12))
        ttk.Radiobutton(mode_box, text="CSV File", variable=self.input_mode_var, value="csv", command=self._on_input_mode_change).pack(side="left", padx=(0, 12))
        ttk.Radiobutton(mode_box, text="Demo Preset", variable=self.input_mode_var, value="preset", command=self._on_input_mode_change).pack(side="left")

        # Preset Dropdown (visible when preset chosen)
        self.preset_frame = ttk.Frame(s1_card, style="Card.TFrame")
        self.preset_var = tk.StringVar(value="Sample 1: Conflict to Reconciliation")
        self.preset_combo = ttk.Combobox(self.preset_frame, textvariable=self.preset_var, values=list(SAMPLE_PRESETS.keys()), state="readonly", width=42)
        self.preset_combo.pack(side="left", fill="x", expand=True)
        self.preset_combo.bind("<<ComboboxSelected>>", lambda e: self._load_preset_conversation(self.preset_var.get()))

        # File Picker (visible when whatsapp or csv chosen)
        self.file_picker_frame = ttk.Frame(s1_card, style="Card.TFrame")
        self.file_path_var = tk.StringVar(value="No file selected")
        ttk.Button(self.file_picker_frame, text="Browse File...", style="Secondary.TButton", command=self._browse_input_file).pack(side="left", padx=(0, 8))
        ttk.Label(self.file_picker_frame, textvariable=self.file_path_var, font=("Segoe UI", 8, "italic"), style="Card.TLabel").pack(side="left", fill="x", expand=True)

        # Text Editor
        self.text_editor = scrolledtext.ScrolledText(s1_card, wrap="word", font=("Consolas", 9), height=10,
                                                     bg="#FFFDF6", fg="#292A2D", insertbackground="#292A2D")
        self.text_editor.pack(fill="both", expand=True, pady=(4, 6))
        self.text_editor.bind("<<Modified>>", self._on_text_editor_modified)

        # -------------------------------------------------------------
        # STEP 3: Configure Analysis (Collapsible Progressive Disclosure)
        # -------------------------------------------------------------
        s3_card = ttk.Frame(left_frame, style="Card.TFrame", padding=12)
        s3_card.pack(fill="x", pady=(0, 10))

        header_row = ttk.Frame(s3_card, style="Card.TFrame")
        header_row.pack(fill="x")
        ttk.Label(header_row, text="Step 3 — Analysis Settings", font=("Segoe UI", 11, "bold"), style="Card.TLabel").pack(side="left")
        
        self.adv_open_var = tk.BooleanVar(value=False)
        self.adv_toggle_btn = ttk.Button(header_row, text="⚙️ Show Advanced Options ▼", style="Secondary.TButton", command=self._toggle_advanced_settings)
        self.adv_toggle_btn.pack(side="right")

        # Primary Model Choice (Always visible)
        mod_box = ttk.Frame(s3_card, style="Card.TFrame")
        mod_box.pack(fill="x", pady=(8, 4))
        ttk.Label(mod_box, text="Model Architecture:", font=("Segoe UI", 9, "bold"), style="Card.TLabel").pack(side="left", padx=(0, 10))

        self.model_var = tk.StringVar(value="roberta_context")
        ttk.Radiobutton(mod_box, text="RoBERTa Context-Aware", variable=self.model_var, value="roberta_context").pack(side="left", padx=(0, 8))
        ttk.Radiobutton(mod_box, text="RoBERTa Independent", variable=self.model_var, value="roberta_independent").pack(side="left", padx=(0, 8))
        ttk.Radiobutton(mod_box, text="TF-IDF Baseline", variable=self.model_var, value="baseline").pack(side="left")

        # Collapsible Container for Sensitivity and Context Sliders
        self.advanced_container = ttk.Frame(s3_card, style="Card.TFrame")
        
        # Sensitivity Slider tau
        tau_box = ttk.Frame(self.advanced_container, style="Card.TFrame")
        tau_box.pack(fill="x", pady=(6, 2))
        ttk.Label(tau_box, text="Turning-Point Sensitivity (τ):", style="Card.TLabel").pack(side="left")
        self.tau_lbl = ttk.Label(tau_box, text="0.40", font=("Segoe UI", 9, "bold"), style="Card.TLabel")
        self.tau_lbl.pack(side="right")
        self.tau_slider = ttk.Scale(self.advanced_container, from_=0.10, to=0.90, value=0.40, command=lambda v: self.tau_lbl.config(text=f"{float(v):.2f}"))
        self.tau_slider.pack(fill="x", pady=(0, 6))

        # Context Window k
        k_box = ttk.Frame(self.advanced_container, style="Card.TFrame")
        k_box.pack(fill="x", pady=(4, 2))
        ttk.Label(k_box, text="Context Window Length (k):", style="Card.TLabel").pack(side="left")
        self.k_lbl = ttk.Label(k_box, text="3 preceding turns", font=("Segoe UI", 9, "bold"), style="Card.TLabel")
        self.k_lbl.pack(side="right")
        self.k_slider = ttk.Scale(self.advanced_container, from_=0, to=5, value=3, command=lambda v: self.k_lbl.config(text=f"{int(float(v))} preceding turns"))
        self.k_slider.pack(fill="x", pady=(0, 4))

        # -------------------------------------------------------------
        # STEP 4: Run Analysis Action
        # -------------------------------------------------------------
        s4_card = ttk.Frame(left_frame, style="Card.TFrame", padding=12)
        s4_card.pack(fill="x")

        self.run_btn = ttk.Button(s4_card, text="🚀  Analyze Conversation", style="Primary.TButton", command=self._execute_analysis)
        self.run_btn.pack(fill="x", pady=(2, 6))

        self.stale_warning_lbl = ttk.Label(
            s4_card,
            text="",
            font=("Segoe UI", 8, "italic"),
            foreground=self.colors["gold"],
            style="Card.TLabel"
        )
        self.stale_warning_lbl.pack(anchor="center")

        # -------------------------------------------------------------
        # STEP 2: Review & Prepare (Right Column Preview Pane)
        # -------------------------------------------------------------
        s2_card = ttk.Frame(right_frame, style="Card.TFrame", padding=12)
        s2_card.pack(fill="both", expand=True)

        ttk.Label(s2_card, text="Step 2 — Review & Prepare", font=("Segoe UI", 11, "bold"), style="Card.TLabel").pack(anchor="w")
        ttk.Label(
            s2_card,
            text="Verify parsed turns and speaker attributions before running model inference.",
            font=("Segoe UI", 8),
            style="Card.TLabel",
            foreground=self.colors["text_muted"]
        ).pack(anchor="w", pady=(0, 8))

        # Summary stats ribbon of preview
        self.preview_stats_box = ttk.Frame(s2_card, style="Card.TFrame")
        self.preview_stats_box.pack(fill="x", pady=(0, 6))

        self.preview_count_lbl = ttk.Label(self.preview_stats_box, text="Messages: 0 | Speakers: 0", font=("Segoe UI", 9, "bold"), style="Card.TLabel")
        self.preview_count_lbl.pack(side="left")

        ttk.Button(self.preview_stats_box, text="🔄 Refresh Preview", style="Secondary.TButton", command=self._refresh_parsed_preview).pack(side="right")

        # Preview Treeview
        preview_cols = ("idx", "speaker", "preview_text")
        self.preview_tree = ttk.Treeview(s2_card, columns=preview_cols, show="headings", height=16)
        self.preview_tree.heading("idx", text="#", anchor="center")
        self.preview_tree.heading("speaker", text="Speaker", anchor="w")
        self.preview_tree.heading("preview_text", text="Message Content", anchor="w")

        self.preview_tree.column("idx", width=38, anchor="center")
        self.preview_tree.column("speaker", width=95, anchor="w")
        self.preview_tree.column("preview_text", width=260, anchor="w")

        p_scroll = ttk.Scrollbar(s2_card, orient="vertical", command=self.preview_tree.yview)
        self.preview_tree.configure(yscrollcommand=p_scroll.set)
        p_scroll.pack(side="right", fill="y")
        self.preview_tree.pack(side="left", fill="both", expand=True)

    def _toggle_advanced_settings(self):
        is_open = self.adv_open_var.get()
        if is_open:
            self.advanced_container.pack_forget()
            self.adv_toggle_btn.config(text="⚙️ Show Advanced Options ▼")
            self.adv_open_var.set(False)
        else:
            self.advanced_container.pack(fill="x", pady=(6, 2))
            self.adv_toggle_btn.config(text="⚙️ Hide Advanced Options ▲")
            self.adv_open_var.set(True)

    def _on_input_mode_change(self):
        mode = self.input_mode_var.get()
        self.preset_frame.pack_forget()
        self.file_picker_frame.pack_forget()

        if mode == "preset":
            self.preset_frame.pack(fill="x", pady=(0, 6))
            self._load_preset_conversation(self.preset_var.get())
        elif mode in ["whatsapp", "csv"]:
            self.file_picker_frame.pack(fill="x", pady=(0, 6))
            hint = "WhatsApp Export (.txt)" if mode == "whatsapp" else "CSV File (.csv)"
            self.file_path_var.set(f"Click 'Browse File...' to select {hint}")
        else:
            self._refresh_parsed_preview()

    def _browse_input_file(self):
        mode = self.input_mode_var.get()
        if mode == "whatsapp":
            fpath = filedialog.askopenfilename(filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        else:
            fpath = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])

        if fpath:
            self.selected_file_path = Path(fpath)
            self.file_path_var.set(self.selected_file_path.name)
            try:
                with open(self.selected_file_path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                self.text_editor.delete("1.0", tk.END)
                self.text_editor.insert("1.0", content)
                self._refresh_parsed_preview()
            except Exception as e:
                messagebox.showerror("File Error", f"Unable to read file: {e}")

    def _load_preset_conversation(self, key):
        if key in SAMPLE_PRESETS:
            self.text_editor.delete("1.0", tk.END)
            self.text_editor.insert("1.0", SAMPLE_PRESETS[key])
            self._refresh_parsed_preview()

    def _on_text_editor_modified(self, event=None):
        if self.text_editor.edit_modified():
            self.text_editor.edit_modified(False)
            self.is_results_stale = True
            if self.current_analysis_result:
                self.stale_warning_lbl.config(text="⚠️ Input text modified. Results on Dashboard are out-of-date.")
            self._refresh_parsed_preview()

    def _refresh_parsed_preview(self):
        raw_text = self.text_editor.get("1.0", tk.END).strip()
        for item in self.preview_tree.get_children():
            self.preview_tree.delete(item)

        if not raw_text:
            self.preview_count_lbl.config(text="Messages: 0 | Speakers: 0")
            return

        lines = [l.strip() for l in raw_text.split("\n") if l.strip()]
        rows = []
        for i, l in enumerate(lines):
            # Parse speaker if present
            if l.startswith("[") and "]" in l and ":" in l.split("]")[1]:
                post_bracket = l.split("]")[1]
                parts = post_bracket.split(":", 1)
                spk = parts[0].strip()
                txt = parts[1].strip()
            elif ":" in l:
                parts = l.split(":", 1)
                spk = parts[0].strip()
                txt = parts[1].strip()
            else:
                spk = f"Speaker_{(i % 2) + 1}"
                txt = l

            rows.append({"turn_id": i, "speaker": spk, "text": txt})
            self.preview_tree.insert("", "end", values=(i, spk, txt[:50] + ("..." if len(txt) > 50 else "")))

        num_speakers = len(set(r["speaker"] for r in rows))
        self.preview_count_lbl.config(text=f"Messages: {len(rows)} | Speakers: {num_speakers}")

    def _execute_analysis(self):
        raw_text = self.text_editor.get("1.0", tk.END).strip()
        if not raw_text:
            messagebox.showwarning("Empty Input", "Please provide conversation messages before analyzing.")
            return

        if not self.analyzer:
            messagebox.showinfo("Initializing", "Sentiment models are still loading. Please wait a moment.")
            return

        # Disable submit & show staged progress
        self.run_btn.config(state="disabled")
        self.progress.pack(side="right", padx=6)
        self.progress.start(10)
        self.status_var.set("Stage 1/4: Preparing conversation messages...")

        thread = threading.Thread(target=self._analysis_worker, args=(raw_text,), daemon=True)
        thread.start()

    def _analysis_worker(self, raw_text: str):
        try:
            model_type = self.model_var.get()
            tau = float(self.tau_slider.get())
            k = int(float(self.k_slider.get()))

            self.root.after(0, lambda: self.status_var.set(f"Stage 2/4: Predicting sentiment with {model_type}..."))
            
            # Run inference
            result = self.analyzer.analyze_conversation(
                input_data=raw_text,
                input_type="text",
                model_type=model_type,
                context_window=k,
                turning_point_threshold=tau
            )

            self.root.after(0, lambda: self.status_var.set("Stage 3/4: Calculating trajectory & turning points..."))
            self.root.after(0, lambda: self.status_var.set("Stage 4/4: Generating evidence-backed explanation..."))

            self.root.after(0, lambda: self._on_analysis_success(result))
        except Exception as e:
            self.root.after(0, lambda: self._on_analysis_failure(str(e)))

    def _on_analysis_success(self, result: Dict[str, Any]):
        self.progress.stop()
        self.progress.pack_forget()
        self.run_btn.config(state="normal")
        self.is_results_stale = False
        self.stale_warning_lbl.config(text="")

        if not result.get("success", False):
            self.status_var.set("Analysis failed.")
            messagebox.showerror("Analysis Error", result.get("error", "Unknown error."))
            return

        self.current_analysis_result = result
        self.status_var.set(f"Complete. {len(result['predictions_df'])} turns evaluated with {result['model_used']}.")

        # Populate Results Dashboard
        self._populate_results_dashboard(result)
        # Navigate to Dashboard
        self.notebook.select(self.tab_results)

    def _on_analysis_failure(self, err_msg: str):
        self.progress.stop()
        self.progress.pack_forget()
        self.run_btn.config(state="normal")
        self.status_var.set(f"Error: {err_msg}")
        messagebox.showerror("Execution Error", f"Unable to complete analysis:\n{err_msg}")

    # =========================================================================
    # SECTION 3: RESULTS DASHBOARD
    # =========================================================================
    def _build_results_view(self):
        # Top-level notebook or tab sections for Results
        res_notebook = ttk.Notebook(self.tab_results)
        res_notebook.pack(fill="both", expand=True)

        # Tab A: Summary & Trajectory Visualization
        self.tab_res_viz = ttk.Frame(res_notebook, padding=8)
        res_notebook.add(self.tab_res_viz, text=" 📈 Trajectory & Dynamics ")
        self._build_viz_subpanel()

        # Tab B: Message Explorer
        self.tab_res_msgs = ttk.Frame(res_notebook, padding=8)
        res_notebook.add(self.tab_res_msgs, text=" 🔍 Message Explorer ")
        self._build_msgs_subpanel()

        # Tab C: Written Evidence Report
        self.tab_res_rep = ttk.Frame(res_notebook, padding=8)
        res_notebook.add(self.tab_res_rep, text=" 📄 Evidence Report ")
        self._build_report_subpanel()

        # Tab D: Data & Export Center
        self.tab_res_exp = ttk.Frame(res_notebook, padding=8)
        res_notebook.add(self.tab_res_exp, text=" 💾 Export Center ")
        self._build_export_subpanel()

    def _build_viz_subpanel(self):
        # 1. KPI Metric Ribbon
        self.kpi_container = ttk.Frame(self.tab_res_viz)
        self.kpi_container.pack(fill="x", pady=(0, 8))

        self.kpi_widgets = {}
        metrics_meta = [
            ("Total Messages", "0", "turns", "Total conversation messages analyzed"),
            ("Average Mood", "Neutral", "mean", "Average emotional tone across all messages"),
            ("Overall Shift", "Steady", "drift", "Whether the mood improved or dropped by the end"),
            ("Mood Stability", "Smooth", "vol", "How consistent the emotional tone remained"),
            ("Key Shifts", "0", "tps", "Noticeable changes in conversation mood")
        ]

        for title, default_val, key, tooltip_desc in metrics_meta:
            card = ttk.Frame(self.kpi_container, style="Card.TFrame", padding=8)
            card.pack(side="left", fill="both", expand=True, padx=3)
            
            lbl = ttk.Label(card, text=title, font=("Segoe UI", 9, "bold"), foreground=self.colors["text_muted"], style="Card.TLabel")
            lbl.pack(anchor="center")
            
            val = ttk.Label(card, text=default_val, font=("Segoe UI", 12, "bold"), style="Card.TLabel")
            val.pack(anchor="center", pady=(2, 0))
            self.kpi_widgets[key] = val

        # 2. Chart Mode Switcher Toolbar
        chart_switch_bar = ttk.Frame(self.tab_res_viz, style="Card.TFrame", padding=6)
        chart_switch_bar.pack(fill="x", pady=(0, 6))

        ttk.Label(chart_switch_bar, text="Visualization View:", font=("Segoe UI", 9, "bold"), style="Card.TLabel").pack(side="left", padx=(0, 8))

        self.btn_chart_arc = ttk.Button(chart_switch_bar, text="🌊 Sentiment Arc", style="FilterActive.TButton", command=lambda: self._switch_chart_mode("arc"))
        self.btn_chart_arc.pack(side="left", padx=3)

        self.btn_chart_tree = ttk.Button(chart_switch_bar, text="🗺️ Tree Map", style="Secondary.TButton", command=lambda: self._switch_chart_mode("treemap"))
        self.btn_chart_tree.pack(side="left", padx=3)

        self.btn_chart_sankey = ttk.Button(chart_switch_bar, text="🔀 Sankey Flow", style="Secondary.TButton", command=lambda: self._switch_chart_mode("sankey"))
        self.btn_chart_sankey.pack(side="left", padx=3)

        # Main Visualization Matplotlib Canvas
        self.plot_frame = ttk.Frame(self.tab_res_viz, style="Card.TFrame", padding=6)
        self.plot_frame.pack(fill="both", expand=True)

        self.fig = Figure(figsize=(9, 4.6), dpi=100)
        self.fig.patch.set_facecolor("#F8F6EF")
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        self.toolbar = NavigationToolbar2Tk(self.canvas, self.plot_frame)
        self.toolbar.update()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        # 3. Expandable "How to Read This Chart" Drawer
        guide_drawer = ttk.Frame(self.tab_res_viz, style="Card.TFrame", padding=8)
        guide_drawer.pack(fill="x", pady=(6, 0))

        self.chart_guide_title = ttk.Label(guide_drawer, text="ℹ️ How to Read This Sentiment Arc Chart", font=("Segoe UI", 9, "bold"), style="Card.TLabel")
        self.chart_guide_title.pack(anchor="w")
        self.chart_guide_desc = ttk.Label(
            guide_drawer,
            text=self._get_chart_guide_text("arc"),
            font=("Segoe UI", 8),
            style="Card.TLabel",
            foreground=self.colors["text_muted"],
            justify="left"
        )
        self.chart_guide_desc.pack(anchor="w", pady=(2, 0))

        # 4. Sponsor Showcase Banner (Non-intrusive)
        sponsor_bar = ttk.Frame(self.tab_res_viz, style="Card.TFrame", padding=6)
        sponsor_bar.pack(fill="x", pady=(6, 0))
        ttk.Label(sponsor_bar, text="SPONSORED", font=("Segoe UI", 7, "bold"), foreground="#C9A94A", style="Card.TLabel").pack(side="left", padx=(4, 8))
        ttk.Label(sponsor_bar, text="✨ Explore smart AI communication tools for seamless team workflows.", font=("Segoe UI", 9), style="Card.TLabel").pack(side="left")

    def _get_chart_guide_text(self, mode: str) -> str:
        if mode == "arc":
            return (
                "• Horizontal axis shows conversation turn index (t = 0, 1, 2...).\n"
                "• Continuous dark line plots the continuous Emotional Arc smoothed curve showing narrative trajectory.\n"
                "• Soft Green Zone (> +0.15) = positive polarity; Soft Red Zone (< -0.15) = negative polarity; Dashed line = equilibrium (s=0).\n"
                "• Star markers denote algorithmically flagged turning points where turn-to-turn shift |Δs| >= τ.\n"
                "• Top title classifies the story archetype (e.g. 'Man in a Hole' dip & recovery, 'Rags to Riches' rise, 'Tragedy' decline)."
            )
        elif mode == "treemap":
            return (
                "• Groups conversation messages and feedback by Topic Clusters (Issues, Support, Product, Resolution, General).\n"
                "• Rectangle Area is strictly proportional to Feedback Frequency (number of turns / comments in that cluster).\n"
                "• Color indicates Sentiment Tone: Green = Positive feedback, Slate/Gray = Neutral comments, Red = Negative issues.\n"
                "• Labels show topic cluster name, sentiment class, turn count, and percentage share of total conversation."
            )
        elif mode == "sankey":
            return (
                "• Illustrates the Markov Flow of sentiment between categories from turn t (left) to turn t+1 (right).\n"
                "• Specifically highlights how Neutral comments evolve over time into Positive (de-escalation) or Negative (escalation).\n"
                "• Width of each curved ribbon represents the volume of turn-to-turn transitions.\n"
                "• Top annotations summarize the exact percentage of neutral comments that evolved to positive vs negative."
            )
        return ""

    def _switch_chart_mode(self, mode: str):
        self.active_chart_mode = mode
        mapping = {
            "arc": self.btn_chart_arc,
            "treemap": self.btn_chart_tree,
            "sankey": self.btn_chart_sankey
        }
        for m, btn in mapping.items():
            btn.configure(style="FilterActive.TButton" if m == mode else "Secondary.TButton")
        
        titles = {
            "arc": "ℹ️ How to Read This Sentiment Arc Chart",
            "treemap": "ℹ️ How to Read This Sentiment Tree Map",
            "sankey": "ℹ️ How to Read This Sentiment Sankey Diagram"
        }
        if hasattr(self, "chart_guide_title"):
            self.chart_guide_title.config(text=titles.get(mode, "ℹ️ How to Read This Chart"))
        if hasattr(self, "chart_guide_desc"):
            self.chart_guide_desc.config(text=self._get_chart_guide_text(mode))

        if self.current_analysis_result:
            self._render_active_chart()

    def _build_msgs_subpanel(self):
        # Filtering toolbar
        filter_bar = ttk.Frame(self.tab_res_msgs, style="Card.TFrame", padding=6)
        filter_bar.pack(fill="x", pady=(0, 6))

        ttk.Label(filter_bar, text="Filter Messages:", font=("Segoe UI", 9, "bold"), style="Card.TLabel").pack(side="left", padx=(0, 10))
        
        self.btn_f_all = ttk.Button(filter_bar, text="All", style="FilterActive.TButton", command=lambda: self._apply_message_filter("all"))
        self.btn_f_all.pack(side="left", padx=2)
        self.btn_f_pos = ttk.Button(filter_bar, text="Positive [▲]", style="Secondary.TButton", command=lambda: self._apply_message_filter("positive"))
        self.btn_f_pos.pack(side="left", padx=2)
        self.btn_f_neu = ttk.Button(filter_bar, text="Neutral [●]", style="Secondary.TButton", command=lambda: self._apply_message_filter("neutral"))
        self.btn_f_neu.pack(side="left", padx=2)
        self.btn_f_neg = ttk.Button(filter_bar, text="Negative [▼]", style="Secondary.TButton", command=lambda: self._apply_message_filter("negative"))
        self.btn_f_neg.pack(side="left", padx=2)
        self.btn_f_tps = ttk.Button(filter_bar, text="Shifts Only [⚡]", style="Secondary.TButton", command=lambda: self._apply_message_filter("shifts"))
        self.btn_f_tps.pack(side="left", padx=2)

        # Paned layout: Top = Table, Bottom = Context Inspection Card
        paned = ttk.PanedWindow(self.tab_res_msgs, orient="vertical")
        paned.pack(fill="both", expand=True)

        table_frame = ttk.Frame(paned)
        paned.add(table_frame, weight=3)

        cols = ("turn_id", "speaker", "sentiment", "polarity", "p_neg", "p_neu", "p_pos", "tp", "text")
        self.msg_tree = ttk.Treeview(table_frame, columns=cols, show="headings", selectmode="browse")

        self.msg_tree.heading("turn_id", text="#", anchor="center")
        self.msg_tree.heading("speaker", text="Speaker", anchor="w")
        self.msg_tree.heading("sentiment", text="Predicted Class", anchor="center")
        self.msg_tree.heading("polarity", text="Polarity (s_t)", anchor="center")
        self.msg_tree.heading("p_neg", text="P(Neg)", anchor="center")
        self.msg_tree.heading("p_neu", text="P(Neu)", anchor="center")
        self.msg_tree.heading("p_pos", text="P(Pos)", anchor="center")
        self.msg_tree.heading("tp", text="Turning Point?", anchor="center")
        self.msg_tree.heading("text", text="Utterance Message", anchor="w")

        self.msg_tree.column("turn_id", width=38, anchor="center")
        self.msg_tree.column("speaker", width=105, anchor="w")
        self.msg_tree.column("sentiment", width=100, anchor="center")
        self.msg_tree.column("polarity", width=95, anchor="center")
        self.msg_tree.column("p_neg", width=62, anchor="center")
        self.msg_tree.column("p_neu", width=62, anchor="center")
        self.msg_tree.column("p_pos", width=62, anchor="center")
        self.msg_tree.column("tp", width=100, anchor="center")
        self.msg_tree.column("text", width=380, anchor="w")

        m_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.msg_tree.yview)
        self.msg_tree.configure(yscrollcommand=m_scroll.set)
        m_scroll.pack(side="right", fill="y")
        self.msg_tree.pack(side="left", fill="both", expand=True)

        self.msg_tree.bind("<<TreeviewSelect>>", self._on_msg_tree_select)

        # Bottom Context Inspection Card
        detail_card = ttk.Frame(paned, style="Card.TFrame", padding=10)
        paned.add(detail_card, weight=1)

        ttk.Label(detail_card, text="Message Detail & Preceding Context Window:", font=("Segoe UI", 9, "bold"), style="Card.TLabel").pack(anchor="w")
        self.detail_text = scrolledtext.ScrolledText(detail_card, wrap="word", font=("Segoe UI", 9), height=5)
        self.detail_text.pack(fill="both", expand=True, pady=(4, 0))

    def _apply_message_filter(self, filter_key: str):
        self.active_filter = filter_key
        # Update button highlights
        buttons = [self.btn_f_all, self.btn_f_pos, self.btn_f_neu, self.btn_f_neg, self.btn_f_tps]
        for b in buttons:
            b.configure(style="Secondary.TButton")
        
        mapping = {"all": self.btn_f_all, "positive": self.btn_f_pos, "neutral": self.btn_f_neu, "negative": self.btn_f_neg, "shifts": self.btn_f_tps}
        if filter_key in mapping:
            mapping[filter_key].configure(style="FilterActive.TButton")

        if self.current_analysis_result:
            self._render_messages_table(self.current_analysis_result["predictions_df"], self.current_analysis_result["trajectory_stats"])

    def _on_msg_tree_select(self, event=None):
        sel = self.msg_tree.selection()
        if not sel or not self.current_analysis_result:
            return

        item = self.msg_tree.item(sel[0])
        turn_id = int(item["values"][0])
        df = self.current_analysis_result["predictions_df"]

        if turn_id >= len(df):
            return

        row = df.iloc[turn_id]
        context_k = int(float(self.k_slider.get()))
        start_ctx = max(0, turn_id - context_k)

        out = [
            f"Turn {turn_id} — Speaker: {row['speaker']}",
            f"Predicted Sentiment: {row['pred_sentiment'].upper()} (Polarity s_t: {row['polarity_score']:+.4f})",
            f"Class Probabilities: P(Neg)={row['prob_negative']:.3f}, P(Neu)={row['prob_neutral']:.3f}, P(Pos)={row['prob_positive']:.3f}",
            "",
            "--- Preceding Conversational Context Window ---"
        ]
        if start_ctx == turn_id:
            out.append("(Initial conversation turn — no preceding history)")
        else:
            for p in range(start_ctx, turn_id):
                p_row = df.iloc[p]
                out.append(f"Turn {p} [{p_row['speaker']}]: \"{p_row['text']}\"")

        out.append("")
        out.append(f"--- Current Turn Message ---")
        out.append(f"\"{row['text']}\"")

        self.detail_text.delete("1.0", tk.END)
        self.detail_text.insert("1.0", "\n".join(out))

    def _build_report_subpanel(self):
        ttk.Label(self.tab_res_rep, text="Evidence-Grounded Analysis & Interpretation Report", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 6))
        self.report_box = scrolledtext.ScrolledText(self.tab_res_rep, wrap="word", font=("Consolas", 10))
        self.report_box.pack(fill="both", expand=True)

    def _build_export_subpanel(self):
        card = ttk.Frame(self.tab_res_exp, style="Card.TFrame", padding=18)
        card.pack(fill="both", expand=True)

        ttk.Label(card, text="Data & Audit Export Center", font=("Segoe UI", 13, "bold"), style="Card.TLabel").pack(anchor="w", pady=(0, 4))
        ttk.Label(
            card,
            text="Export full analytical records, formatted reports, and publication plots with formula-injection defenses (Risk #87).",
            font=("Segoe UI", 9),
            style="Card.TLabel",
            foreground=self.colors["text_muted"]
        ).pack(anchor="w", pady=(0, 16))

        grid = ttk.Frame(card, style="Card.TFrame")
        grid.pack(fill="x", pady=6)

        ttk.Button(grid, text="💾  Export Predictions CSV", style="Primary.TButton", command=self._export_csv_action).grid(row=0, column=0, padx=8, pady=8, sticky="ew")
        ttk.Button(grid, text="📄  Export Markdown Report (.md)", style="Secondary.TButton", command=self._export_report_action).grid(row=0, column=1, padx=8, pady=8, sticky="ew")
        ttk.Button(grid, text="📊  Export Full JSON Analysis", style="Secondary.TButton", command=self._export_json_action).grid(row=1, column=0, padx=8, pady=8, sticky="ew")
        ttk.Button(grid, text="🖼️  Save Trajectory Chart (PNG)", style="Secondary.TButton", command=self._export_chart_action).grid(row=1, column=1, padx=8, pady=8, sticky="ew")

        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)

        # Defensive Audit Notice
        audit_note = ttk.Frame(card, style="Card.TFrame", padding=12)
        audit_note.pack(fill="x", pady=(20, 0))
        ttk.Label(audit_note, text="🔒 Compliance & Integrity Defenses:", font=("Segoe UI", 9, "bold"), style="Card.TLabel").pack(anchor="w")
        ttk.Label(
            audit_note,
            text=(
                "• Formula Injection Protection: Any cell beginning with '=', '+', '-', or '@' is automatically prepended with an apostrophe (').\n"
                "• Local Storage: All exports are saved directly to your local machine without external telemetry."
            ),
            font=("Segoe UI", 8),
            style="Card.TLabel",
            foreground=self.colors["text_muted"],
            justify="left"
        ).pack(anchor="w", pady=(4, 0))

    def _populate_results_dashboard(self, result: Dict[str, Any]):
        stats = result["trajectory_stats"]
        df = result["predictions_df"]

        # 1. Update KPI ribbon
        mean_p = stats.get("mean_polarity", 0.0)
        net_d = stats.get("net_change", 0.0)
        vol = stats.get("volatility", 0.0)
        tps = stats.get("turning_points", [])

        # 1. Update KPI ribbon with layman-friendly descriptors
        mood_str = "😊 Positive" if mean_p > 0.15 else ("😟 Negative" if mean_p < -0.15 else "😐 Neutral")
        shift_str = "↗ Improved" if net_d > 0.15 else ("↘ Dropped" if net_d < -0.15 else "➡ Steady")
        vol_str = "Smooth" if vol < 0.15 else ("Moderate" if vol < 0.35 else "Bumpy")

        self.kpi_widgets["turns"].config(text=str(len(df)))
        self.kpi_widgets["mean"].config(
            text=f"{mood_str} ({mean_p:+.2f})",
            foreground=self.colors["pos"] if mean_p > 0.1 else (self.colors["neg"] if mean_p < -0.1 else self.colors["neu"])
        )
        self.kpi_widgets["drift"].config(
            text=f"{shift_str} ({net_d:+.2f})",
            foreground=self.colors["pos"] if net_d > 0.1 else (self.colors["neg"] if net_d < -0.1 else self.colors["neu"])
        )
        self.kpi_widgets["vol"].config(text=f"{vol_str} ({vol:.2f})")
        self.kpi_widgets["tps"].config(text=str(len(tps)))

        # 2. Render Active Visualization View
        self._render_active_chart()

        # 3. Populate Message Explorer
        self._render_messages_table(df, stats)

        # 4. Populate Written Report
        self._render_report_text(result["explanation"])

    def _render_active_chart(self):
        if not self.current_analysis_result:
            return
        df = self.current_analysis_result["predictions_df"]
        stats = self.current_analysis_result["trajectory_stats"]

        if self.active_chart_mode == "arc":
            self._render_sentiment_arc(df, stats)
        elif self.active_chart_mode == "treemap":
            self._render_treemap(df, stats)
        elif self.active_chart_mode == "sankey":
            self._render_sankey(df, stats)
        else:
            self._render_sentiment_arc(df, stats)

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

    def _render_sentiment_arc(self, df: pd.DataFrame, stats: Dict[str, Any]):
        self.fig.clear()
        self.fig.patch.set_facecolor("#F8F6EF")

        # 2 Subplots: Top = Polarity & Smoothed Arc, Bottom = Class Probabilities Breakdown
        ax1 = self.fig.add_subplot(2, 1, 1)
        ax2 = self.fig.add_subplot(2, 1, 2, sharex=ax1)

        for ax in (ax1, ax2):
            ax.set_facecolor("#FFFDF6")
            ax.tick_params(colors="#777873", labelsize=8)
            ax.spines["bottom"].set_color("#E8E4D9")
            ax.spines["top"].set_color("#E8E4D9")
            ax.spines["left"].set_color("#E8E4D9")
            ax.spines["right"].set_color("#E8E4D9")

        turns = np.arange(len(df))
        scores = np.array(stats.get("scores", []), dtype=float)
        if len(scores) == 0:
            self.canvas.draw()
            return

        archetype = self._classify_sentiment_arc_archetype(scores)

        # Subplot 1: Polarity & Continuous Smoothed Sentiment Arc
        ax1.axhspan(0.15, 1.0, color="#5AAE91", alpha=0.10, label="Positive (> +0.15)")
        ax1.axhspan(-0.15, 0.15, color="#8795A5", alpha=0.07, label="Neutral Zone")
        ax1.axhspan(-1.0, -0.15, color="#D97873", alpha=0.10, label="Negative (< -0.15)")
        ax1.axhline(0, color="#B0ADA5", linestyle="--", linewidth=0.9, label="Equilibrium (s=0)")

        # Raw turn polarity line
        ax1.plot(turns, scores, marker="o", markersize=4, color="#8795A5", alpha=0.55, linestyle=":", linewidth=1.2, label="Turn Score ($s_t$)")

        # Continuous Smoothed Sentiment Arc
        if len(scores) >= 3:
            try:
                poly_deg = min(3, max(1, len(scores) // 2))
                poly_coeffs = np.polyfit(turns, scores, poly_deg)
                arc_line = np.poly1d(poly_coeffs)(turns)
                ax1.plot(turns, arc_line, color="#292A2D", linewidth=2.5, label="Emotional Arc Curve")
                ax1.fill_between(turns, arc_line, 0, color="#292A2D", alpha=0.08)
            except Exception:
                ax1.plot(turns, scores, color="#292A2D", linewidth=2.2, label="Emotional Arc Curve")
        else:
            ax1.plot(turns, scores, color="#292A2D", linewidth=2.2, label="Emotional Arc Curve")

        # Turning Point Flags
        for tp in stats.get("turning_points", []):
            t_idx = tp["turn_index"]
            s_val = tp["score_after"]
            col = self.colors["pos"] if tp["delta"] > 0 else self.colors["neg"]
            ax1.plot(t_idx, s_val, marker="*", markersize=13, color=col, zorder=5)
            ax1.annotate(
                f"T{t_idx} ({tp['delta']:+.2f})",
                xy=(t_idx, s_val),
                xytext=(t_idx, s_val + (0.16 if s_val >= 0 else -0.18)),
                ha="center",
                fontsize=8,
                fontweight="bold",
                color=col,
                bbox=dict(boxstyle="round,pad=0.2", facecolor="#FFFFFF", edgecolor=col, alpha=0.9),
                arrowprops=dict(arrowstyle="->", color=col, lw=1)
            )

        ax1.set_ylim(-1.05, 1.05)
        ax1.set_ylabel("Polarity ($s_t$)", fontsize=9, fontweight="bold", color="#292A2D")
        ax1.set_title(f"Sentiment Arc: {archetype}   [Net Drift: {stats.get('net_drift', 0):+.2f}]", fontsize=11, fontweight="bold", pad=8, color="#292A2D")
        ax1.grid(True, linestyle=":", alpha=0.5, color="#E8E4D9")
        ax1.legend(loc="upper left", fontsize=8, framealpha=0.9, facecolor="#FFFDF6", edgecolor="#E8E4D9")

        # Subplot 2: Probability Distribution Stacked Bar Chart
        p_neg = df["prob_negative"].values
        p_neu = df["prob_neutral"].values
        p_pos = df["prob_positive"].values

        ax2.bar(turns, p_neg, color="#D97873", label="Negative", width=0.65, alpha=0.85)
        ax2.bar(turns, p_neu, bottom=p_neg, color="#8795A5", label="Neutral", width=0.65, alpha=0.85)
        ax2.bar(turns, p_pos, bottom=p_neg + p_neu, color="#5AAE91", label="Positive", width=0.65, alpha=0.85)

        ax2.set_ylim(0, 1.02)
        ax2.set_xlabel("Conversation Turn Index ($t$)", fontsize=9, fontweight="bold", color="#292A2D")
        ax2.set_ylabel("Class Probability", fontsize=9, fontweight="bold", color="#292A2D")
        ax2.set_xticks(turns)
        ax2.set_xticklabels([f"T{t}" for t in turns], fontsize=8, rotation=45 if len(turns) > 16 else 0)
        ax2.grid(True, linestyle=":", alpha=0.4, color="#E8E4D9")
        ax2.legend(loc="lower left", fontsize=8, framealpha=0.9, ncol=3, facecolor="#FFFDF6", edgecolor="#E8E4D9")

        self.fig.tight_layout()
        self.canvas.draw()

    def _render_trajectory_plot(self, df: pd.DataFrame, stats: Dict[str, Any]):
        """Alias for backwards compatibility."""
        self._render_sentiment_arc(df, stats)

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

    def _render_treemap(self, df: pd.DataFrame, stats: Dict[str, Any]):
        self.fig.clear()
        self.fig.patch.set_facecolor("#F8F6EF")

        ax = self.fig.add_subplot(1, 1, 1)
        ax.set_facecolor("#FFFDF6")
        ax.set_xlim(0, 100)
        ax.set_ylim(0, 100)
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)

        items = self._cluster_feedback_messages(df)
        total_items = sum(it["count"] for it in items)
        if total_items == 0:
            ax.text(50, 50, "No messages to display in Tree Map", ha="center", va="center", fontsize=11, color="#777873")
            self.canvas.draw()
            return

        rects = self._compute_treemap_rects(items, x=2.0, y=2.0, w=96.0, h=93.0)

        color_map = {
            "positive": ("#5AAE91", "#1B4D3E"),
            "neutral": ("#8795A5", "#2C3E50"),
            "negative": ("#D97873", "#5C1D1A")
        }

        for item in rects:
            rx, ry, rw, rh = item["rect"]
            sent = item["sentiment"]
            fill_color, text_color = color_map.get(sent, ("#B0ADA5", "#292A2D"))

            # Draw rectangle patch
            patch = mpatches.FancyBboxPatch(
                (rx + 0.4, ry + 0.4),
                max(0.1, rw - 0.8),
                max(0.1, rh - 0.8),
                boxstyle="round,pad=0.2",
                facecolor=fill_color,
                edgecolor="#FFFDF6",
                linewidth=1.5,
                alpha=0.88
            )
            ax.add_patch(patch)

            # Center text formatting
            cx = rx + rw / 2.0
            cy = ry + rh / 2.0
            pct = (item["count"] / total_items) * 100

            if rw > 14 and rh > 12:
                ax.text(
                    cx, cy + (rh * 0.12),
                    item["topic"],
                    ha="center", va="center",
                    fontsize=9 if rw > 22 else 8,
                    fontweight="bold",
                    color="#FFFFFF"
                )
                ax.text(
                    cx, cy - (rh * 0.12),
                    f"{sent.capitalize()}: {item['count']} ({pct:.1f}%)",
                    ha="center", va="center",
                    fontsize=8 if rw > 22 else 7,
                    fontweight="bold",
                    color="#F8F6EF"
                )
            elif rw > 8 and rh > 6:
                ax.text(
                    cx, cy,
                    f"{item['topic'][:10]}..\n{item['count']} ({pct:.0f}%)",
                    ha="center", va="center",
                    fontsize=7,
                    color="#FFFFFF"
                )

        # Legend
        legend_elements = [
            mpatches.Patch(facecolor="#5AAE91", label="Positive Sentiment", alpha=0.88),
            mpatches.Patch(facecolor="#8795A5", label="Neutral Sentiment", alpha=0.88),
            mpatches.Patch(facecolor="#D97873", label="Negative Sentiment", alpha=0.88)
        ]
        ax.legend(handles=legend_elements, loc="upper right", bbox_to_anchor=(0.99, 1.04), ncol=3, fontsize=8, facecolor="#FFFDF6", edgecolor="#E8E4D9")
        ax.set_title(f"Sentiment Tree Map — Grouped by Topic Clusters (Size = Feedback Frequency, N = {total_items})", fontsize=11, fontweight="bold", pad=12, color="#292A2D")

        self.fig.tight_layout()
        self.canvas.draw()

    def _render_sankey(self, df: pd.DataFrame, stats: Dict[str, Any]):
        self.fig.clear()
        self.fig.patch.set_facecolor("#F8F6EF")

        ax = self.fig.add_subplot(1, 1, 1)
        ax.set_facecolor("#FFFDF6")
        ax.set_xlim(0, 100)
        ax.set_ylim(0, 100)
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)

        preds = [str(s).lower() for s in df["pred_sentiment"].values]
        if len(preds) < 2:
            ax.text(50, 50, "Need at least 2 conversation turns to compute sentiment transitions", ha="center", va="center", fontsize=11, color="#777873")
            self.canvas.draw()
            return

        states = ["positive", "neutral", "negative"]
        state_labels = {"positive": "Positive", "neutral": "Neutral", "negative": "Negative"}
        color_map = {"positive": "#5AAE91", "neutral": "#8795A5", "negative": "#D97873"}

        # Build transition matrix
        trans = {s1: {s2: 0 for s2 in states} for s1 in states}
        for i in range(len(preds) - 1):
            s_from = preds[i] if preds[i] in states else "neutral"
            s_to = preds[i + 1] if preds[i + 1] in states else "neutral"
            trans[s_from][s_to] += 1

        total_trans = len(preds) - 1

        # Source totals & Target totals
        src_totals = {s: sum(trans[s].values()) for s in states}
        tgt_totals = {s: sum(trans[other][s] for other in states) for s in states}

        # Calculate node heights and positions
        y_margin = 12.0
        gap = 5.0
        avail_h = 100.0 - (2 * y_margin) - (2 * gap)

        src_y = {}
        curr_y = 100.0 - y_margin
        for s in states:
            h = max(2.0, (src_totals[s] / total_trans) * avail_h) if total_trans > 0 else avail_h / 3.0
            src_y[s] = (curr_y - h, curr_y)
            curr_y -= (h + gap)

        tgt_y = {}
        curr_y = 100.0 - y_margin
        for s in states:
            h = max(2.0, (tgt_totals[s] / total_trans) * avail_h) if total_trans > 0 else avail_h / 3.0
            tgt_y[s] = (curr_y - h, curr_y)
            curr_y -= (h + gap)

        x_src_right = 26.0
        x_src_left = 14.0
        x_tgt_left = 74.0
        x_tgt_right = 86.0

        # Draw connecting Bézier ribbons
        src_curr_flow_y = {s: src_y[s][1] for s in states}
        tgt_curr_flow_y = {s: tgt_y[s][1] for s in states}

        for s1 in states:
            s1_total = max(1, src_totals[s1])
            s1_h = src_y[s1][1] - src_y[s1][0]
            for s2 in states:
                cnt = trans[s1][s2]
                if cnt == 0:
                    continue
                s2_total = max(1, tgt_totals[s2])
                s2_h = tgt_y[s2][1] - tgt_y[s2][0]

                flow_h_src = (cnt / s1_total) * s1_h
                flow_h_tgt = (cnt / s2_total) * s2_h

                y_s_top = src_curr_flow_y[s1]
                y_s_bot = y_s_top - flow_h_src
                src_curr_flow_y[s1] = y_s_bot

                y_t_top = tgt_curr_flow_y[s2]
                y_t_bot = y_t_top - flow_h_tgt
                tgt_curr_flow_y[s2] = y_t_bot

                # Create Bézier Ribbon Path
                c_dx = (x_tgt_left - x_src_right) * 0.5
                verts = [
                    (x_src_right, y_s_top),
                    (x_src_right + c_dx, y_s_top),
                    (x_tgt_left - c_dx, y_t_top),
                    (x_tgt_left, y_t_top),
                    (x_tgt_left, y_t_bot),
                    (x_tgt_left - c_dx, y_t_bot),
                    (x_src_right + c_dx, y_s_bot),
                    (x_src_right, y_s_bot),
                    (x_src_right, y_s_top),
                ]
                codes = [
                    MplPath.MOVETO,
                    MplPath.CURVE4,
                    MplPath.CURVE4,
                    MplPath.CURVE4,
                    MplPath.LINETO,
                    MplPath.CURVE4,
                    MplPath.CURVE4,
                    MplPath.CURVE4,
                    MplPath.CLOSEPOLY,
                ]
                path = MplPath(verts, codes)
                patch = mpatches.PathPatch(path, facecolor=color_map[s1], edgecolor=color_map[s1], alpha=0.36, lw=0.5)
                ax.add_patch(patch)

        # Draw Source Nodes (Left)
        for s in states:
            y_bot, y_top = src_y[s]
            h = y_top - y_bot
            rect = mpatches.FancyBboxPatch((x_src_left, y_bot), x_src_right - x_src_left, h, boxstyle="round,pad=0.2", facecolor=color_map[s], edgecolor="#FFFDF6", linewidth=1.5)
            ax.add_patch(rect)
            ax.text(
                x_src_left - 1.5, y_bot + h / 2.0,
                f"{state_labels[s]}\n({src_totals[s]})",
                ha="right", va="center", fontsize=8, fontweight="bold", color="#292A2D"
            )

        # Draw Target Nodes (Right)
        for s in states:
            y_bot, y_top = tgt_y[s]
            h = y_top - y_bot
            rect = mpatches.FancyBboxPatch((x_tgt_left, y_bot), x_tgt_right - x_tgt_left, h, boxstyle="round,pad=0.2", facecolor=color_map[s], edgecolor="#FFFDF6", linewidth=1.5)
            ax.add_patch(rect)
            ax.text(
                x_tgt_right + 1.5, y_bot + h / 2.0,
                f"{state_labels[s]}\n({tgt_totals[s]})",
                ha="left", va="center", fontsize=8, fontweight="bold", color="#292A2D"
            )

        # Column Headers
        ax.text((x_src_left + x_src_right) / 2.0, 98.0, "Initial State (Turn t)", ha="center", va="center", fontsize=9, fontweight="bold", color="#292A2D")
        ax.text((x_tgt_left + x_tgt_right) / 2.0, 98.0, "Next State (Turn t+1)", ha="center", va="center", fontsize=9, fontweight="bold", color="#292A2D")

        # Specific Neutral Evolution Callout
        neu_total = src_totals["neutral"]
        if neu_total > 0:
            n_pos = trans["neutral"]["positive"]
            n_neg = trans["neutral"]["negative"]
            n_neu = trans["neutral"]["neutral"]
            p_pos = (n_pos / neu_total) * 100.0
            p_neg = (n_neg / neu_total) * 100.0
            p_neu = (n_neu / neu_total) * 100.0
            insight = f"Neutral Evolution Dynamics: {n_pos} ({p_pos:.0f}%) -> Positive  •  {n_neg} ({p_neg:.0f}%) -> Negative  •  {n_neu} ({p_neu:.0f}%) -> Neutral"
        else:
            insight = "Neutral Evolution: No neutral initial states detected in this dialogue."

        bbox_props = dict(boxstyle="round,pad=0.5", facecolor="#FFFDF6", edgecolor="#E8E4D9", alpha=0.95)
        ax.text(50.0, 4.0, insight, ha="center", va="center", fontsize=8, fontweight="bold", color="#292A2D", bbox=bbox_props)

        ax.set_title("Sentiment Sankey Flow — Evolution of Sentiments Over Time", fontsize=11, fontweight="bold", pad=12, color="#292A2D")

        self.fig.tight_layout()
        self.canvas.draw()

    def _render_messages_table(self, df: pd.DataFrame, stats: Dict[str, Any]):
        for item in self.msg_tree.get_children():
            self.msg_tree.delete(item)

        tp_indices = {tp["turn_index"]: tp["delta"] for tp in stats.get("turning_points", [])}

        for idx, row in df.iterrows():
            sent = row["pred_sentiment"]
            is_tp = idx in tp_indices

            # Filtering logic
            if self.active_filter == "positive" and sent != "positive":
                continue
            elif self.active_filter == "neutral" and sent != "neutral":
                continue
            elif self.active_filter == "negative" and sent != "negative":
                continue
            elif self.active_filter == "shifts" and not is_tp:
                continue

            symbol = "[▲] Pos" if sent == "positive" else ("[▼] Neg" if sent == "negative" else "[●] Neu")
            tp_str = f"⚡ SHIFT ({tp_indices[idx]:+.2f})" if is_tp else ""

            self.msg_tree.insert(
                "",
                "end",
                values=(
                    idx,
                    row["speaker"],
                    symbol,
                    f"{row['polarity_score']:+.4f}",
                    f"{row['prob_negative']:.2f}",
                    f"{row['prob_neutral']:.2f}",
                    f"{row['prob_positive']:.2f}",
                    tp_str,
                    row["text"]
                )
            )

        self.detail_text.delete("1.0", tk.END)
        self.detail_text.insert("1.0", "Select a turn above to inspect full message text and its preceding conversational context window.")

    def _render_report_text(self, explanation: Dict[str, Any]):
        self.report_box.delete("1.0", tk.END)
        if not explanation:
            self.report_box.insert("1.0", "No explanation generated.")
            return

        lines = [
            "=" * 74,
            "CONVERSATION SENTIMENT TRAJECTORY & SHIFT EXPLANATION REPORT",
            "=" * 74,
            "",
            "1. EXECUTIVE OVERVIEW",
            f"   • Overall Pattern:       {explanation.get('summary_description', 'N/A')}",
            f"   • Total Analyzed Turns:  {explanation.get('total_turns', 0)}",
            f"   • Mean Polarity:         {explanation.get('mean_polarity', 0.0):+.4f}",
            f"   • Net Score Drift:       {explanation.get('net_change', 0.0):+.4f}",
            f"   • Emotional Volatility:  {explanation.get('volatility', 0.0):.4f}",
            "",
            "2. CANDIDATE TURNING POINTS (Algorithmic Shifts)",
        ]

        tps = explanation.get("turning_points", [])
        if not tps:
            lines.append("   • No dramatic emotional turning points detected at current threshold.")
        else:
            for i, tp in enumerate(tps, 1):
                lines.append(f"   [{i}] Turn {tp['turn_index']} — {tp['speaker']} (Shift: {tp['delta']:+.2f})")
                lines.append(f"       Message: \"{tp['text']}\"")
                lines.append(f"       Score Before: {tp['score_before']:+.2f}  ==>  Score After: {tp['score_after']:+.2f}")
                lines.append(f"       Preceding Conversational Context:")
                for ctx_msg in tp.get("preceding_context", []):
                    lines.append(f"         > {ctx_msg}")
                lines.append("")

        lines.extend([
            "3. SPEAKER DYNAMICS",
        ])
        spk_stats = explanation.get("speaker_statistics", {})
        for spk, s_data in spk_stats.items():
            lines.append(f"   • {spk}:")
            lines.append(f"       Turn Share: {s_data.get('turns', 0)} ({s_data.get('turn_percentage', 0.0):.1f}% of conversation)")
            lines.append(f"       Mean Polarity: {s_data.get('mean_polarity', 0.0):+.3f}")
            lines.append(f"       Dominant Sentiment: {s_data.get('dominant_sentiment', 'N/A').capitalize()}")

        lines.extend([
            "",
            "4. SCIENTIFIC BOUNDARIES & EPISTEMIC DISCLAIMER",
            f"   {explanation.get('epistemic_disclaimer', 'This trajectory is an algorithmic model indicator and does not reflect clinical emotional truth.')}",
            "",
            "=" * 74
        ])

        self.report_box.insert("1.0", "\n".join(lines))

    # Export Handlers
    def _export_csv_action(self):
        if not self.current_analysis_result:
            messagebox.showwarning("No Data", "Please run an analysis first.")
            return

        fpath = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if not fpath:
            return

        df = self.current_analysis_result["predictions_df"].copy()
        # Risk #87 defense against formula injection
        for col in ["text", "speaker", "pred_sentiment"]:
            if col in df.columns:
                df[col] = df[col].astype(str).apply(
                    lambda x: f"'{x}" if x.startswith(("=", "+", "-", "@")) else x
                )

        df.to_csv(fpath, index=False, encoding="utf-8")
        messagebox.showinfo("Export Complete", f"Data safely exported to:\n{fpath}")

    def _export_report_action(self):
        if not self.current_analysis_result:
            messagebox.showwarning("No Data", "Please run an analysis first.")
            return

        fpath = filedialog.asksaveasfilename(defaultextension=".md", filetypes=[("Markdown files", "*.md"), ("Text files", "*.txt")])
        if not fpath:
            return

        content = self.report_box.get("1.0", tk.END)
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(content)
        messagebox.showinfo("Export Complete", f"Report saved to:\n{fpath}")

    def _export_json_action(self):
        if not self.current_analysis_result:
            messagebox.showwarning("No Data", "Please run an analysis first.")
            return

        fpath = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if not fpath:
            return

        payload = {
            "model_used": self.current_analysis_result["model_used"],
            "trajectory_stats": self.current_analysis_result["trajectory_stats"],
            "explanation": self.current_analysis_result["explanation"],
            "predictions": self.current_analysis_result["predictions_df"].to_dict(orient="records")
        }
        with open(fpath, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        messagebox.showinfo("Export Complete", f"JSON audit exported to:\n{fpath}")

    def _export_chart_action(self):
        if not self.current_analysis_result:
            messagebox.showwarning("No Data", "Please run an analysis first.")
            return

        fpath = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG images", "*.png")])
        if not fpath:
            return

        self.fig.savefig(fpath, dpi=300, bbox_inches="tight")
        messagebox.showinfo("Export Complete", f"Chart saved to:\n{fpath}")

    # =========================================================================
    # SECTION 4: BUILT-IN USER GUIDE & HELP
    # =========================================================================
    def _build_guide_view(self):
        guide_text = scrolledtext.ScrolledText(self.tab_guide, wrap="word", font=("Segoe UI", 10), bg=self.colors["card_bg"], padx=16, pady=16)
        guide_text.pack(fill="both", expand=True)

        guide_content = """
===============================================================================
SENTIMENT TRAJECTORY ANALYSIS — USER GUIDE & REFERENCE
===============================================================================

1. WHAT DOES THIS APPLICATION DO?
-------------------------------------------------------------------------------
Sentiment analysis is a machine learning technique that evaluates individual text 
utterances to predict whether they express positive, neutral, or negative sentiment.

Trajectory analysis examines how those predictions evolve sequentially across 
turns in a conversation. By tracking turn-by-turn polarity and detecting significant 
shifts, the system maps the conversational arc and provides an evidence-based 
written explanation.

2. STEP-BY-STEP WALKTHROUGH
-------------------------------------------------------------------------------
Step 1: Choose Your Input Method
  • Paste Text: Enter messages in 'Speaker: Message' format.
  • WhatsApp (.txt): Upload an exported WhatsApp chat file.
  • CSV File: Upload a structured dataset with turn_id, speaker, and text columns.
  • Demo Preset: Pick one of our preloaded benchmark dialogues.

Step 2: Review and Prepare
  • Check the 'Step 2' pane on the right side of the workspace.
  • Confirm that the messages were parsed into correct turns and speaker names.

Step 3: Configure Settings (Optional)
  • Choose your model: RoBERTa Context-Aware (recommended) or Baseline.
  • In Advanced Settings, adjust Turning-Point Sensitivity (τ) or Context Window (k).

Step 4: Run Analysis
  • Click '🚀 Analyze Conversation'.
  • View results in the Results Dashboard (Trajectory, Messages, Report, Exports).

3. KEY CONCEPTS & GLOSSARY
-------------------------------------------------------------------------------
• Polarity Score (s_t):
  A continuous mathematical value defined as:
      s_t = P(positive) - P(negative)
  Ranging from -1.0 (strongly negative) to +1.0 (strongly positive). A score near 
  zero indicates either neutral expression or balanced positive/negative probabilities.

• Context Window (k):
  The number of preceding messages prepended to the current utterance during 
  inference. Incorporating previous turns helps the model resolve sarcasm, pronouns, 
  and conversational replies.

• Turning Point (Candidate Shift):
  An inflection point where the turn-to-turn delta |Δs| exceeds the configured 
  sensitivity threshold τ, or where a sign reversal across neutral occurs.

• Volatility (σ):
  The standard deviation of score changes (Δs) across the conversation. High 
  volatility indicates frequent emotional fluctuations; low volatility indicates 
  emotional stability.

4. SCIENTIFIC ACCURACY & LIMITATIONS
-------------------------------------------------------------------------------
• The polarity score is a model output, NOT a direct biological measurement of a 
  person's internal thoughts or medical emotion.
• Sarcasm, cultural idioms, and non-verbal cues (prosody, facial expression) may 
  affect accuracy.
• A turning point is an algorithmic flag, not proof of real-world causal conflict.

===============================================================================
"""
        guide_text.insert("1.0", guide_content.strip())
        guide_text.config(state="disabled")

    def _build_status_bar(self):
        status_bar = ttk.Frame(self.root, relief="sunken", padding="8 4 8 4")
        status_bar.pack(side="bottom", fill="x")

        self.status_var = tk.StringVar(value="Ready.")
        ttk.Label(status_bar, textvariable=self.status_var, font=("Segoe UI", 9)).pack(side="left")

        self.progress = ttk.Progressbar(status_bar, mode="indeterminate", length=160)


def main():
    root = tk.Tk()
    app = SentimentTrajectoryDesktopApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
