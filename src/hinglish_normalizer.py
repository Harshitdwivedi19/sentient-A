"""
src/hinglish_normalizer.py

Phonetic normalization, elongation compression, script detection,
and transliteration utilities for Hindi (Devanagari) and Romanized Hindi (Hinglish)
conversational WhatsApp dialogue.
"""

import re
from typing import List, Tuple, Dict, Any, Optional

# Curated high-frequency Hinglish conversational markers commonly seen in WhatsApp
HINGLISH_MARKERS = {
    # Auxiliary verbs & copulas
    "hai", "hain", "ho", "hu", "hoon", "tha", "thi", "the", "raha", "rahi", "rahe",
    "hoga", "hogi", "hoge", "kar", "karo", "karna", "kare", "karta", "karti",
    "gaya", "gayi", "gaye", "diya", "diyi", "diye", "liya", "liye", "chahiye",
    # Negations & questions
    "nahi", "nhi", "nahin", "na", "mat", "kya", "kyu", "kyun", "kab", "kahan", "kaise", "kaun", "kitna", "kitni",
    # Pronouns & address terms
    "bhai", "yaar", "yrr", "dost", "mera", "meri", "mere", "tera", "teri", "tere",
    "apna", "apni", "apne", "aap", "hum", "tum", "woh", "ye", "yeh", "inhe", "unhe",
    # Conjunctions & prepositions
    "aur", "or", "lekin", "magar", "par", "se", "ko", "me", "mein", "pe", "ka", "ki", "ke",
    "bhi", "toh", "to", "tak", "saath", "liye",
    # Adverbs & intensifiers
    "bohot", "bahut", "bhot", "ekdum", "zyada", "jyada", "kam", "jaldi", "abhi", "aaj", "kal",
    # Sentiment & evaluative adjectives (Positive)
    "accha", "achha", "acha", "badhiya", "mast", "shandar", "zabardast", "dhanyawad",
    "shukriya", "sahi", "theek", "thik", "badiya", "khush", "pyara", "sundar",
    # Sentiment & evaluative adjectives (Negative)
    "bekar", "bakwas", "kharab", "gussa", "pareshan", "dard", "mushkil", "galat",
    "bura", "naraz", "chinta", "dukh", "shikayat", "problem", "fayda"
}

# Devanagari to Roman transliteration mapping for synthetic augmentation
DEVA_VOWELS = {
    'अ': 'a', 'आ': 'aa', 'इ': 'i', 'ई': 'ee', 'उ': 'u', 'ऊ': 'oo',
    'ऋ': 'ri', 'ए': 'e', 'ऐ': 'ai', 'ओ': 'o', 'औ': 'au', 'अं': 'an', 'अः': 'ah'
}

DEVA_MATRAS = {
    'ा': 'a', 'ि': 'i', 'ी': 'ee', 'ु': 'u', 'ू': 'oo', 'ृ': 'ri',
    'े': 'e', 'ै': 'ai', 'ो': 'o', 'ौ': 'au', 'ं': 'n', 'ँ': 'n', '्': ''
}

DEVA_CONSONANTS = {
    'क': 'k', 'ख': 'kh', 'ग': 'g', 'घ': 'gh', 'ङ': 'ng',
    'च': 'ch', 'छ': 'chh', 'ज': 'j', 'झ': 'jh', 'ञ': 'ny',
    'ट': 't', 'ठ': 'th', 'ड': 'd', 'ढ': 'dh', 'ण': 'n',
    'त': 't', 'थ': 'th', 'द': 'd', 'ध': 'dh', 'न': 'n',
    'प': 'p', 'फ': 'ph', 'ब': 'b', 'भ': 'bh', 'म': 'm',
    'य': 'y', 'र': 'r', 'ल': 'l', 'व': 'v', 'श': 'sh', 'ष': 'sh', 'स': 's', 'ह': 'h',
    'ड़': 'd', 'ढ़': 'dh', 'फ़': 'f', 'ज़': 'z', 'क़': 'q', 'ख़': 'kh', 'ग़': 'gh'
}

# Slang & shorthand standardizations for WhatsApp Romanized Hindi
WHATSAPP_SHORTCUTS = {
    "bht": "bohot",
    "bhoot": "bohot",
    "bhoooot": "bohot",
    "nhi": "nahi",
    "nay": "nahi",
    "yrr": "yaar",
    "thx": "thanks",
    "thnx": "thanks",
    "dhnywd": "dhanyawad",
    "plz": "please",
    "pls": "please",
    "thik": "theek",
    "tk": "theek",
    "achaa": "accha",
    "achha": "accha",
    "acha": "accha",
    "buraa": "bura",
    "khrb": "kharab",
    "bdiya": "badhiya",
    "mastt": "mast"
}


def compress_character_elongations(text: str) -> str:
    """
    Collapses 3 or more repeated identical characters down to 2.
    Example:
        'achhaaaaa' -> 'achhaa'
        'booooohot' -> 'boohot'
        'mastttttt' -> 'mastt'
    """
    return re.sub(r'([a-zA-Z\u0900-\u097F])\1{2,}', r'\1\1', text)


def normalize_whatsapp_text(text: str) -> str:
    """
    Cleans and standardizes conversational WhatsApp text:
    - Normalizes multi-spaces
    - Collapses phonetic elongations
    - Normalizes common WhatsApp shorthand tokens
    """
    if not text or not isinstance(text, str):
        return ""

    # Compress elongation
    cleaned = compress_character_elongations(text)

    # Word-level shorthand expansion
    tokens = cleaned.split()
    normalized_tokens = []
    for tok in tokens:
        lower_tok = tok.lower().strip(".,!?:;\"'()[]{}~")
        if lower_tok in WHATSAPP_SHORTCUTS:
            normalized_tokens.append(WHATSAPP_SHORTCUTS[lower_tok])
        else:
            normalized_tokens.append(tok)

    return " ".join(normalized_tokens)


def detect_language_mode(text: str) -> str:
    """
    Classifies text into one of three linguistic modes:
    - 'hi_deva': Written in Devanagari script (हिंदी)
    - 'hi_roman': Written in Romanized Hindi / Hinglish (e.g., 'bohot badhiya service hai bhai')
    - 'en': Standard English conversational text
    """
    if not text or not isinstance(text, str):
        return "en"

    # 1. Check for Devanagari Unicode range: \u0900 - \u097F
    deva_chars = sum(1 for c in text if '\u0900' <= c <= '\u097F')
    total_letters = sum(1 for c in text if c.isalpha())

    if total_letters > 0 and (deva_chars / total_letters) > 0.15:
        return "hi_deva"

    # 2. Check for Hinglish lexical markers
    words = [w.lower().strip(".,!?:;\"'()[]{}~") for w in text.split()]
    hinglish_hits = sum(1 for w in words if w in HINGLISH_MARKERS)

    # If 2 or more distinct Hinglish markers or >= 18% of tokens match
    if hinglish_hits >= 2 or (len(words) > 0 and (hinglish_hits / len(words)) >= 0.18):
        return "hi_roman"

    return "en"


def detect_batch_language(texts: List[str]) -> str:
    """
    Detects predominant language across a dialogue collection of turns.
    Returns: 'hi_deva' | 'hi_roman' | 'en'
    """
    counts = {"hi_deva": 0, "hi_roman": 0, "en": 0}
    for t in texts:
        m = detect_language_mode(t)
        counts[m] += 1

    if counts["hi_deva"] > 0 and counts["hi_deva"] >= 0.25 * len(texts):
        return "hi_deva"
    if counts["hi_roman"] >= 0.25 * len(texts) or (counts["hi_deva"] + counts["hi_roman"]) >= 0.35 * len(texts):
        return "hi_roman"
    return "en"


def transliterate_devanagari_to_roman(text: str) -> str:
    """
    Robust transliteration from Devanagari script to Romanized Hindi (Hinglish).
    Used for automated dataset augmentation and pairing.
    """
    result = []
    i = 0
    n = len(text)

    while i < n:
        c = text[i]
        if c in DEVA_VOWELS:
            result.append(DEVA_VOWELS[c])
            i += 1
        elif c in DEVA_CONSONANTS:
            base = DEVA_CONSONANTS[c]
            # Check next character for matra or virama
            if i + 1 < n:
                next_c = text[i + 1]
                if next_c in DEVA_MATRAS:
                    matra = DEVA_MATRAS[next_c]
                    result.append(base + matra)
                    i += 2
                    continue
                elif next_c == '्':  # Halant / Virama (no inherent vowel)
                    result.append(base)
                    i += 2
                    continue
            # Default inherent schwa 'a' for consonants (omitted at word end in Hindi)
            is_word_end = (i + 1 == n or not ('\u0900' <= text[i + 1] <= '\u097F'))
            if is_word_end:
                result.append(base)
            else:
                result.append(base + 'a')
            i += 1
        elif c in DEVA_MATRAS:
            result.append(DEVA_MATRAS[c])
            i += 1
        else:
            result.append(c)
            i += 1

    out = "".join(result)
    # Clean up double vowels and standardize typical transliterations
    out = re.sub(r'aa+', 'a', out)
    out = re.sub(r'ee+', 'i', out)
    out = re.sub(r'oo+', 'u', out)
    return out
