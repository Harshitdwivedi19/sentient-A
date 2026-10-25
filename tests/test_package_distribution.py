"""
tests/test_package_distribution.py

Automated tests for sentient-a Python package metadata, distribution artifacts,
and command-line interface execution.
"""

import sys
import subprocess
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_package_import_and_metadata():
    """Verify sentient package can be imported directly and exposes required symbols."""
    import sentient

    assert hasattr(sentient, "__version__")
    assert sentient.__version__ == "1.2.0"
    assert hasattr(sentient, "ConversationSentimentAnalyzer")
    assert hasattr(sentient, "compute_trajectory_statistics")
    assert hasattr(sentient, "generate_executive_summary_and_results")
    assert hasattr(sentient, "normalize_whatsapp_text")
    assert hasattr(sentient, "detect_language_mode")


def test_package_programmatic_analysis():
    """Verify programmatic conversation analysis through the top-level package namespace."""
    from sentient import ConversationSentimentAnalyzer

    analyzer = ConversationSentimentAnalyzer(default_model="hindi_baseline")
    dialogue = (
        "Customer: Mera order abhi tak deliver nahi hua, bohot delay hai\n"
        "Support: Sir, hum abhi courier se coordinate karke update dete hain\n"
        "Customer: Theek hai, shukriya aapki madad ke liye"
    )
    result = analyzer.analyze_conversation(dialogue, model_type="auto")
    assert result["success"] is True
    assert "summary_and_results" in result

    sum_res = result["summary_and_results"]
    assert "executive_summary" in sum_res
    assert "analysis_results" in sum_res
    assert "health_status" in sum_res["analysis_results"]


def test_distribution_artifacts_exist():
    """Verify built .whl and .tar.gz distribution archives exist in dist/ directory."""
    dist_dir = PROJECT_ROOT / "dist"
    wheels = list(dist_dir.glob("sentient_a-*-py3-none-any.whl"))
    tarballs = list(dist_dir.glob("sentient_a-*.tar.gz"))

    assert len(wheels) >= 1, "Expected sentient_a wheel (.whl) in dist/"
    assert len(tarballs) >= 1, "Expected sentient_a source distribution (.tar.gz) in dist/"

    # Check non-trivial size
    assert wheels[0].stat().st_size > 10_000, "Wheel archive unexpectedly small"
    assert tarballs[0].stat().st_size > 10_000, "Sdist archive unexpectedly small"


def test_cli_version_and_help():
    """Verify sentient CLI entrypoint runs correctly via subprocess."""
    # Test --version
    res_v = subprocess.run(
        [sys.executable, "-m", "sentient.cli", "--version"],
        capture_output=True,
        text=True,
        check=True
    )
    assert "sentient-a 1.2.0" in res_v.stdout

    # Test --help
    res_h = subprocess.run(
        [sys.executable, "-m", "sentient.cli", "--help"],
        capture_output=True,
        text=True,
        check=True
    )
    assert "usage: sentient" in res_h.stdout
    assert "analyze" in res_h.stdout
    assert "gui" in res_h.stdout
    assert "api" in res_h.stdout
