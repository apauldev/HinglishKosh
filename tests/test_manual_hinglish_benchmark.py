"""Manual Hinglish benchmark — how Indians actually type.

These are hand-written Hinglish romanizations of Hindi sentences,
written the way an Indian would type on WhatsApp / social media.
Used to benchmark the engine against real-world usage.
"""

import pytest

from src.processing.transliterate import transliterate_rule_based

# (Hindi sentence, Manual Hinglish — how an Indian would type)
MANUAL_HINGLISH = [
    # --- Definitions / explanations ---
    (
        "जो किसी कंपनी या संस्था पर आधारित हो और उसी के द्वारा संचालित होता हो",
        "jo kisi company ya sanstha pe aadharit ho aur usi ke dwara sanchalit hota ho",
    ),
    (
        "संभव न होने की अवस्था या भाव",
        "sambhav na hone ki avastha ya bhav",
    ),
    (
        "सम्पूर्ण रूप से नष्ट होना या बरबाद होना",
        "sampoorn roop se nasht hona ya barbad hona",
    ),
    (
        "एक दूसरे से संबंधित होने की अवस्था या भाव",
        "ek dusre se sambandhit hone ki avastha ya bhav",
    ),
    (
        "संभालने की क्रिया या भाव",
        "sambhalne ki kriya ya bhav",
    ),
    (
        "हाथ की हथेली के ऊपर पंजे के पास की पाँचों उँगलियों के सिरों का समूह",
        "hath ki hatheli ke upar panje ke pass ki paanchon ungliyon ke siron ka samuh",
    ),
    (
        "बहुत से लोगों के एक जगह इक्कठा होने पर होनेवाली गहरी या घनी स्थिति",
        "bahut se logon ke ek jagah ikattha hone par hone wali gehri ya ghani sthiti",
    ),
    (
        "जिसके पास रहने का कोई निश्चित स्थान न हो और जो कहीं भी चला जाए, वहाँ रहे",
        "jiske paas rehne ka koi fixed jagah na ho aur jo kahin bhi chala jaye, wahan rahe",
    ),
    (
        "जिसका मुकाबला न किया जा सके, सब से अच्छा या बढ़कर, जैसे कोई वाला या व्यक्ति",
        "jiska muqabla na kiya ja sake, sab se accha ya badhkar, jaise koi wala ya vyakti",
    ),
    (
        "किसी काम, समस्या आदि को दुरुस्त करने की कोई तरकीब या वजह",
        "kisi kaam, samasya aadi ko durust karne ki koi tarkeeb ya wajah",
    ),
    (
        "हर वक्त या हर समय होने या रहने वाला",
        "har waqt ya har samay hone ya rehne wala",
    ),
    (
        "बिना किसी प्रकार का अंतर या भेद हुए एक ही प्रकार का होने की अवस्था या भाव",
        "bina kisi prakar ka antar ya bhed hue ek hi prakar ka hone ki avastha ya bhav",
    ),
    (
        "ज्ञान प्राप्त करने की क्रिया या भाव",
        "gyan prapt karne ki kriya ya bhav",
    ),
    (
        "वह स्थान जहाँ पानी इकट्ठा किया गया हो अथवा पानी इकट्ठा होने की क्रिया",
        "wo jagah jahan paani ikattha kiya gaya ho ya paani ikattha hone ki kriya",
    ),
    (
        "पानी में मिली हुई मिट्टी, धूल या और कोई गंदी चीज",
        "paani me mili hui mitti, dhool ya aur koi gandi cheez",
    ),
    (
        "जिसका कोई विकल्प न हो या जो सबसे अच्छा हो",
        "jiska koi vikalp na ho ya jo sabse accha ho",
    ),
    # --- Common sentences ---
    (
        "नमस्ते, आप कैसे हैं?",
        "namaste, aap kaise hain?",
    ),
    (
        "मैं ठीक हूँ, धन्यवाद",
        "main theek hoon, dhanyavad",
    ),
    (
        "आज मौसम बहुत अच्छा है",
        "aaj mausam bahut accha hai",
    ),
    (
        "क्या तुम मेरी मदद कर सकते हो?",
        "kya tum meri madad kar sakte ho?",
    ),
    (
        "मुझे हिंदी बोलना नहीं आता",
        "mujhe hindi bolna nahi aata",
    ),
    (
        "यह कितने का है?",
        "ye kitne ka hai?",
    ),
    (
        "मुझे यह पसंद नहीं आया",
        "mujhe ye pasand nahi aaya",
    ),
    (
        "क्या तुम मुझे अपना नंबर दे सकते हो?",
        "kya tum mujhe apna number de sakte ho?",
    ),
    (
        "मैं कल आ जाऊँगा",
        "main kal aa jaunga",
    ),
    (
        "तुम्हें कब तक तैयार होना है?",
        "tumhe kab tak taiyar hona hai?",
    ),
    (
        "यह बहुत महँगा है",
        "ye bahut mehnga hai",
    ),
    (
        "मैंने तुम्हें बहुत देर से बुलाया",
        "maine tumhe bahut der se bulaya",
    ),
    (
        "क्या तुम मेरे साथ चलोगे?",
        "kya tum mere saath chaloge?",
    ),
    (
        "मुझे एक गिलास पानी चाहिए",
        "mujhe ek glass paani chahiye",
    ),
    (
        "तुम्हारा घर कहाँ है?",
        "tumhara ghar kahan hai?",
    ),
    (
        "मैं रोज़ सुबह जल्दी उठता हूँ",
        "main roz subah jaldi uthta hoon",
    ),
    (
        "यह बहुत अच्छा विचार है",
        "ye bahut accha vichar hai",
    ),
    (
        "क्या तुम मुझे यह समझा सकते हो?",
        "kya tum mujhe ye samjha sakte ho?",
    ),
    (
        "मैं तुमसे प्यार करता हूँ",
        "main tumse pyar karta hoon",
    ),
    (
        "तुम मेरी ज़िंदगी में बहुत ज़रूरी हो",
        "tum meri zindagi mein bahut zaroori ho",
    ),
    # --- Everyday phrases ---
    (
        "खाना खा लिया?",
        "khana kha liya?",
    ),
    (
        "सो जाओ अब",
        "so jao ab",
    ),
    (
        "कल स्कूल जाना है",
        "kal school jana hai",
    ),
    (
        "मम्मी ने बुलाया है",
        "mummy ne bulaya hai",
    ),
    (
        "पापा ऑफिस गए हैं",
        "papa office gaye hain",
    ),
    (
        "दरवाज़ा बंद कर दो",
        "darwaza band kar do",
    ),
    (
        "लाइट जला दो",
        "light jala do",
    ),
    (
        "पंखा चला दो",
        "pankha chala do",
    ),
    (
        "मेरा फ़ोन कहाँ है?",
        "mera phone kahan hai?",
    ),
    (
        "चाबी कहाँ रखी है?",
        "chabi kahan rakhi hai?",
    ),
    # --- Actions / verbs ---
    (
        "मुझे जाना है",
        "mujhe jana hai",
    ),
    (
        "तुम क्या कर रहे हो?",
        "tum kya kar rahe ho?",
    ),
    (
        "मैं पढ़ रहा हूँ",
        "main padh raha hoon",
    ),
    (
        "वो सो रहा है",
        "wo so raha hai",
    ),
    (
        "बच्चे खेल रहे हैं",
        "bachche khel rahe hain",
    ),
    (
        "गाड़ी चला रहा हूँ",
        "gadi chala raha hoon",
    ),
    (
        "खाना बना रही हूँ",
        "khana bana rahi hoon",
    ),
    (
        "देख रहा हूँ",
        "dekh raha hoon",
    ),
    (
        "सुन रहा हूँ",
        "sun raha hoon",
    ),
    (
        "बोल रहा हूँ",
        "bol raha hoon",
    ),
    # --- Time expressions ---
    (
        "आज कल से ज़्यादा गर्म है",
        "aaj kal se zyada garm hai",
    ),
    (
        "कल रात बहुत बारिश हुई",
        "kal raat bahut barish hui",
    ),
    (
        "परसों से काम शुरू होगा",
        "parson se kaam shuru hoga",
    ),
    (
        "अभी दोपहर है",
        "abhi dopahar hai",
    ),
    (
        "शाम को मिलते हैं",
        "sham ko milte hain",
    ),
    (
        "रात को फ़ोन करना",
        "raat ko phone karna",
    ),
    (
        "सुबह जल्दी उठना है",
        "subah jaldi uthna hai",
    ),
    (
        "बहुत देर हो गई",
        "bahut der ho gayi",
    ),
    (
        "अभी तक नहीं आया",
        "abhi tak nahi aaya",
    ),
    (
        "जल्दी आओ",
        "jaldi aao",
    ),
    # --- Emotions / feelings ---
    (
        "मुझे बहुत गुस्सा आ रहा है",
        "mujhe bahut gussa aa raha hai",
    ),
    (
        "मैं बहुत खुश हूँ",
        "main bahut khush hoon",
    ),
    (
        "मुझे बहुत दुख हुआ",
        "mujhe bahut dukh hua",
    ),
    (
        "मैं बहुत परेशान हूँ",
        "main bahut pareshan hoon",
    ),
    (
        "तुमसे मिलकर बहुत अच्छा लगा",
        "tumse milkar bahut accha laga",
    ),
    (
        "मैं तुम्हें बहुत याद करता हूँ",
        "main tumhe bahut yaad karta hoon",
    ),
    (
        "यह सुनकर बहुत खुशी हुई",
        "ye sunkar bahut khushi hui",
    ),
    (
        "मुझे बहुत तनाव है",
        "mujhe bahut tanav hai",
    ),
    (
        "मैं बहुत थक गया हूँ",
        "main bahut thak gaya hoon",
    ),
    (
        "मुझे बहुत भूख लगी है",
        "mujhe bahut bhook lagi hai",
    ),
    # --- Objects / things ---
    (
        "मेरी किताब कहाँ है?",
        "meri kitab kahan hai?",
    ),
    (
        "यह बहुत महँगा है",
        "ye bahut mehnga hai",
    ),
    (
        "वो बहुत सस्ता है",
        "wo bahut sasta hai",
    ),
    (
        "मुझे एक नया फ़ोन चाहिए",
        "mujhe ek naya phone chahiye",
    ),
    (
        "यह बहुत अच्छा है",
        "ye bahut accha hai",
    ),
    (
        "वो बहुत बुरा है",
        "wo bahut bura hai",
    ),
    (
        "मेरे पास पैसे नहीं हैं",
        "mere paas paise nahi hain",
    ),
    (
        "तुम्हारे पास कितने पैसे हैं?",
        "tumhare paas kitne paise hain?",
    ),
    (
        "यह कितने का है?",
        "ye kitne ka hai?",
    ),
    (
        "वो बहुत महँगा है",
        "wo bahut mehnga hai",
    ),
    # --- Places ---
    (
        "मैं घर पर हूँ",
        "main ghar par hoon",
    ),
    (
        "वो ऑफिस में है",
        "wo office mein hai",
    ),
    (
        "हम स्कूल में हैं",
        "hum school mein hain",
    ),
    (
        "वो बाज़ार गया है",
        "wo bazaar gaya hai",
    ),
    (
        "मैं मंदिर जा रहा हूँ",
        "main mandir ja raha hoon",
    ),
    (
        "वो अस्पताल में है",
        "wo aspatal mein hai",
    ),
    (
        "हम पार्क में हैं",
        "hum park mein hain",
    ),
    (
        "वो दुकान पर है",
        "wo dukan par hai",
    ),
    (
        "मैं बस में हूँ",
        "main bus mein hoon",
    ),
    (
        "वो ट्रेन में है",
        "wo train mein hai",
    ),
    # --- Relationships ---
    (
        "वो मेरा भाई है",
        "wo mera bhai hai",
    ),
    (
        "वो मेरी बहन है",
        "wo meri behen hai",
    ),
    (
        "वो मेरे पापा हैं",
        "wo mere papa hain",
    ),
    (
        "वो मेरी मम्मी हैं",
        "wo meri mummy hain",
    ),
    (
        "वो मेरा दोस्त है",
        "wo mera dost hai",
    ),
    (
        "वो मेरी गर्लफ्रेंड है",
        "wo meri girlfriend hai",
    ),
    (
        "वो मेरा बॉयफ्रेंड है",
        "wo mera boyfriend hai",
    ),
    (
        "वो मेरे टीचर हैं",
        "wo mere teacher hain",
    ),
    (
        "वो मेरे बॉस हैं",
        "wo mere boss hain",
    ),
    (
        "वो मेरे पड़ोसी हैं",
        "wo mere padosi hain",
    ),
]


class TestManualHinglishBenchmark:
    """Benchmark engine against manually-written Hinglish."""

    def test_manual_hinglish_accuracy(self):
        """Check word-level accuracy against manually-written Hinglish."""
        total_words = 0
        matching_words = 0
        failures = []

        for hindi, manual in MANUAL_HINGLISH:
            engine = transliterate_rule_based(hindi)
            manual_words = manual.split()
            engine_words = engine.split()

            for mw, ew in zip(manual_words, engine_words):
                total_words += 1
                if mw.lower() == ew.lower():
                    matching_words += 1
                else:
                    if len(failures) < 20:
                        failures.append((hindi[:30], mw, ew))

        word_pct = (matching_words / total_words) * 100

        print("\n=== Manual Hinglish Benchmark ===")
        print(f"Total words: {total_words}")
        print(f"Matching words: {matching_words} ({word_pct:.1f}%)")
        print("\nSample failures:")
        for ctx, mw, ew in failures[:10]:
            print(f"  '{mw}' vs '{ew}' (in: {ctx}...)")

        # We expect at least 50% word-level match
        assert word_pct >= 50, f"Only {word_pct:.1f}% word match (expected ≥50%)"

    def test_common_patterns(self):
        """Verify common patterns that Indians always get right."""
        patterns = [
            ("नमस्ते", "namaste"),
            ("पानी", "paani"),
            ("खाना", "khana"),
            ("घर", "ghar"),
            ("दोस्त", "dost"),
            ("बहन", "behen"),
            ("भाई", "bhai"),
            ("मम्मी", "mammi"),
            ("पापा", "papa"),
            ("स्कूल", "school"),
            ("ऑफिस", "office"),
            ("बाज़ार", "bazaar"),
            ("अस्पताल", "aspatal"),
            ("मंदिर", "mandir"),
            ("किताब", "kitab"),
            ("फ़ोन", "phone"),
            ("गाड़ी", "gaadi"),
            ("दरवाज़ा", "darwaza"),
            ("पंखा", "pankha"),
            ("लाइट", "light"),
        ]

        failures = []
        for hindi, expected in patterns:
            engine = transliterate_rule_based(hindi)
            if engine != expected:
                failures.append((hindi, expected, engine))

        if failures:
            msg = "Common pattern failures:\n"
            for hindi, expected, engine in failures:
                msg += f"  {hindi}: expected '{expected}', got '{engine}'\n"
            pytest.fail(msg)

    def test_function_words(self):
        """Verify common function words."""
        patterns = [
            ("मैं", "main"),
            ("तुम", "tum"),
            ("वो", "wo"),
            ("हम", "hum"),
            ("यह", "ye"),
            ("वह", "wo"),
            ("क्या", "kya"),
            ("कैसे", "kaise"),
            ("कहाँ", "kahan"),
            ("कब", "kab"),
            ("क्यों", "kyun"),
            ("नहीं", "nahi"),
            ("हाँ", "haan"),
            ("अच्छा", "accha"),
            ("बुरा", "bura"),
            ("बड़ा", "bada"),
            ("छोटा", "chhota"),
            ("नया", "naya"),
            ("पुराना", "purana"),
            ("लंबा", "lamba"),
        ]

        failures = []
        for hindi, expected in patterns:
            engine = transliterate_rule_based(hindi)
            if engine != expected:
                failures.append((hindi, expected, engine))

        if failures:
            msg = "Function word failures:\n"
            for hindi, expected, engine in failures:
                msg += f"  {hindi}: expected '{expected}', got '{engine}'\n"
            pytest.fail(msg)
