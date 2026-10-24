"""
tests/test_mobile_and_api.py

Integration verification for:
1. Android Mobile APK binary and assets
2. Unique visual branding identity
3. FastAPI REST server & Mobile endpoints
"""

import sys
import zipfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.api import app

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_android_apk_binary_integrity():
    apk_path = PROJECT_ROOT / "dist" / "SentimentTrajectory.apk"
    assert apk_path.exists(), f"APK file missing at {apk_path}"
    assert apk_path.stat().st_size > 50 * 1024, "APK file is suspiciously small"

    with zipfile.ZipFile(apk_path, "r") as z:
        names = z.namelist()
        assert "classes.dex" in names, "classes.dex missing from APK"
        assert "AndroidManifest.xml" in names, "AndroidManifest.xml missing from APK"
        assert any(n.startswith("assets/") for n in names), "assets/ missing from APK"
        assert any(n.startswith("META-INF/") for n in names), "Digital signature missing from APK"


def test_mobile_assets_and_branding():
    mobile_assets = PROJECT_ROOT / "mobile" / "assets"
    assert (mobile_assets / "index.html").exists(), "Mobile index.html missing"
    assert (mobile_assets / "app.js").exists(), "Mobile app.js missing"
    assert (mobile_assets / "style.css").exists(), "Mobile style.css missing"
    assert (mobile_assets / "logo.png").exists(), "Mobile branding logo missing"

    # Verify custom branding
    branding_dir = PROJECT_ROOT / "assets" / "branding"
    assert (branding_dir / "logo_master_512.png").exists(), "Master logo missing"
    assert (branding_dir / "app_icon.ico").exists(), "Windows app icon missing"


def test_api_health_endpoint(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "supported_models" in data


def test_api_analyze_text_endpoint(client):
    payload = {
        "conversation_text": "Alice: I am frustrated with the delay.\nBob: I understand and I will fix it right now.\nAlice: Thank you very much!",
        "model_type": "baseline",
        "turning_point_threshold": 0.3,
        "context_window": 2
    }
    response = client.post("/api/analyze/text", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "trajectory_stats" in data
    assert "predictions" in data
    assert len(data["predictions"]) == 3
    assert "explanation" in data


def test_mobile_web_mount(client):
    response = client.get("/mobile/")
    assert response.status_code == 200
    assert "Sentient Trajectory" in response.text
