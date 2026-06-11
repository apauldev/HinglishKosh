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
    # Greetings & basics
    "नमस्ते": "namaste", "हाँ": "haan", "नहीं": "nahi", "हां": "haan",
    "ठीक": "theek", "बिल्कुल": "bilkul", "धन्यवाद": "dhanyavaad",
    "माफ़": "maaf", "कृपया": "kripya",
    # Food & drink
    "पानी": "paani", "खाना": "khana", "चाय": "chai", "दूध": "doodh",
    "रोटी": "roti", "दाल": "daal", "चावल": "chawal", "सब्ज़ी": "sabzi",
    "मीठा": "meetha", "खट्टा": "khatta", "नमक": "namak", "मिर्च": "mirch",
    "हल्दी": "haldi", "जीरा": "jeera", "अदरक": "adrak", "लहसुन": "lahsun",
    "प्याज़": "pyaaz", "टमाटर": "tamatar", "आलू": "aaloo", "पनीर": "paneer",
    "दही": "dahi", "लस्सी": "lassi", "जूस": "juice", "केला": "kela",
    "सेब": "seb", "अंगूर": "angoor", "आम": "aam", "नींबू": "nimbu",
    "इलायची": "elaichi", "दालचीनी": "dalchini", "मेथी": "methi",
    "धनिया": "dhaniya", "पुदीना": "pudina", "मछली": "machli",
    "काली मिर्च": "kali mirch", "लाल मिर्च": "lal mirch",
    # Family
    "माँ": "maa", "पिता": "pita", "भाई": "bhai", "बहन": "behen",
    "बेटा": "beta", "बेटी": "beti", "दादा": "dada", "दादी": "dadi",
    "चाचा": "chacha", "चाची": "chachi", "मामा": "mama", "मामी": "mami",
    "बुआ": "bua", "ताया": "taya", "ताई": "tai",
    # Body
    "सिर": "sir", "आँख": "aankh", "कान": "kaan", "नाक": "naak",
    "मुँह": "munh", "हाथ": "haath", "पैर": "pair", "दिल": "dil",
    "पेट": "pet", "कमर": "kamar", "गर्दन": "gardan", "कंधा": "kandha",
    # Places
    "घर": "ghar", "देश": "desh", "शहर": "shahar", "गाँव": "gaon",
    "सड़क": "sadak", "बाज़ार": "bazaar", "दुकान": "dukaan",
    "स्कूल": "school", "अस्पताल": "aspatal", "मंदिर": "mandir",
    # Animals
    "कुत्ता": "kutta", "बिल्ली": "billi", "गाय": "gaay", "भैंस": "bhains",
    "घोड़ा": "ghoda", "हाथी": "haathi", "शेर": "sher", "बंदर": "bandar",
    "चिड़िया": "chidiya", "मोर": "mor", "मछली": "machhli",
    # Common verbs/nouns
    "पैसा": "paisa", "काम": "kaam", "प्यार": "pyaar", "दोस्त": "dost",
    "यार": "yaar", "बच्चा": "bachcha", "औरत": "aurat", "आदमी": "aadmi",
    "लड़का": "ladka", "लड़की": "ladki", "बूढ़ा": "boodha", "जवान": "jawaan",
    "अच्छा": "achcha", "बुरा": "bura", "बड़ा": "bada", "छोटा": "chhota",
    "नया": "naya", "पुराना": "purana", "लंबा": "lamba", "छोटा": "chhota",
    "सोना": "sona", "चाँदी": "chandi", "ताँबा": "tamba", "लोहा": "loha",
    "आग": "aag", "हवा": "hawa", "पानी": "paani", "धूप": "dhoop",
    "बारिश": "barish", "बर्फ़": "barf", "बिजली": "bijli",
    "सुबह": "subah", "शाम": "shaam", "रात": "raat", "दिन": "din",
    "रात": "raat", "आज": "aaj", "कल": "kal", "अभी": "abhi",
    "कभी": "kabhi", "हमेशा": "hamesha", "कभी-कभी": "kabhi-kabhi",
    # Question words
    "क्या": "kya", "कौन": "kaun", "कहाँ": "kahaan", "कब": "kab",
    "क्यों": "kyon", "कैसा": "kaisa", "कितना": "kitna",
    # Numbers
    "एक": "ek", "दो": "do", "तीन": "teen", "चार": "chaar", "पाँच": "paanch",
    "छह": "chhah", "सात": "saat", "आठ": "aath", "नौ": "nau", "दस": "das",
    # Adjectives
    "बहुत": "bahut", "थोड़ा": "thoda", "सारा": "saara", "कोई": "koi",
    "सब": "sab", "हर": "har", "कुछ": "kuch", "और": "aur",
    "यह": "yeh", "वह": "woh", "ये": "ye", "वो": "wo",
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


def iso_to_hinglish(text: str) -> str:
    """Convert ISO 15919 / academic romanization to informal Hinglish.

    Strips diacritics and maps to common Indian spellings:
      cāy → chai, āg → aag, havā → hawa, pānī → paani
    """
    if not text:
        return ""

    # Step 1: Strip diacritics with smart vowel handling
    # Long vowels: ā→aa, ī→ee, ū→oo
    # Short vowels stay as-is
    replacements = [
        ("ā", "aa"), ("ī", "ee"), ("ū", "oo"),
        ("ē", "e"), ("ō", "o"),
        ("ṛ", "ri"), ("ṝ", "ri"),
        ("ṃ", "n"), ("ṁ", "n"), ("ḥ", "h"),
        ("ṅ", "n"), ("ñ", "n"), ("ṇ", "n"),
        ("ṭ", "t"), ("ḍ", "d"),
        ("ṣ", "sh"), ("ś", "sh"),
    ]
    result = text
    for old, new in replacements:
        result = result.replace(old, new)

    # Step 2: Handle trailing long vowels
    # "aa" at end of word → "a" (havaa → hawa, sonaa → sona)
    result = re.sub(r"aa$", "a", result)
    # "ee" at end → "i" (paanee → paani)
    result = re.sub(r"ee$", "i", result)

    # Step 3: Common word corrections
    lower = result.lower().strip()
    hinglish_words = {
        "cay": "chai", "caay": "chai",
        "ag": "aag",
        "pani": "paani", "panii": "paani",
        "dudh": "doodh",
        "kitab": "kitab", "kitaab": "kitab",
        "machli": "machli", "machlee": "machli",
        "sona": "sona", "sonaa": "sona",
        "hava": "hawa", "havaa": "hawa", "hawa": "hawa",
        "vaise": "waise", "vaisa": "waisa",
        "vo": "wo", "voh": "woh",
    }
    if lower in hinglish_words:
        return hinglish_words[lower]

    # Step 4: Final cleanup
    result = re.sub(r"\s+", " ", result).strip()
    return result


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
