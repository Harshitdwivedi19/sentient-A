"""
tests/test_whatsapp_parser.py

Unit tests for WhatsApp export ingestion:
- Android format verification
- iOS format verification
- Multi-line handling
- System notice scrubbing
- Sessionization on inactivity gaps
"""

import pytest
from src.whatsapp_parser import parse_whatsapp_raw_lines, sessionize_messages


def test_android_and_ios_parsing():
    sample_lines = [
        "12/10/2023, 10:15 - Alice: Hey Bob, how are you doing today?",
        "12/10/2023, 10:16 - Bob: I am doing great! Excited about the project.",
        "[12/10/2023, 10:17:30 AM] Alice: Awesome! Let us sync at noon.",
    ]
    records = parse_whatsapp_raw_lines(sample_lines)
    assert len(records) == 3
    assert records[0]["speaker"] == "Alice"
    assert records[0]["text"] == "Hey Bob, how are you doing today?"
    assert records[1]["speaker"] == "Bob"
    assert records[2]["speaker"] == "Alice"


def test_multiline_message_concatenation():
    sample_lines = [
        "15/08/23, 14:00 - Alice: Here is the plan:\n",
        "Step 1: Ingest WhatsApp logs\n",
        "Step 2: Run inference\n",
        "15/08/23, 14:02 - Bob: Sounds good!\n",
    ]
    records = parse_whatsapp_raw_lines(sample_lines)
    assert len(records) == 2
    assert "Step 1: Ingest WhatsApp logs" in records[0]["text"]
    assert "Step 2: Run inference" in records[0]["text"]
    assert records[1]["speaker"] == "Bob"


def test_system_notice_filtering():
    sample_lines = [
        "10/05/2023, 09:00 - Messages and calls are end-to-end encrypted. No one outside of this chat, not even WhatsApp, can read or listen to them.",
        "10/05/2023, 09:01 - Alice: Good morning!",
        "10/05/2023, 09:02 - Bob: <Media omitted>",
        "10/05/2023, 09:03 - Bob: This message was deleted",
        "10/05/2023, 09:04 - Bob: Did you see the file?",
    ]
    records = parse_whatsapp_raw_lines(sample_lines)
    # Only "Good morning!" and "Did you see the file?" should remain
    assert len(records) == 2
    assert records[0]["text"] == "Good morning!"
    assert records[1]["text"] == "Did you see the file?"


def test_dialogue_sessionization_gap():
    sample_lines = [
        # Session 0: Morning conversation
        "01/01/2024, 09:00 - Alice: Happy New Year!",
        "01/01/2024, 09:05 - Bob: Happy New Year Alice!",
        # Session 1: Evening conversation (gap > 2 hours)
        "01/01/2024, 18:00 - Alice: Any plans for tonight?",
        "01/01/2024, 18:02 - Bob: Just resting at home.",
    ]
    records = parse_whatsapp_raw_lines(sample_lines)
    df = sessionize_messages(records, inactivity_gap_minutes=120)

    assert len(df) == 4
    # Check that dialogue_id splits correctly
    assert df.loc[0, "dialogue_id"] == 0
    assert df.loc[0, "turn_id"] == 0
    assert df.loc[1, "dialogue_id"] == 0
    assert df.loc[1, "turn_id"] == 1

    assert df.loc[2, "dialogue_id"] == 1
    assert df.loc[2, "turn_id"] == 0
    assert df.loc[3, "dialogue_id"] == 1
    assert df.loc[3, "turn_id"] == 1
