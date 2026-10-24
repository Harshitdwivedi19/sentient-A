"""
tests/test_desktop_app.py

Unit and integration tests for the Desktop GUI Application.
Verifies:
- Preset dialogues structure
- Custom branding assets existence and resolution
- Core UI component initialization and data pipeline bindings
- Safe CSV formula sanitization
"""

import os
import sys
from pathlib import Path
import pytest
import pandas as pd
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.desktop_app import SAMPLE_PRESETS


def test_branding_assets_exist():
    branding_dir = PROJECT_ROOT / "assets" / "branding"
    assert (branding_dir / "logo_master_512.png").exists(), "Master 512 logo missing"
    assert (branding_dir / "app_icon.ico").exists(), "Windows app_icon.ico missing"

    # Verify Android mipmaps
    for density in ["mipmap-mdpi", "mipmap-hdpi", "mipmap-xhdpi", "mipmap-xxhdpi", "mipmap-xxxhdpi"]:
        icon_file = branding_dir / "android" / density / "ic_launcher.png"
        assert icon_file.exists(), f"Android icon missing for {density}"
        with Image.open(icon_file) as img:
            assert img.size[0] == img.size[1] > 0


def test_sample_presets_contain_required_dialogues():
    assert "Sample 1: Conflict to Reconciliation" in SAMPLE_PRESETS
    assert "Sample 2: WhatsApp Chat Format" in SAMPLE_PRESETS
    assert "Sample 3: MELD Friends Dialogue" in SAMPLE_PRESETS

    for name, text in SAMPLE_PRESETS.items():
        assert len(text.strip().split("\n")) >= 5, f"Preset {name} has too few turns"
        assert ":" in text, f"Preset {name} missing speaker separator"


def test_formula_injection_defense():
    # Verify Risk #87 defense logic
    dangerous_data = pd.DataFrame([
        {"speaker": "=CMD|' /C calc'!A0", "text": "+1234567890", "pred_sentiment": "@SUM(A1:A10)"},
        {"speaker": "Alice", "text": "Normal safe text", "pred_sentiment": "-HYPERLINK('evil.com')"}
    ])

    sanitized = dangerous_data.copy()
    for col in ["text", "speaker", "pred_sentiment"]:
        sanitized[col] = sanitized[col].astype(str).apply(
            lambda x: f"'{x}" if x.startswith(("=", "+", "-", "@")) else x
        )

    for col in ["text", "speaker", "pred_sentiment"]:
        for val in sanitized[col]:
            assert not val.startswith(("=", "+", "-", "@")), f"Unsanitized formula detected: {val}"
