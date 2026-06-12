"""Transliteration wrapper — converts Devanagari to Roman (Hinglish).

Uses a rule-based fallback when GoVarnam/IndicTrans models are unavailable.
"""

from __future__ import annotations

import re
import unicodedata

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

_DEVANAGARI_SIGN_MAP = {
    "ं": "n",
    "ँ": "n",
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


# Common Hindi words with well-known romanizations
_COMMON_WORDS = {
    "नमस्ते": "namaste",
    "हाँ": "haan",
    "नहीं": "nahi",
    "हां": "haan",
    "ठीक": "theek",
    "बिल्कुल": "bilkul",
    "धन्यवाद": "dhanyavaad",
    "माफ़": "maaf",
    "कृपया": "kripya",
    "जी": "ji",
    "सर": "sir",
    "मैडम": "madam",
    "अच्छा": "achcha",
    "बुरा": "bura",
    "सही": "sahi",
    "गलत": "galat",
    "हो": "ho",
    "है": "hai",
    "था": "tha",
    "थी": "thi",
    "होगा": "hoga",
    "करो": "karo",
    "चलो": "chalo",
    "आओ": "aao",
    "जाओ": "jao",
    "बैठो": "baitho",
    "सो": "so",
    "उठो": "utho",
    "देखो": "dekho",
    "सुनो": "suno",
    "बोलो": "bolo",
    "पढ़ो": "padho",
    "लिखो": "likho",
    "खाओ": "khao",
    "पियो": "piyo",
    "पी": "pi",
    "लो": "lo",
    "दे": "de",
    "रख": "rakh",
    "कर": "kar",
    "रहा": "raha",
    "रही": "rahi",
    "रहे": "rahe",
    "गया": "gaya",
    "गई": "gai",
    "गए": "gaye",
    "एक": "ek",
    "दो": "do",
    "तीन": "teen",
    "चार": "chaar",
    "पाँच": "paanch",
    "छह": "chhah",
    "सात": "saat",
    "आठ": "aath",
    "नौ": "nau",
    "दस": "das",
    "ग्यारह": "gyarah",
    "बारह": "barah",
    "तेरह": "terah",
    "चौदह": "chaudah",
    "पंद्रह": "pandrah",
    "सोलह": "solah",
    "सत्रह": "satrah",
    "अठारह": "atharah",
    "उन्नीस": "unnees",
    "बीस": "bees",
    "मैं": "main",
    "तू": "tu",
    "तुम": "tum",
    "आप": "aap",
    "वह": "woh",
    "यह": "yeh",
    "वो": "wo",
    "ये": "ye",
    "हम": "ham",
    "तुम्हारा": "tumhara",
    "उसका": "uska",
    "इसका": "iska",
    "मेरा": "mera",
    "उनका": "unka",
    "कौन": "kaun",
    "क्या": "kya",
    "कहाँ": "kahaan",
    "कब": "kab",
    "क्यों": "kyon",
    "कैसा": "kaisa",
    "कितना": "kitna",
    "कितनी": "kitni",
    "कितने": "kitne",
    "कैसे": "kaise",
    "माँ": "maa",
    "मां": "maa",
    "पिता": "pita",
    "पापा": "papa",
    "बाप": "baap",
    "भाई": "bhai",
    "बहन": "behen",
    "बेटा": "beta",
    "बेटी": "beti",
    "दादा": "dada",
    "दादी": "dadi",
    "नाना": "nana",
    "नानी": "nani",
    "चाचा": "chacha",
    "चाची": "chachi",
    "मामा": "mama",
    "मामी": "mami",
    "बुआ": "bua",
    "ताया": "taya",
    "ताई": "tai",
    "ससुर": "sasur",
    "सास": "saas",
    "बहू": "bahu",
    "दामाद": "daamaad",
    "भाभी": "bhabhi",
    "जीजा": "jija",
    "साला": "sala",
    "साली": "sali",
    "पति": "pati",
    "पत्नी": "patni",
    "सिर": "sir",
    "माथा": "matha",
    "आँख": "aankh",
    "कान": "kaan",
    "नाक": "naak",
    "मुँह": "munh",
    "होंठ": "honth",
    "दाँत": "daant",
    "जीभ": "jibh",
    "गला": "gala",
    "कंधा": "kandha",
    "हाथ": "haath",
    "उंगली": "ungli",
    "पंजा": "panja",
    "सीना": "seena",
    "पेट": "pet",
    "कमर": "kamar",
    "कूल्हा": "kulha",
    "घुटना": "ghutna",
    "पैर": "pair",
    "तलवा": "talva",
    "एड़ी": "edi",
    "नाखून": "nakhun",
    "बाल": "baal",
    "पानी": "paani",
    "खाना": "khana",
    "चाय": "chai",
    "दूध": "doodh",
    "रोटी": "roti",
    "दाल": "daal",
    "चावल": "chawal",
    "सब्ज़ी": "sabzi",
    "मीठा": "meetha",
    "खट्टा": "khatta",
    "नमक": "namak",
    "मिर्च": "mirch",
    "हल्दी": "haldi",
    "जीरा": "jeera",
    "अदरक": "adrak",
    "लहसुन": "lahsun",
    "प्याज़": "pyaaz",
    "टमाटर": "tamatar",
    "आलू": "aaloo",
    "पनीर": "paneer",
    "दही": "dahi",
    "लस्सी": "lassi",
    "जूस": "juice",
    "केला": "kela",
    "सेब": "seb",
    "अंगूर": "angoor",
    "आम": "aam",
    "नींबू": "nimbu",
    "इलायची": "elaichi",
    "दालचीनी": "dalchini",
    "मेथी": "methi",
    "धनिया": "dhaniya",
    "पुदीना": "pudina",
    "मछली": "machli",
    "काली मिर्च": "kali mirch",
    "लाल मिर्च": "lal mirch",
    "चीनी": "cheeni",
    "शहद": "shahad",
    "नमकीन": "namkeen",
    "चटनी": "chatni",
    "पापड़": "papad",
    "अचार": "achaar",
    "मक्खन": "makhan",
    "घी": "ghee",
    "तेल": "tel",
    "सिरका": "sirka",
    "मसाला": "masala",
    "हरी मिर्च": "hari mirch",
    "धनिया पत्ती": "dhaniya patti",
    "तुलसी": "tulsi",
    "करी पत्ता": "curry patta",
    "कपड़ा": "kapda",
    "कपड़े": "kapde",
    "कुर्ता": "kurta",
    "पजामा": "pajama",
    "साड़ी": "sari",
    "जूता": "joota",
    "चप्पल": "chappal",
    "टोपी": "topi",
    "दुपट्टा": "dupatta",
    "गहना": "gahna",
    "अंगूठी": "angoothi",
    "चूड़ी": "chudi",
    "कंगन": "kangan",
    "हार": "haar",
    "मंगलसूत्र": "mangalsutra",
    "ब्लाउज़": "blouse",
    "बिछिया": "bichiya",
    "लहंगा": "lahanga",
    "घाघरा": "ghaghra",
    "चोली": "choli",
    "घर": "ghar",
    "देश": "desh",
    "शहर": "shahar",
    "गाँव": "gaon",
    "सड़क": "sadak",
    "बाज़ार": "bazaar",
    "दुकान": "dukaan",
    "स्कूल": "school",
    "अस्पताल": "aspatal",
    "मंदिर": "mandir",
    "मस्जिद": "masjid",
    "चर्च": "church",
    "गिरजाघर": "girjaghar",
    "कमरा": "kamra",
    "बेडरूम": "bedroom",
    "किचन": "kitchen",
    "बाथरूम": "bathroom",
    "बैठक": "baithak",
    "दालान": "dalaan",
    "आँगन": "aangan",
    "बरामदा": "baramda",
    "छत": "chhat",
    "दीवार": "deewar",
    "दरवाज़ा": "darwaza",
    "खिड़की": "khidki",
    "तालाब": "taalab",
    "पोखर": "pokhar",
    "ताला": "tala",
    "चाबी": "chabi",
    "गली": "gali",
    "मोहल्ला": "mohalla",
    "नगर": "nagar",
    "राजधानी": "rajdhaani",
    "राज्य": "rajya",
    "प्रांत": "prant",
    "जिला": "jila",
    "तहसील": "tehsil",
    "पंचायत": "panchayat",
    "थाना": "thana",
    "चौकी": "chowki",
    "कुत्ता": "kutta",
    "बिल्ली": "billi",
    "गाय": "gaay",
    "भैंस": "bhains",
    "घोड़ा": "ghoda",
    "हाथी": "haathi",
    "शेर": "sher",
    "बंदर": "bandar",
    "चिड़िया": "chidiya",
    "मोर": "mor",
    "मेंढक": "medhak",
    "साँप": "saanp",
    "बिच्छू": "bichhoo",
    "मकड़ी": "makdi",
    "चींटी": "chinti",
    "मच्छर": "machchar",
    "मुर्गी": "murgi",
    "मुर्गा": "murga",
    "बत्तख": "battakh",
    "हिरण": "hiran",
    "बाघ": "baagh",
    "तेंदुआ": "tendua",
    "भालू": "bhaaloo",
    "लोमड़ी": "lomdi",
    "खरगोश": "khargosh",
    "उल्लू": "ullu",
    "कबूतर": "kabootar",
    "चील": "cheel",
    "गिद्ध": "giddh",
    "आग": "aag",
    "हवा": "hawa",
    "धूप": "dhoop",
    "बारिश": "barish",
    "बर्फ़": "barf",
    "बिजली": "bijli",
    "बादल": "baadal",
    "सूरज": "suraj",
    "चाँद": "chaand",
    "तारा": "tara",
    "रात": "raat",
    "दिन": "din",
    "सुबह": "subah",
    "शाम": "shaam",
    "दोपहर": "dopahar",
    "पहाड़": "pahaad",
    "नदी": "nadi",
    "झील": "jheel",
    "समुद्र": "samudra",
    "समंदर": "samundar",
    "द्वीप": "dweep",
    "जंगल": "jungle",
    "पेड़": "ped",
    "फूल": "phool",
    "पत्ता": "patta",
    "जड़": "jad",
    "बीज": "beej",
    "आज": "aaj",
    "कल": "kal",
    "अभी": "abhi",
    "कभी": "kabhi",
    "हमेशा": "hamesha",
    "कभी-कभी": "kabhi-kabhi",
    "अब": "ab",
    "फिर": "phir",
    "तब": "tab",
    "जब": "jab",
    "महीना": "mahina",
    "साल": "saal",
    "हफ़्ता": "hafta",
    "परसों": "parson",
    "प्यार": "pyaar",
    "नफ़रत": "nafrat",
    "ख़ुशी": "khushi",
    "ग़म": "gam",
    "दुख": "dukh",
    "सुख": "sukh",
    "गुस्सा": "gussa",
    "शांति": "shanti",
    "डर": "dar",
    "हिम्मत": "himmat",
    "ताकत": "taakat",
    "कमज़ोरी": "kamzori",
    "आँसू": "aansu",
    "मुस्कान": "muskuraahat",
    "हँसी": "hansi",
    "रोना": "rona",
    "चिल्लाना": "chillana",
    "चुप": "chup",
    "शर्म": "sharm",
    "लाज": "laaj",
    "घमंड": "ghamand",
    "अकड़": "akad",
    "विनम्रता": "vinamrata",
    "दया": "daya",
    "करुणा": "karuna",
    "जाना": "jaana",
    "आना": "aana",
    "करना": "karna",
    "देना": "dena",
    "लेना": "lena",
    "पीना": "peena",
    "सोना": "sona",
    "जागना": "jaagna",
    "बैठना": "baithna",
    "खड़ा": "khada",
    "चलना": "chalna",
    "दौड़ना": "daudna",
    "हँसना": "hansna",
    "गाना": "gaana",
    "पढ़ना": "padhna",
    "लिखना": "likhna",
    "पढ़ाना": "padhana",
    "सिखाना": "sikhana",
    "सीखना": "seekhna",
    "समझना": "samajhna",
    "समझाना": "samjhana",
    "सोचना": "sochna",
    "जानना": "jaanna",
    "पूछना": "poochhna",
    "बताना": "batana",
    "कहना": "kehna",
    "सुनना": "sunna",
    "देखना": "dekhna",
    "छूना": "chhuna",
    "चुभना": "chubhna",
    "कटना": "katna",
    "फटना": "fatna",
    "बहना": "behna",
    "रुकना": "rukna",
    "टिकना": "tikna",
    "लगना": "lagna",
    "उठना": "uthna",
    "गिरना": "girna",
    "बड़ा": "bada",
    "छोटा": "chhota",
    "लंबा": "lamba",
    "चौड़ा": "chauda",
    "तंग": "tang",
    "मोटा": "mota",
    "पतला": "patla",
    "भारी": "bhaari",
    "हल्का": "halka",
    "तेज़": "tez",
    "धीमा": "dheema",
    "नया": "naya",
    "पुराना": "purana",
    "जवान": "jawaan",
    "बूढ़ा": "boodha",
    "अमीर": "ameer",
    "ग़रीब": "gareeb",
    "सुंदर": "sundar",
    "बदसूरत": "badsurat",
    "साफ़": "saaf",
    "गंदा": "ganda",
    "स्वस्थ": "swasth",
    "बीमार": "bimar",
    "ख़ुश": "khush",
    "उदास": "udaas",
    "गुस्सैल": "gussail",
    "शांत": "shant",
    "ताकतवर": "taakatvar",
    "कमज़ोर": "kamzor",
    "सस्ता": "sasta",
    "महँगा": "mehnga",
    "पक्का": "pakka",
    "कच्चा": "kaccha",
    "गर्म": "garm",
    "ठंडा": "thanda",
    "सूखा": "sookha",
    "गीला": "geela",
    "नम": "nam",
    "ख़ाली": "khaali",
    "भरा": "bhara",
    "खुला": "khula",
    "बंद": "band",
    "टूटा": "toota",
    "जुड़ा": "juda",
    "बर्तन": "bartan",
    "कढ़ाही": "kadhai",
    "तवा": "tawa",
    "चम्मच": "chammach",
    "चाकू": "chaku",
    "प्लेट": "plate",
    "कटोरा": "katora",
    "गिलास": "gilaas",
    "बोतल": "botal",
    "डिब्बा": "dibba",
    "रसोई": "rasoi",
    "चूल्हा": "choolha",
    "सिलबट्टा": "silbatta",
    "ओखली": "okhli",
    "मूसल": "moosal",
    "सपना": "sapna",
    "ख़्वाब": "khwaab",
    "हक़ीक़त": "haqeeqat",
    "सच": "sach",
    "झूठ": "jhoth",
    "इंसाफ़": "insaaf",
    "अंधेरा": "andhera",
    "रोशनी": "roshni",
    "आवाज़": "aawaaz",
    "चुप्पी": "chuppi",
    "ख़ामोशी": "khamoshi",
    "शोर": "shor",
    "एकांत": "ekaant",
    "भीड़": "bheed",
    "अकेला": "akela",
    "अंजान": "anjaan",
    "जाना-पहचाना": "jaana-pahchaana",
    "पराया": "paraya",
    "अपना": "apna",
    "इज़्ज़त": "izzat",
    "बेइज़्ज़ती": "beizzati",
    "शर्मिंदगी": "sharmindagi",
    "गर्व": "garv",
    "किताब": "kitab",
    "कलम": "kalam",
    "कागज़": "kagaz",
    "कुर्सी": "kurshi",
    "मेज़": "mez",
    "लाइट": "light",
    "पंखा": "pankha",
    "गैस": "gas",
    "फ़ोन": "phone",
    "मोबाइल": "mobile",
    "टीवी": "tv",
    "रेडियो": "radio",
    "अख़बार": "akhbaar",
    "पत्र": "patra",
    "चिट्ठी": "chiththi",
    "डाक": "daak",
    "टिकट": "ticket",
    "स्टेशन": "station",
    "बस": "bus",
    "ट्रेन": "train",
    "हवाई जहाज़": "hawai jahaz",
    "साइकिल": "cycle",
    "गाड़ी": "gaadi",
    "कार": "car",
    "ट्रक": "truck",
    "बाइक": "bike",
    "स्कूटर": "scooter",
    "रिक्शा": "riksha",
    "ठेला": "thela",
    "हेलमेट": "helmet",
    "चश्मा": "chashma",
    "घड़ी": "ghadi",
    "तकिया": "takiya",
    "गिलाफ़": "gilaaf",
    "चादर": "chadar",
    "कंबल": "kambal",
    "रज़ाई": "razai",
    "गद्दा": "gadda",
    "तौलिया": "towliya",
    "साबुन": "sabun",
    "शैम्पू": "shampoo",
    "ब्रश": "brush",
    "टूथपेस्ट": "toothpaste",
    "मंजन": "manjan",
    "दातुन": "daatun",
    "नल": "nal",
    "बाल्टी": "balti",
    "मग": "mag",
    "तस्वीर": "tasveer",
    "फ़ोटो": "photo",
    "आईना": "aaina",
    "शीशा": "sheesha",
    "लकड़ी": "lakdi",
    "पत्थर": "patthar",
    "लोहा": "loha",
    "ताँबा": "tamba",
    "चाँदी": "chandi",
    "पीतल": "peetal",
    "काँसा": "kaansa",
    "कांच": "kaanch",
    "प्लास्टिक": "plastic",
    "रेशम": "resham",
    "ऊन": "oon",
    "रुई": "rui",
    "धागा": "dhaaga",
    "सुई": "sui",
    "कैंची": "kaainchi",
    "सिलाई": "silai",
    "धोबी": "dhobi",
    "नाई": "nai",
    "मोची": "mochi",
    "लोहार": "lohar",
    "बढ़ई": "badhai",
    "किसान": "kisan",
    "मज़दूर": "mazdoor",
    "दुकानदार": "dukaandaar",
    "व्यापारी": "vyapaari",
    "अध्यापक": "adhyapak",
    "वकील": "vakeel",
    "डॉक्टर": "doctor",
    "इंजीनियर": "engineer",
    "नर्स": "nurse",
    "पुलिस": "police",
    "फ़ौजी": "fauji",
    "सैनिक": "sainik",
    "राजा": "raja",
    "रानी": "rani",
    "मंत्री": "mantri",
    "प्रधानमंत्री": "pradhanmantri",
    "राष्ट्रपति": "rashtrapati",
    "संसद": "sansad",
    "सरकार": "sarkar",
    "विपक्ष": "vipaksh",
    "चुनाव": "chunav",
    "वोट": "vote",
    "पार्टी": "party",
    "मतदान": "matdaan",
    "लोकतंत्र": "loktantra",
    "स्वतंत्रता": "swatantrata",
    "आज़ादी": "azaadi",
    "गणतंत्र": "ganatantra",
    "धर्म": "dharm",
    "ईश्वर": "ishwar",
    "भगवान": "bhagwan",
    "अल्लाह": "allah",
    "गुरु": "guru",
    "पुजारी": "pujari",
    "मौलवी": "maulvi",
    "पादरी": "padri",
}


def transliterate_rule_based(text: str) -> str:
    """Rule-based Devanagari to Roman transliteration.

    This is a fallback — use GoVarnam or IndicTrans for production quality.
    """
    if not text:
        return ""

    text = unicodedata.normalize("NFC", text)

    # Check common words first
    if text in _COMMON_WORDS:
        return _COMMON_WORDS[text]

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
    if _should_strip_final_inherent_a(text) and roman.endswith("a"):
        roman = roman[:-1]
    roman = re.sub(r"aa\b", "a", roman)
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
    # Replace nasalized vowels before stripping diacritics
    result = re.sub(r"ā̃", "aan", result)  # हाँ: hā̃ → haan
    result = re.sub(r"ī̃", "i", result)  # नहीं: nahī̃ → nahi
    result = re.sub(r"ū̃", "oon", result)
    result = re.sub(r"ẽ", "en", result)
    result = re.sub(r"õ", "on", result)
    # Remove remaining combining marks
    result = re.sub(r"[\u0300-\u036f]", "", result)
    result = result.replace("jñ", "gy")

    # Step 1: Strip diacritics with smart vowel handling
    replacements = [
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
        ("ġ", "g"),  # ग़ → g
    ]
    for old, new in replacements:
        result = result.replace(old, new)

    # Step 2: Handle remaining nasalized vowels
    result = re.sub(r"ã", "an", result)
    result = re.sub(r"ĩ", "in", result)
    result = re.sub(r"ũ", "un", result)

    # Step 3: Convert c → ch for Hindi palatal (च)
    # But only when followed by a vowel (not in words like 'accha')
    result = re.sub(r"ca", "cha", result)
    result = re.sub(r"co", "cho", result)
    result = re.sub(r"ci", "chi", result)
    result = re.sub(r"cu", "chu", result)
    result = re.sub(r"ce", "che", result)
    # Fix 'c' at end of word (pā̃c → paanch)
    result = re.sub(r"c$", "ch", result)

    # Step 4: v → w (Hindi व is pronounced 'w' in most words)
    # But keep 'v' in specific patterns (dhanyavaad, maulvi, talva)
    result = re.sub(r"v", "w", result)
    # Fix specific words where 'v' should stay
    result = re.sub(r"dhanyawad", "dhanyavaad", result)
    result = re.sub(r"maulwi", "maulvi", result)
    result = re.sub(r"talwa", "talva", result)
    result = re.sub(r"paadri", "padri", result)
    result = re.sub(r"pujaari", "pujari", result)

    # Step 6: ay → ai (चाय: cāy → chai, not chaay)
    # Handle 'aay' → 'ai' first (cāy → caay → chai)
    result = re.sub(r"aay$", "ai", result)
    result = re.sub(r"aay([^aeiou])", r"ai\1", result)
    # Then regular 'ay' → 'ai'
    result = re.sub(r"ay$", "ai", result)
    result = re.sub(r"ay([^aeiou])", r"ai\1", result)

    # Step 7: Handle trailing long vowels
    result = re.sub(r"aa$", "a", result)
    result = re.sub(r"ee$", "i", result)
    result = re.sub(r"oo$", "u", result)

    # Step 8: Fix anusvara before labials (ṃ → m before b, m, p)
    result = re.sub(r"nm", "m", result)
    result = re.sub(r"nb", "mb", result)
    result = re.sub(r"np", "mp", result)

    # Step 9: Common word corrections (after all ISO conversions)
    word_fixes = {
        "woh": "woh",  # वह (already correct)
        "yeh": "yeh",  # यह (already correct)
        "wah": "woh",  # वह
        "yah": "yeh",  # यह
        "bahan": "behen",  # बहन
        "mai": "main",  # मैं
        "maidam": "madam",  # मैडम
        "sar": "sir",  # सर
        "accha": "achcha",  # अच्छा
        "gae": "gaye",  # गए
        "chah": "chhah",  # छह
        "maan": "maa",  # माँ/मां
        "kŕpaya": "kripya",  # कृपया
        "koolha": "kulha",  # कूल्हा
        "eeshwar": "ishwar",  # ईश्वर
        "eeshwara": "ishwar",  # ईश्वर (alternate form)
        "bhagwaan": "bhagwan",  # भगवान
        "bhagawaan": "bhagwan",  # भगवान (with v→w)
        "allaah": "allah",  # अल्लाह
        "jeeja": "jija",  # जीजा
        "naxoon": "nakhun",  # नाखून
        "naaxoon": "nakhun",  # नाखून
        "nakhoon": "nakhun",  # नाखून
        "jnyan": "gyaan",  # ज्ञान
        "jnyaan": "gyaan",  # ज्ञान
        "zindagee": "zindagi",  # जिंदगी
        "khadee": "khadi",  # खड़ी
        "ladkee": "ladki",  # लड़की
        "betee": "beti",  # बेटी
        "nadee": "nadi",  # नदी
        # Family words with double vowels
        "daada": "dada",  # दादा
        "daadi": "dadi",  # दादी
        "naana": "nana",  # नाना
        "naani": "nani",  # नानी
        "chaacha": "chacha",  # चाचा
        "chaachi": "chachi",  # चाची
        "maama": "mama",  # मामा
        "maami": "mami",  # मामी
        "paapa": "papa",  # पापा
        "taaya": "taya",  # ताया
        "taai": "tai",  # ताई
        "bhaabhi": "bhabhi",  # भाभी
        "saala": "sala",  # साला
        "saali": "sali",  # साली
        # Common words with double vowels
        "bhaai": "bhai",  # भाई
        "jaao": "jao",  # जाओ
        "khaao": "khao",  # खाओ
        "gyaarah": "gyarah",  # ग्यारह
        "baarah": "barah",  # बारह
        "athaarah": "atharah",  # अठारह
        "tumhaara": "tumhara",  # तुम्हारा
        "maatha": "matha",  # माथा
        "jeebh": "jibh",  # जीभ
        "khaana": "khana",  # खाना
        "chaawal": "chawal",  # चावल
        "tamaatar": "tamatar",  # टमाटर
        "aalu": "aaloo",  # आलू
        "joos": "juice",  # जूस
        "neembu": "nimbu",  # नींबू
        "dhanyawaad": "dhanyavaad",  # धन्यवाद
        # More common words
        "aao": "aao",  # आओ (correct)
        "baap": "baap",  # बाप (correct)
        "saas": "saas",  # सास (correct)
        "daamaad": "daamaad",  # दामाद (correct)
        "sarkar": "sarkar",  # सरकार (correct)
        "chunav": "chunav",  # चुनाव (correct)
        "azaadi": "azaadi",  # आज़ादी (correct)
        "ganatantra": "ganatantra",  # गणतंत्र (correct)
        "pujari": "pujari",  # पुजारी (correct)
        "maulvi": "maulvi",  # मौलवी (correct)
        "padri": "padri",  # पादरी (correct)
    }
    lower = result.lower()
    if lower in word_fixes:
        return word_fixes[lower]

    # Step 10: Final cleanup
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
