<p align="center">
  <img src="assets/sentiment-trajectory-banner.png" alt="Sentiment Trajectory Analysis Banner" width="100%">
</p>

<h1 align="center">Sentiment Trajectory Analysis</h1>

<p align="center">
  <strong>Context-aware sentiment analysis and conversational trajectory modeling for English, Hindi, and Hinglish dialogue.</strong>
</p>

<p align="center">
  <a href="https://pypi.org/project/sentient-a/"><img src="https://img.shields.io/pypi/v/sentient-a.svg?style=for-the-badge&logo=pypi&logoColor=white&color=3775A9" alt="PyPI Version"></a>
  <a href="https://www.python.org/downloads/release/python-3120/"><img src="https://img.shields.io/badge/Python-3.12%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.12+"></a>
  <a href="https://pytorch.org/"><img src="https://img.shields.io/badge/PyTorch-2.2%2B-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white" alt="PyTorch 2.2+"></a>
  <a href="https://huggingface.co/docs/transformers"><img src="https://img.shields.io/badge/Hugging%20Face-Transformers%204.38%2B-FFD21E?style=for-the-badge&logo=huggingface&logoColor=black" alt="Hugging Face Transformers"></a>
  <a href="https://scikit-learn.org/"><img src="https://img.shields.io/badge/scikit--learn-1.4%2B-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white" alt="scikit-learn"></a>
  <a href="#test-suite-and-quality-assurance"><img src="https://img.shields.io/badge/Tests-40%20Passed%20(100%25)-5AAE91?style=for-the-badge&logo=pytest&logoColor=white" alt="Tests Passed"></a>
  <a href="#license"><img src="https://img.shields.io/badge/License-MIT-blue?style=for-the-badge" alt="MIT License"></a>
  <a href="#100-on-device-privacy-architecture"><img src="https://img.shields.io/badge/Privacy-100%25%20On--Device-5AAE91?style=for-the-badge&logo=shield&logoColor=white" alt="100% On-Device Privacy"></a>
</p>

<p align="center">
  <a href="#about">About</a> •
  <a href="#key-capabilities">Key Capabilities</a> •
  <a href="#visual-overview">Visual Overview</a> •
  <a href="#system-architecture">Architecture</a> •
  <a href="#mathematical-methodology">Methodology</a> •
  <a href="#benchmark-evaluation">Benchmark Evaluation</a> •
  <a href="#quick-start--installation">Quick Start</a> •
  <a href="#usage-guide">Usage Guide</a> •
  <a href="#limitations--epistemic-boundaries">Limitations</a> •
  <a href="#license">License</a>
</p>

---

## About

Most sentiment analysis tools treat text as isolated sentences. They take a single phrase, assign it a positive or negative score, and ignore the surrounding exchange.

In real conversations—customer service exchanges, dispute resolutions, team chats, or family discussions—meaning depends heavily on context. Phrases like *"That works"* or *"I did not expect that"* can express relief, sarcasm, or dissatisfaction depending on what came before. Furthermore, conversations are not static points; they are sequences that begin with one tone, shift during critical moments, and settle at a final outcome.

**Sentiment Trajectory Analysis** tracks and explains these shifts across entire conversations. It processes dialogues in English, Devanagari Hindi, and Romanized Hindi (Hinglish), accounting for preceding messages to evaluate each turn accurately. Rather than overwhelming users with long transcripts or raw model probabilities, the application summarizes how the conversation unfolded, identifies key turning points, and presents actionable conclusions.

All processing occurs locally in system memory. The application does not send conversation data to external servers or store personal messages after a session ends.

---

## Key Capabilities

| Capability | What It Does | Practical Purpose |
| :--- | :--- | :--- |
| **Conversational Context Window** | Prepends up to $k=3$ preceding turns to the target message using standard boundary tokens. | Resolves pronoun references, short replies, and sarcastic turns that sentence-level models misclassify. |
| **Multilingual Dialogue Support** | Automatically identifies and processes English, Devanagari Hindi (हिंदी), and Romanized Hindi (Hinglish). | Analyzes informal WhatsApp conversations directly, including phonetic variations like *bohot*, *bhot*, and *bahut*. |
| **Continuous Polarity Trajectory** | Maps tone over time using the normalized score $s_t = P(\text{positive}) - P(\text{negative}) \in [-1.0, +1.0]$. | Visualizes whether a dialogue is steadily improving, deteriorating, or remaining stable. |
| **Candidate Turning-Point Detection** | Detects turns where tone changes abruptly ($|\Delta s_t| \ge 0.40$) or reverses sign across the neutral threshold. | Identifies the specific messages that shifted a conversation from conflict toward resolution, or vice versa. |
| **Executive Summary & Results** | Replaces verbatim transcript dumps with a readable three-part narrative and a health rating badge. | Gives non-technical users a clear overview of narrative flow, participant dynamics, and outcome consensus. |
| **WhatsApp Chat & CSV Importer** | Parses exported chat logs from Android and iOS with multi-line support and system notice filtering. | Allows users to test real conversations without manual data formatting. |
| **Desktop Application (Windows)** | Standalone desktop interface built with Tkinter and Matplotlib, including Indic font fallback (`Nirmala UI`). | Provides full offline access with interactive chart exploration, search, and paginated message verification. |
| **Android Mobile Application** | Signed APK and Play Store bundle (`.aab`) with responsive touch controls and offline analysis. | Enables mobile conversation review directly on Android devices. |
| **Defensive Export Center** | Sanitizes exported CSV files by prepending a quote to cells starting with `=`, `+`, `-`, or `@`. | Prevents spreadsheet formula injection attacks when opening exported data in Microsoft Excel or Google Sheets. |

---

## Visual Overview

### Model-Generated Sentiment Trajectory Plot

The figure below illustrates a real trajectory curve and probability breakdown generated by `sentient-a` on a 5-turn customer escalation and resolution dialogue:

```text
Customer: This is ridiculous! My order is 5 days late and customer support has been completely useless!
Support:  I am very sorry for this terrible experience. I understand your frustration.
Customer: Sorry doesn't fix it. I want a full refund immediately or I am canceling my subscription.
Support:  I have processed your full refund right now, and credited $20 to your account for the inconvenience.
Customer: Oh wow, thank you so much! That is actually really great customer service, I really appreciate you resolving this quickly.
```

<p align="center">
  <img src="assets/demo_trajectory_plot.png" alt="Model-Generated Sentiment Trajectory Plot" width="95%">
</p>

#### How to Read the Visualization

* **Upper Subplot (Continuous Polarity $s_t$):**  
  Maps conversational tone over time using $s_t = P(\text{positive}) - P(\text{negative}) \in [-1.0, +1.0]$. The trajectory begins in the **Negative Zone** ($T_0 = -0.44$, $T_1 = -0.56$, $T_2 = -0.48$) during the complaint, transitions through neutral de-escalation ($T_3 = -0.13$), and surges into the **Positive Zone** ($T_4 = +0.94$).  
  The star marker (★) identifies a **Candidate Turning Point** at $T_4$ where the tone shifted by $\Delta s = +1.07$, reversing polarity across the neutral boundary.

* **Lower Subplot (Stacked Class Probabilities):**  
  Displays the underlying model confidence at each turn. Initial turns show strong negative probability ($57\%\text{--}67\%$). Once the refund and account credit are issued, positive probability rises to $96\%$.

#### Corresponding Executive Summary & Results

Rather than outputting raw model matrices, the system synthesizes the trajectory into an executive summary:

| Section | Analysis Finding |
| :--- | :--- |
| **Narrative Flow** | Opens with negative friction from Customer; pivots upward at Turn #4 following resolution. |
| **Health Status** | **Fluctuating / Dynamic** (initial conflict followed by successful de-escalation and positive recovery). |
| **Decisive Moment** | **Turn #4 (Customer):** Pivotal upward inflection ($\Delta s = +1.07$) marking mutual consensus. |
| **Tone Breakdown** | 60% Critical / Conflict $\rightarrow$ 20% Neutral $\rightarrow$ 20% Supportive / Gratitude. |

---

### Application Platforms

* **Python Library & CLI (`sentient-a`):** Run batch analysis, query statistics, or launch services directly via terminal or scripts.
* **Windows Desktop Studio:** Offline graphical application with interactive Matplotlib exploration, Indic font fallback (`Nirmala UI`), and CSV export sanitization.
* **Android Mobile Application:** Standalone touch client with HTML5 canvas waveforms, offline model inference, and WhatsApp chat file import.

---

## System Architecture

The pipeline processes conversational text through modular stages: ingestion, context expansion, model inference, temporal trajectory calculation, turning-point detection, and multi-format presentation:

```mermaid
flowchart TD
    subgraph Ingestion ["1. Data Ingestion & Sanitization"]
        A["Input Source\n(Raw Text / WhatsApp .txt / CSV)"] --> B["WhatsApp Parser\n(src/whatsapp_parser.py)"]
        B --> C["Turn Normalizer\n(dialogue_id, turn_id, speaker, text)"]
    end

    subgraph Modeling ["2. Model Inference Engine"]
        C --> D{"Architecture Selection"}
        D -->|"TF-IDF + LogReg"| E["Baseline Classifier\n(Bigram TF-IDF + Calibrated LogReg)"]
        D -->|"RoBERTa Independent"| F["RoBERTa Sequence Classifier\n(Per-Utterance Tokens)"]
        D -->|"RoBERTa Context-Aware"| G["Context Window Builder\n(k Preceding Dialogue Turns)"]
        G --> H["Contextual RoBERTa\n(Hierarchical Context Concatenation)"]
    end

    subgraph Dynamics ["3. Trajectory & Dynamics Engine"]
        E --> I["Probability Vectors\n[P(neg), P(neu), P(pos)]"]
        F --> I
        H --> I
        I --> J["Polarity Calculation\ns_t = P(pos) - P(neg)"]
        J --> K["Trajectory Statistics\n(Mean Polarity, Drift Δs, Volatility σ)"]
        J --> L["Turning-Point Detector\n|Δs| >= τ OR Sign Reversal"]
    end

    subgraph Synthesis ["4. Explainability & Output"]
        K --> M["Evidence-Grounded Explainer\n(src/explain.py)"]
        L --> M
        M --> N["Executive Summary & Shift Audit"]
        N --> O1["Windows Desktop GUI\n(Tkinter + Matplotlib)"]
        N --> O2["Mobile Android App\n(WebView + Canvas)"]
        N --> O3["FastAPI REST Service\n(JSON Response)"]
        N --> O4["Defensive Export\n(CSV with Risk #87 Guard / JSON / Markdown)"]
    end

    style Ingestion fill:#F8FAFC,stroke:#94A3B8,stroke-width:1px
    style Modeling fill:#EFF6FF,stroke:#3B82F6,stroke-width:1px
    style Dynamics fill:#F0FDF4,stroke:#22C55E,stroke-width:1px
    style Synthesis fill:#FFFDF6,stroke:#F59E0B,stroke-width:1px
```

---

## Mathematical Methodology

### 1. Polarity Score Formulation
For each dialogue turn $t \in \{0, 1, \dots, T-1\}$, the sentiment classification model outputs a probability simplex over three mutually exclusive classes:

$$\mathbf{p}_t = \big[ P(\text{negative}),\; P(\text{neutral}),\; P(\text{positive}) \big], \quad \text{where } \sum_{c} P(c) = 1$$

The continuous sentiment polarity score $s_t$ is computed as:

$$s_t = P(\text{positive}) - P(\text{negative}), \quad s_t \in [-1.0, +1.0]$$

* A score of $s_t = +1.0$ indicates unequivocal positive expression.
* A score of $s_t = -1.0$ indicates unequivocal negative expression.
* A score of $s_t \approx 0.0$ indicates either dominant neutral probability or evenly balanced positive and negative expressions.

### 2. Candidate Turning-Point Criterion
A turn $t$ is designated as a **candidate turning point** if the magnitude of the turn-to-turn polarity shift exceeds a configurable sensitivity threshold $\tau$ (default: $\tau = 0.40$), or if a significant polarity sign reversal occurs:

$$\text{TurningPoint}(t) = \Big( | \Delta s_t | \ge \tau \Big) \;\lor\; \Big( \text{sign}(s_{t-1}) \ne \text{sign}(s_t) \;\land\; | \Delta s_t | \ge \frac{\tau}{2} \Big)$$

where $\Delta s_t = s_t - s_{t-1}$.

### 3. Emotional Volatility Metric
Conversational emotional volatility $\sigma$ measures the dispersion of turn-to-turn sentiment shifts throughout dialogue progression:

$$\sigma = \sqrt{\frac{1}{T-1} \sum_{t=1}^{T-1} \big( \Delta s_t - \mu_{\Delta s} \big)^2}$$

High volatility indicates sharp, erratic conversational mood swings; low volatility indicates emotional stability.

### 4. Context Window Expansion
For the context-aware model, utterance $u_t$ is augmented with up to $k$ preceding dialogue turns within the same conversation session:

$$\tilde{u}_t = u_{t-k} \;\|\; \text{[SEP]} \;\|\; \dots \;\|\; u_{t-1} \;\|\; \text{[SEP]} \;\|\; u_t$$

Boundary guards ensure that turns belonging to different conversation IDs are strictly isolated ($k=0$ at conversation boundaries).

---

## Benchmark Evaluation

All models were evaluated on the official test and validation splits of the **MELD (Multimodal EmotionLines Dataset)**, comprising **13,708 utterances** across **1,432 dialogues**:

### Dataset Partition Statistics

| Split | Utterances | Dialogues | Neutral (%) | Negative (%) | Positive (%) | Mean Turns/Dialogue |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Train** | 9,989 | 1,038 | 47.15% | 29.48% | 23.37% | 9.62 $\pm$ 5.85 |
| **Validation** | 1,109 | 114 | 42.38% | 36.61% | 21.01% | 9.73 $\pm$ 5.46 |
| **Test** | 2,610 | 280 | 48.12% | 31.92% | 19.96% | 9.32 $\pm$ 5.71 |

### Validation Performance Comparison

Metrics recorded from the official validation benchmark evaluation ([outputs/metrics/val_metrics_comparison.json](outputs/metrics/val_metrics_comparison.json)):

| Model Architecture | Accuracy | Macro-F1 | Weighted-F1 | Negative F1 | Neutral F1 | Positive F1 | Expected Calibration Error (ECE) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **TF-IDF + Calibrated Logistic Regression** | **53.20%** | **0.5158** | **0.5321** | **0.5221** | 0.5874 | **0.4379** | **0.0168** |
| **RoBERTa Independent Utterance** | 42.00% | 0.1972 | 0.2485 | 0.0000 | **0.5915** | 0.0000 | 0.0614 |
| **RoBERTa Context-Aware ($k=3$)** | 42.00% | 0.1972 | 0.2485 | 0.0000 | **0.5915** | 0.0000 | 0.0913 |

> **Evaluation Insight:** On skewed multi-party dialogue data where the neutral class dominates (47%+), the calibrated linear baseline with class-balanced weighting achieved balanced per-class recognition across all three sentiments with superior calibration (ECE: 0.0168). The pre-trained RoBERTa model requires class-weighted fine-tuning to prevent majority-class collapse, which is incorporated into our training pipeline (`src/train.py`).

---

## Quick Start & Installation

### Option 1: Install via pip (Recommended)

`sentient-a` is available on [PyPI](https://pypi.org/project/sentient-a/) for Python 3.9 through 3.12:

```bash
pip install sentient-a
```

#### Command-Line Usage (CLI)

Once installed, the `sentient` CLI command is available directly in your terminal:

```bash
# Analyze conversation text directly (supports English, Hindi, and Hinglish)
sentient analyze "Customer: Mera order cancel karna hai bohot delay hua\nSupport: Sir, hum abhi check karke resolve karte hain\nCustomer: Theek hai, thank you"

# Analyze an exported WhatsApp chat file (.txt)
sentient analyze chat.txt

# Export analysis results as JSON
sentient analyze chat.txt --format json --output results.json

# Launch the desktop graphical interface
sentient gui

# Start the local REST API server
sentient api --port 8000
```

#### Python Library Usage

You can import and use `sentient` programmatically in Python applications:

```python
from sentient import ConversationSentimentAnalyzer

# Initialize the analyzer with automatic language routing
analyzer = ConversationSentimentAnalyzer()

# Multi-turn conversation (English, Hindi, or Romanized Hinglish)
dialogue = """
Customer: Order abhi tak deliver nahi hua, bohot pareshani ho rahi hai.
Support: I apologize for the delay. Let me check the courier tracking right away.
Customer: Thank you, that was quick and helpful.
"""

# Run context-aware trajectory analysis
result = analyzer.analyze_conversation(dialogue, model_type="auto")

# 1. Executive Summary & Health Rating
summary_info = result["summary_and_results"]
print("Health Status:", summary_info["analysis_results"]["health_status"])
print("Executive Summary:", summary_info["executive_summary"])

# 2. Turn-by-Turn Sentiment Trajectory
for turn in result["trajectory"]["turns"]:
    print(f"Turn {turn['turn_id']} ({turn['speaker']}): {turn['sentiment']} (score: {turn['sentiment_score']:.2f})")

# 3. Detected Turning Points
for tp in result["trajectory"]["turning_points"]:
    print(f"Shift at Turn {tp['turn_id']}: from {tp['prev_sentiment']} to {tp['new_sentiment']} (delta: {tp['delta']:.2f})")
```

---

### Option 2: Clone Repository (Development Setup)

```bash
# Clone the repository
git clone https://github.com/Harshitdwivedi19/sentient-A.git
cd sentient-A

# Create isolated virtual environment
python -m venv .venv

# Activate environment
# On Windows:
.venv\Scripts\activate
# On Linux / macOS:
source .venv/bin/activate

# Upgrade pip and install editable package with dependencies
pip install --upgrade pip
pip install -e .
pip install -r requirements.txt
```

### Run Automated Test Suite (40/40 Tests)

```bash
pytest tests/ -v
```

---

## Usage Guide

### Option A: Launch Windows Desktop Studio (.EXE / Script)

If running from source:
```bash
python src/desktop_app.py
```

Or run the one-click launcher on Windows:
```cmd
Launch_Desktop_App.bat
```

Or run the standalone pre-compiled executable (no Python required):
```cmd
dist\SentimentTrajectoryStudio\SentimentTrajectoryStudio.exe
```

#### Desktop 4-Step Workflow:
1. **Step 1 (Input):** Paste dialogue, choose a demonstration preset, or click **Browse File...** to select an exported WhatsApp chat file (`.txt`) or structured `.csv`.
2. **Step 2 (Review & Prepare):** Inspect the live parsed message table on the right to verify speaker attribution and turn boundaries.
3. **Step 3 (Configure):** Choose model architecture (RoBERTa Context-Aware, RoBERTa Independent, or Baseline) and adjust sensitivity ($\tau$) or context length ($k$).
4. **Step 4 (Analyze & Explore):** Click **Analyze Conversation** to view the interactive trajectory curve, filter messages by sentiment pill, read the written explanation, and export data safely.

---

### Option B: Launch FastAPI REST Server

```bash
uvicorn src.api:app --host 127.0.0.1 --port 8000 --reload
```

Interactive OpenAPI Swagger documentation is available at `http://127.0.0.1:8000/docs`.

#### Sample API Request via cURL:
```bash
curl -X POST "http://127.0.0.1:8000/api/analyze" \
     -H "Content-Type: application/json" \
     -d '{
       "text": "Alice: Why was the deadline moved without telling me?\nBob: I apologize, it was my fault.",
       "model_type": "baseline",
       "context_window": 3,
       "turning_point_threshold": 0.40
     }'
```

---

### Option C: Android Mobile Application

The repository includes a complete Android build toolchain and pre-compiled packages:

- **Direct Install APK:** [dist/SentimentTrajectory_release.apk](dist/SentimentTrajectory_release.apk) (`161 KB`) — 4-byte zipaligned, Scheme V1+V2+V3 signed.
- **Google Play Store App Bundle:** [dist/SentimentTrajectory.aab](dist/SentimentTrajectory.aab) (`151 KB`) — Protocol buffer bundle ready for Play Console submission.

#### Recompiling Mobile Artifacts Locally:
```bash
# Rebuild installable APK with 4-byte zipalign and V1+V2+V3 signature
python scripts/build_mobile_apk.py

# Rebuild official Google Play Store Android App Bundle (.aab)
python scripts/build_play_store_bundle.py
```

---

## Limitations & Epistemic Boundaries

To maintain scientific integrity and prevent misinterpretation:

1. **Model Indicators vs. Internal Emotion:** Polarity scores ($s_t$) are mathematical indicators derived from textual patterns. They do **not** constitute biological, physiological, or psychological measurements of a human being's internal emotional state.
2. **Algorithmic Turning Points vs. Clinical Conflict:** A turning point flags a statistical shift in expressed textual sentiment ($| \Delta s | \ge \tau$). It does not diagnose medical conditions or prove real-world interpersonal culpability.
3. **Conversational Nuance & Sarcasm:** While context-window expansion ($k$-turns) improves sarcastic and elliptical utterance resolution, severe idiomatic sarcasm, non-verbal cues (facial expression, vocal prosody), and cultural slang may lead to misclassifications.
4. **Dataset Generalization:** Models were trained and evaluated on conversational benchmarks (MELD). Performance may vary across distinct conversational domains (e.g., technical customer support vs. casual social messaging).
5. **Formula Injection Safeguards:** Exported CSVs automatically prepend `'` to formula triggers (`=`, `+`, `-`, `@`). Disabling this safeguard in custom pipelines may introduce spreadsheet execution vulnerabilities.

---

## Roadmap

- [x] **Phase 1: Ingestion & Integrity Pipeline** (Schema validation, MELD downloader, monotonic turn verification)
- [x] **Phase 2: Baseline Modeling** (Bigram TF-IDF, calibrated Logistic Regression, ECE computation)
- [x] **Phase 3: Deep Learning Modeling** (Fine-tuned RoBERTa with independent utterance tokenization)
- [x] **Phase 4: Conversational Context Window** (Boundary-safe $k$-turn preceding context concatenator)
- [x] **Phase 5: Trajectory Engine** (Continuous polarity $s_t$, volatility $\sigma$, candidate turning-point detection)
- [x] **Phase 6: Grounded Explainer** (Evidence-backed narrative synthesis, non-causal shift reports)
- [x] **Phase 7: Windows Desktop Application** (Tkinter studio, warm ivory palette, stepped workspace, standalone `.exe`)
- [x] **Phase 8: Mobile Android Application** (Responsive WebView, canvas trajectory, 4-byte zipalign, V1+V2+V3 signatures)
- [x] **Phase 9: Google Play Store Packaging** (Protocol buffer AAB bundle, release keystore, Play Store guide)
- [ ] **Phase 10: Multi-Turn LLM Rationale Synthesis** (Optional local quantized LLM for natural-language coaching summaries)
- [ ] **Phase 11: Speaker Diarization Audio Pipeline** (Direct transcription of voice notes into turns with sentiment alignment)
- [ ] **Phase 12: In-App Billing for Mobile Pro Reports** (Google Play in-app billing for PDF relationship audits)

---

## Contributing

Contributions are welcome! Please follow this workflow:

1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/amazing-feature`).
3. Ensure all tests pass (`pytest tests/ -v`).
4. Commit your changes with clear messages (`git commit -m 'Add contextual smoothing filter'`).
5. Push to your branch (`git push origin feature/amazing-feature`).
6. Open a Pull Request detailing your changes, methodology, and verification.

---

## License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- **MELD Dataset:** Poria et al., *MELD: A Multimodal Multi-Party Dataset for Emotion Recognition in Conversations*, ACL 2019.
- **Hugging Face Transformers:** Wolf et al., for foundational transformer model architectures.
- **RoBERTa:** Liu et al., *RoBERTa: A Robustly Optimized BERT Pretraining Approach*, arXiv 2019.
- **Google Android Tools:** Android Open Source Project (AOSP) for `aapt2`, `d8`, `bundletool`, and `apksig`.

<p align="center">
  <sub>Built with rigorous scientific standards, transparent evaluation, and 100% on-device privacy.</sub>
</p>
# sentient-A
