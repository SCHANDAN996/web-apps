import os

# ------------------------------------------------------------------
# 1. कॉन्फ़िगरेशन
# ------------------------------------------------------------------
BASE_DIR = "Intermediate_12th_Math_WorldClass"
LEVEL = "intermediate"

BOOK_INTRO_HI = (
    "प्रिय पाठक,\n"
    "यह पुस्तक आपके संघर्षों को समझती है – क्योंकि मैं भी वहाँ था जहाँ आप आज हैं।\n"
    "यह यात्रा केवल सीखने की नहीं, बल्कि उस सफल स्वरूप से मिलने की है जो आप कल बनने वाले हैं।\n"
    "हर अध्याय एक नया द्वार खोलेगा – बस पहला कदम उठाइए।"
)

BOOK_INTRO_EN = (
    "Dear learner,\n"
    "This book understands your struggle – because I have been where you are today.\n"
    "This journey is not just about learning, but about meeting the successful version of you that you are going to become tomorrow.\n"
    "Each chapter will open a new door – just take the first step."
)

# ------------------------------------------------------------------
# 2. अध्याय सूची (अब 23 अध्याय, नए चैप्टर जोड़े गए हैं)
# ------------------------------------------------------------------
chapters = [
    ("01_Number_System", "संख्या प्रणाली (उन्नत)", "Number System (Advanced)"),
    ("02_LCM_HCF", "ल.स.प. और म.स.प.", "LCM & HCF"),
    ("03_Simplification", "सरलीकरण", "Simplification"),
    ("04_Fractions_Decimals", "भिन्न और दशमलव", "Fractions & Decimals"),
    ("05_Percentage", "प्रतिशत", "Percentage"),
    ("06_Average", "औसत", "Average"),
    ("07_Ratio_Proportion", "अनुपात और समानुपात", "Ratio & Proportion"),
    ("08_Profit_Loss", "लाभ और हानि", "Profit & Loss"),
    ("09_Simple_Interest", "साधारण ब्याज", "Simple Interest"),
    ("10_Compound_Interest", "चक्रवृद्धि ब्याज", "Compound Interest"),
    ("11_Time_Work", "समय और कार्य", "Time & Work"),
    ("12_Time_Distance", "समय और दूरी", "Time & Distance"),
    ("13_Mixture_Alligation", "मिश्रण और पृथ्थीकरण", "Mixture & Alligation"),
    ("14_Mensuration", "क्षेत्रमिति", "Mensuration"),
    ("15_Geometry", "ज्यामिति", "Geometry"),
    ("16_Algebra", "बीजगणित", "Algebra"),
    ("17_Trigonometry", "त्रिकोणमिति", "Trigonometry"),
    ("18_Data_Interpretation", "डेटा व्याख्या", "Data Interpretation"),
    ("19_Statistics", "सांख्यिकी", "Statistics"),
    ("20_Probability", "प्रायिकता", "Probability"),
    ("21_Permutation_Combination", "क्रमचय और संचय", "Permutation & Combination"),
    ("22_Number_Series", "संख्या श्रेणी", "Number Series"),
    ("23_Quadratic_Equations", "द्विघात समीकरण एवं श्रेणी", "Quadratic Equations & Series"),
]

# ------------------------------------------------------------------
# 3. प्रैक्टिस सेट का कठिनाई वितरण (वही नियम)
# ------------------------------------------------------------------
def get_practice_difficulty_instruction(set_num, lang):
    if set_num == 1:
        return (
            "प्रश्न 1 से 20 तक आसान (Easy) हों, प्रश्न 21 से 25 तक मध्यम (Medium) हों।"
            if lang == 'hi' else
            "Questions 1 to 20 should be Easy, Questions 21 to 25 should be Medium."
        )
    elif set_num in [2, 3, 4]:
        return (
            "सभी 25 प्रश्न मध्यम (Medium) स्तर के हों।"
            if lang == 'hi' else
            "All 25 questions should be Medium."
        )
    elif set_num == 5:
        return (
            "प्रश्न 101 से 120 तक मध्यम (Medium), प्रश्न 121 से 125 तक कठिन (Hard) हों।"
            if lang == 'hi' else
            "Questions 101 to 120 should be Medium, Questions 121 to 125 should be Hard."
        )
    else:
        return (
            "सभी 25 प्रश्न कठिन (Hard) स्तर के हों।"
            if lang == 'hi' else
            "All 25 questions should be Hard."
        )

# ------------------------------------------------------------------
# 4. फ़ाइल निर्माण फ़ंक्शन
# ------------------------------------------------------------------
def create_chapter_structure(base_dir, chapter_list):
    os.makedirs(base_dir, exist_ok=True)

    # किताब का इंट्रो
    with open(os.path.join(base_dir, "00_Book_Introduction_hi.txt"), 'w', encoding='utf-8') as f:
        f.write(BOOK_INTRO_HI)
    with open(os.path.join(base_dir, "00_Book_Introduction_en.txt"), 'w', encoding='utf-8') as f:
        f.write(BOOK_INTRO_EN)

    for folder_suffix, topic_hi, topic_en in chapter_list:
        chapter_dir = os.path.join(base_dir, f"Chapter_{folder_suffix}")
        os.makedirs(chapter_dir, exist_ok=True)

        # ⚡ सख्त निर्देश के साथ प्री-प्रॉम्प्ट (अब 8 खंड)
        chapter_intro_prompt = (
            "🚨 **सख्त निर्देश (STRICT RULE):**\n"
            "- आप जो भी सेक्शन जनरेट करें, केवल वही सामग्री दें जो किताब के लिए आवश्यक है।\n"
            "- कोई भी अतिरिक्त शब्द, संदर्भ, नमस्कार, परिचय, समापन टिप्पणी, या \"यह रहा आपका उत्तर\" जैसा मेटा-टेक्स्ट न लिखें।\n"
            "- आउटपुट सीधे किताब में चिपकाने लायक होना चाहिए — बिना एक भी अनावश्यक शब्द के।\n"
            "- इस नियम का पालन हर प्रतिक्रिया में सख्ती से करें।\n\n"
            "--------------------------------------------\n\n"
            "👉 आज हम \"स्टूडेंट स्टेशन\" नाम की एक हिंदी-अंग्रेजी द्विभाषी पुस्तक शृंखला का Intermediate (12वीं) स्तर का अध्याय तैयार कर रहे हैं।\n"
            "यह पुस्तक SSC CGL (Mains), IBPS PO, RRB NTPC, CAT, और अन्य प्रतियोगी परीक्षाओं के लिए है।\n"
            f"इस सत्र में अध्याय का नाम: **\"{topic_hi} / {topic_en}\"** है।\n\n"
            "अध्याय निम्नलिखित 8 खंडों में बनेगा। हर खंड को मैं बारी-बारी से generate करने का निर्देश दूँगा।\n\n"
            "### खंड और उनकी विशेषताएँ\n"
            "1. **📖 Content (मुख्य सामग्री)** – हिंदी और अंग्रेजी, दोनों में अलग-अलग।\n"
            "   - शक्तिशाली हुक (कहानी/चौंकाने वाला तथ्य) से शुरुआत\n"
            "   - छोटे-छोटे पैराग्राफ़ (खंडन सिद्धांत)\n"
            "   - हर 2-3 पैराग्राफ बाद Active Recall प्रॉम्प्ट (🧠)\n"
            "   - कम से कम एक मजेदार स्मृति-सहायक ट्रिक (Mnemonic)\n"
            "   - अंत में सारांश तालिका और \"2 दिन बाद दोहराएँ\" संकेत\n"
            "   - भाषा अत्यंत सरल, संवादात्मक, प्रेरक\n\n"
            "2. **📋 Important Formulas (महत्वपूर्ण सूत्र)** – हिंदी और अंग्रेजी में अलग-अलग।\n"
            "   - केवल सूत्र और संक्षिप्त संकेत, कोई व्याख्या नहीं\n"
            "   - सारणीबद्ध रूप में\n"
            "   - सूत्र का नाम, सूत्र, और एक-पंक्ति का उपयोग-संकेत\n\n"
            "3. **🧒 Feynman (फेनमैन व्याख्या)** – हिंदी और अंग्रेजी में अलग-अलग।\n"
            "   - सबसे कठिन अवधारणा को 12 वर्षीय बच्चे जैसी भाषा में समझाना\n"
            "   - मजेदार कहानी + एक अविस्मरणीय ट्रिक\n\n"
            "4. **🗺️ Mind Map** – एक ही बार में, Mermaid कोड में।\n"
            "   - सभी मुख्य और उप-अवधारणाओं का संबंध\n\n"
            "5. **🃏 Flashcards** – हिंदी और अंग्रेजी में अलग-अलग, 15-20 कार्ड।\n"
            "   - सामने प्रश्न, पीछे संक्षिप्त उत्तर\n"
            "   - कम से कम 2 कार्ड में म्नेमोनिक ट्रिक पूछना\n\n"
            "6. **📊 PYQ विश्लेषण** – हिंदी और अंग्रेजी में अलग-अलग।\n"
            "   - पिछले 10 वर्षों के PYQ का डेटा-संचालित विश्लेषण\n"
            "   - शीर्ष 10 हाई-यील्ड प्रश्न समाधान सहित\n"
            "   - प्रश्नों के \"हुक\" या \"ट्रैप\" की व्याख्या\n\n"
            "7. **🪄 Short Tricks** – हिंदी और अंग्रेजी में अलग-अलग।\n"
            "   - 10-15 यादगार स्मृति-सहायक ट्रिक्स (कीवर्ड, लोकस, एक्रोनिम)\n"
            "   - हर ट्रिक एक अलग बॉक्स में\n\n"
            "8. **📝 Practice (MCQs)** – हिंदी और अंग्रेजी दोनों के लिए 6 सेट (कुल 150 प्रश्न)।\n"
            "   - सेट 1: Q1–20 Easy, Q21–25 Medium\n"
            "   - सेट 2, 3, 4: पूरे 25 Medium\n"
            "   - सेट 5: Q101–120 Medium, Q121–125 Hard\n"
            "   - सेट 6: पूरे 25 Hard\n"
            "   - हर प्रश्न: 4 विकल्प, सही उत्तर, चरण-दर-चरण हल, स्रोत (NCERT/परीक्षा)\n\n"
            "➡️ **मैं अब बारी-बारी से आपको प्रॉम्प्ट दूँगा, जैसे \"Content हिंदी बनाओ\", \"Formulas हिंदी दो\" आदि।**\n"
            "कृपया हर बार केवल वही खंड generate करें, और पूरी quality बनाए रखें।"
        )
        with open(os.path.join(chapter_dir, "Chapter_Intro_Prompt.txt"), 'w', encoding='utf-8') as f:
            f.write(chapter_intro_prompt)

        # --- सामान्य सेक्शन फ़ाइलें ---
        files = {
            # 📖 Content
            f"Content_hi.txt": (
                f"# Chapter: {topic_hi}, Level: {LEVEL}\n\n"
                f"@content_agent lang=hi level={LEVEL} role='अनुभवी शिक्षक और संज्ञानात्मक मनोवैज्ञानिक' "
                f"'{topic_hi}' के लिए एक ऐसा अध्याय लिखो जो 12वीं स्तर के छात्रों के लिए जटिल लगने वाली अवधारणाओं को भी बेहद सरल बना दे।\n"
                "चरण-दर-चरण (Chain-of-Thought) लिखो:\n"
                "1. पहले अध्याय की रूपरेखा और सीखने के उद्देश्य लिखो।\n"
                "2. फिर एक शक्तिशाली हुक (कहानी/चौंकाने वाला तथ्य/विरोधाभास) से शुरुआत करो।\n"
                f"3. '{topic_hi}' से जुड़ी आम समस्या को पहचानो और भावनात्मक जुड़ाव बनाओ।\n"
                "4. मुख्य सामग्री को छोटे-छोटे टुकड़ों में बाँटो (खंडन सिद्धांत)।\n"
                "5. हर 2-3 पैराग्राफ बाद एक Active Recall Prompt (🧠) रखो।\n"
                "6. कम से कम एक मजेदार स्मृति-सहायक ट्रिक (Mnemonic) दो।\n"
                "7. अंत में एक सारांश तालिका और 'इसे 2 दिन बाद दोहराएँ' का निर्देश दो।\n"
                "भाषा अत्यंत सरल, संवादात्मक और प्रेरक रखो, लेकिन विषय की गहराई 12वीं स्तर की हो।"
            ),
            f"Content_en.txt": (
                f"# Chapter: {topic_en}, Level: {LEVEL}\n\n"
                f"@content_agent lang=en level={LEVEL} role='experienced educator and cognitive psychologist' "
                f"'Write a chapter on {topic_en} that makes even complex 12th-grade concepts feel incredibly simple. "
                "Follow Chain-of-Thought:\n"
                "1. First, outline the chapter and learning goals.\n"
                "2. Start with a powerful hook (story, shocking fact, contradiction).\n"
                f"3. Acknowledge the learner's common struggle with '{topic_en}' and build empathy.\n"
                "4. Break content into small chunks (Segmenting Principle).\n"
                "5. After every 2-3 paragraphs, insert an Active Recall Prompt (🧠).\n"
                "6. Include at least one memory trick (mnemonic) that is weird or funny.\n"
                "7. End with a summary table and 'Review this after 2 days' prompt.\n"
                "Keep language extremely simple, conversational, and motivational, but depth at 12th grade level."
            ),

            # 📋 Important Formulas (नया सेक्शन)
            f"Important_Formulas_hi.txt": (
                f"# Chapter: {topic_hi}, Level: {LEVEL}\n\n"
                f"@content_agent lang=hi level={LEVEL} "
                f"'{topic_hi}' के सभी महत्वपूर्ण सूत्रों, समीकरणों और नियमों की एक सूची तैयार करो।\n"
                "निर्देश:\n"
                "- केवल सूत्र और एक-पंक्ति का संकेत (कब इस्तेमाल करना है), कोई विस्तृत व्याख्या नहीं।\n"
                "- साफ़ तालिका (टेबल) में प्रस्तुत करो: सूत्र का नाम | सूत्र | उपयोग-संकेत\n"
                "- सभी सूत्रों को कवर करो जो परीक्षा में प्रश्न हल करने के लिए आवश्यक हैं।\n"
                "- भाषा सरल और सटीक हो।"
            ),
            f"Important_Formulas_en.txt": (
                f"# Chapter: {topic_en}, Level: {LEVEL}\n\n"
                f"@content_agent lang=en level={LEVEL} "
                f"'List all important formulas, equations, and rules for {topic_en}.\n"
                "Instructions:\n"
                "- Only formulas and a one-line hint (when to use), no detailed explanation.\n"
                "- Present in a clean table: Formula Name | Formula | Use-Hint\n"
                "- Cover all formulas essential for solving exam questions.\n"
                "- Keep language simple and precise.'"
            ),

            # 🧒 Feynman
            f"Feynman_hi.txt": (
                f"# Chapter: {topic_hi}, Level: {LEVEL}\n\n"
                f"@content_agent lang=hi level={LEVEL} role='रिचर्ड फेनमैन जैसा शिक्षक' "
                f"'{topic_hi}' की सबसे कठिन अवधारणा को इतनी सरल भाषा में समझाओ कि 12 साल का बच्चा भी समझ जाए। "
                "एक मजेदार, वास्तविक जीवन की कहानी (स्टोरी) बुनो। एक ऐसी ट्रिक बताओ जो कभी न भूले। "
                "अंत में एक प्रश्न पूछो।"
            ),
            f"Feynman_en.txt": (
                f"# Chapter: {topic_en}, Level: {LEVEL}\n\n"
                f"@content_agent lang=en level={LEVEL} role='a teacher like Richard Feynman' "
                f"'Explain the hardest concept of {topic_en} so simply that a 12-year-old can understand. "
                "Weave a fun real-life story. Give a trick that they will never forget. End with a question."
            ),

            # 🗺️ Mind Map
            f"Mind_Map.txt": (
                f"# Chapter: {topic_en}, Level: {LEVEL}\n\n"
                f"@content_agent 'Create a detailed mind map (Mermaid code) for the chapter \"{topic_en}\". "
                "Show main concepts, sub-concepts, and their interconnections clearly.'"
            ),

            # 🃏 Flashcards
            f"Flashcards_hi.txt": (
                f"# Chapter: {topic_hi}, Level: {LEVEL}\n\n"
                f"@content_agent lang=hi level={LEVEL} "
                f"'{topic_hi}' के लिए 15-20 फ्लैशकार्ड बनाओ। हर कार्ड में सामने एक प्रश्न (जिज्ञासा पैदा करे) और पीछे संक्षिप्त उत्तर। "
                "कम से कम 2 कार्ड में म्नेमोनिक ट्रिक का सवाल पूछो।"
            ),
            f"Flashcards_en.txt": (
                f"# Chapter: {topic_en}, Level: {LEVEL}\n\n"
                f"@content_agent lang=en level={LEVEL} "
                f"'Create 15-20 flashcards for {topic_en}. Each card: front a curiosity-invoking question, back concise answer. "
                "Include at least 2 cards that ask about a mnemonic trick.'"
            ),

            # 📊 PYQ
            f"PYQ_hi.txt": (
                f"# Chapter: {topic_hi}, Level: {LEVEL}\n\n"
                f"@pyq_agent lang=hi level={LEVEL} "
                f"'{topic_hi}' के लिए पिछले 10 वर्षों के PYQ का विश्लेषण करो (SSC CGL Mains, IBPS PO, RRB NTPC, CAT आदि)। "
                "शीर्ष 10 हाई-यील्ड प्रश्नों को हल सहित दो। "
                "यह भी बताओ कि ये प्रश्न किस 'हुक' या 'ट्रैप' का उपयोग करते हैं।"
            ),
            f"PYQ_en.txt": (
                f"# Chapter: {topic_en}, Level: {LEVEL}\n\n"
                f"@pyq_agent lang=en level={LEVEL} "
                f"'Analyse PYQs of {topic_en} for last 10 years (SSC CGL Mains, IBPS PO, RRB NTPC, CAT etc.). "
                "Give top 10 high-yield questions with solutions. "
                "Also explain what psychological hook or trap each question uses.'"
            ),

            # 🪄 Short Tricks
            f"Short_Tricks_hi.txt": (
                f"# Chapter: {topic_hi}, Level: {LEVEL}\n\n"
                f"@content_agent lang=hi level={LEVEL} role='स्मृति-सहायक तकनीक विशेषज्ञ' "
                f"'{topic_hi}' के सभी मुख्य सूत्रों, नियमों और अवधारणाओं के लिए 10-15 मज़ेदार और अजीबोगरीब स्मृति-सहायक ट्रिक्स (Mnemonics) तैयार करो। "
                "हर ट्रिक ऐसी हो जो एक बार पढ़ने पर कभी न भूले। जहाँ संभव हो, कीवर्ड विधि, लोकस विधि, या एक्रोनिम्स का उपयोग करो। "
                "हर ट्रिक को एक छोटे बॉक्स में लिखो।"
            ),
            f"Short_Tricks_en.txt": (
                f"# Chapter: {topic_en}, Level: {LEVEL}\n\n"
                f"@content_agent lang=en level={LEVEL} role='mnemonic specialist' "
                f"'Create 10-15 fun and outrageous memory tricks (Mnemonics) for all key formulas, rules and concepts of {topic_en}. "
                "Each trick should be unforgettable. Use Keyword Method, Loci, or Acronyms wherever possible. "
                "Present each trick in a separate box.'"
            ),
        }

        # --- प्रैक्टिस सेट (6 सेट × 25 प्रश्न, कुल 150) ---
        for set_num in range(1, 7):
            start_q = (set_num - 1) * 25 + 1
            end_q = set_num * 25
            diff_hi = get_practice_difficulty_instruction(set_num, 'hi')
            diff_en = get_practice_difficulty_instruction(set_num, 'en')

            files[f"Practice_hi_Set_{set_num:02d}.txt"] = (
                f"# Chapter: {topic_hi}, Level: {LEVEL}, Set: {set_num}/6\n\n"
                f"@content_agent +mcq_generator_bilingual lang=hi level={LEVEL} "
                f"'{topic_hi}' के लिए 25 बहुविकल्पीय प्रश्न (MCQs) तैयार करो। "
                f"यह सेट {set_num} है (कुल 6 सेट, 150 प्रश्न)। "
                f"प्रश्न संख्या {start_q} से {end_q} तक होनी चाहिए। "
                f"{diff_hi} "
                "हर प्रश्न में 4 विकल्प, सही उत्तर, चरण-दर-चरण हल, और स्रोत (NCERT/परीक्षा नाम) ज़रूर दो।"
            )
            files[f"Practice_en_Set_{set_num:02d}.txt"] = (
                f"# Chapter: {topic_en}, Level: {LEVEL}, Set: {set_num}/6\n\n"
                f"@content_agent +mcq_generator_bilingual lang=en level={LEVEL} "
                f"'Generate 25 MCQs for {topic_en}. "
                f"This is Set {set_num} (total 6 sets, 150 questions). "
                f"Questions must be numbered {start_q} to {end_q}. "
                f"{diff_en} "
                "Each with 4 options, correct answer, step-by-step solution, and source (NCERT/exam name).'"
            )

        # सभी फ़ाइलें बनाएँ
        for file_name, content in files.items():
            file_path = os.path.join(chapter_dir, file_name)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

        # README (अपडेट: अब 8 खंड)
        readme = (
            f"# {topic_hi} / {topic_en}\n\n"
            f"**Level:** {LEVEL}\n\n"
            "## ⚠️ ज़रूरी: सबसे पहले `Chapter_Intro_Prompt.txt` पढ़ें!\n"
            "इस फ़ाइल में सख्त निर्देश और पूरे अध्याय का खाका है। इसे AI को देने के बाद ही सेक्शन बनवाएँ।\n\n"
            "##  फ़ाइलें\n"
            "| फ़ाइल | सामग्री |\n"
            "|--------|----------|\n"
            "| Chapter_Intro_Prompt.txt | **चैप्टर शुरू करने का प्री-प्रॉम्प्ट (सख्त नियम के साथ)** |\n"
            "| Content_hi/en | मुख्य पाठ |\n"
            "| Important_Formulas_hi/en | **महत्वपूर्ण सूत्रों की तालिका** |\n"
            "| Feynman_hi/en | फ़ेनमैन व्याख्या |\n"
            "| Mind_Map.txt | माइंड मैप |\n"
            "| Flashcards_hi/en | फ़्लैशकार्ड (15-20) |\n"
            "| PYQ_hi/en | PYQ विश्लेषण |\n"
            "| Short_Tricks_hi/en | स्मृति-सहायक ट्रिक्स (10-15) |\n"
            "| Practice_hi/en_Set_01..06 | **150 MCQs** (6 सेट × 25 प्रश्न, सही वितरण: Easy 20, Medium 100, Hard 30) |\n"
            "\n## उपयोग विधि\n"
            "1. `Chapter_Intro_Prompt.txt` की पूरी सामग्री कॉपी करें और AI को दें।\n"
            "2. फिर एक-एक सेक्शन के लिए छोटे निर्देश दें (जैसे \"Content हिंदी बनाओ\", \"Formulas हिंदी दो\")।\n"
            "3. AI केवल शुद्ध सामग्री देगा — उसे संबंधित .txt फ़ाइल में सेव करें।\n"
            "4. सभी फ़ाइलें तैयार होने पर अध्याय पूर्ण।\n"
        )
        with open(os.path.join(chapter_dir, "README.md"), 'w', encoding='utf-8') as f:
            f.write(readme)

    print(f"✅ वर्ल्ड-क्लास बुक स्ट्रक्चर '{base_dir}' में तैयार है।")

# ------------------------------------------------------------------
# 5. मुख्य एक्जीक्यूशन
# ------------------------------------------------------------------
if __name__ == "__main__":
    create_chapter_structure(BASE_DIR, chapters)