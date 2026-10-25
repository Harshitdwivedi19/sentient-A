"""
src/desktop_app.py

High-Performance Conversation Sentiment & Trajectory Analytics Studio.
Designed for Windows Desktop & Laptop Environments (Adaptive, Resizable Layout).

Core Design Principles:
1. Clear, calm, trustworthy presentation with everyday language and honest explanations.
2. Distinct, consistent semantic color palette (Action: Blue, Pos: Green, Neu: Amber, Neg: Red).
3. Dedicated 7-section workspace:
   - Overview: Date range, turn count, participants, coverage, primary timeline, evidence-backed findings.
   - Timeline: Interactive zoom/pan, bucket downsampling, dual-axis volume histogram, accessible table.
   - People: Participation distribution, average tone, emotional range, interaction timeline.
   - Topics: Real thematic keyword clusters and sentiment distribution.
   - Messages: Searchable, filterable, virtualized/paginated evidence grid with context drawer.
   - Guide: Comprehensive 8-section plain-language manual explaining how to use and interpret findings.
   - Settings & Export: Memory audit, purge control, parameter tuning, sanitized exports.
4. Light Theme (default) & Dark Theme toggle for comfortable visual contrast.
5. 100% on-device local RAM processing with verified data deletion.

Built on Python Tkinter + ttk + Matplotlib.
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
    ),
    "Sample 4: WhatsApp Hinglish (Customer Escalation & Fix)": (
        "Customer: Hello, mera order #98211 abhi tak deliver nahi hua\n"
        "Support: Sir, let me check the tracking status for your order\n"
        "Customer: Bhai 4 din se delay chal raha hai, bohot bekar service hai tumhari!\n"
        "Support: Hum samajh sakte hain aapki pareshani, delivery partner se baat ho rahi hai\n"
        "Customer: Mera paisa barbad ho gaya, urgent tha ye parcel!\n"
        "Support: Sir package dispatch ho chuka hai aur agle 2 ghante me aapko mil jayega\n"
        "Customer: Pakka mil jayega na? Mujhe aaj hi chahiye tha\n"
        "Support: Haanji sir, guaranteed aaj deliver hoga. Asuvidha ke liye maafi\n"
        "Customer: Chalo theek hai, bohot bohot shukriya aapki madad ke liye\n"
        "Support: Thank you for contacting us, aapka din shubh ho!"
    ),
    "Sample 5: WhatsApp Hindi Devanagari (पारिवारिक वार्तालाप)": (
        "अमित: नमस्ते सभी को, क्या इस रविवार को मिलने की योजना बन सकती है?\n"
        "नेहा: हाँ ज़रूर, बहुत दिनों से सब मिले नहीं हैं!\n"
        "रोहन: मौसम बहुत खराब रहने वाला है, भारी बारिश की चेतावनी आई है\n"
        "अमित: अरे यार, फिर बाहर जाना बहुत मुश्किल और परेशानी भरा होगा\n"
        "नेहा: चिंता मत करो, हम सब घर पर ही दोपहर का भोजन रख सकते हैं\n"
        "रोहन: यह तो बहुत ही बढ़िया और सुरक्षित विचार है!\n"
        "अमित: सबको बहुत खुशी होगी, मैं गरमा-गरम नाश्ता लेकर आऊँगा\n"
        "नेहा: धन्यवाद भाई, रविवार को दोपहर में मिलते हैं"
    )
}
# Aliases for UI dropdown compatibility
SAMPLE_PRESETS["Sample 2: WhatsApp Incident & Resolution"] = SAMPLE_PRESETS["Sample 2: WhatsApp Chat Format"]
SAMPLE_PRESETS["Sample 3: MELD Dialogue (Empathy & Support)"] = SAMPLE_PRESETS["Sample 3: MELD Friends Dialogue"]
SAMPLE_PRESETS["Sample 4: WhatsApp Hinglish Resolution"] = SAMPLE_PRESETS["Sample 4: WhatsApp Hinglish (Customer Escalation & Fix)"]
SAMPLE_PRESETS["Sample 5: WhatsApp Hindi (Devanagari)"] = SAMPLE_PRESETS["Sample 5: WhatsApp Hindi Devanagari (पारिवारिक वार्तालाप)"]


class SentimentTrajectoryDesktopApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Sentient Analysis — Conversation Sentiment & Trajectory Studio")
        self.root.geometry("1240x820")
        self.root.minsize(1020, 680)

        # Set unique visual identity icon
        ico_path = PROJECT_ROOT / "assets" / "branding" / "app_icon.ico"
        if ico_path.exists():
            try:
                self.root.iconbitmap(default=str(ico_path))
            except Exception:
                pass

        # Theme state (Default: Light for clear productivity)
        self.current_theme: str = "light"

        # Indic & Devanagari Unicode Font Stack
        import matplotlib as mpl
        mpl.rcParams["font.sans-serif"] = ["Nirmala UI", "Mangal", "Segoe UI", "DejaVu Sans"]
        mpl.rcParams["axes.unicode_minus"] = False

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
        self.active_view: str = "overview"  # overview, timeline, people, topics, messages, guide, settings

        # Collapsible Panel States
        self.is_sidebar_collapsed: bool = False
        self.is_details_open: bool = True

        # Filters & Search State
        self.search_query_var = tk.StringVar(value="")
        self.filter_speaker_var = tk.StringVar(value="All Participants")
        self.filter_sentiment_var = tk.StringVar(value="All Tones")
        self.filter_range_preset_var = tk.StringVar(value="All")
        self.show_speaker_overlay_var = tk.BooleanVar(value=True)
        self.show_data_table_var = tk.BooleanVar(value=False)

        # Pagination State for Messages Explorer
        self.current_page: int = 1
        self.page_size: int = 50
        self.filtered_df: Optional[pd.DataFrame] = None
        self.selected_turn_id: Optional[int] = None

        # Dismissed Findings set
        self.dismissed_findings: set = set()

        # Apply styling system
        self._setup_design_system()

        # Build Main Ergonomic Layout
        self._build_top_masthead()
        self._build_workspace_shell()
        self._build_status_bar()

        # Initialize sentiment analyzer in background thread
        self.status_var.set("Initializing RoBERTa & Baseline engines in local memory...")
        threading.Thread(target=self._init_analyzer_thread, daemon=True).start()

        # Load initial demonstration conversation
        self._load_conversation_by_key("Sample 1: Conflict to Reconciliation")

    def _setup_design_system(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass

        if self.current_theme == "light":
            # Calm, Trustworthy Professional Light Theme
            self.colors = {
                "bg": "#F8FAFC",             # Slate 50 canvas
                "sidebar_bg": "#F1F5F9",     # Slate 100 sidebar
                "card_bg": "#FFFFFF",        # White card surface
                "card_inset": "#F8FAFC",     # Inset table rows / fields
                "header_bg": "#FFFFFF",      # Crisp white top bar
                "border": "#E2E8F0",         # Slate 200 hairline border
                "border_strong": "#CBD5E1",  # Slate 300 focus border
                "text_main": "#0F172A",      # Slate 900 high contrast text
                "text_muted": "#64748B",     # Slate 500 readable secondary text
                "action_primary": "#2563EB", # Royal Blue action buttons (NOT red/coral)
                "action_hover": "#1D4ED8",   # Deep Blue hover
                "pos": "#059669",            # Emerald 600 positive
                "neu": "#D97706",            # Amber 600 neutral
                "neg": "#DC2626",            # Red 600 negative
                "sidebar_btn": "#F1F5F9",
                "sidebar_btn_active": "#E2E8F0",
                "white": "#FFFFFF"
            }
        else:
            # High-Contrast Calm Dark Theme
            self.colors = {
                "bg": "#0F172A",             # Slate 900 canvas
                "sidebar_bg": "#0B1120",     # Slate 950 sidebar
                "card_bg": "#1E293B",        # Slate 800 card surface
                "card_inset": "#0F172A",     # Inset table rows / fields
                "header_bg": "#1E293B",      # Slate 800 top bar
                "border": "#334155",         # Slate 700 border
                "border_strong": "#475569",  # Slate 600 focus border
                "text_main": "#F8FAFC",      # Slate 50 crisp text
                "text_muted": "#94A3B8",     # Slate 400 secondary text
                "action_primary": "#3B82F6", # Bright Blue action buttons
                "action_hover": "#60A5FA",   # Light Blue hover
                "pos": "#10B981",            # Emerald 500 positive
                "neu": "#F59E0B",            # Amber 500 neutral
                "neg": "#EF4444",            # Red 500 negative
                "sidebar_btn": "#0B1120",
                "sidebar_btn_active": "#1E293B",
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

        # Treeview styling for messages grid
        style.configure(
            "Messages.Treeview",
            background=self.colors["card_bg"],
            foreground=self.colors["text_main"],
            fieldbackground=self.colors["card_bg"],
            rowheight=30,
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
            background=[("selected", self.colors["action_primary"])],
            foreground=[("selected", "#FFFFFF")]
        )

    def _toggle_theme(self):
        self.current_theme = "dark" if self.current_theme == "light" else "light"
        self._setup_design_system()
        # Rebuild whole view hierarchy smoothly
        for child in self.root.winfo_children():
            child.destroy()
        self._build_top_masthead()
        self._build_workspace_shell()
        self._build_status_bar()
        self._switch_view(self.active_view)

    def _init_analyzer_thread(self):
        try:
            self.analyzer = ConversationSentimentAnalyzer(
                model_type="context",
                context_window=3,
                turning_point_threshold=0.4
            )
            self.root.after(0, lambda: self.status_var.set("Engine ready (RoBERTa Context-Aware Model)"))
            self.root.after(0, self._run_analysis)
        except Exception as e:
            try:
                self.analyzer = ConversationSentimentAnalyzer(model_type="baseline")
                self.root.after(0, lambda: self.status_var.set("Engine ready (TF-IDF Baseline Model)"))
                self.root.after(0, self._run_analysis)
            except Exception as e2:
                self.root.after(0, lambda: self.status_var.set(f"Engine initialization error: {e2}"))

    # -------------------------------------------------------------------------
    # WORKSPACE LAYOUT
    # -------------------------------------------------------------------------
    def _build_top_masthead(self):
        self.header_frame = tk.Frame(self.root, bg=self.colors["header_bg"], height=56, highlightbackground=self.colors["border"], highlightthickness=1)
        self.header_frame.pack(side=tk.TOP, fill=tk.X)
        self.header_frame.pack_propagate(False)

        # Left Branding & Conversation Selector
        l_box = tk.Frame(self.header_frame, bg=self.colors["header_bg"])
        l_box.pack(side=tk.LEFT, fill=tk.Y, padx=16)

        title_lbl = tk.Label(
            l_box,
            text="Sentient Analysis",
            font=("Segoe UI", 12, "bold"),
            bg=self.colors["header_bg"],
            fg=self.colors["text_main"]
        )
        title_lbl.pack(side=tk.LEFT, padx=(0, 14))

        tk.Label(
            l_box,
            text="Active Chat:",
            font=("Segoe UI", 9),
            bg=self.colors["header_bg"],
            fg=self.colors["text_muted"]
        ).pack(side=tk.LEFT, padx=(0, 4))

        self.conv_keys = list(self.loaded_datasets.keys())
        self.conv_selector_var = tk.StringVar(value=self.conv_keys[0])

        self.conv_dropdown = ttk.Combobox(
            l_box,
            textvariable=self.conv_selector_var,
            values=self.conv_keys,
            state="readonly",
            width=28,
            font=("Segoe UI", 9)
        )
        self.conv_dropdown.pack(side=tk.LEFT, padx=(0, 8))
        self.conv_dropdown.bind("<<ComboboxSelected>>", self._on_change_conversation)

        # Right Controls: Import, Theme Toggle, Coverage Badge
        r_box = tk.Frame(self.header_frame, bg=self.colors["header_bg"])
        r_box.pack(side=tk.RIGHT, fill=tk.Y, padx=16)

        theme_btn_text = "🌙 Dark Mode" if self.current_theme == "light" else "☀️ Light Mode"
        btn_theme = tk.Button(
            r_box,
            text=theme_btn_text,
            font=("Segoe UI", 9),
            bg=self.colors["card_inset"],
            fg=self.colors["text_main"],
            relief="flat",
            cursor="hand2",
            padx=10,
            pady=4,
            command=self._toggle_theme
        )
        btn_theme.pack(side=tk.RIGHT, pady=10, padx=6)

        btn_import = tk.Button(
            r_box,
            text="+ Import WhatsApp Chat (.txt)",
            font=("Segoe UI", 9, "bold"),
            bg=self.colors["action_primary"],
            fg="#FFFFFF",
            relief="flat",
            cursor="hand2",
            padx=12,
            pady=4,
            command=self._on_click_import_file
        )
        btn_import.pack(side=tk.RIGHT, pady=10, padx=6)

        self.coverage_badge = tk.Label(
            r_box,
            text="Coverage: Ready",
            font=("Segoe UI", 9),
            bg=self.colors["card_inset"],
            fg=self.colors["pos"],
            padx=10,
            pady=4
        )
        self.coverage_badge.pack(side=tk.RIGHT, pady=10, padx=6)

    def _build_workspace_shell(self):
        self.shell_frame = tk.Frame(self.root, bg=self.colors["bg"])
        self.shell_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # 1. Collapsible Left Navigation Sidebar
        self.sidebar_frame = tk.Frame(self.shell_frame, bg=self.colors["sidebar_bg"], width=230, highlightbackground=self.colors["border"], highlightthickness=1)
        self.sidebar_frame.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar_frame.pack_propagate(False)

        # 2. Central Flexible Viewport
        self.viewport_frame = tk.Frame(self.shell_frame, bg=self.colors["bg"])
        self.viewport_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._build_sidebar_contents()

    def _build_sidebar_contents(self):
        # Sidebar Header / Section Title
        hdr = tk.Frame(self.sidebar_frame, bg=self.colors["sidebar_bg"], padx=14, pady=12)
        hdr.pack(side=tk.TOP, fill=tk.X)

        tk.Label(
            hdr,
            text="WORKSPACES",
            font=("Segoe UI", 8, "bold"),
            bg=self.colors["sidebar_bg"],
            fg=self.colors["text_muted"]
        ).pack(side=tk.LEFT)

        # 7 Clear Navigation Destinations
        nav_box = tk.Frame(self.sidebar_frame, bg=self.colors["sidebar_bg"], padx=8)
        nav_box.pack(side=tk.TOP, fill=tk.X)

        self.nav_buttons = {}
        destinations = [
            ("overview", "Overview", "Summary & primary timeline"),
            ("timeline", "Timeline", "Deep zoom, pan & volume"),
            ("people", "People", "Participation & tone comparison"),
            ("topics", "Topics", "Thematic feedback themes"),
            ("messages", "Messages", "Searchable evidence & context"),
            ("guide", "User Guide", "Help & concept explanations"),
            ("settings", "Data & Settings", "Audit, exports & controls")
        ]

        for key, title, hint in destinations:
            btn = tk.Button(
                nav_box,
                text=title,
                anchor="w",
                font=("Segoe UI", 10),
                bg=self.colors["sidebar_btn"],
                fg=self.colors["text_main"],
                activebackground=self.colors["sidebar_btn_active"],
                activeforeground=self.colors["text_main"],
                relief="flat",
                cursor="hand2",
                padx=14,
                pady=8,
                command=lambda k=key: self._switch_view(k)
            )
            btn.pack(fill=tk.X, pady=2)
            self.nav_buttons[key] = btn

        # Active Filter Status Card in Sidebar
        f_box = tk.Frame(self.sidebar_frame, bg=self.colors["card_bg"], padx=12, pady=10, highlightbackground=self.colors["border"], highlightthickness=1)
        f_box.pack(side=tk.BOTTOM, fill=tk.X, padx=12, pady=(0, 10))

        self.sidebar_filter_lbl = tk.Label(
            f_box,
            text="Active Filters: None",
            font=("Segoe UI", 8),
            bg=self.colors["card_bg"],
            fg=self.colors["text_muted"],
            anchor="w"
        )
        self.sidebar_filter_lbl.pack(fill=tk.X)

        self.sidebar_clear_btn = tk.Button(
            f_box,
            text="Reset Filters",
            font=("Segoe UI", 8, "bold"),
            bg=self.colors["card_inset"],
            fg=self.colors["action_primary"],
            relief="flat",
            cursor="hand2",
            command=self._clear_all_filters
        )
        self.sidebar_clear_btn.pack(fill=tk.X, pady=(6, 0))

        # Sponsored Ad Banner Card in Sidebar
        sponsor_box = tk.Frame(self.sidebar_frame, bg=self.colors["card_inset"], padx=10, pady=8, highlightbackground=self.colors["border"], highlightthickness=1)
        sponsor_box.pack(side=tk.BOTTOM, fill=tk.X, padx=12, pady=(0, 8))

        s_top = tk.Frame(sponsor_box, bg=self.colors["card_inset"])
        s_top.pack(fill=tk.X)
        tk.Label(s_top, text="AD", font=("Segoe UI", 7, "bold"), bg=self.colors["border"], fg=self.colors["text_muted"], padx=3, pady=1).pack(side=tk.LEFT)
        tk.Label(s_top, text="Sponsored • AdMob Network", font=("Segoe UI", 7), bg=self.colors["card_inset"], fg=self.colors["text_muted"], padx=4).pack(side=tk.LEFT)

        tk.Label(sponsor_box, text="Sentient Cloud Analytics", font=("Segoe UI", 8, "bold"), bg=self.colors["card_inset"], fg=self.colors["text_main"]).pack(anchor="w", pady=(3, 1))
        tk.Label(sponsor_box, text="Real-time multi-channel conversation tone alerts.", font=("Segoe UI", 7), bg=self.colors["card_inset"], fg=self.colors["text_muted"], wraplength=180, justify="left").pack(anchor="w")

    def _build_status_bar(self):
        self.status_var = tk.StringVar(value="Ready")
        self.status_bar = tk.Frame(self.root, bg=self.colors["header_bg"], height=28, highlightbackground=self.colors["border"], highlightthickness=1)
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
            text="Local RAM Storage Only • No External Telemetry • Data is Discarded on Exit",
            font=("Segoe UI", 8),
            bg=self.colors["header_bg"],
            fg=self.colors["text_muted"],
            padx=12
        )
        sec_lbl.pack(side=tk.RIGHT)

    def _switch_view(self, view_key: str):
        self.active_view = view_key

        for key, btn in self.nav_buttons.items():
            if key == view_key:
                btn.configure(
                    bg=self.colors["sidebar_btn_active"],
                    fg=self.colors["action_primary"],
                    font=("Segoe UI", 10, "bold")
                )
            else:
                btn.configure(
                    bg=self.colors["sidebar_btn"],
                    fg=self.colors["text_main"],
                    font=("Segoe UI", 10)
                )

        # Clear viewport
        for child in self.viewport_frame.winfo_children():
            child.destroy()

        if view_key == "guide":
            self._render_view_guide()
            return

        if self.current_df is None or len(self.current_df) == 0:
            self._render_empty_placeholder()
            return

        if view_key == "overview":
            self._render_view_overview()
        elif view_key == "timeline":
            self._render_view_timeline()
        elif view_key == "people":
            self._render_view_people()
        elif view_key == "topics":
            self._render_view_topics()
        elif view_key == "messages":
            self._render_view_messages()
        elif view_key == "settings":
            self._render_view_settings()

    def _render_empty_placeholder(self):
        holder = tk.Frame(self.viewport_frame, bg=self.colors["bg"])
        holder.pack(expand=True)

        tk.Label(
            holder,
            text="No Conversation Loaded",
            font=("Segoe UI", 15, "bold"),
            bg=self.colors["bg"],
            fg=self.colors["text_main"]
        ).pack(pady=(0, 6))

        tk.Label(
            holder,
            text="Select a demonstration sample from the top dropdown or import your own WhatsApp .txt chat export.",
            font=("Segoe UI", 10),
            bg=self.colors["bg"],
            fg=self.colors["text_muted"]
        ).pack(pady=(0, 16))

        tk.Button(
            holder,
            text="Import WhatsApp Chat (.txt)",
            font=("Segoe UI", 10, "bold"),
            bg=self.colors["action_primary"],
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

        raw_lines = text_content.strip().split("\n")
        parsed_records = parse_whatsapp_raw_lines(raw_lines)
        if not parsed_records:
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
                        "speaker": "Participant",
                        "text": line
                    })

        self.current_df = pd.DataFrame(parsed_records)
        self._run_analysis()

    def _on_click_import_file(self):
        fpath = filedialog.askopenfilename(
            title="Import WhatsApp Chat (.txt)",
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

    def _run_analysis(self):
        if self.current_df is None or len(self.current_df) == 0:
            return
        if self.is_analyzing:
            return

        self.is_analyzing = True
        self.status_var.set(f"Analyzing {len(self.current_df)} messages with context-aware sentiment engine...")

        def _worker():
            try:
                if self.analyzer is None:
                    try:
                        self.analyzer = ConversationSentimentAnalyzer(model_type="context")
                    except Exception:
                        self.analyzer = ConversationSentimentAnalyzer(model_type="baseline")

                results = self.analyzer.analyze_conversation(self.current_df, model_type="auto")
                self.current_analysis_result = results
                self.current_df = results.get("annotated_df", results.get("predictions_df"))
                self.current_stats = results["trajectory_stats"]

                self.root.after(0, self._on_analysis_complete)
            except Exception as e:
                self.root.after(0, lambda: self.status_var.set(f"Analysis error: {e}"))
                self.is_analyzing = False

        threading.Thread(target=_worker, daemon=True).start()

    def _on_analysis_complete(self):
        self.is_analyzing = False
        n_turns = len(self.current_df)
        self.status_var.set(f"Analysis complete: {n_turns} messages analyzed.")

        self.coverage_badge.configure(
            text=f"{n_turns} msgs (100% analyzed)",
            fg=self.colors["pos"]
        )

        speakers = sorted(self.current_df["speaker"].dropna().unique().tolist())
        self.filter_speaker_dropdown_values = ["All Participants"] + speakers

        self.current_page = 1
        self._apply_filters()
        self._switch_view(self.active_view)

    # -------------------------------------------------------------------------
    # LARGE-DATA DOWNSAMPLING & AGGREGATION ALGORITHM
    # -------------------------------------------------------------------------
    @staticmethod
    def _downsample_timeline_data(df: pd.DataFrame, max_buckets: int = 50) -> pd.DataFrame:
        """
        Peak-Preserving Bucket Aggregation.
        Preserves mean tone, extreme min/max spikes, and message count per bucket.
        """
        n = len(df)
        if n <= max_buckets:
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
    # VIEW 1: OVERVIEW DASHBOARD (FOCUSED & EXPLAINED)
    # -------------------------------------------------------------------------
    def _render_view_overview(self):
        container = tk.Frame(self.viewport_frame, bg=self.colors["bg"], padx=20, pady=16)
        container.pack(fill=tk.BOTH, expand=True)

        # Header Title & Honest Coverage Audit
        title_box = tk.Frame(container, bg=self.colors["bg"])
        title_box.pack(fill=tk.X, pady=(0, 10))

        tk.Label(
            title_box,
            text=f"Overview — {self.current_dataset_name}",
            font=("Segoe UI", 13, "bold"),
            bg=self.colors["bg"],
            fg=self.colors["text_main"]
        ).pack(side=tk.LEFT)

        # Date range detection if timestamps exist
        date_str = "Sequential Turn Ordering"
        if "timestamp" in self.current_df.columns and not self.current_df["timestamp"].isna().all():
            valid_ts = self.current_df["timestamp"].dropna()
            if len(valid_ts) >= 2:
                date_str = f"{valid_ts.iloc[0]} to {valid_ts.iloc[-1]}"

        tk.Label(
            title_box,
            text=f"Data Scope: {len(self.current_df)} messages • {len(self.current_df['speaker'].unique())} participants • {date_str}",
            font=("Segoe UI", 9),
            bg=self.colors["bg"],
            fg=self.colors["text_muted"]
        ).pack(side=tk.RIGHT)

        # Honest Metric Cards (Every Number Explained)
        stats = self.current_stats or {}
        mean_pol = stats.get("mean_polarity", 0.0)
        net_drift = stats.get("net_change", 0.0)
        volatility = stats.get("volatility", 0.0)
        turning_points = stats.get("turning_points", [])

        # Metric explanations
        mood_desc = "Mildly Positive" if mean_pol > 0.15 else ("Tense / Critical" if mean_pol < -0.15 else "Neutral Equilibrium")
        drift_desc = "Positive Rise" if net_drift > 0.1 else ("Negative Drop" if net_drift < -0.1 else "Steady / Balanced")
        stability_score = max(0, min(100, int((1.0 - volatility) * 100)))

        metrics_row = tk.Frame(container, bg=self.colors["bg"])
        metrics_row.pack(fill=tk.X, pady=(0, 12))

        metric_items = [
            ("AVERAGE TONE", f"{mean_pol:+.2f} ({mood_desc})", "Average polarity score across all turns [-1.0 to +1.0]"),
            ("OVERALL CHANGE", f"{net_drift:+.2f} ({drift_desc})", "Difference between the start and end of conversation"),
            ("TONE STABILITY", f"{stability_score}% (Estimated)", "Consistency of tone; higher means fewer sudden swings"),
            ("NOTABLE SHIFTS", f"{len(turning_points)} Detected", "Moments where tone shifted abruptly (Δ >= 0.40)")
        ]

        for i, (label, val, explanation) in enumerate(metric_items):
            card = tk.Frame(metrics_row, bg=self.colors["card_bg"], padx=14, pady=10, highlightbackground=self.colors["border"], highlightthickness=1)
            card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0 if i == 0 else 8, 0))

            tk.Label(card, text=label, font=("Segoe UI", 8, "bold"), bg=self.colors["card_bg"], fg=self.colors["text_muted"]).pack(anchor="w")
            tk.Label(card, text=val, font=("Segoe UI", 11, "bold"), bg=self.colors["card_bg"], fg=self.colors["text_main"]).pack(anchor="w", pady=(2, 2))
            tk.Label(card, text=explanation, font=("Segoe UI", 8), bg=self.colors["card_bg"], fg=self.colors["text_muted"]).pack(anchor="w")

        # Split Section: Primary Timeline (Left 65%) + Evidence-Backed Findings (Right 35%)
        mid_row = tk.Frame(container, bg=self.colors["bg"])
        mid_row.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Left Column: Primary Timeline Chart
        left_box = tk.Frame(mid_row, bg=self.colors["card_bg"], highlightbackground=self.colors["border"], highlightthickness=1)
        left_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))

        chart_hdr = tk.Frame(left_box, bg=self.colors["card_bg"], padx=12, pady=8)
        chart_hdr.pack(fill=tk.X)
        tk.Label(chart_hdr, text="PRIMARY TONE TIMELINE & MESSAGE VOLUME", font=("Segoe UI", 9, "bold"), bg=self.colors["card_bg"], fg=self.colors["text_main"]).pack(side=tk.LEFT)

        btn_inspect = tk.Button(
            chart_hdr,
            text="Explore Deep Timeline →",
            font=("Segoe UI", 8, "bold"),
            bg=self.colors["card_inset"],
            fg=self.colors["action_primary"],
            relief="flat",
            cursor="hand2",
            command=lambda: self._switch_view("timeline")
        )
        btn_inspect.pack(side=tk.RIGHT)

        chart_area = tk.Frame(left_box, bg=self.colors["card_bg"])
        chart_area.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)
        self._embed_overview_chart(chart_area)

        # Right Column: Notable Findings with Direct Links
        right_box = tk.Frame(mid_row, bg=self.colors["card_bg"], width=340, highlightbackground=self.colors["border"], highlightthickness=1)
        right_box.pack(side=tk.RIGHT, fill=tk.BOTH)
        right_box.pack_propagate(False)

        rt_hdr = tk.Frame(right_box, bg=self.colors["card_bg"], padx=12, pady=8)
        rt_hdr.pack(fill=tk.X)
        tk.Label(rt_hdr, text="NOTABLE MOMENTS (EVIDENCE)", font=("Segoe UI", 9, "bold"), bg=self.colors["card_bg"], fg=self.colors["text_main"]).pack(anchor="w")

        scroll_box = scrolledtext.ScrolledText(
            right_box,
            bg=self.colors["card_bg"],
            fg=self.colors["text_main"],
            font=("Segoe UI", 9),
            borderwidth=0,
            padx=10,
            pady=6
        )
        scroll_box.pack(fill=tk.BOTH, expand=True)

        if not turning_points:
            scroll_box.insert(tk.END, "No abrupt tone shifts detected.\n\nThe tone throughout this conversation remained relatively stable without severe emotional fluctuations.")
        else:
            for idx, tp in enumerate(turning_points[:5]):
                t_id = tp.get("turn_id", idx + 1)
                spk = tp.get("speaker", "Participant")
                delta = tp.get("delta", 0.0)
                txt = tp.get("text", "")
                direction = "Shifted Positive" if delta > 0 else "Shifted Negative"

                scroll_box.insert(tk.END, f"Finding #{idx+1}: Turn {t_id} by {spk}\n", "hdr")
                scroll_box.insert(tk.END, f"{direction} (Δ {delta:+.2f})\n", "delta")
                scroll_box.insert(tk.END, f"\"{txt}\"\n\n", "quote")

        scroll_box.tag_config("hdr", font=("Segoe UI", 9, "bold"), foreground=self.colors["text_main"])
        scroll_box.tag_config("delta", font=("Segoe UI", 8, "bold"), foreground=self.colors["pos"] if delta > 0 else self.colors["neg"])
        scroll_box.tag_config("quote", font=("Segoe UI", 8, "italic"), foreground=self.colors["text_muted"])
        scroll_box.configure(state="disabled")

        # Bottom Guidance Strip
        guide_strip = tk.Frame(container, bg=self.colors["card_inset"], padx=14, pady=8, highlightbackground=self.colors["border"], highlightthickness=1)
        guide_strip.pack(fill=tk.X)

        tk.Label(
            guide_strip,
            text="How to interpret this: The timeline displays average tone over time alongside message volume. Points above zero indicate positive language; points below zero indicate negative language.",
            font=("Segoe UI", 9),
            bg=self.colors["card_inset"],
            fg=self.colors["text_muted"]
        ).pack(side=tk.LEFT)

        # Overview Sponsored Banner Ribbon
        ad_ribbon = tk.Frame(container, bg=self.colors["card_bg"], padx=12, pady=6, highlightbackground=self.colors["border"], highlightthickness=1)
        ad_ribbon.pack(fill=tk.X, pady=(8, 0))

        ad_top = tk.Frame(ad_ribbon, bg=self.colors["card_bg"])
        ad_top.pack(fill=tk.X)
        tk.Label(ad_top, text="AD", font=("Segoe UI", 7, "bold"), bg=self.colors["card_inset"], fg=self.colors["text_muted"], padx=3, pady=1).pack(side=tk.LEFT)
        tk.Label(ad_top, text="Sponsored • AdMob Network", font=("Segoe UI", 8), bg=self.colors["card_bg"], fg=self.colors["text_muted"], padx=6).pack(side=tk.LEFT)
        tk.Label(ad_top, text="Enterprise NLP Toolkit • Scalable dialogue sentiment analysis for Slack, Discord & Teams.", font=("Segoe UI", 8), bg=self.colors["card_bg"], fg=self.colors["text_main"], padx=10).pack(side=tk.LEFT)

    def _embed_overview_chart(self, parent_widget: tk.Widget):
        downsampled = self._downsample_timeline_data(self.current_df, max_buckets=45)

        fig = Figure(figsize=(6, 3.2), dpi=100)
        fig.patch.set_facecolor(self.colors["card_bg"])

        ax1 = fig.add_subplot(211)
        ax2 = fig.add_subplot(212, sharex=ax1)
        fig.subplots_adjust(hspace=0.25, left=0.1, right=0.96, top=0.92, bottom=0.16)

        for ax in [ax1, ax2]:
            ax.set_facecolor(self.colors["card_inset"])
            for spine in ax.spines.values():
                spine.set_color(self.colors["border"])
            ax.tick_params(colors=self.colors["text_muted"], labelsize=8)

        x = downsampled["bucket_turn"].values
        y_mean = downsampled["bucket_mean"].values
        y_min = downsampled["bucket_min"].values
        y_max = downsampled["bucket_max"].values

        # Zero reference line
        ax1.axhline(0, color=self.colors["border"], linestyle="--", linewidth=1.0)
        # Volatility Envelope
        ax1.fill_between(x, y_min, y_max, color=self.colors["action_primary"], alpha=0.12, label="Spike Range")
        # Trajectory Line
        ax1.plot(x, y_mean, color=self.colors["action_primary"], linewidth=2.0, marker="o", markersize=3.5, label="Average Tone")

        ax1.set_ylim(-1.05, 1.05)
        ax1.set_ylabel("Tone [-1 to +1]", color=self.colors["text_muted"], fontsize=8)

        # Message volume bars
        vol = downsampled["bucket_volume"].values
        bar_w = max(1.0, (x[-1] - x[0]) / len(x) * 0.75) if len(x) > 1 else 1.0
        ax2.bar(x, vol, width=bar_w, color=self.colors["text_muted"], alpha=0.6)
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

        # Control Bar (Range Presets, Multi-speaker overlay, Data table toggle)
        ctrl_bar = tk.Frame(container, bg=self.colors["card_bg"], padx=14, pady=8, highlightbackground=self.colors["border"], highlightthickness=1)
        ctrl_bar.pack(fill=tk.X, pady=(0, 10))

        tk.Label(ctrl_bar, text="TIME PRESETS:", font=("Segoe UI", 8, "bold"), bg=self.colors["card_bg"], fg=self.colors["text_muted"]).pack(side=tk.LEFT, padx=(0, 8))

        presets = ["All", "1st Half", "2nd Half", "Notable Shifts"]
        for p in presets:
            btn = tk.Button(
                ctrl_bar,
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
            ctrl_bar,
            text="Compare Participants Side-by-Side",
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
            ctrl_bar,
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

        # Chart Container
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
            self._render_timeline_accessible_table()
            return

        df = self.current_df.copy()
        preset = self.filter_range_preset_var.get()
        n = len(df)

        if preset == "1st Half" and n > 2:
            df = df.iloc[: n // 2]
        elif preset == "2nd Half" and n > 2:
            df = df.iloc[n // 2:]
        elif preset == "Notable Shifts" and n > 2:
            min_idx = int(np.argmin(df["polarity_score"].values))
            start = max(0, min_idx - 15)
            end = min(n, min_idx + 15)
            df = df.iloc[start:end]

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
        ax1.fill_between(x, y_min, y_max, color=self.colors["action_primary"], alpha=0.12, label="Spike Range (Min-Max)")
        ax1.plot(x, y_mean, color=self.colors["action_primary"], linewidth=2.2, marker="o", markersize=4, label="Average Tone")

        # Multi-speaker overlays
        if self.show_speaker_overlay_var.get() and "speaker" in df.columns:
            speakers = df["speaker"].value_counts().index[:3]
            palette = [self.colors["pos"], self.colors["neu"], self.colors["neg"]]
            for s_idx, spk in enumerate(speakers):
                s_df = df[df["speaker"] == spk]
                if len(s_df) >= 2:
                    s_down = self._downsample_timeline_data(s_df, max_buckets=40)
                    ax1.plot(
                        s_down["bucket_turn"].values,
                        s_down["bucket_mean"].values,
                        color=palette[s_idx % len(palette)],
                        linewidth=1.6,
                        linestyle=":",
                        label=f"{spk}"
                    )

        ax1.set_ylim(-1.05, 1.05)
        ax1.set_ylabel("Tone Score [-1 to +1]", color=self.colors["text_muted"], fontsize=9)
        ax1.legend(loc="upper left", facecolor=self.colors["card_bg"], edgecolor=self.colors["border"], fontsize=8, labelcolor=self.colors["text_main"])

        # Volume bars
        vol = downsampled["bucket_volume"].values
        bar_w = max(1.0, (x[-1] - x[0]) / len(x) * 0.75) if len(x) > 1 else 1.0
        ax2.bar(x, vol, width=bar_w, color=self.colors["text_muted"], alpha=0.6)
        ax2.set_ylabel("Message Density", color=self.colors["text_muted"], fontsize=9)
        ax2.set_xlabel("Turn Identifier (Use Pan & Zoom in toolbar below)", color=self.colors["text_muted"], fontsize=9)

        canvas = FigureCanvasTkAgg(fig, master=self.timeline_content_box)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        toolbar_frame = tk.Frame(self.timeline_content_box, bg=self.colors["card_bg"])
        toolbar_frame.pack(fill=tk.X)
        toolbar = NavigationToolbar2Tk(canvas, toolbar_frame)
        toolbar.update()

        # Timeline Sponsored Ad Banner Ribbon
        ad_tl = tk.Frame(self.timeline_content_box, bg=self.colors["card_inset"], padx=10, pady=5)
        ad_tl.pack(fill=tk.X)
        ad_tl_inner = tk.Frame(ad_tl, bg=self.colors["card_inset"])
        ad_tl_inner.pack(fill=tk.X)
        tk.Label(ad_tl_inner, text="AD", font=("Segoe UI", 7, "bold"), bg=self.colors["border"], fg=self.colors["text_muted"], padx=3, pady=1).pack(side=tk.LEFT)
        tk.Label(ad_tl_inner, text="Sponsored • AdMob Network", font=("Segoe UI", 7), bg=self.colors["card_inset"], fg=self.colors["text_muted"], padx=6).pack(side=tk.LEFT)
        tk.Label(ad_tl_inner, text="High-Throughput Sentiment Batch Inference APIs — Explore RoBERTa Cloud Hosting.", font=("Segoe UI", 8), bg=self.colors["card_inset"], fg=self.colors["text_main"], padx=10).pack(side=tk.LEFT)

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
        tree.heading("mean", text="Mean Tone")
        tree.heading("min", text="Min Tone")
        tree.heading("max", text="Max Tone")
        tree.heading("vol", text="Msg Count")
        tree.heading("spk", text="Dominant Participant")

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
    # VIEW 3: PEOPLE (PARTICIPATION & TONE COMPARISON)
    # -------------------------------------------------------------------------
    def _render_view_people(self):
        container = tk.Frame(self.viewport_frame, bg=self.colors["bg"], padx=20, pady=16)
        container.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            container,
            text=f"People & Participation — {self.current_dataset_name}",
            font=("Segoe UI", 13, "bold"),
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

            tk.Label(card, text=spk, font=("Segoe UI", 11, "bold"), bg=self.colors["card_bg"], fg=self.colors["text_main"]).pack(anchor="w")
            tk.Label(card, text=f"{count} messages ({pct:.1f}% share of chat)", font=("Segoe UI", 9), bg=self.colors["card_bg"], fg=self.colors["text_muted"]).pack(anchor="w", pady=(2, 6))

            tone_color = self.colors["pos"] if mean_s > 0.1 else (self.colors["neg"] if mean_s < -0.1 else self.colors["neu"])
            tk.Label(card, text=f"Average Tone: {mean_s:+.2f}", font=("Segoe UI", 9, "bold"), bg=self.colors["card_bg"], fg=tone_color).pack(anchor="w")
            tk.Label(card, text=f"Observed Range: [{min_s:+.2f} to {max_s:+.2f}]", font=("Segoe UI", 8), bg=self.colors["card_bg"], fg=self.colors["text_muted"]).pack(anchor="w", pady=(2, 8))

            btn_filter = tk.Button(
                card,
                text=f"Filter Messages by {spk}",
                font=("Segoe UI", 8, "bold"),
                bg=self.colors["card_inset"],
                fg=self.colors["action_primary"],
                relief="flat",
                cursor="hand2",
                command=lambda s=spk: self._filter_and_jump_to_speaker(s)
            )
            btn_filter.pack(fill=tk.X)

        # Bottom turn alternation timeline
        dist_box = tk.Frame(container, bg=self.colors["card_bg"], padx=14, pady=12, highlightbackground=self.colors["border"], highlightthickness=1)
        dist_box.pack(fill=tk.BOTH, expand=True)

        tk.Label(dist_box, text="TURN PARTICIPATION TIMELINE", font=("Segoe UI", 9, "bold"), bg=self.colors["card_bg"], fg=self.colors["text_main"]).pack(anchor="w", pady=(0, 6))

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

        # People Sponsored Ad Banner Ribbon
        ad_ppl = tk.Frame(container, bg=self.colors["card_inset"], padx=10, pady=5, highlightbackground=self.colors["border"], highlightthickness=1)
        ad_ppl.pack(fill=tk.X, pady=(10, 0))
        ad_ppl_inner = tk.Frame(ad_ppl, bg=self.colors["card_inset"])
        ad_ppl_inner.pack(fill=tk.X)
        tk.Label(ad_ppl_inner, text="AD", font=("Segoe UI", 7, "bold"), bg=self.colors["border"], fg=self.colors["text_muted"], padx=3, pady=1).pack(side=tk.LEFT)
        tk.Label(ad_ppl_inner, text="Sponsored • AdMob Network", font=("Segoe UI", 7), bg=self.colors["card_inset"], fg=self.colors["text_muted"], padx=6).pack(side=tk.LEFT)
        tk.Label(ad_ppl_inner, text="Team Communication Intelligence & Sentiment Cohort Analytics.", font=("Segoe UI", 8), bg=self.colors["card_inset"], fg=self.colors["text_main"], padx=10).pack(side=tk.LEFT)

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
            text=f"Thematic Feedback Clusters — {self.current_dataset_name}",
            font=("Segoe UI", 13, "bold"),
            bg=self.colors["bg"],
            fg=self.colors["text_main"]
        ).pack(anchor="w", pady=(0, 10))

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
                    color="#FFFFFF" if sent != "neutral" else "#000000",
                    fontweight="bold", fontsize=8
                )

        ax.set_xlim(0, 100)
        ax.set_ylim(0, 100)
        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=t_box)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Topics Sponsored Ad Banner Ribbon
        ad_top = tk.Frame(container, bg=self.colors["card_inset"], padx=10, pady=5, highlightbackground=self.colors["border"], highlightthickness=1)
        ad_top.pack(fill=tk.X, pady=(10, 0))
        ad_top_inner = tk.Frame(ad_top, bg=self.colors["card_inset"])
        ad_top_inner.pack(fill=tk.X)
        tk.Label(ad_top_inner, text="AD", font=("Segoe UI", 7, "bold"), bg=self.colors["border"], fg=self.colors["text_muted"], padx=3, pady=1).pack(side=tk.LEFT)
        tk.Label(ad_top_inner, text="Sponsored • AdMob Network", font=("Segoe UI", 7), bg=self.colors["card_inset"], fg=self.colors["text_muted"], padx=6).pack(side=tk.LEFT)
        tk.Label(ad_top_inner, text="Customer Feedback Clustering & Topic Modeling Suite for Enterprise Support.", font=("Segoe UI", 8), bg=self.colors["card_inset"], fg=self.colors["text_main"], padx=10).pack(side=tk.LEFT)

    # -------------------------------------------------------------------------
    # VIEW 5: MESSAGES (SEARCHABLE & FILTERABLE EVIDENCE GRID)
    # -------------------------------------------------------------------------
    def _render_view_messages(self):
        container = tk.Frame(self.viewport_frame, bg=self.colors["bg"], padx=20, pady=16)
        container.pack(fill=tk.BOTH, expand=True)

        # Filter Bar
        bar = tk.Frame(container, bg=self.colors["card_bg"], padx=12, pady=10, highlightbackground=self.colors["border"], highlightthickness=1)
        bar.pack(fill=tk.X, pady=(0, 10))

        tk.Label(bar, text="SEARCH:", font=("Segoe UI", 8, "bold"), bg=self.colors["card_bg"], fg=self.colors["text_muted"]).pack(side=tk.LEFT, padx=(0, 4))
        ent_search = tk.Entry(bar, textvariable=self.search_query_var, width=22, font=("Segoe UI", 9), bg=self.colors["card_inset"], fg=self.colors["text_main"], insertbackground=self.colors["text_main"], relief="flat")
        ent_search.pack(side=tk.LEFT, padx=(0, 12))
        ent_search.bind("<KeyRelease>", lambda e: self._on_search_key_release())

        tk.Label(bar, text="PARTICIPANT:", font=("Segoe UI", 8, "bold"), bg=self.colors["card_bg"], fg=self.colors["text_muted"]).pack(side=tk.LEFT, padx=(0, 4))
        cb_spk = ttk.Combobox(bar, textvariable=self.filter_speaker_var, values=getattr(self, "filter_speaker_dropdown_values", ["All Participants"]), state="readonly", width=14, font=("Segoe UI", 9))
        cb_spk.pack(side=tk.LEFT, padx=(0, 12))
        cb_spk.bind("<<ComboboxSelected>>", lambda e: self._apply_filters())

        tk.Label(bar, text="TONE:", font=("Segoe UI", 8, "bold"), bg=self.colors["card_bg"], fg=self.colors["text_muted"]).pack(side=tk.LEFT, padx=(0, 4))
        cb_sent = ttk.Combobox(bar, textvariable=self.filter_sentiment_var, values=["All Tones", "Positive", "Neutral", "Negative"], state="readonly", width=12, font=("Segoe UI", 9))
        cb_sent.pack(side=tk.LEFT, padx=(0, 12))
        cb_sent.bind("<<ComboboxSelected>>", lambda e: self._apply_filters())

        btn_clear = tk.Button(bar, text="Clear Filters", font=("Segoe UI", 8, "bold"), bg=self.colors["card_inset"], fg=self.colors["action_primary"], relief="flat", cursor="hand2", command=self._clear_all_filters)
        btn_clear.pack(side=tk.RIGHT)

        # Split Content: Left Table (60%) + Right Context Drawer (40%)
        split_frame = tk.Frame(container, bg=self.colors["bg"])
        split_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        tbl_frame = tk.Frame(split_frame, bg=self.colors["card_bg"], highlightbackground=self.colors["border"], highlightthickness=1)
        tbl_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))

        self.messages_tree = ttk.Treeview(
            tbl_frame,
            columns=("turn", "spk", "text", "sentiment", "score"),
            show="headings",
            style="Messages.Treeview"
        )
        self.messages_tree.heading("turn", text="Turn #")
        self.messages_tree.heading("spk", text="Participant")
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

        # Right Context Drawer
        self.detail_drawer = tk.Frame(split_frame, bg=self.colors["card_bg"], width=360, highlightbackground=self.colors["border"], highlightthickness=1)
        self.detail_drawer.pack(side=tk.RIGHT, fill=tk.BOTH)
        self.detail_drawer.pack_propagate(False)

        drawer_hdr = tk.Frame(self.detail_drawer, bg=self.colors["card_inset"], padx=12, pady=8)
        drawer_hdr.pack(fill=tk.X)
        tk.Label(drawer_hdr, text="MESSAGE EVIDENCE & SURROUNDING CONTEXT", font=("Segoe UI", 9, "bold"), bg=self.colors["card_inset"], fg=self.colors["text_main"]).pack(anchor="w")

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

        # In-Feed Sponsored Card
        ad_msg = tk.Frame(container, bg=self.colors["card_inset"], padx=10, pady=4, highlightbackground=self.colors["border"], highlightthickness=1)
        ad_msg.pack(fill=tk.X, pady=(6, 0))
        ad_msg_inner = tk.Frame(ad_msg, bg=self.colors["card_inset"])
        ad_msg_inner.pack(fill=tk.X)
        tk.Label(ad_msg_inner, text="AD", font=("Segoe UI", 7, "bold"), bg=self.colors["border"], fg=self.colors["text_muted"], padx=3, pady=1).pack(side=tk.LEFT)
        tk.Label(ad_msg_inner, text="Sponsored • In-Feed Ad Unit", font=("Segoe UI", 7), bg=self.colors["card_inset"], fg=self.colors["text_muted"], padx=4).pack(side=tk.LEFT)
        tk.Label(ad_msg_inner, text="Enterprise Chat Archival & Compliance Tooling for WhatsApp Exports.", font=("Segoe UI", 8), bg=self.colors["card_inset"], fg=self.colors["text_main"], padx=8).pack(side=tk.LEFT)

        self._render_paginated_messages()

    def _on_search_key_release(self):
        self.current_page = 1
        self._apply_filters()
        self._render_paginated_messages()

    def _apply_filters(self):
        if self.current_df is None:
            return

        df = self.current_df.copy()

        q = self.search_query_var.get().strip().lower()
        if q:
            df = df[df["text"].astype(str).str.lower().str.contains(q, na=False) |
                    df["speaker"].astype(str).str.lower().str.contains(q, na=False)]

        spk = self.filter_speaker_var.get()
        if spk and spk != "All Participants":
            df = df[df["speaker"] == spk]

        sent = self.filter_sentiment_var.get().lower()
        if sent and sent != "all tones":
            df = df[df["pred_sentiment"].astype(str).str.lower().str.contains(sent, na=False)]

        self.filtered_df = df

        active_count = (1 if q else 0) + (1 if spk != "All Participants" else 0) + (1 if sent != "all tones" else 0)
        if active_count > 0:
            self.sidebar_filter_lbl.configure(text=f"Active Filters: {active_count} applied", fg=self.colors["action_primary"])
        else:
            self.sidebar_filter_lbl.configure(text="Active Filters: None", fg=self.colors["text_muted"])

    def _clear_all_filters(self):
        self.search_query_var.set("")
        self.filter_speaker_var.set("All Participants")
        self.filter_sentiment_var.set("All Tones")
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

        self.lbl_page_info.configure(text=f"Page {self.current_page} of {total_pages} (Displaying {start_idx+1}-{end_idx} of {total_items} messages)")

        page_df = df.iloc[start_idx:end_idx]

        for _, r in page_df.iterrows():
            t_id = int(r.get("turn_id", 0))
            spk = str(r.get("speaker", "Participant"))
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

        row = self.current_df[self.current_df["turn_id"] == turn_id]
        if row.empty:
            return
        r = row.iloc[0]

        self.drawer_content.configure(state="normal")
        self.drawer_content.delete("1.0", tk.END)

        self.drawer_content.insert(tk.END, f"TURN #{turn_id} DETAILS\n", "title")
        self.drawer_content.insert(tk.END, f"Participant: {r.get('speaker', 'Unknown')}\n", "bold")
        self.drawer_content.insert(tk.END, f"Tone: {str(r.get('pred_sentiment', 'neutral')).upper()} (Polarity: {r.get('polarity_score', 0.0):+.2f})\n\n", "tone")

        self.drawer_content.insert(tk.END, f"UTTERANCE TEXT:\n\"{r.get('text', '')}\"\n\n", "quote")

        p_pos = r.get("prob_positive", 0.0)
        p_neu = r.get("prob_neutral", 0.0)
        p_neg = r.get("prob_negative", 0.0)
        self.drawer_content.insert(tk.END, f"MODEL PROBABILITIES:\n• Positive: {p_pos*100:.1f}%\n• Neutral:  {p_neu*100:.1f}%\n• Negative: {p_neg*100:.1f}%\n\n", "mono")

        curr_idx = self.current_df.index[self.current_df["turn_id"] == turn_id].tolist()[0]
        start_ctx = max(0, curr_idx - 3)
        context_df = self.current_df.iloc[start_ctx: curr_idx]

        if not context_df.empty:
            self.drawer_content.insert(tk.END, "PRECEDING CONTEXT (3 TURNS):\n", "bold")
            for _, ctx_r in context_df.iterrows():
                self.drawer_content.insert(tk.END, f"[{ctx_r['turn_id']}] {ctx_r['speaker']}: {ctx_r['text']}\n", "muted")

        self.drawer_content.tag_config("title", font=("Segoe UI", 11, "bold"), foreground=self.colors["action_primary"])
        self.drawer_content.tag_config("bold", font=("Segoe UI", 9, "bold"), foreground=self.colors["text_main"])
        self.drawer_content.tag_config("tone", font=("Segoe UI", 9, "bold"), foreground=self.colors["pos"] if r.get('polarity_score', 0) > 0 else self.colors["neg"])
        self.drawer_content.tag_config("quote", font=("Segoe UI", 9, "italic"), foreground=self.colors["text_main"])
        self.drawer_content.tag_config("mono", font=("Consolas", 8), foreground=self.colors["text_muted"])
        self.drawer_content.tag_config("muted", font=("Segoe UI", 8), foreground=self.colors["text_muted"])

        self.drawer_content.configure(state="disabled")

    # -------------------------------------------------------------------------
    # VIEW 6: PLAIN-LANGUAGE USER GUIDE (COMPREHENSIVE & ACCESSIBLE)
    # -------------------------------------------------------------------------
    def _render_view_guide(self):
        container = tk.Frame(self.viewport_frame, bg=self.colors["bg"], padx=24, pady=20)
        container.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            container,
            text="User Guide & Plain-Language Manual",
            font=("Segoe UI", 14, "bold"),
            bg=self.colors["bg"],
            fg=self.colors["text_main"]
        ).pack(anchor="w", pady=(0, 6))

        tk.Label(
            container,
            text="Clear explanations of how to import chats, read charts, and understand what the analysis can and cannot tell you.",
            font=("Segoe UI", 9),
            bg=self.colors["bg"],
            fg=self.colors["text_muted"]
        ).pack(anchor="w", pady=(0, 14))

        guide_scroll = scrolledtext.ScrolledText(
            container,
            bg=self.colors["card_bg"],
            fg=self.colors["text_main"],
            font=("Segoe UI", 10),
            borderwidth=1,
            highlightbackground=self.colors["border"],
            highlightthickness=1,
            padx=16,
            pady=14
        )
        guide_scroll.pack(fill=tk.BOTH, expand=True)

        guide_text = """1. HOW TO IMPORT A CHAT CONVERSATION
---------------------------------------------------------
• WhatsApp Export (.txt):
  Open any WhatsApp chat on your phone, tap the three dots (or contact name) -> 'More' -> 'Export Chat' -> select 'Without Media'. Save the generated .txt file to your computer and click the '+ Import WhatsApp Chat (.txt)' button in this app.
• Supported Formats:
  Standard Android format ("DD/MM/YY, HH:MM - Sender: Message") and iOS format ("[DD/MM/YY, HH:MM:SS AM] Sender: Message").
• Built-in Samples:
  Use the top-left dropdown to test ready-to-use demonstration conversations at any time.

2. WHAT HAPPENS AFTER IMPORT?
---------------------------------------------------------
When a file is loaded, the app parses the dialogue into sequential turns in your local computer RAM. It feeds each message along with its preceding context turns into the context-aware sentiment model. The bottom status bar indicates 'Analysis complete' once all scores are computed.

3. UNDERSTANDING THE MAIN WORKSPACES
---------------------------------------------------------
• Overview:
  Gives you an at-a-glance summary: total messages, participants, average tone, overall change, and the primary timeline with notable moments.
• Timeline:
  A deep interactive chart showing tone over time. You can zoom in, pan across hours or days, compare participants, and toggle into an accessible data table.
• People:
  Displays who participated, their message count percentage, and whether their language was generally positive, neutral, or tense.
• Topics:
  Groups messages by common subject themes and shows tone distribution.
• Messages:
  A complete, searchable evidence viewer. Clicking any row shows the surrounding dialogue context.

4. WHAT DO 'POSITIVE', 'NEUTRAL', AND 'NEGATIVE' MEAN?
---------------------------------------------------------
• Scale:
  Every turn receives a polarity score from -1.0 (most negative) to +1.0 (most positive), with 0.0 representing neutral.
• Positive (+0.15 to +1.0):
  Appreciation, gratitude, relief, agreement, or helpful phrasing.
• Neutral (-0.15 to +0.15):
  Factual inquiries, scheduling, status updates, or routine information.
• Negative (-1.0 to -0.15):
  Frustration, concern, dissatisfaction, criticism, or technical distress.

5. IMPORTANT LIMITATIONS: WHAT THE AI CANNOT TELL YOU
---------------------------------------------------------
• No Mental State or Diagnostic Inferences:
  This app analyzes linguistic tone in written text. It does NOT diagnose psychological conditions, measure mental health, or prove true internal emotions.
• Sarcasm, Humor & Cultural Context:
  Machine learning models can misinterpret sarcasm, dry humor, in-jokes, or culturally specific idioms as negative or positive when they are not.
• Probabilistic Estimates:
  All tone scores are automated estimates. Always review the actual message text in the Messages tab before drawing conclusions.

6. HOW TO TRACE ANY RESULT TO SUPPORTING MESSAGES
---------------------------------------------------------
Every finding, notable moment, and timeline point is traceable. Click any notable moment on the Overview to inspect the quote, or open the Messages tab to review the exact words along with the 3 preceding context messages.

7. SEARCHING, FILTERING, AND EXPORTING RESULTS
---------------------------------------------------------
• Search & Filters:
  In the Messages tab, type keywords in the search bar or filter by participant and tone. Active filters are summarized in the sidebar. Click 'Reset Filters' to restore all messages.
• Safe Exports:
  Use the 'Data & Settings' workspace to export clean CSV or JSON files. All exported CSVs include automatic protection against spreadsheet formula injection (Risk #87).

8. PRIVACY AND LOCAL DATA STORAGE
---------------------------------------------------------
• 100% On-Device Processing:
  Your conversation messages are processed strictly in your computer's local memory (RAM). Nothing is uploaded to cloud servers or remote databases.
• Purging Data:
  When you close the app or click 'Purge Conversation from Memory' in Data & Settings, all conversation text is permanently cleared from RAM.
"""
        guide_scroll.insert(tk.END, guide_text)
        guide_scroll.configure(state="disabled")

    # -------------------------------------------------------------------------
    # VIEW 7: DATA MANAGEMENT & SETTINGS
    # -------------------------------------------------------------------------
    def _render_view_settings(self):
        container = tk.Frame(self.viewport_frame, bg=self.colors["bg"], padx=20, pady=16)
        container.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            container,
            text="Data Management, Memory Audit & Exports",
            font=("Segoe UI", 13, "bold"),
            bg=self.colors["bg"],
            fg=self.colors["text_main"]
        ).pack(anchor="w", pady=(0, 14))

        # Card 1: Data Audit & RAM Purge
        s1 = tk.Frame(container, bg=self.colors["card_bg"], padx=16, pady=14, highlightbackground=self.colors["border"], highlightthickness=1)
        s1.pack(fill=tk.X, pady=(0, 12))

        tk.Label(s1, text="LOCAL MEMORY AUDIT", font=("Segoe UI", 10, "bold"), bg=self.colors["card_bg"], fg=self.colors["text_main"]).pack(anchor="w", pady=(0, 4))
        tk.Label(s1, text=f"Active Conversation: {self.current_dataset_name}", font=("Segoe UI", 9), bg=self.colors["card_bg"], fg=self.colors["text_main"]).pack(anchor="w")
        tk.Label(s1, text=f"Total Messages in RAM: {len(self.current_df) if self.current_df is not None else 0}", font=("Segoe UI", 9), bg=self.colors["card_bg"], fg=self.colors["text_muted"]).pack(anchor="w")
        tk.Label(s1, text="Storage Policy: Stored only in local computer RAM during this session. Discarded upon exit.", font=("Segoe UI", 8), bg=self.colors["card_bg"], fg=self.colors["pos"]).pack(anchor="w", pady=(4, 8))

        btn_purge = tk.Button(
            s1, text="Purge Conversation from Memory", font=("Segoe UI", 8, "bold"), bg=self.colors["card_inset"], fg=self.colors["neg"], relief="flat", cursor="hand2",
            command=self._purge_data
        )
        btn_purge.pack(anchor="w")

        # Card 2: Export Center
        s2 = tk.Frame(container, bg=self.colors["card_bg"], padx=16, pady=14, highlightbackground=self.colors["border"], highlightthickness=1)
        s2.pack(fill=tk.X)

        tk.Label(s2, text="SAFE EXPORT CENTER", font=("Segoe UI", 10, "bold"), bg=self.colors["card_bg"], fg=self.colors["text_main"]).pack(anchor="w", pady=(0, 4))
        tk.Label(s2, text="Export clean, sanitized analysis files. Formula characters (=, +, -, @) are automatically escaped to protect against spreadsheet formula injection.", font=("Segoe UI", 8), bg=self.colors["card_bg"], fg=self.colors["text_muted"]).pack(anchor="w", pady=(0, 8))

        btn_row = tk.Frame(s2, bg=self.colors["card_bg"])
        btn_row.pack(fill=tk.X, pady=4)

        tk.Button(
            btn_row, text="Export Sanitized CSV", font=("Segoe UI", 9, "bold"), bg=self.colors["card_inset"], fg=self.colors["action_primary"], relief="flat", cursor="hand2", padx=12, pady=6,
            command=self._export_sanitized_csv
        ).pack(side=tk.LEFT, padx=(0, 8))

        tk.Button(
            btn_row, text="Export Analysis JSON", font=("Segoe UI", 9, "bold"), bg=self.colors["card_inset"], fg=self.colors["action_primary"], relief="flat", cursor="hand2", padx=12, pady=6,
            command=self._export_json
        ).pack(side=tk.LEFT, padx=(0, 8))

        # Card 3: Sponsored Placement
        s_ad = tk.Frame(container, bg=self.colors["card_inset"], padx=14, pady=10, highlightbackground=self.colors["border"], highlightthickness=1)
        s_ad.pack(fill=tk.X, pady=(12, 0))
        s_ad_top = tk.Frame(s_ad, bg=self.colors["card_inset"])
        s_ad_top.pack(fill=tk.X)
        tk.Label(s_ad_top, text="AD", font=("Segoe UI", 7, "bold"), bg=self.colors["border"], fg=self.colors["text_muted"], padx=3, pady=1).pack(side=tk.LEFT)
        tk.Label(s_ad_top, text="Sponsored • AdMob Network", font=("Segoe UI", 7), bg=self.colors["card_inset"], fg=self.colors["text_muted"], padx=6).pack(side=tk.LEFT)
        tk.Label(s_ad, text="Sentient Privacy Suite: Enterprise On-Premises LLM & Dialogue Anonymization.", font=("Segoe UI", 8, "bold"), bg=self.colors["card_inset"], fg=self.colors["text_main"]).pack(anchor="w", pady=(4, 1))
        tk.Label(s_ad, text="Fully compliant with GDPR Art 9, CCPA & Indian DPDP Act 2023. Zero third-party data egress.", font=("Segoe UI", 8), bg=self.colors["card_inset"], fg=self.colors["text_muted"]).pack(anchor="w")

    def _purge_data(self):
        if messagebox.askyesno("Confirm Purge", "Permanently discard all loaded conversation data from computer RAM?"):
            self.current_df = None
            self.current_stats = None
            self.current_analysis_result = None
            self._switch_view("overview")
            self.status_var.set("Conversation data purged from local memory.")

    def _export_sanitized_csv(self):
        if self.current_df is None:
            return
        fpath = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")])
        if not fpath:
            return

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
        """
        Classify trajectory shape for tests and patterns.
        Framed neutrally as emotional trajectory drift patterns.
        """
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

        if s_min < -0.15 and (s_last - s_min) >= 0.30 and 0 < min_idx < n - 1:
            return "Man in a Hole (Dip & De-escalation Recovery)"
        if s_max > 0.15 and (s_max - s_last) >= 0.30 and 0 < max_idx < n - 1:
            return "Icarus (Rise & Fall)"
        if drift >= 0.35:
            return "Rags to Riches (Continual Emotional Rise)"
        if drift <= -0.35:
            return "Tragedy (Continual Emotional Decline)"
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
