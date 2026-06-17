"""Error audit — measures where the dictionary makes mistakes.

Runs four independent audits:
  1. Transliteration accuracy — classifies rule-based engine failures
  2. Merge quality — checks WordNet vs Wiktionary overlap and conflicts
  3. Safety filter coverage — finds gaps in profanity detection
  4. Confidence faithfulness — checks if scores correlate with quality signals

Usage:
    python -m src.quality.audit
    python -m src.quality.audit --audit transliteration,merge
    python -m src.quality.audit --data-dir data/output --sample 500
"""

from __future__ import annotations

import argparse
import json
import logging
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from src.processing.transliterate import (
    _load_common_words,
    transliterate_rule_based,
)
from src.safety.profanity_list import ProfanityMatcher, _normalize_text

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
)
logger = logging.getLogger("audit")


# ─── Data ───────────────────────────────────────────────────────────────────

DIACRITICS = frozenset(
    "\u0101\u012b\u016b\u0113\u014d\u1e43\u1e25\u1e63\u015b\u1e6d\u1e0d\u1e47\u1e45\u00f1"
)
PASS_WORDS_500 = {
    "अंगूठा": "angootha",
    "अंगूर": "angoor",
    "अंदर": "andar",
    "अंबर": "ambar",
    "अचार": "achaar",
    "अदरक": "adrak",
    "अध्यापक": "adhyapak",
    "अनशन": "anashan",
    "अनार": "anaar",
    "अन्याय": "anyaay",
    "अस्पताल": "aspatal",
    "आँख": "aankh",
    "आग": "aag",
    "आज": "aaj",
    "आना": "aana",
    "आम": "aam",
    "आलू": "aaloo",
    "इंजीनियर": "engineer",
    "इज़्ज़त": "izzat",
    "उंगली": "ungli",
    "उठना": "uthna",
    "उदास": "udaas",
    "उल्टा": "ulta",
    "उल्लू": "ullu",
    "ऊँचा": "ooncha",
    "ऊपर": "upar",
    "एड़ी": "edi",
    "ओले": "ole",
    "कंधा": "kandha",
    "कच्चा": "kaccha",
    "कछुआ": "kachhua",
    "कटोरा": "katora",
    "कढ़ाही": "kadhai",
    "कपड़ा": "kapda",
    "कपड़े": "kapde",
    "कबूतर": "kabootar",
    "कमज़ोर": "kamzor",
    "कमर": "kamar",
    "करना": "karna",
    "करुणा": "karuna",
    "कल": "kal",
    "कश्ती": "kashti",
    "कहना": "kehna",
    "काँटा": "kaanta",
    "कान": "kaan",
    "कार": "car",
    "किसान": "kisan",
    "कुत्ता": "kutta",
    "कुर्ता": "kurta",
    "कूल्हा": "kulha",
    "केला": "kela",
    "कोशिश": "koshish",
    "खजूर": "khajoor",
    "खट्टा": "khatta",
    "खड़ा": "khada",
    "ख़ुश": "khush",
    "ख़ुशी": "khushi",
    "खाली": "khaali",
    "खिड़की": "khidki",
    "खुला": "khula",
    "खून": "khoon",
    "खोना": "khona",
    "गंदा": "ganda",
    "गगन": "gagan",
    "गद्दा": "gadda",
    "गधा": "gadha",
    "गर्दन": "gardan",
    "गर्म": "garm",
    "गर्मी": "garmi",
    "गर्व": "garv",
    "गला": "gala",
    "गली": "gali",
    "गाँव": "gaon",
    "गाना": "gaana",
    "गाय": "gaay",
    "गाली देना": "gaali dena",
    "गिद्ध": "giddh",
    "गिरना": "girna",
    "गिलास": "gilaas",
    "गीला": "geela",
    "गुस्सा": "gussa",
    "गोल": "gol",
    "घंटा": "ghanta",
    "घमंड": "ghamand",
    "घुटना": "ghutna",
    "घोड़ा": "ghoda",
    "चटनी": "chatni",
    "चम्मच": "chammach",
    "चर्चा": "charcha",
    "चलना": "chalna",
    "चाँद": "chaand",
    "चाकू": "chaku",
    "चादर": "chadar",
    "चावल": "chawal",
    "चिंता": "chinta",
    "चिड़िया": "chidiya",
    "चिल्लाना": "chillana",
    "चूल्हा": "choolha",
    "चौड़ा": "chauda",
    "छत": "chhat",
    "छुपाना": "chhupaana",
    "छोटा": "chhota",
    "जंगल": "jungle",
    "जलेबी": "jalebi",
    "ज़मीन": "zameen",
    "जांघ": "jaangh",
    "जागना": "jaagna",
    "जाना": "jaana",
    "जीप": "jeep",
    "जीरा": "jeera",
    "झील": "jheel",
    "टमाटर": "tamatar",
    "ट्रक": "truck",
    "ट्रेन": "train",
    "ठंडा": "thanda",
    "डर": "dar",
    "डॉक्टर": "doctor",
    "तकिया": "takiya",
    "तवा": "tawa",
    "ताकत": "taakat",
    "ताज़ा": "taaza",
    "तालाब": "taalab",
    "तीखा": "teekha",
    "तेंदुआ": "tendua",
    "तेज़": "tez",
    "त्योहार": "tyohaar",
    "थाली": "thaali",
    "दया": "daya",
    "दरवाज़ा": "darwaza",
    "दाँत": "daant",
    "दाढ़ी": "daadhi",
    "दाल": "daal",
    "दिखाना": "dikhaana",
    "दिन": "din",
    "दीवार": "deewar",
    "दुकान": "dukaan",
    "दुख": "dukh",
    "दुनिया": "duniya",
    "दुपट्टा": "dupatta",
    "दूर": "door",
    "देखना": "dekhna",
    "देना": "dena",
    "देश": "desh",
    "दोपहर": "dopahar",
    "दौड़ना": "daudna",
    "धनिया": "dhaniya",
    "धागा": "dhaaga",
    "धीमा": "dheema",
    "धूप": "dhoop",
    "धोती": "dhoti",
    "धोना": "dhona",
    "धोबी": "dhobi",
    "नदी": "nadi",
    "नफ़रत": "nafrat",
    "नया": "naya",
    "नर्स": "nurse",
    "नाई": "nai",
    "नाक": "naak",
    "नाखून": "nakhun",
    "नाग": "naag",
    "नींबू": "nimbu",
    "नीचा": "neecha",
    "नीचे": "neeche",
    "नीचे आना": "neeche aana",
    "पंजा": "panja",
    "पकाना": "pakaana",
    "पक्का": "pakka",
    "पक्षी": "pakshi",
    "पजामा": "pajama",
    "पढ़ना": "padhna",
    "पतला": "patla",
    "पत्थर": "patthar",
    "परसों": "parson",
    "पल": "pal",
    "पलक": "palak",
    "पशु": "pashu",
    "पसीना": "paseena",
    "पाना": "paana",
    "पापड़": "papad",
    "पास": "paas",
    "पिस्ता": "pista",
    "पीठ": "peeth",
    "पीना": "peena",
    "पुराना": "purana",
    "पुल": "pul",
    "पुलिस": "police",
    "पेट": "pet",
    "पेड़": "ped",
    "पैर": "pair",
    "पौधा": "paudha",
    "प्याज़": "pyaaz",
    "प्यार": "pyaar",
    "प्लेट": "plate",
    "फ़ौजी": "fauji",
    "बंदर": "bandar",
    "बड़ा": "bada",
    "बढ़ई": "badhai",
    "बताना": "batana",
    "बत्तख": "battakh",
    "बर्तन": "bartan",
    "बस": "bus",
    "बसंत": "basant",
    "बहस": "bahas",
    "बाँह": "baanh",
    "बाइक": "bike",
    "बाघ": "baagh",
    "बाज": "baaj",
    "बाज़ार": "bazaar",
    "बादल": "baadal",
    "बाल": "baal",
    "बिच्छू": "bichhoo",
    "बिजली": "bijli",
    "बिल्ली": "billi",
    "बिस्तर": "bistar",
    "बैठक": "baithak",
    "बैठना": "baithna",
    "बैल": "bail",
    "बोतल": "botal",
    "ब्लाउज़": "blouse",
    "भरा": "bhara",
    "भारी": "bhaari",
    "भूकंप": "bhookamp",
    "भैंस": "bhains",
    "भोजन": "bhojan",
    "भौंह": "bhaunh",
    "मंदिर": "mandir",
    "मकड़ी": "makdi",
    "मकान": "makaan",
    "मछली": "machli",
    "मज़दूर": "mazdoor",
    "मस्जिद": "masjid",
    "महँगा": "mehnga",
    "महीना": "mahina",
    "मिट्टी": "mitti",
    "मीठा": "meetha",
    "मुँह": "munh",
    "मुर्गा": "murga",
    "मुर्गी": "murgi",
    "मेज़": "mez",
    "मेट्रो": "metro",
    "मेला": "mela",
    "मोची": "mochi",
    "मोटा": "mota",
    "मोर": "mor",
    "मौसम": "mausam",
    "रज़ाई": "razai",
    "रात": "raat",
    "राय": "raay",
    "रुकना": "rukna",
    "रेत": "ret",
    "रोटी": "roti",
    "रोना": "rona",
    "लंबा": "lamba",
    "लगना": "lagna",
    "लड़ाई": "ladaai",
    "लड्डू": "laddu",
    "लाज": "laaj",
    "लिखना": "likhna",
    "लेना": "lena",
    "लोहार": "lohar",
    "वकील": "vakeel",
    "शक": "shak",
    "शरद": "sharad",
    "शहर": "shahar",
    "शादी": "shaadi",
    "शाम": "shaam",
    "शिक्षक": "shikshak",
    "शेर": "sher",
    "संतरा": "santara",
    "सच": "sach",
    "सज़ा": "saza",
    "सड़क": "sadak",
    "सब्ज़ी": "sabzi",
    "सभा": "sabha",
    "समझना": "samajhna",
    "समय": "samay",
    "समोसा": "samosa",
    "सरकार": "sarkar",
    "सर्दी": "sardi",
    "सस्ता": "sasta",
    "साँप": "saanp",
    "साइकिल": "cycle",
    "साड़ी": "sari",
    "साफ़": "saaf",
    "साल": "saal",
    "सुंदर": "sundar",
    "सुई": "sui",
    "सुख": "sukh",
    "सुनना": "sunna",
    "सुबह": "subah",
    "सूखा": "sookha",
    "सूरज": "suraj",
    "सेब": "seb",
    "सैनिक": "sainik",
    "सोचना": "sochna",
    "सोना": "sona",
    "स्कूटर": "scooter",
    "स्कूल": "school",
    "स्वस्थ": "swasth",
    "हँसना": "hansna",
    "हँसी": "hansi",
    "हड्डी": "haddi",
    "हथेली": "hatheli",
    "हफ़्ता": "hafta",
    "हल्का": "halka",
    "हल्दी": "haldi",
    "हवा": "hawa",
    "हाथ": "haath",
    "हिम्मत": "himmat",
    "हिरण": "hiran",
    "होंठ": "honth",
    "होना": "hona",
}

XFAIL_WORDS_500 = {
    "अंदर आना": "andar aana",
    "अंदर जाना": "andar jaana",
    "अखरोट": "akhrot",
    "अजवाइन": "ajwain",
    "अनानास": "ananas",
    "अपराध": "apradh",
    "अमरूद": "amrood",
    "असफलता": "asafalta",
    "आँवला": "aanwla",
    "आँसू": "aansoo",
    "आंदोलन": "andolan",
    "आज़ादी": "azadi",
    "आसमान": "aasman",
    "उड़ना": "udna",
    "उत्सव": "utsav",
    "उबालना": "ubaalna",
    "ऊपर जाना": "oopar jaana",
    "कराहना": "karahna",
    "कलाई": "kalai",
    "काटना": "kaatna",
    "कानून": "kanoon",
    "काम करना": "kaam karna",
    "किशमिश": "kishmish",
    "कुम्हार": "kumhar",
    "कुर्सी": "kursi",
    "कूटना": "kootna",
    "केकड़ा": "kekda",
    "कैंची": "kainchi",
    "कॉलेज": "college",
    "कोट": "coat",
    "कोशिश करना": "koshish karna",
    "कोहनी": "kohni",
    "कौआ": "kauwa",
    "खत्म करना": "khatam karna",
    "खाली करना": "khaali karna",
    "खेलना": "khelna",
    "खोजना": "khojna",
    "खोलना": "kholna",
    "गहरा": "gahra",
    "ग़म": "gham",
    "गुफा": "gufa",
    "घटना": "ghatna",
    "घर आना": "ghar aana",
    "घर जाना": "ghar jaana",
    "घिसना": "ghisna",
    "घूमना": "ghoomna",
    "चाहना": "chahna",
    "चीखना": "cheekhna",
    "चीरना": "cheerna",
    "चुप रहना": "chup rehna",
    "छाती": "chhati",
    "छिपकली": "chhipkali",
    "छुपना": "chhupna",
    "जन्मदिन": "janamdin",
    "जानवर": "jaanwar",
    "जीतना": "jeetna",
    "जीभ": "jeebh",
    "जेल": "jail",
    "जैकेट": "jacket",
    "जोड़ना": "jodna",
    "झगड़ना": "jhagadna",
    "झरना": "jharna",
    "झूठ": "jhooth",
    "झूठ बोलना": "jhooth bolna",
    "टहलना": "tahalna",
    "टैक्सी": "taxi",
    "ट्रैक्टर": "tractor",
    "डरना": "darna",
    "ढूँढना": "dhoondhna",
    "तकलीफ": "takleef",
    "तड़पना": "tadapna",
    "तरबूज": "tarbooj",
    "तलवा": "talwa",
    "तारा": "taara",
    "तारीख": "tarikh",
    "तूफ़ान": "toofan",
    "तैयार करना": "taiyar karna",
    "तैरना": "tairna",
    "तोड़ना": "todna",
    "दफ्तर": "daftar",
    "दर्जी": "darzi",
    "दिखना": "dikhna",
    "धरती": "dharti",
    "धोखा": "dhoka",
    "नहाना": "nahana",
    "नाचना": "naachna",
    "नारियल": "nariyal",
    "नाव": "naav",
    "नाश्ता": "nashta",
    "न्याय": "nyay",
    "पकौड़ा": "pakoda",
    "पढ़ाई करना": "padhai karna",
    "पता चलना": "pata chalna",
    "पता लगाना": "pata lagana",
    "पपीता": "papita",
    "परदा": "parda",
    "परेशानी": "pareshani",
    "पर्व": "parv",
    "पहाड़": "pahad",
    "पहुँचना": "pahuncha",
    "पिंडली": "pindli",
    "पीटना": "peetna",
    "पीसना": "peesna",
    "पूछना": "poochna",
    "पृथ्वी": "prithvi",
    "फर्श": "farsh",
    "फैलना": "failna",
    "फोड़ना": "fodna",
    "बंद करना": "band karna",
    "बचना": "bachna",
    "बचाना": "bachana",
    "बटन": "button",
    "बढ़ना": "badhna",
    "बदलना": "badalna",
    "बनाना": "banana",
    "बरसात": "barsaat",
    "बर्फ़": "baraf",
    "बहादुर": "bahadur",
    "बाँधना": "baandhna",
    "बाढ़": "baadh",
    "बादाम": "badam",
    "बारिश": "baarish",
    "बाहर": "bahar",
    "बाहर आना": "bahar aana",
    "बाहर जाना": "bahar jaana",
    "बीमार": "bimaar",
    "बोलना": "bolna",
    "भरना": "bharna",
    "भालू": "bhaloo",
    "भूलना": "bhoolna",
    "मदद करना": "madad karna",
    "माथा": "maatha",
    "मानना": "maanna",
    "मारना": "maarna",
    "मिनट": "minute",
    "मिलना": "milna",
    "मिलाना": "milana",
    "मुस्कान": "muskurahat",
    "मुस्कुराना": "muskurana",
    "मूँगफली": "moongfali",
    "मूँछ": "mooch",
    "मेंढक": "mendhak",
    "युद्ध": "yudh",
    "रगड़ना": "ragadna",
    "रहना": "rehna",
    "रास्ता": "rasta",
    "रिक्शा": "rickshaw",
    "रैली": "rally",
    "रोकना": "rokna",
    "लगाना": "lagana",
    "लड़ना": "ladna",
    "लहसुन": "lehsun",
    "लीची": "lichi",
    "लूँगी": "lungi",
    "लौटना": "lautna",
    "वादा करना": "vada karna",
    "वापस आना": "wapas aana",
    "वापस जाना": "wapas jaana",
    "विचार": "vichar",
    "विश्वास": "vishwas",
    "वैन": "van",
    "शर्ट": "shirt",
    "शर्म": "sharam",
    "शांत": "shaant",
    "शांति": "shaanti",
    "शुरू करना": "shuru karna",
    "सच बोलना": "sach bolna",
    "सफलता": "safalta",
    "समुद्र": "samundar",
    "सरसों": "sarson",
    "सलवार": "salwar",
    "सलाद": "salad",
    "सलाह": "salah",
    "साफ़ करना": "saaf karna",
    "सिनेमा": "cinema",
    "सिपाही": "sipahi",
    "सीढ़ी": "sidhi",
    "सीधा": "sidha",
    "सुझाव": "sujhav",
    "सुनार": "sunar",
    "सूखना": "sookhna",
    "स्वेटर": "sweater",
    "हड़ताल": "hadtal",
    "हलवा": "halwa",
    "हारना": "haarna",
    "हिम्मत करना": "himmat karna",
    "हिलाना": "hilana",
    "होटल": "hotel",
}


# ─── Helpers ────────────────────────────────────────────────────────────────

def has_devanagari(text: str) -> bool:
    return any("\u0900" <= c <= "\u097f" for c in text)


def _classify_romanization_error(actual: str, expected: str) -> str:
    """Classify the type of romanization error."""
    if len(actual) != len(expected):
        if actual.rstrip("a") == expected.rstrip("a"):
            return "trailing_schwa"
        if expected.rstrip("a") == actual.rstrip("a"):
            return "extra_trailing_schwa"
        if len(actual) < len(expected) - 1:
            return "missing_chars"
        if len(actual) > len(expected) + 1:
            return "extra_chars"
        return "length_mismatch"

    diff_positions = [(i, a, e) for i, (a, e) in enumerate(zip(actual, expected)) if a != e]
    if not diff_positions:
        return "none"

    vw_issues = any(a == "v" and e == "w" or a == "w" and e == "v" for _, a, e in diff_positions)
    vowel_issues = any(
        a in "aeiou" and e in "aeiou" and a != e
        for _, a, e in diff_positions
    )

    if vw_issues and not vowel_issues:
        return "v_w"
    if vowel_issues and not vw_issues:
        return "vowel_length"
    if vw_issues and vowel_issues:
        return "v_w_and_vowel"
    return "other_consonant"


# ─── Audit 1: Transliteration ───────────────────────────────────────────────

def audit_transliteration(dictionary: list[dict] | None = None) -> dict:
    """Audit transliteration accuracy on known benchmarks and live data."""
    results: dict[str, Any] = {}

    # 1a. Benchmark against the 500-word hand-curated set
    common = _load_common_words()
    benchmark_errors: list[dict] = []
    benchmark = {}
    benchmark.update({w: e for w, e in PASS_WORDS_500.items()})
    benchmark.update({w: e for w, e in XFAIL_WORDS_500.items()})

    pass_count = 0
    fail_count = 0
    fail_by_type: Counter = Counter()
    common_word_coverage = 0
    common_word_correct = 0

    for hindi, expected in benchmark.items():
        actual = transliterate_rule_based(hindi)
        if actual == expected:
            pass_count += 1
        else:
            fail_count += 1
            error_type = _classify_romanization_error(actual, expected)
            fail_by_type[error_type] += 1
            benchmark_errors.append({
                "hindi": hindi,
                "expected": expected,
                "actual": actual,
                "error_type": error_type,
            })
        if hindi in common:
            common_word_coverage += 1
            if common[hindi] == expected:
                common_word_correct += 1

    results["benchmark"] = {
        "total": len(benchmark),
        "pass": pass_count,
        "fail": fail_count,
        "accuracy_pct": round(pass_count * 100 / len(benchmark), 1),
        "fail_by_type": dict(fail_by_type.most_common()),
        "common_words_in_benchmark": {
            "total": common_word_coverage,
            "correct": common_word_correct,
            "coverage_pct": round(common_word_correct * 100 / max(common_word_coverage, 1), 1),
        },
    }
    results["error_examples"] = benchmark_errors[:50]

    # 1b. Live data audit: scan all dictionary entries for diacritics
    if dictionary:
        diacritic_entries = []
        missing_roman = []
        for entry in dictionary:
            roman = entry.get("word_hinglish_roman", "")
            if not roman:
                missing_roman.append(entry)
                continue
            if any(ch in DIACRITICS for ch in roman):
                diacritic_entries.append(entry)

        results["live_data"] = {
            "total_entries": len(dictionary),
            "diacritics_in_roman": len(diacritic_entries),
            "missing_roman": len(missing_roman),
            "diacritic_pct": round(len(diacritic_entries) * 100 / len(dictionary), 3),
        }
        if diacritic_entries:
            results["diacritic_examples"] = [
                {
                    "hindi": e["word_hindi"],
                    "roman": e["word_hinglish_roman"],
                    "source": e.get("source", ""),
                }
                for e in diacritic_entries[:30]
            ]

    return results


# ─── Audit 2: Merge Quality ─────────────────────────────────────────────────

def audit_merge_quality(dictionary: list[dict]) -> dict:
    """Audit post-dedup merge quality: coverage, conflicts, completeness.

    Post-dedup every entry has exactly one primary source, but merged entries
    carry a `sources` list with all contributors. We audit on that signal
    instead of word_hindi overlap (which is always zero post-dedup).
    """
    wn_entries = [e for e in dictionary if e.get("source") == "WordNet"]
    wk_entries = [e for e in dictionary if e.get("source") == "Wiktionary"]

    # Entries that were actually merged from multiple sources
    merged = [e for e in dictionary if len(e.get("sources", [])) > 1]

    # Source-pair distribution (e.g., how many came from WordNet+Wiktionary)
    pair_counts: Counter = Counter()
    for e in merged:
        pair = tuple(sorted(set(e.get("sources", []))))
        pair_counts[pair] += 1

    # Completeness on merged entries: do they carry both Hindi and English defs?
    has_hi = sum(1 for e in merged if e.get("definition_hi"))
    has_en = sum(1 for e in merged if e.get("definition_en"))
    has_both = sum(1 for e in merged if e.get("definition_hi") and e.get("definition_en"))

    # Definition conflict: the surviving primary def differs in language from
    # what one side contributed. Look for entries where definition_hi and
    # definition_en are textually identical (suggests one side never had a
    # distinct gloss and the other was duplicated into both fields).
    identical_lang_fields = 0
    for e in merged:
        hi = e.get("definition_hi", "")
        en = e.get("definition_en", "")
        if hi and en and hi == en:
            identical_lang_fields += 1

    # Conflict samples: merged entries with very short or empty primary def
    # but the surviving entry clearly came from only one side.
    thin_merges = [
        {
            "word": e.get("word_hindi", ""),
            "roman": e.get("word_hinglish_roman", ""),
            "sources": e.get("sources", []),
            "definition": e.get("definition", "")[:120],
            "definition_hi": (e.get("definition_hi") or "")[:80],
            "definition_en": (e.get("definition_en") or "")[:80],
        }
        for e in merged
        if len(e.get("definition", "")) < 20
    ][:30]

    results = {
        "totals": {
            "wordnet": len(wn_entries),
            "wiktionary": len(wk_entries),
        },
        "merge_coverage": {
            "merged_entries": len(merged),
            "merged_pct": round(len(merged) * 100 / max(len(dictionary), 1), 1),
            "source_pair_distribution": {
                ", ".join(pair): count for pair, count in pair_counts.most_common()
            },
        },
        "completeness": {
            "has_definition_hi": has_hi,
            "has_definition_en": has_en,
            "has_both": has_both,
            "hi_pct": round(has_hi * 100 / max(len(merged), 1), 1),
            "en_pct": round(has_en * 100 / max(len(merged), 1), 1),
            "both_pct": round(has_both * 100 / max(len(merged), 1), 1),
        },
        "potential_issues": {
            "identical_hi_and_en": identical_lang_fields,
            "thin_definition_count": len(thin_merges),
        },
    }
    if thin_merges:
        results["potential_issues"]["thin_examples"] = thin_merges

    return results


# ─── Audit 3: Safety Filter ─────────────────────────────────────────────────

def audit_safety_filter(dictionary: list[dict]) -> dict:
    """Audit profanity coverage: false negatives, coverage gaps."""
    profanity_matcher = ProfanityMatcher()
    wordlist = profanity_matcher.wordlist

    results: dict[str, Any] = {
        "wordlist_size": len(wordlist),
        "wordlist_sample": sorted(wordlist)[:20],
    }

    # 3a. Severity distribution
    severity_dist = Counter()
    for entry in dictionary:
        s = entry.get("severity_score", 0)
        bucket = f"{s:.1f}"
        severity_dist[bucket] += 1
    results["severity_distribution"] = dict(severity_dist.most_common())

    # 3b. Find profane words in definitions NOT caught by current filter
    false_negatives = []

    for entry in dictionary:
        roman = entry.get("word_hinglish_roman", "").lower()
        definition = entry.get("definition", "").lower()
        example = entry.get("example_sentence", "").lower()

        # Check definition words against profanity list
        def_words = set(_normalize_text(definition).split()) if definition else set()
        ex_words = set(_normalize_text(example).split()) if example else set()
        all_text_words = def_words | ex_words

        # Skip the headword itself (already checked by the filter)
        head_norm = _normalize_text(roman) if roman else ""

        for w in all_text_words:
            if w in wordlist and w != head_norm:
                false_negatives.append({
                    "word_hindi": entry.get("word_hindi", ""),
                    "word_hinglish_roman": roman,
                    "profanity_word": w,
                    "source": entry.get("source", ""),
                    "severity_score": entry.get("severity_score", 0),
                    "definition_snippet": definition[:120] if definition else "",
                    "example_snippet": example[:120] if example else "",
                })
                break

    results["false_negatives"] = {
        "count": len(false_negatives),
        "examples": false_negatives[:30],
    }

    # 3c. Check if any known Hindi profanity variants are missing
    # Common spelling variations that should probably be in the list
    suggested_words = [
        "bhen", "bahan", "maa ki", "teri", "mard", "kamina",
        "kamine", "sala", "saala", "harami", "haramipan",
        "kutti", "kuttiya", "ullu", "ullu ka pattha",
    ]
    missing = [w for w in suggested_words if w not in wordlist]
    results["suggested_additions"] = {
        "total_suggested": len(suggested_words),
        "already_in_list": len(suggested_words) - len(missing),
        "missing": missing,
    }

    return results


# ─── Audit 4: Confidence Faithfulness ────────────────────────────────────────

def audit_confidence(dictionary: list[dict]) -> dict:
    """Check if confidence scores actually correlate with quality signals."""
    buckets: dict[str, list[dict]] = defaultdict(list)
    for entry in dictionary:
        c = entry.get("confidence_score", 0)
        bucket = f"{c:.2f}"
        buckets[bucket].append(entry)

    analysis = []
    for bucket in sorted(buckets.keys()):
        entries = buckets[bucket]
        n = len(entries)

        def_lengths = [len(e.get("definition", "")) for e in entries]
        has_example = sum(1 for e in entries if e.get("example_sentence"))
        has_toxicity = sum(1 for e in entries if e.get("toxicity_flags"))
        sources = Counter(e.get("source", "unknown") for e in entries)
        has_dev_def = sum(
            1 for e in entries
            if has_devanagari(e.get("definition", ""))
        )
        completeness = sum(
            1 for e in entries
            if e.get("definition") and len(e["definition"]) > 10 and e.get("example_sentence")
        )

        analysis.append({
            "bucket": bucket,
            "count": n,
            "pct_of_total": round(n * 100 / len(dictionary), 1),
            "avg_def_length": round(sum(def_lengths) / n, 1) if n else 0,
            "pct_with_example": round(has_example * 100 / n, 1),
            "pct_with_toxicity": round(has_toxicity * 100 / n, 1),
            "pct_dev_def": round(has_dev_def * 100 / n, 1),
            "pct_complete": round(completeness * 100 / n, 1),
            "source_distribution": dict(sources.most_common(5)),
        })

    # Check if confidence correlates with being in common_words
    common = _load_common_words()
    in_common = 0
    not_in_common = 0
    for entry in dictionary:
        if entry.get("word_hindi") in common:
            in_common += 1
        else:
            not_in_common += 1

    return {
        "buckets": analysis,
        "total_entries": len(dictionary),
        "romanization_coverage": {
            "in_common_words_json": in_common,
            "not_in_common_words_json": not_in_common,
            "pct_overridden": round(in_common * 100 / len(dictionary), 1),
        },
    }


# ─── Main ────────────────────────────────────────────────────────────────────

def load_dictionary(data_dir: str | Path) -> list[dict] | None:
    """Load the dictionary from JSON or SQLite."""
    data_dir = Path(data_dir)

    # Try SQLite first (faster)
    db_path = data_dir / "hinglish_dict.db"
    if db_path.exists():
        logger.info("  Loading from SQLite: %s", db_path)
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM dictionary").fetchall()
        conn.close()
        return [dict(r) for r in rows]

    # Fallback to JSON
    for name in ["hinglish_dictionary_v1.json", "hinglish_dictionary_v1.min.json"]:
        path = data_dir / name
        if path.exists():
            logger.info("  Loading from JSON: %s", path)
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            return data.get("dictionary", [])

    return None


def run_audit(args: argparse.Namespace) -> int:
    """Run selected audits and print results."""
    audits_to_run = [a.strip() for a in args.audit.split(",")] if args.audit else []
    run_all = not audits_to_run

    logger.info("=" * 60)
    logger.info("  HinglishKosh — Error Audit")
    logger.info("=" * 60)

    # Load dictionary only for audits that need it
    dictionary = None

    # ── Transliteration ──
    if run_all or "transliteration" in audits_to_run:
        logger.info("\n─── Audit 1: Transliteration Accuracy ───\n")
        result = audit_transliteration()
        bm = result["benchmark"]
        logger.info(
            "  Benchmark (500 words): %d/%d = %s%%",
            bm["pass"], bm["total"], bm["accuracy_pct"],
        )
        logger.info("  Failures by type:")
        for err_type, count in bm["fail_by_type"].items():
            logger.info("    %s: %d", err_type, count)
        cw = bm["common_words_in_benchmark"]
        logger.info(
            "  Common words in benchmark: %d/%d correct (%s%%)",
            cw["correct"], cw["total"], cw["coverage_pct"],
        )

        if not args.suppress_examples and result.get("error_examples"):
            logger.info("\n  Top error examples:")
            for ex in result["error_examples"][:15]:
                logger.info(
                    "    [%s] %s → expected='%s' actual='%s'",
                    ex["error_type"], ex["hindi"], ex["expected"], ex["actual"],
                )

        # Now audit live data if available (pass dict)
        if args.data_dir:
            if dictionary is None:
                dictionary = load_dictionary(args.data_dir)
            if dictionary:
                live = audit_transliteration(dictionary)
                ld = live.get("live_data", {})
                if ld:
                    logger.info(
                        "\n  Live data: %d entries with diacritics in roman (%s%%)",
                        ld.get("diacritics_in_roman", 0), ld.get("diacritic_pct", 0),
                    )
                    if ld.get("missing_roman"):
                        logger.info(
                            "  WARNING: %d entries have empty romanization!",
                            ld["missing_roman"],
                        )

    # ── Merge Quality ──
    if run_all or "merge" in audits_to_run:
        logger.info("\n─── Audit 2: Merge Quality ───\n")
        if dictionary is None:
            dictionary = load_dictionary(args.data_dir)
        if not dictionary:
            logger.info("  SKIP: No dictionary data available")
        else:
            result = audit_merge_quality(dictionary)
            totals = result["totals"]
            cov = result["merge_coverage"]
            comp = result["completeness"]
            issues = result["potential_issues"]
            logger.info(
                "  WordNet: %d entries, Wiktionary: %d entries",
                totals["wordnet"], totals["wiktionary"],
            )
            logger.info(
                "  Merged entries: %d (%s%% of total)",
                cov["merged_entries"], cov["merged_pct"],
            )
            logger.info("  Source pair distribution:")
            for pair, count in cov["source_pair_distribution"].items():
                logger.info("    %s: %d", pair, count)
            logger.info(
                "  Definition completeness on merged entries: hi=%s%%, en=%s%%, both=%s%%",
                comp["hi_pct"], comp["en_pct"], comp["both_pct"],
            )
            logger.info(
                "  Issues: %d entries with identical hi/en fields, %d with thin definitions",
                issues["identical_hi_and_en"], issues["thin_definition_count"],
            )

    # ── Safety Filter ──
    if run_all or "safety" in audits_to_run:
        logger.info("\n─── Audit 3: Safety Filter Coverage ───\n")
        if dictionary is None:
            dictionary = load_dictionary(args.data_dir)
        if not dictionary:
            logger.info("  SKIP: No dictionary data available")
        else:
            result = audit_safety_filter(dictionary)
            logger.info("  Wordlist: %d profanity entries", result["wordlist_size"])
            logger.info("  Severity distribution:")
            for bucket, count in sorted(result.get("severity_distribution", {}).items()):
                logger.info("    score=%s: %d entries", bucket, count)

            fn = result.get("false_negatives", {})
            logger.info(
                "  Definitions/examples with uncaught profanity: %d entries",
                fn.get("count", 0),
            )
            for ex in fn.get("examples", [])[:10]:
                logger.info(
                    "    '%s' contains '%s' (severity=%s, source=%s)",
                    ex["word_hinglish_roman"], ex["profanity_word"],
                    ex["severity_score"], ex["source"],
                )

            sa = result.get("suggested_additions", {})
            if sa.get("missing"):
                logger.info(
                    "  %d suggested additions not in wordlist: %s",
                    len(sa["missing"]), ", ".join(sa["missing"][:10]),
                )

    # ── Confidence Faithfulness ──
    if run_all or "confidence" in audits_to_run:
        logger.info("\n─── Audit 4: Confidence Faithfulness ───\n")
        if dictionary is None:
            dictionary = load_dictionary(args.data_dir)
        if not dictionary:
            logger.info("  SKIP: No dictionary data available")
        else:
            result = audit_confidence(dictionary)
            logger.info("  Confidence score distribution:")
            logger.info(
                "    %-8s %-8s %-18s %-16s %-14s %s",
                "Score", "Count", "% of Total", "Avg Def Len", "% Example", "Top Source",
            )
            for b in result["buckets"]:
                top_src = (
                    list(b["source_distribution"].keys())[0] if b["source_distribution"] else ""
                )
                logger.info(
                    "    %-8s %-8d %-18s %-16s %-14s %s",  # noqa: E501
                    b["bucket"], b["count"], f"{b['pct_of_total']}%",
                    b["avg_def_length"], f"{b['pct_with_example']}%", top_src,
                )

            cov = result["romanization_coverage"]
            logger.info(
                "\n  Romanization: %d/%d entries overridden by common_words.json (%s%%)",
                cov["in_common_words_json"], cov["not_in_common_words_json"],
                cov["pct_overridden"],
            )

    logger.info("\n" + "=" * 60)
    logger.info("  Audit complete")
    logger.info("=" * 60)

    return 0


def main():
    parser = argparse.ArgumentParser(
        description="HinglishKosh error audit — find where the dictionary makes mistakes",
    )
    parser.add_argument(
        "--audit",
        default="",
        help="Comma-separated audits: transliteration,merge,safety,confidence (default: all)",
    )
    parser.add_argument(
        "--data-dir",
        default="data/output",
        help="Directory with dictionary JSON or SQLite (default: data/output)",
    )
    parser.add_argument(
        "--sample",
        type=int,
        default=0,
        help="Sample N entries from dictionary for faster runs (0 = all)",
    )
    parser.add_argument(
        "--suppress-examples",
        action="store_true",
        help="Suppress detailed error examples in output",
    )

    args = parser.parse_args()
    sys.exit(run_audit(args))


if __name__ == "__main__":
    main()
