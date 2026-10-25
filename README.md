<p align="center">
  <img src="assets/sentiment-trajectory-banner.png" alt="Sentiment Trajectory Analysis Banner" width="100%">
</p>

<h1 align="center">Sentiment Trajectory Analysis</h1>

<p align="center">
  <strong>Context-aware sentiment analysis and conversational trajectory modeling for English, Hindi, and Hinglish dialogue.</strong>
</p>

<p align="center">
  <a href="https://www.python.org/downloads/release/python-3120/"><img src="https://img.shields.io/badge/Python-3.12%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.12+"></a>
  <a href="https://pytorch.org/"><img src="https://img.shields.io/badge/PyTorch-2.2%2B-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white" alt="PyTorch 2.2+"></a>
  <a href="https://huggingface.co/docs/transformers"><img src="https://img.shields.io/badge/Hugging%20Face-Transformers%204.38%2B-FFD21E?style=for-the-badge&logo=huggingface&logoColor=black" alt="Hugging Face Transformers"></a>
  <a href="https://scikit-learn.org/"><img src="https://img.shields.io/badge/scikit--learn-1.4%2B-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white" alt="scikit-learn"></a>
  <a href="#test-suite-and-quality-assurance"><img src="https://img.shields.io/badge/Tests-36%20Passed%20(100%25)-5AAE91?style=for-the-badge&logo=pytest&logoColor=white" alt="Tests Passed"></a>
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
  <a href="#project-structure">Project Structure</a> •
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
Below is a real trajectory curve and class probability breakdown generated by the sentiment inference engine on a multi-turn reconciliation dialogue:

<p align="center">
  <img src="assets/demo_trajectory_plot.png" alt="Model-Generated Sentiment Trajectory Plot" width="95%">
</p>

### Application Platforms & Themes

```
┌──────────────────────────────────────────────┐  ┌──────────────────────────────────────────────┐
│          Windows Desktop Studio              │  │           Android Mobile App                 │
│                                              │  │                                              │
│  • Warm Ivory Theme (#F8F6EF & #FFFDF6)      │  │  • Responsive 4-Tab Navigation               │
│  • 4-Section Notebook Architecture           │  │  • HTML5 2D Canvas Trajectory Waveform       │
│  • Interactive Paned Message Inspector       │  │  • Filterable Chat Stream with Shift Badges  │
│  • Embedded Matplotlib Plot with Pan/Zoom    │  │  • Protocol Buffer Bundle for Google Play    │
│  • Standalone .EXE (No Python Needed)        │  │  • 4-Byte ZipAligned & Scheme V1+V2+V3 Signed│
└──────────────────────────────────────────────┘  └──────────────────────────────────────────────┘
```

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

### Prerequisites
- Python 3.11 or Python 3.12
- Git
- Windows, macOS, or Linux

### 1. Clone Repository & Setup Virtual Environment

```bash
# Clone the repository
git clone https://github.com/your-username/sentiment-trajectory-analysis.git
cd sentiment-trajectory-analysis

# Create isolated virtual environment
python -m venv .venv

# Activate environment
# On Windows:
.venv\Scripts\activate
# On Linux / macOS:
source .venv/bin/activate

# Upgrade pip and install pinned dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Download MELD Dataset & Prepare Processed Data

```bash
# Download official MELD splits, validate turn ordering, and standardize schema
python src/prepare_data.py
```

### 3. Run Automated Test Suite (26/26 Tests)

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

## Project Structure

```
sentiment-trajectory-analysis/
├── assets/
│   ├── branding/
│   │   ├── logo_master_512.png         # Master 512x512 high-res branding icon
│   │   ├── play_store_feature_graphic_1024x500.png # Google Play Store banner
│   │   ├── app_icon.ico                # Windows desktop executable icon
│   │   └── android/                    # Multi-density mipmap icons (mdpi to xxxhdpi)
│   ├── demo_trajectory_plot.png        # Generated demonstration trajectory plot
│   └── sentiment-trajectory-banner.png # GitHub README repository banner
├── build_tools/
│   └── android/                        # Standalone Android CLI toolchain
│       ├── aapt2.exe                   # Google Android resource compiler
│       ├── r8.jar                      # Google D8 Dalvik bytecode converter
│       ├── bundletool.jar              # Official Google Play App Bundle builder
│       ├── apksig.jar                  # Official Google APK signature engine (v1-v4)
│       └── android.jar                 # Android API platform stubs
├── configs/
│   └── config.yaml                     # Pinned hyperparameters, paths, and label mappings
├── data/
│   ├── raw/                            # Raw MELD benchmark CSV files
│   └── processed/                      # Schema-normalized train.csv, val.csv, test.csv
├── dist/
│   ├── SentimentTrajectory.aab         # Official Google Play Store Android App Bundle
│   ├── SentimentTrajectory_release.apk # Production-signed 4-byte aligned Android APK
│   ├── release.keystore                # Production cryptographic keystore
│   └── SentimentTrajectoryStudio/      # Compiled Windows desktop distribution directory
├── docs/
│   └── privacy_policy.html             # Standalone 100% on-device privacy policy web page
├── mobile/                             # Android application source tree
│   ├── AndroidManifest.xml             # Manifest targeting Android 14 (API 34)
│   ├── assets/                         # Responsive HTML5/JS/CSS mobile app
│   │   ├── app.js                      # Canvas trajectory renderer & standalone engine
│   │   ├── index.html                  # Mobile 4-tab stepped interface
│   │   └── style.css                   # Mobile warm ivory & charcoal styling
│   └── src/                            # Native Java MainActivity & WebAppInterface
├── models/
│   ├── baseline_tfidf/                 # Trained TF-IDF vectorizer & Logistic Regression model
│   ├── roberta_context/                # Context-aware fine-tuned RoBERTa safetensors
│   └── roberta_independent/            # Independent utterance RoBERTa safetensors
├── outputs/
│   ├── figures/                        # Generated confusion matrices & trajectory figures
│   └── metrics/                        # Benchmark evaluation JSON records
├── scripts/
│   ├── build_desktop_exe.py            # PyInstaller desktop compilation pipeline
│   ├── build_mobile_apk.py             # Android APK build, zipalign & apksig pipeline
│   ├── build_play_store_bundle.py      # Google Play .aab bundle compilation pipeline
│   ├── generate_branding.py            # Unique visual identity generator
│   └── setup_android_tools.py          # Standalone Android toolchain fetcher
├── src/
│   ├── api.py                          # FastAPI REST service & mobile asset mount
│   ├── context.py                      # Context window builder & conversation boundary guard
│   ├── desktop_app.py                  # Standalone Tkinter desktop studio application
│   ├── evaluate.py                     # Evaluation metrics, calibration, and error analysis
│   ├── explain.py                      # Evidence-grounded trajectory narrative report generator
│   ├── predict.py                      # Unified inference pipeline with frozen .exe support
│   ├── prepare_data.py                 # MELD dataset ingestion & schema validation
│   ├── train.py                        # Model training routines (TF-IDF & RoBERTa)
│   ├── trajectory.py                   # Polarity scoring, temporal dynamics & turning points
│   └── whatsapp_parser.py              # Exported WhatsApp chat regex parser & sessionizer
├── tests/
│   ├── test_baseline.py                # Unit tests for baseline vectorizer & model artifacts
│   ├── test_context.py                 # Context window boundary & zero-leakage tests
│   ├── test_data_integrity.py          # Schema adherence & monotonic turn ordering tests
│   ├── test_desktop_app.py             # GUI presets & Risk #87 CSV defense tests
│   ├── test_mobile_and_api.py          # APK/AAB binary integrity & REST endpoint tests
│   ├── test_roberta.py                 # RoBERTa model artifact & probability tests
│   └── test_whatsapp_parser.py         # WhatsApp format parsing & multiline tests
├── PLAY_STORE_SUBMISSION_GUIDE.md      # Complete step-by-step Google Play publishing guide
├── PRIVACY_POLICY.md                   # Markdown privacy policy
├── pytest.ini                          # Test configuration
└── requirements.txt                    # Pinned Python dependencies
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
