"""
src/whatsapp_parser.py

Ingestion and normalization engine for WhatsApp exported chat logs (.txt).
Supports:
- Android format: "15/10/2023, 14:32 - Sender: Message"
- iOS format: "[15/10/23, 2:32:15 PM] Sender: Message"
- Multi-line message continuation
- System message filtering (encryption notices, group updates)
- Media omission scrubbing (<Media omitted>)
- Automatic dialogue sessionization based on inactivity thresholds
"""

import re
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd

logger = logging.getLogger(__name__)

# Standard WhatsApp regex patterns
# Pattern 1 (Android): DD/MM/YY(YY), HH:MM(:SS) (AM/PM) - Sender: Message
ANDROID_REGEX = re.compile(
    r"^(\d{1,2}/\d{1,2}/\d{2,4}),?\s+(\d{1,2}:\d{2}(?::\d{2})?(?:\s*[apAP][mM])?)\s+-\s+([^:]+?):\s*(.*)$"
)

# Pattern 2 (iOS): [DD/MM/YY(YY), HH:MM(:SS) (AM/PM)] Sender: Message
IOS_REGEX = re.compile(
    r"^\[(\d{1,2}/\d{1,2}/\d{2,4}),?\s+(\d{1,2}:\d{2}(?::\d{2})?(?:\s*[apAP][mM])?)\]\s+([^:]+?):\s*(.*)$"
)

# System notice patterns to ignore
SYSTEM_NOTICE_PATTERNS = [
    re.compile(r"Messages and calls are end-to-end encrypted", re.IGNORECASE),
    re.compile(r"<Media omitted>", re.IGNORECASE),
    re.compile(r"image omitted", re.IGNORECASE),
    re.compile(r"video omitted", re.IGNORECASE),
    re.compile(r"audio omitted", re.IGNORECASE),
    re.compile(r"sticker omitted", re.IGNORECASE),
    re.compile(r"This message was deleted", re.IGNORECASE),
    re.compile(r"You deleted this message", re.IGNORECASE),
    re.compile(r"created group", re.IGNORECASE),
    re.compile(r"added you", re.IGNORECASE),
    re.compile(r"changed the subject", re.IGNORECASE),
]


def is_system_notice(text: str) -> bool:
    """Check if message is an automated WhatsApp system message."""
    for pattern in SYSTEM_NOTICE_PATTERNS:
        if pattern.search(text):
            return True
    return False


def parse_timestamp(date_str: str, time_str: str) -> Optional[datetime]:
    """Attempt parsing multiple common date-time permutations in WhatsApp exports."""
    date_str = date_str.strip()
    time_str = time_str.strip().replace("\u202f", " ")  # Clean narrow no-break space
    
    # Common format combinations
    date_formats = ["%d/%m/%y", "%d/%m/%Y", "%m/%d/%y", "%m/%d/%Y"]
    time_formats = [
        "%H:%M", "%H:%M:%S",
        "%I:%M %p", "%I:%M:%S %p",
        "%I:%M%p", "%I:%M:%S%p"
    ]
    
    for df in date_formats:
        for tf in time_formats:
            fmt = f"{df} {tf}"
            try:
                return datetime.strptime(f"{date_str} {time_str}", fmt)
            except ValueError:
                continue
    return None


def parse_whatsapp_raw_lines(raw_lines: List[str]) -> List[Dict[str, Any]]:
    """Parse raw text lines into structured records, assembling multi-line messages."""
    records = []
    current_record = None

    for line_idx, line in enumerate(raw_lines):
        line_clean = line.strip("\r\n\ufeff")
        if not line_clean:
            continue

        android_match = ANDROID_REGEX.match(line_clean)
        ios_match = IOS_REGEX.match(line_clean)
        match = android_match or ios_match

        if match:
            # Commit previously accumulated message
            if current_record:
                if not is_system_notice(current_record["text"]):
                    records.append(current_record)
                current_record = None

            date_str, time_str, sender, message_text = match.groups()
            sender = sender.strip()

            # Ignore system lines where sender is WhatsApp notice
            if is_system_notice(sender) or is_system_notice(message_text):
                continue

            dt = parse_timestamp(date_str, time_str)
            current_record = {
                "timestamp": dt,
                "speaker": sender,
                "text": message_text.strip(),
            }
        else:
            # Continuation of previous multi-line message
            if current_record:
                current_record["text"] += " " + line_clean.strip()

    # Commit last message
    if current_record and not is_system_notice(current_record["text"]):
        records.append(current_record)

    return records


def sessionize_messages(
    records: List[Dict[str, Any]],
    inactivity_gap_minutes: int = 120
) -> pd.DataFrame:
    """
    Cluster a continuous stream of chat messages into discrete conversation sessions (dialogues).
    A new dialogue starts when the time gap between consecutive messages exceeds inactivity_gap_minutes.
    """
    if not records:
        return pd.DataFrame(columns=["dialogue_id", "turn_id", "speaker", "text", "timestamp"])

    dialogue_id = 0
    turn_id = 0
    last_dt = None
    processed_rows = []

    for rec in records:
        curr_dt = rec["timestamp"]

        # If timestamps are present, check inactivity gap
        if curr_dt and last_dt:
            time_gap = (curr_dt - last_dt).total_seconds() / 60.0
            if time_gap >= inactivity_gap_minutes:
                dialogue_id += 1
                turn_id = 0

        # Minimum text length validation
        text = rec["text"].strip()
        if not text:
            continue

        processed_rows.append({
            "dialogue_id": dialogue_id,
            "turn_id": turn_id,
            "speaker": rec["speaker"],
            "text": text,
            "timestamp": curr_dt.isoformat() if curr_dt else None,
        })

        turn_id += 1
        if curr_dt:
            last_dt = curr_dt

    df = pd.DataFrame(processed_rows)
    return df


def parse_whatsapp_file(
    file_path: Path,
    inactivity_gap_minutes: int = 120
) -> pd.DataFrame:
    """
    High-level entrypoint: loads an exported WhatsApp .txt file, parses messages,
    filters noise, and assigns dialogue_id and turn_id.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"WhatsApp file not found: {file_path}")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except UnicodeDecodeError:
        with open(file_path, "r", encoding="latin-1") as f:
            lines = f.readlines()

    records = parse_whatsapp_raw_lines(lines)
    df = sessionize_messages(records, inactivity_gap_minutes=inactivity_gap_minutes)
    logger.info(f"Parsed {len(df):,} WhatsApp turns across {df['dialogue_id'].nunique() if len(df) else 0:,} dialogue sessions.")
    return df
