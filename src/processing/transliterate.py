"""Transliteration wrapper — converts Devanagari to Roman (Hinglish).

Uses a rule-based fallback when GoVarnam/IndicTrans models are unavailable.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Optional

# Devanagari to Roman mapping (ISO 15919 inspired, simplified for Hinglish)
_DEVANAGARI_MAP = {
    # Vowels
    "अ": "a", "आ": "aa", "इ": "i", "ई": "ee", "उ": "u", "ऊ": "oo",
    "ए": "e", "ऐ": "ai", "ओ": "o", "औ": "au", "ऋ": "ri",
    # Matras (dependent vowels)
    "ा": "aa", "ि": "i", "ी": "ee", "ु": "u", "ू": "oo",
    "े": "e", "ै": "ai", "ो": "o", "ौ": "au", "ृ": "ri",
    # Consonants
    "क": "k", "ख": "kh", "ग": "g", "घ": "gh", "ङ": "ng",
    "च": "ch", "छ": "chh", "ज": "j", "झ": "jh", "ञ": "ny",
    "ट": "t", "ठ": "th", "ड": "d", "ढ": "dh", "ण": "n",
    "त": "t", "थ": "th", "द": "d", "ध": "dh", "न": "n",
    "प": "p", "फ": "ph", "ब": "b", "भ": "bh", "म": "m",
    "य": "y", "र": "r", "ल": "l", "व": "v", "श": "sh",
    "ष": "sh", "स": "s", "ह": "h",
    # Nukta variants
    "क़": "q", "ख़": "kh", "ग़": "g", "ज़": "z", "फ़": "f",
    # Numbers
    "०": "0", "१": "1", "२": "2", "३": "3", "४": "4",
    "५": "5", "६": "6", "७": "7", "८": "8", "९": "9",
    # Special
    "ं": "n", "ँ": "n", "ः": "h", "्": "", "़": "",
    "ॐ": "om",
}

# Common Hindi words with well-known romanizations
_COMMON_WORDS = {
    "नमस्ते": "namaste", "पानी": "paani", "खाना": "khana", "सोना": "sona",
    "किताब": "kitab", "घर": "ghar", "दूध": "doodh", "चाय": "chai",
    "रोटी": "roti", "दाल": "daal", "चावल": "chawal", "मछली": "machli",
    "सब्ज़ी": "sabzi", "मीठा": "meetha", "खट्टा": "khatta", "नमक": "namak",
    "मिर्च": "mirch", "हल्दी": "haldi", "जीरा": "jeera", "अदरक": "adrak",
    "लहसुन": "lahsun", "प्याज़": "pyaaz", "टमाटर": "tamatar", "आलू": "aaloo",
    "पनीर": "paneer", "दही": "dahi", "लस्सी": "lassi", "जूस": "juice",
    "केला": "kela", "सेब": "seb", "अंगूर": "angoor", "आम": "aam",
    "नींबू": "nimbu", "इलायची": "elaichi", "दालचीनी": "dalchini",
    "मेथी": "methi", "धनिया": "dhaniya", "पुदीना": "pudina",
    "काली मिर्च": "kali mirch", "लाल मिर्च": "lal mirch",
}


def transliterate_rule_based(text: str) -> str:
    """Rule-based Devanagari to Roman transliteration.

    This is a fallback — use GoVarnam or IndicTrans for production quality.
    """
    if not text:
        return ""

    # Check common words first
    if text in _COMMON_WORDS:
        return _COMMON_WORDS[text]

    result = []
    i = 0
    while i < len(text):
        char = text[i]

        if char in _DEVANAGARI_MAP:
            result.append(_DEVANAGARI_MAP[char])
        elif "\u0900" <= char <= "\u097F":
            # Unknown Devanagari character — skip
            pass
        else:
            # Non-Devanagari (Latin, digits, punctuation) — keep as-is
            result.append(char)

        i += 1

    # Clean up double vowels and consonants
    roman = "".join(result)
    roman = re.sub(r"(.)\1{2,}", r"\1\1", roman)  # max 2 repeats
    roman = re.sub(r"\baa\b", "aa", roman)
    roman = re.sub(r"\s+", " ", roman).strip()

    return roman


def transliterate(text: str, method: str = "rule_based") -> str:
    """Transliterate Devanagari text to Roman script.

    Args:
        text: Devanagari text to transliterate.
        method: "rule_based" (always available) or "govarnam" / "indictrans".

    Returns:
        Romanized text.
    """
    if not text:
        return ""

    if method == "rule_based":
        return transliterate_rule_based(text)

    # Try GoVarnam
    if method == "govarnam":
        try:
            from varnam import varnam  # type: ignore
            result = varnam.transliterate(text)
            if result:
                return result
        except (ImportError, Exception):
            pass
        # Fallback
        return transliterate_rule_based(text)

    # Try IndicTrans
    if method == "indictrans":
        try:
            from indictrans import Transliterator  # type: ignore
            t = Transliterator(source="deva", target="roman", roman=True)
            result = t.transliterate(text)
            if result:
                return result
        except (ImportError, Exception):
            pass
        return transliterate_rule_based(text)

    return transliterate_rule_based(text)
