"""
sentient — Conversational Sentiment & Emotional Trajectory Studio.

Context-aware conversation sentiment analysis and emotional trajectory modeling
for English, Devanagari Hindi, and Romanized Hindi (Hinglish) dialogues.
"""

from pathlib import Path
import sys

# Ensure package root is importable
PKG_ROOT = Path(__file__).resolve().parent
REPO_ROOT = PKG_ROOT.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

__version__ = "1.2.0"
__author__ = "Harshit Dwivedi"

from src.predict import ConversationSentimentAnalyzer
from src.context import build_context_representations
from src.trajectory import compute_trajectory_statistics
from src.explain import (
    generate_conversation_explanation,
    generate_executive_summary_and_results,
)
from src.hinglish_normalizer import (
    normalize_whatsapp_text,
    detect_language_mode,
    detect_batch_language,
    transliterate_devanagari_to_roman,
)
from src.whatsapp_parser import (
    parse_whatsapp_file,
    parse_whatsapp_raw_lines,
    sessionize_messages,
)

__all__ = [
    "__version__",
    "ConversationSentimentAnalyzer",
    "build_context_representations",
    "compute_trajectory_statistics",
    "generate_conversation_explanation",
    "generate_executive_summary_and_results",
    "normalize_whatsapp_text",
    "detect_language_mode",
    "detect_batch_language",
    "transliterate_devanagari_to_roman",
    "parse_whatsapp_file",
    "parse_whatsapp_raw_lines",
    "sessionize_messages",
]
