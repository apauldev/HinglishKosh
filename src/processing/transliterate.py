"""Transliteration wrapper — converts Devanagari to Roman (Hinglish).

Uses a rule-based fallback when GoVarnam/IndicTrans models are unavailable.
"""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

# Devanagari to Roman mapping (ISO 15919 inspired, simplified for Hinglish)
_DEVANAGARI_INDEPENDENT_VOWELS = {
    "अ": "a",
    "आ": "aa",
    "इ": "i",
    "ई": "ee",
    "उ": "u",
    "ऊ": "oo",
    "ए": "e",
    "ऐ": "ai",
    "ओ": "o",
    "औ": "au",
    "ऋ": "ri",
}

_DEVANAGARI_MATRAS = {
    "ा": "aa",
    "ि": "i",
    "ी": "ee",
    "ु": "u",
    "ू": "oo",
    "े": "e",
    "ै": "ai",
    "ो": "o",
    "ौ": "au",
    "ृ": "ri",
}

_DEVANAGARI_CONSONANTS = {
    "क": "k",
    "ख": "kh",
    "ग": "g",
    "घ": "gh",
    "ङ": "ng",
    "च": "ch",
    "छ": "chh",
    "ज": "j",
    "झ": "jh",
    "ञ": "ny",
    "ट": "t",
    "ठ": "th",
    "ड": "d",
    "ढ": "dh",
    "ण": "n",
    "त": "t",
    "थ": "th",
    "द": "d",
    "ध": "dh",
    "न": "n",
    "प": "p",
    "फ": "ph",
    "ब": "b",
    "भ": "bh",
    "म": "m",
    "य": "y",
    "र": "r",
    "ल": "l",
    "व": "v",
    "श": "sh",
    "ष": "sh",
    "स": "s",
    "ह": "h",
    # Nukta variants
    "क़": "q",
    "ख़": "kh",
    "ग़": "g",
    "ड़": "d",
    "ढ़": "dh",
    "ऱ": "r",
    "ज़": "z",
    "फ़": "f",
}

_ANUSVARA_SENTINEL = "\x01"

_DEVANAGARI_SIGN_MAP = {
    "ं": _ANUSVARA_SENTINEL,
    "ँ": _ANUSVARA_SENTINEL,
    "ः": "h",
    "्": "",
    "ॐ": "om",
}

_DEVANAGARI_BASE_CONSONANTS = {
    "क",
    "ख",
    "ग",
    "घ",
    "ङ",
    "च",
    "छ",
    "ज",
    "झ",
    "ञ",
    "ट",
    "ठ",
    "ड",
    "ढ",
    "ण",
    "त",
    "थ",
    "द",
    "ध",
    "न",
    "प",
    "फ",
    "ब",
    "भ",
    "म",
    "य",
    "र",
    "ल",
    "व",
    "श",
    "ष",
    "स",
    "ह",
}

_DEVANAGARI_NUMBERS = {
    "०": "0",
    "१": "1",
    "२": "2",
    "३": "3",
    "४": "4",
    "५": "5",
    "६": "6",
    "७": "7",
    "८": "8",
    "९": "9",
}

_DEVANAGARI_NUKTA = "़"
_DEVANAGARI_VIRAMA = "्"


def _compose_nukta_consonant(text: str, index: int) -> tuple[str, int]:
    """Return a composed consonant and how many extra chars were consumed."""
    char = text[index]
    if (
        char in _DEVANAGARI_BASE_CONSONANTS
        and index + 1 < len(text)
        and text[index + 1] == _DEVANAGARI_NUKTA
    ):
        combined = char + _DEVANAGARI_NUKTA
        if combined in _DEVANAGARI_CONSONANTS:
            return combined, 1
    return char, 0


def _should_strip_final_inherent_a(text: str) -> bool:
    """Detect whether a transliterated word should drop a trailing schwa."""
    for char in reversed(text):
        if char.isspace():
            continue
        if unicodedata.category(char)[0] in {"P", "S"}:
            continue
        return char in _DEVANAGARI_CONSONANTS or char in _DEVANAGARI_BASE_CONSONANTS
    return False


# Common Hindi words with well-known romanizations — loaded lazily from JSON
_COMMON_WORDS: dict[str, str] | None = None
_COMMON_WORDS_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "common_words.json"


def _load_common_words() -> dict[str, str]:
    """Load common words from data/common_words.json (cached)."""
    global _COMMON_WORDS
    if _COMMON_WORDS is None:
        if _COMMON_WORDS_PATH.exists():
            with open(_COMMON_WORDS_PATH, encoding="utf-8") as f:
                _COMMON_WORDS = json.load(f)
        else:
            _COMMON_WORDS = {}
    return _COMMON_WORDS


_V_TO_W_EXCEPTIONS = frozenset(
    {
        "vakeel",
        "vyapaari",
        "vyaapaar",
    }
)


# ISO 15919 → Hinglish word-level corrections (applied after rule-based conversion)
_ISO_WORD_FIXES: dict[str, str] = {
    "woh": "woh",
    "yeh": "yeh",
    "wah": "woh",
    "yah": "yeh",
    "bahan": "behen",
    "mai": "main",
    "maidam": "madam",
    "sar": "sir",
    "accha": "achcha",
    "gae": "gaye",
    "chah": "chhah",
    "maan": "maa",
    "kŕpaya": "kripya",
    "koolha": "kulha",
    "eeshwar": "ishwar",
    "eeshwara": "ishwar",
    "bhagwaan": "bhagwan",
    "bhagawaan": "bhagwan",
    "allaah": "allah",
    "jeeja": "jija",
    "naxoon": "nakhun",
    "naaxoon": "nakhun",
    "nakhoon": "nakhun",
    "jnyan": "gyaan",
    "jnyaan": "gyaan",
    "zindagee": "zindagi",
    "khadee": "khadi",
    "ladkee": "ladki",
    "betee": "beti",
    "nadee": "nadi",
    "daada": "dada",
    "daadi": "dadi",
    "naana": "nana",
    "naani": "nani",
    "chaacha": "chacha",
    "chaachi": "chachi",
    "maama": "mama",
    "maami": "mami",
    "paapa": "papa",
    "taaya": "taya",
    "taai": "tai",
    "bhaabhi": "bhabhi",
    "saala": "sala",
    "saali": "sali",
    "bhaai": "bhai",
    "jaao": "jao",
    "khaao": "khao",
    "gyaarah": "gyarah",
    "baarah": "barah",
    "athaarah": "atharah",
    "tumhaara": "tumhara",
    "maatha": "matha",
    "jeebh": "jibh",
    "khaana": "khana",
    "chaawal": "chawal",
    "tamaatar": "tamatar",
    "aalu": "aaloo",
    "joos": "juice",
    "neembu": "nimbu",
    "dhanyawaad": "dhanyavaad",
    "aao": "aao",
    "baap": "baap",
    "saas": "saas",
    "daamaad": "daamaad",
    "sarkar": "sarkar",
    "chunav": "chunav",
    "azaadi": "azaadi",
    "ganatantra": "ganatantra",
    "pujari": "pujari",
    "maulvi": "maulvi",
    "padri": "padri",
}


def _apply_v_to_w(roman: str) -> str:
    """Convert 'v' to 'w' in transliterated text (Hindi व → w).

    Keeps 'v' at the start of words (common in Hindi romanization: vidya, vyapaar).
    Exceptions: words where 'v' is the correct English-like spelling.
    """
    words = roman.split(" ")
    result = []
    for word in words:
        if word.lower() in _V_TO_W_EXCEPTIONS:
            result.append(word)
        else:
            # Keep 'v' at start of word, convert 'v' elsewhere to 'w'
            if word.startswith("v") or word.startswith("V"):
                result.append(word[0] + re.sub(r"v", "w", word[1:]))
            else:
                result.append(re.sub(r"v", "w", word))
    return " ".join(result)


def transliterate_rule_based(text: str) -> str:
    """Rule-based Devanagari to Roman transliteration.

    This is a fallback — use GoVarnam or IndicTrans for production quality.
    """
    if not text:
        return ""

    text = unicodedata.normalize("NFC", text)

    # Check common words first
    common = _load_common_words()
    if text in common:
        return common[text]

    result = []
    i = 0
    while i < len(text):
        char = text[i]

        char, consumed = _compose_nukta_consonant(text, i)
        i += consumed

        if char in _DEVANAGARI_INDEPENDENT_VOWELS:
            result.append(_DEVANAGARI_INDEPENDENT_VOWELS[char])
        elif char in _DEVANAGARI_CONSONANTS:
            base = _DEVANAGARI_CONSONANTS[char]
            next_char = text[i + 1] if i + 1 < len(text) else ""
            if next_char == _DEVANAGARI_VIRAMA:
                result.append(base)
                i += 1
            elif next_char in _DEVANAGARI_MATRAS:
                result.append(base + _DEVANAGARI_MATRAS[next_char])
                i += 1
            else:
                result.append(base + "a")
        elif char in _DEVANAGARI_NUMBERS:
            result.append(_DEVANAGARI_NUMBERS[char])
        elif char in _DEVANAGARI_SIGN_MAP:
            result.append(_DEVANAGARI_SIGN_MAP[char])
        elif "\u0900" <= char <= "\u097f":
            # Unknown Devanagari character — skip
            pass
        else:
            # Non-Devanagari (Latin, digits, punctuation) — keep as-is
            result.append(char)

        i += 1

    # Clean up repeated letters and trim the final inherent vowel for Devanagari words.
    roman = "".join(result)
    roman = re.sub(r"jny", "gy", roman)

    # v → w (Hindi व is pronounced 'w' in most words)
    roman = _apply_v_to_w(roman)

    # Anusvāra assimilation: ṃ → m before labial consonants (p, ph, b, bh, m)
    roman = re.sub(_ANUSVARA_SENTINEL + r"([pbm])", r"m\1", roman)
    roman = roman.replace(_ANUSVARA_SENTINEL, "n")

    if _should_strip_final_inherent_a(text) and roman.endswith("a"):
        roman = roman[:-1]

    # Collapse trailing double vowels (inherent vowel at word end)
    # Keep mid-word 'aa' from ā matra (vyapaar, kahaan, gyaan)
    roman = re.sub(r"aa\b", "a", roman)
    roman = re.sub(r"ee\b", "i", roman)
    roman = re.sub(r"oo\b", "u", roman)

    roman = re.sub(r"(.)\1{2,}", r"\1\1", roman)  # max 2 repeats
    roman = re.sub(r"\s+", " ", roman).strip()

    return roman


def iso_to_hinglish(text: str) -> str:
    """Convert ISO 15919 / academic romanization to informal Hinglish.

    Strips diacritics and maps to common Indian spellings:
      cāy → chai, āg → aag, havā → hawa, pānī → paani
    """
    if not text:
        return ""

    result = text

    # Step 0: Handle combining characters first (e.g., ā̃, ĩ)
    result = re.sub(r"ā̃", "aan", result)
    result = re.sub(r"ī̃", "i", result)
    result = re.sub(r"ū̃", "oon", result)
    result = re.sub(r"ẽ", "en", result)
    result = re.sub(r"õ", "on", result)
    result = re.sub(r"[\u0300-\u036f]", "", result)
    result = result.replace("jñ", "gy")

    # Step 1: Strip diacritics with smart vowel handling
    _iso_diacritic_map = [
        ("ā", "aa"),
        ("ī", "i"),
        ("ū", "oo"),
        ("ē", "e"),
        ("ō", "o"),
        ("ṛ", "ri"),
        ("ṝ", "ri"),
        ("ṃ", "n"),
        ("ṁ", "n"),
        ("ḥ", "h"),
        ("ṅ", "n"),
        ("ñ", "n"),
        ("ṇ", "n"),
        ("ṭ", "t"),
        ("ḍ", "d"),
        ("ṣ", "sh"),
        ("ś", "sh"),
        ("ġ", "g"),
    ]
    for old, new in _iso_diacritic_map:
        result = result.replace(old, new)

    # Step 2: Handle remaining nasalized vowels
    result = re.sub(r"ã", "an", result)
    result = re.sub(r"ĩ", "in", result)
    result = re.sub(r"ũ", "un", result)

    # Step 3: Convert c → ch for Hindi palatal (च) before vowels
    result = re.sub(r"c([aeiou])", r"ch\1", result)
    result = re.sub(r"c$", "ch", result)

    # Step 4: v → w (Hindi व is pronounced 'w' in most words)
    result = _apply_v_to_w(result)

    # Step 5: ay → ai (चाय: cāy → chai, not chaay)
    result = re.sub(r"aay$", "ai", result)
    result = re.sub(r"aay([^aeiou])", r"ai\1", result)
    result = re.sub(r"ay$", "ai", result)
    result = re.sub(r"ay([^aeiou])", r"ai\1", result)

    # Step 6: Collapse trailing double vowels (inherent vowel at word end)
    result = re.sub(r"aa$", "a", result)
    result = re.sub(r"ee$", "i", result)
    result = re.sub(r"oo$", "u", result)

    # Step 7: Fix anusvara before labials
    result = re.sub(r"nm", "m", result)
    result = re.sub(r"nb", "mb", result)
    result = re.sub(r"np", "mp", result)

    # Step 8: Common word corrections
    lower = result.lower()
    if lower in _ISO_WORD_FIXES:
        return _ISO_WORD_FIXES[lower]

    # Step 9: Final cleanup
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
