# Sentient Analysis — UI & Interaction Design Specification (Refined)

A calm, trustworthy, and accessible design specification for **Sentient Analysis** across the **Windows Desktop Application** and **Android Mobile APK**.

---

## 1. Product Principles & Epistemic Boundaries

1. **Every Metric is Explained:** No unexplained or decorative scorecards. Every number clearly states what it measures, how it is calculated, and its limitations.
2. **Distinct Semantic Visual Encoding:**
   - **Primary Action / Buttons:** Calm Royal Blue (`#2563EB` light / `#3B82F6` dark) — *never* reused for negative tone.
   - **Positive Tone:** Gentle Emerald Green (`#059669` light / `#10B981` dark).
   - **Neutral Tone:** Soft Amber / Slate (`#D97706` light / `#F59E0B` dark).
   - **Negative Tone:** Crimson Red (`#DC2626` light / `#EF4444` dark).
3. **Evidence-Backed Traceability:** Every chart point, notable moment, and finding directly links to the underlying conversation text and its surrounding $k$-turn dialogue context.
4. **Honest Capabilities (No Clinical Diagnoses or Mind Reading):** The app evaluates linguistic tone in text. It does not diagnose psychological conditions, evaluate personal relationships, or claim to read someone's internal mind.
5. **Truthful Privacy Practices:** 100% local computer RAM processing. No chat messages are transmitted to cloud servers. Data is discarded upon session exit or by clicking "Purge Conversation from Memory".

---

## 2. Desktop Application Architecture (Windows)

### 2.1 Ergonomic Layout Structure
```
+-----------------------------------------------------------------------------------------+
|  Sentient Analysis  | Active Chat: [Sample 1 v] | Status: Ready  | [☀️/🌙] [+ Import Chat] |
+-----------------------------------------------------------------------------------------+
|  SIDEBAR (Collapsible)  |  CENTRAL CONTENT AREA               |  CONTEXT DRAWER        |
|  - Overview             |  (Breathable workspace giving       |  (Collapsible on right |
|  - Timeline             |   charts and data tables room)      |   showing selected turn|
|  - People               |                                     |   and 3-turn context)  |
|  - Topics               |  [ Primary Timeline or Evidence ]   |                        |
|  - Messages             |                                     |                        |
|  - User Guide           |                                     |                        |
|  - Data & Settings      |                                     |                        |
|                         |                                     |                        |
|  Active Filters: None   |                                     |                        |
|  [ Reset Filters ]      |                                     |                        |
+-----------------------------------------------------------------------------------------+
|  Status: 100% Analyzed  | Local RAM Storage Only • No Cloud Telemetry • Discard on Exit|
+-----------------------------------------------------------------------------------------+
```

### 2.2 Key Desktop Screens
1. **Overview:**
   - **Scope Audit:** Shows file name, date range, message count, participants, and 100% local coverage.
   - **Explained Metrics:**
     - *Average Tone:* Mean polarity score between -1.0 (most negative) and +1.0 (most positive).
     - *Overall Change:* Difference between conversation start and conclusion.
     - *Tone Stability:* Variation in turn-to-turn changes (higher % means fewer abrupt swings).
     - *Notable Shifts:* Count of abrupt tone pivots ($\Delta \ge 0.40$).
   - **Primary Dual Timeline:** Downsampled tone curve with volatility envelope + message density bars.
   - **Notable Moments:** Evidence-backed inflection moments with quotes and direct links.
2. **Timeline:**
   - Interactive Matplotlib canvas with Pan, Zoom, and Save toolbar.
   - Peak-preserving bucket downsampling (bins long chats into 50–60 buckets without losing emotional spikes).
   - Presets: `All`, `1st Half`, `2nd Half`, `Notable Shifts`.
   - Side-by-side participant comparison toggle.
   - Accessible Data Table mode toggle.
3. **People:**
   - Participation cards: message count, % share, average tone, observed emotional range.
   - Alternation scatter timeline showing conversational turn-taking.
   - "Filter Messages by Person" shortcut.
4. **Topics:**
   - Thematic feedback clusters (Technical Issues, Service, Product, Delivery) with sentiment breakdown.
5. **Messages:**
   - Paginated Treeview (50 rows/page) preventing GUI freezing on 50,000+ turns.
   - Real-time search with text highlighting.
   - Participant and Tone filter dropdowns with active filter summary.
   - Sliding Context Drawer showing selected message and preceding 3-turn context.
6. **User Guide:**
   - Dedicated 8-section manual explaining how to import chats, read charts, interpret tone scores, and understand AI limitations.
7. **Data & Settings:**
   - RAM audit and immediate "Purge Conversation from Memory" button.
   - Safe CSV export (with automatic spreadsheet formula injection escaping) and JSON export.

---

## 3. Android Mobile Application Architecture (APK & WebView)

### 3.1 Mobile Layout Structure
- **Top Masthead:** Brand logo, title, persistent conversation dropdown, `+ Import` button, and Settings gear icon.
- **Labeled Bottom Navigation Bar:**
  - 📊 **Overview**
  - 📈 **Timeline**
  - 👥 **People**
  - 💬 **Messages**
  - 📖 **Guide**
- **Touch-Friendly Visuals:**
  - Responsive canvas scaling across phones, foldables, and tablets.
  - Minimum 44x44px touch targets.
  - Slide-up bottom sheet context drawer (`.context-drawer`) when tapping any message or notable moment.
  - High-contrast typography with clear hierarchy (1.15rem hero, 0.94rem card titles, 0.84rem message text).

### 3.2 Mobile Large-Data Handling
- **Canvas Downsampling:** Long chats are aggregated into 40–50 uniform buckets with min/max envelopes and density bars.
- **Windowed Message List:** Loads 25 messages per chunk with a "Load More Messages" button, eliminating DOM bloat and scroll lag.
- **Monetization Isolation:** Separate AdMob container located at the bottom of Settings, clearly marked as sponsored without interfering with analysis or data privacy.

---

## 4. Plain-Language User Guide Reference (8 Sections)

1. **How to Import a Chat:** Step-by-step export instructions for WhatsApp (.txt) and standard formats.
2. **What Happens After Import:** In-memory parsing, tokenization, context-aware scoring.
3. **Understanding the Views:** Purpose and usage of Overview, Timeline, People, and Messages.
4. **What Tone Means:** Explanation of the continuous scale from -1.0 (negative) to +1.0 (positive) with 0.0 as neutral.
5. **Important Limitations:** AI evaluates text only; no mental health diagnosis, sarcasm pitfalls, probabilistic uncertainty.
6. **How to Trace Evidence:** How to click any finding to inspect the underlying dialogue and preceding turns.
7. **Searching & Exporting:** Keyword search, multi-filters, and formula-injection-safe CSV export.
8. **Privacy & Data Security:** In-memory processing guarantee and how to purge data.
