import os

# ============================================================
#  स्टूडेंट स्टेशन - रीज़निंग (Reasoning) बुक जनरेशन स्क्रिप्ट
#  संशोधित प्रॉम्प्ट्स (परीक्षक जाल, समय नियम, ब्लर्टिंग, स्किप स्ट्रैटेजी)
# ============================================================

# ----------------------------------------------------------
# 1. सामान्य कॉन्फ़िगरेशन
# ----------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

LEVELS = {
    "foundation": {
        "base_dir": os.path.join(SCRIPT_DIR, "10th_Level", "Reasoning"),
        "book_intro_hi": (
            "प्रिय पाठक,\n"
            "यह पुस्तक आपके संघर्षों को समझती है – क्योंकि मैं भी वहाँ था जहाँ आप आज हैं।\n"
            "यह यात्रा केवल सीखने की नहीं, बल्कि उस सफल स्वरूप से मिलने की है जो आप कल बनने वाले हैं।\n"
            "हर अध्याय एक नया द्वार खोलेगा – बस पहला कदम उठाइए।"
        ),
        "book_intro_en": (
            "Dear learner,\n"
            "This book understands your struggle – because I have been where you are today.\n"
            "This journey is not just about learning, but about meeting the successful version of you that you are going to become tomorrow.\n"
            "Each chapter will open a new door – just take the first step."
        ),
        "chapters": [
            ("01_Analogy", "सादृश्यता", "Analogy", "Verbal"),
            ("02_Classification", "वर्गीकरण", "Classification", "Verbal"),
            ("03_Coding_Decoding", "कोडिंग-डिकोडिंग", "Coding-Decoding", "Verbal"),
            ("04_Blood_Relations", "रक्त संबंध", "Blood Relations", "Verbal"),
            ("05_Direction_Sense", "दिशा ज्ञान", "Direction Sense", "Verbal"),
            ("06_Order_Ranking", "क्रम और स्थान", "Order & Ranking", "Verbal"),
            ("07_Sitting_Arrangement", "बैठक व्यवस्था (सरल)", "Sitting Arrangement (Basic)", "Verbal"),
            ("08_Puzzles_Basic", "पहेलियाँ (सरल)", "Simple Puzzles", "Verbal"),
            ("09_Venn_Diagrams", "वेन आरेख", "Venn Diagrams", "Verbal"),
            ("10_Clock_Calendar", "घड़ी और कैलेंडर", "Clock & Calendar", "Verbal"),
            ("11_Series", "शृंखला (संख्या/अक्षर)", "Number/Letter Series", "Verbal"),
            ("12_Missing_Term", "लुप्त पद", "Missing Term", "Verbal"),
            ("13_Dictionary_Order", "शब्दकोश क्रम", "Dictionary Order", "Verbal"),
            ("14_Alphabet_Questions", "अक्षर आधारित प्रश्न", "Alphabet Questions", "Verbal"),
            ("15_Mathematical_Operations", "गणितीय संक्रियाएँ", "Mathematical Operations", "Verbal"),
            ("16_Statement_Conclusion", "कथन और निष्कर्ष (सरल)", "Statement & Conclusion (Basic)", "Verbal"),
            ("17_Course_of_Action", "कथन और कार्यवाही", "Statement & Course of Action", "Verbal"),
            ("18_Inequality", "असमानता", "Inequality", "Verbal"),
            ("19_Cubes_Dice", "घन-पासा", "Cubes & Dice", "Non-verbal"),
            ("20_Mirror_Water_Images", "दर्पण/जल प्रतिबिंब", "Mirror & Water Images", "Non-verbal"),
            ("21_Paper_Folding_Cutting", "कागज मोड़ना-काटना", "Paper Folding & Cutting", "Non-verbal"),
            ("22_Figure_Series", "आकृति शृंखला/वर्गीकरण", "Figure Series/Classification", "Non-verbal"),
        ],
    },
    "intermediate": {
        "base_dir": os.path.join(SCRIPT_DIR, "12th_Level", "Reasoning"),
        "book_intro_hi": (
            "प्रिय पाठक,\n"
            "यह पुस्तक आपके संघर्षों को समझती है – क्योंकि मैं भी वहाँ था जहाँ आप आज हैं।\n"
            "यह यात्रा केवल सीखने की नहीं, बल्कि उस सफल स्वरूप से मिलने की है जो आप कल बनने वाले हैं।\n"
            "हर अध्याय एक नया द्वार खोलेगा – बस पहला कदम उठाइए।"
        ),
        "book_intro_en": (
            "Dear learner,\n"
            "This book understands your struggle – because I have been where you are today.\n"
            "This journey is not just about learning, but about meeting the successful version of you that you are going to become tomorrow.\n"
            "Each chapter will open a new door – just take the first step."
        ),
        "chapters": [
            # foundation chapters plus advanced versions / new topics
            ("01_Analogy", "सादृश्यता", "Analogy", "Verbal"),
            ("02_Classification", "वर्गीकरण", "Classification", "Verbal"),
            ("03_Coding_Decoding", "कोडिंग-डिकोडिंग", "Coding-Decoding", "Verbal"),
            ("04_Blood_Relations", "रक्त संबंध (कोडेड सहित)", "Blood Relations (Coded)", "Verbal"),
            ("05_Direction_Sense", "दिशा ज्ञान (कोडेड)", "Direction Sense (Coded)", "Verbal"),
            ("06_Order_Ranking", "क्रम और स्थान", "Order & Ranking", "Verbal"),
            ("07_Sitting_Arrangement", "बैठक व्यवस्था (मध्यम)", "Sitting Arrangement (Intermediate)", "Verbal"),
            ("08_Puzzles", "पहेलियाँ (मध्यम)", "Puzzles (Intermediate)", "Verbal"),
            ("09_Venn_Diagrams", "वेन आरेख", "Venn Diagrams", "Verbal"),
            ("10_Clock_Calendar", "घड़ी और कैलेंडर", "Clock & Calendar", "Verbal"),
            ("11_Series", "शृंखला", "Series", "Verbal"),
            ("12_Missing_Term", "लुप्त पद", "Missing Term", "Verbal"),
            ("13_Dictionary_Order", "शब्दकोश क्रम", "Dictionary Order", "Verbal"),
            ("14_Alphabet_Questions", "अक्षर आधारित प्रश्न", "Alphabet Questions", "Verbal"),
            ("15_Mathematical_Operations", "गणितीय संक्रियाएँ", "Mathematical Operations", "Verbal"),
            ("16_Statement_Conclusion", "कथन और निष्कर्ष", "Statement & Conclusion", "Verbal"),
            ("17_Course_of_Action", "कथन और कार्यवाही", "Statement & Course of Action", "Verbal"),
            ("18_Inequality", "असमानता", "Inequality", "Verbal"),
            ("19_Cubes_Dice", "घन-पासा", "Cubes & Dice", "Non-verbal"),
            ("20_Mirror_Water_Images", "दर्पण/जल प्रतिबिंब", "Mirror & Water Images", "Non-verbal"),
            ("21_Paper_Folding_Cutting", "कागज मोड़ना-काटना", "Paper Folding & Cutting", "Non-verbal"),
            ("22_Figure_Series", "आकृति शृंखला/वर्गीकरण", "Figure Series/Classification", "Non-verbal"),
            ("23_Syllogism", "न्याय-वाक्य (Syllogism)", "Syllogism", "Verbal"),
            ("24_Statement_Assumption", "कथन और पूर्वधारणा", "Statement & Assumption", "Verbal"),
            ("25_Statement_Argument", "कथन और तर्क", "Statement & Argument", "Verbal"),
        ],
    },
    "advanced": {
        "base_dir": os.path.join(SCRIPT_DIR, "Graduation_Level", "Reasoning"),
        "book_intro_hi": (
            "प्रिय पाठक,\n"
            "यह पुस्तक आपके संघर्षों को समझती है – क्योंकि मैं भी वहाँ था जहाँ आप आज हैं।\n"
            "यह यात्रा केवल सीखने की नहीं, बल्कि उस सफल स्वरूप से मिलने की है जो आप कल बनने वाले हैं।\n"
            "हर अध्याय एक नया द्वार खोलेगा – बस पहला कदम उठाइए।"
        ),
        "book_intro_en": (
            "Dear learner,\n"
            "This book understands your struggle – because I have been where you are today.\n"
            "This journey is not just about learning, but about meeting the successful version of you that you are going to become tomorrow.\n"
            "Each chapter will open a new door – just take the first step."
        ),
        "chapters": [
            # intermediate chapters + extra advanced topics
            ("01_Analogy", "सादृश्यता", "Analogy", "Verbal"),
            ("02_Classification", "वर्गीकरण", "Classification", "Verbal"),
            ("03_Coding_Decoding", "कोडिंग-डिकोडिंग (उन्नत)", "Coding-Decoding (Advanced)", "Verbal"),
            ("04_Blood_Relations", "रक्त संबंध (कोडेड/जटिल)", "Blood Relations (Coded/Complex)", "Verbal"),
            ("05_Direction_Sense", "दिशा ज्ञान (कोडेड/दूरी)", "Direction Sense (Coded/Distance)", "Verbal"),
            ("06_Order_Ranking", "क्रम और स्थान", "Order & Ranking", "Verbal"),
            ("07_Sitting_Arrangement", "बैठक व्यवस्था (जटिल)", "Sitting Arrangement (Complex)", "Verbal"),
            ("08_Puzzles", "पहेलियाँ (जटिल)", "Puzzles (Complex)", "Verbal"),
            ("09_Venn_Diagrams", "वेन आरेख", "Venn Diagrams", "Verbal"),
            ("10_Clock_Calendar", "घड़ी और कैलेंडर", "Clock & Calendar", "Verbal"),
            ("11_Series", "शृंखला", "Series", "Verbal"),
            ("12_Missing_Term", "लुप्त पद", "Missing Term", "Verbal"),
            ("13_Dictionary_Order", "शब्दकोश क्रम", "Dictionary Order", "Verbal"),
            ("14_Alphabet_Questions", "अक्षर आधारित प्रश्न", "Alphabet Questions", "Verbal"),
            ("15_Mathematical_Operations", "गणितीय संक्रियाएँ", "Mathematical Operations", "Verbal"),
            ("16_Statement_Conclusion", "कथन और निष्कर्ष", "Statement & Conclusion", "Verbal"),
            ("17_Course_of_Action", "कथन और कार्यवाही", "Statement & Course of Action", "Verbal"),
            ("18_Inequality", "असमानता", "Inequality", "Verbal"),
            ("19_Cubes_Dice", "घन-पासा", "Cubes & Dice", "Non-verbal"),
            ("20_Mirror_Water_Images", "दर्पण/जल प्रतिबिंब", "Mirror & Water Images", "Non-verbal"),
            ("21_Paper_Folding_Cutting", "कागज मोड़ना-काटना", "Paper Folding & Cutting", "Non-verbal"),
            ("22_Figure_Series", "आकृति शृंखला/वर्गीकरण", "Figure Series/Classification", "Non-verbal"),
            ("23_Syllogism", "न्याय-वाक्य (Syllogism) (उन्नत)", "Syllogism (Advanced)", "Verbal"),
            ("24_Statement_Assumption", "कथन और पूर्वधारणा", "Statement & Assumption", "Verbal"),
            ("25_Statement_Argument", "कथन और तर्क", "Statement & Argument", "Verbal"),
            ("26_Data_Sufficiency", "आँकड़ों की पर्याप्तता", "Data Sufficiency", "Verbal"),
            ("27_Decision_Making", "निर्णय क्षमता", "Decision Making", "Verbal"),
            ("28_Critical_Reasoning", "आलोचनात्मक तर्क", "Critical Reasoning", "Verbal"),
            ("29_Logical_Consistency", "तार्किक सुसंगति", "Logical Consistency", "Verbal"),
            ("30_Advanced_Puzzles", "उन्नत पहेलियाँ (बहु-शर्तीय)", "Advanced Puzzles (Multi-condition)", "Verbal"),
        ],
    },
}

# ----------------------------------------------------------
# 2. प्रैक्टिस सेट का कठिनाई वितरण
# ----------------------------------------------------------
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

# ----------------------------------------------------------
# 3. प्रॉम्प्ट टेम्पलेट्स (संशोधित)
# ----------------------------------------------------------
def create_prompts_content(topic_hi, topic_en, level, rtype):
    trap_instruction = (
        "⚠️ परीक्षक का जाल (Examiner's Trap):\n"
        "- इस अध्याय के अंत में एक अलग बॉक्स बनाओ जिसका शीर्षक हो \"⚠️ सावधान: परीक्षक का जाल\"।\n"
        "- इसमें इस अध्याय के 2-3 सबसे आम जाल बताओ, जैसे:\n"
        f"  * \"{topic_hi} में विकल्पों में एक से अधिक संभावित संबंध दिखाना\"\n"
        "  * \"कठिन शब्दों का प्रयोग करके छात्र को भ्रमित करना\"\n"
        "  * \"दोहरे संबंध वाले प्रश्न\"\n"
    ) if rtype == "Verbal" else (
        "⚠️ परीक्षक का जाल (Examiner's Trap):\n"
        "- इस अध्याय के अंत में एक अलग बॉक्स बनाओ जिसका शीर्षक हो \"⚠️ सावधान: परीक्षक का जाल\"।\n"
        "- इसमें इस अध्याय के 2-3 सबसे आम जाल बताओ, जैसे:\n"
        "  * \"स्क्रीन पर अस्पष्ट आकृतियाँ\"\n"
        "  * \"एक जैसी दिखने वाली आकृतियों में अंतर छिपाना\"\n"
        "  * \"घुमाव/प्रतिबिंब में थोड़ा बदलाव\"\n"
    )

    prompt_hi = (
        f"# Chapter: {topic_hi}, Level: {level}, Type: {rtype} Reasoning\n\n"
        f"@content_agent lang=hi level={level} role='अनुभवी तर्कशक्ति शिक्षक और संज्ञानात्मक मनोवैज्ञानिक' "
        f"'{topic_hi} ({topic_en})' पर एक ऐसा अध्याय लिखो जो पाठक को शुरू करने के बाद छोड़ने न दे।\n"
        "चरण-दर-चरण (Chain-of-Thought) लिखो:\n"
        "1. पहले अध्याय की रूपरेखा और सीखने के उद्देश्य लिखो।\n"
        "2. एक शक्तिशाली हुक (कहानी/चौंकाने वाला तथ्य) से शुरुआत करो।\n"
        f"3. '{topic_hi}' से जुड़ी आम समस्या को पहचानो और भावनात्मक जुड़ाव बनाओ।\n"
        "4. मुख्य सामग्री को छोटे-छोटे टुकड़ों में बाँटो (खंडन सिद्धांत)।\n"
        "5. हर 2-3 पैराग्राफ बाद एक Active Recall Prompt (🧠) रखो।\n"
        "6. कम से कम एक मजेदार स्मृति-सहायक ट्रिक (Mnemonic) दो।\n"
        "7. अंत में एक सारांश तालिका और 'इसे 2 दिन बाद दोहराएँ' का निर्देश दो।\n\n"
        f"{trap_instruction}\n"
        "भाषा अत्यंत सरल, संवादात्मक और प्रेरक रखो।"
    )

    # Fix: use double quotes to avoid escaping single quotes
    trap_instruction_en = trap_instruction.replace('⚠️ परीक्षक का जाल', "⚠️ Examiner's Trap") \
                                         .replace('सावधान: परीक्षक का जाल', "Caution: Examiner's Trap")
    prompt_en = (
        f"# Chapter: {topic_en}, Level: {level}, Type: {rtype} Reasoning\n\n"
        f"@content_agent lang=en level={level} role='experienced reasoning teacher and cognitive psychologist' "
        f"'Write a chapter on {topic_en} that becomes unputdownable. "
        "Follow Chain-of-Thought:\n"
        "1. Outline and learning goals.\n"
        "2. Start with a powerful hook.\n"
        f"3. Acknowledge common struggle with '{topic_en}'.\n"
        "4. Break content into small chunks.\n"
        "5. Insert Active Recall Prompt (🧠) every 2-3 paragraphs.\n"
        "6. Include at least one mnemonic trick.\n"
        "7. End with summary table and 'Review this after 2 days'.\n\n"
        f"{trap_instruction_en}\n"
        "Keep language extremely simple, conversational, and motivational."
    )
    return prompt_hi, prompt_en

def create_prompts_rules(topic_hi, topic_en, level, rtype):
    prompt_hi = (
        f"# Chapter: {topic_hi}, Level: {level}, Type: {rtype} Reasoning\n\n"
        f"@content_agent lang=hi level={level} "
        f"'{topic_hi}' के सभी महत्वपूर्ण नियमों, दृष्टिकोणों, समय प्रबंधन युक्तियों, और तार्किक सूत्रों (यदि लागू हों) की एक साफ़ तालिका बनाओ।\n"
        "निर्देश:\n"
        "- तालिका के तीन भाग हों:\n"
        "  1. \"मुख्य नियम/दृष्टिकोण\" – नियम का नाम | विवरण | उदाहरण\n"
        "  2. \"समय प्रबंधन\" – 15-सेकंड और 45-सेकंड का नियम (जैसे \"यदि प्रश्न का पैटर्न 15 सेकंड में समझ न आए तो छोड़ दें\")।\n"
        "  3. \"गणितीय/तार्किक सूत्र\" – यदि इस अध्याय में कोई सूत्र प्रयोग होता है तो वह दें; अन्यथा \"इस अध्याय में कोई सूत्र नहीं\" लिखें।\n"
        "- कोई व्याख्या नहीं, केवल सारणीबद्ध जानकारी।\n"
        "- भाषा सरल और सटीक।"
    )
    prompt_en = (
        f"# Chapter: {topic_en}, Level: {level}, Type: {rtype} Reasoning\n\n"
        f"@content_agent lang=en level={level} "
        f"'List all important rules, approaches, time management tips, and logical formulas (if any) for {topic_en} in a clean table.\n"
        "Instructions:\n"
        "- Table has three parts:\n"
        "  1. \"Key Rules/Approaches\" – Rule Name | Description | Example\n"
        "  2. \"Time Management\" – 15-second and 45-second rule (e.g., \"If pattern not understood in 15 sec, skip\").\n"
        "  3. \"Logical/Mathematical Formulas\" – if applicable; otherwise \"No formulas for this chapter\".\n"
        "- No explanation, just tabular data.\n"
        "- Keep language simple and precise."
    )
    return prompt_hi, prompt_en

def create_prompts_feynman(topic_hi, topic_en, level, rtype):
    prompt_hi = (
        f"# Chapter: {topic_hi}, Level: {level}, Type: {rtype} Reasoning\n\n"
        f"@content_agent lang=hi level={level} role='रिचर्ड फेनमैन जैसा शिक्षक' "
        f"'{topic_hi}' की सबसे कठिन अवधारणा को इतनी सरल भाषा में समझाओ कि 12 साल का बच्चा भी समझ जाए। "
        "एक मजेदार, वास्तविक जीवन की कहानी बुनो। एक ऐसी ट्रिक बताओ जो कभी न भूले। "
        "अंत में एक \"ब्लर्टिंग शीट\" (Blurting Sheet) का निर्देश दो: \"अब बिना ऊपर देखे, एक खाली पन्ने पर इस अध्याय की सारी मुख्य बातें लिखने की कोशिश करो।\" "
        "अंत में एक प्रश्न पूछो।"
    )
    prompt_en = (
        f"# Chapter: {topic_en}, Level: {level}, Type: {rtype} Reasoning\n\n"
        f"@content_agent lang=en level={level} role='a teacher like Richard Feynman' "
        f"'Explain the hardest concept of {topic_en} so a 12-year-old can understand. "
        "Weave a fun real-life story. Give an unforgettable trick. "
        "End with a 'Blurting Sheet' instruction: \"Now try to write down all key points of this chapter on a blank sheet without looking up.\" "
        "End with a question."
    )
    return prompt_hi, prompt_en

def create_prompts_mindmap(topic_en, level, rtype):
    return (
        f"# Chapter: {topic_en}, Level: {level}, Type: {rtype} Reasoning\n\n"
        f"@content_agent 'Create a detailed mind map (Mermaid code) for the chapter \"{topic_en}\". "
        "Show main concepts, types, strategies, time management, and common traps clearly.'"
    )

def create_prompts_flashcards(topic_hi, topic_en, level, rtype):
    prompt_hi = (
        f"# Chapter: {topic_hi}, Level: {level}, Type: {rtype} Reasoning\n\n"
        f"@content_agent lang=hi level={level} "
        f"'{topic_hi}' के लिए 15-20 फ्लैशकार्ड बनाओ। "
        "हर कार्ड में सामने एक प्रश्न (जिज्ञासा पैदा करे) और पीछे संक्षिप्त उत्तर। "
        "कम से कम 2 कार्ड में कोई म्नेमोनिक ट्रिक पूछो। "
        "1-2 कार्ड में परीक्षक के जाल से संबंधित प्रश्न पूछो।"
    )
    prompt_en = (
        f"# Chapter: {topic_en}, Level: {level}, Type: {rtype} Reasoning\n\n"
        f"@content_agent lang=en level={level} "
        f"'Create 15-20 flashcards for {topic_en}. "
        "Each card: front a curiosity-invoking question, back concise answer. "
        "At least 2 cards ask about a mnemonic trick. "
        "1-2 cards ask about an examiner's trap related to this topic."
    )
    return prompt_hi, prompt_en

def create_prompts_pyq(topic_hi, topic_en, level, rtype):
    prompt_hi = (
        f"# Chapter: {topic_hi}, Level: {level}, Type: {rtype} Reasoning\n\n"
        f"@pyq_agent lang=hi level={level} "
        f"'{topic_hi}' के पिछले 10 वर्षों के PYQ का विश्लेषण करो। "
        "दो: वर्ष-वार आवृत्ति, उप-विषय भार, परीक्षा-वार वितरण, शीर्ष 10 हाई-यील्ड प्रश्न (समाधान सहित)। "
        "प्रत्येक प्रश्न के लिए बताओ कि वह किस 'हुक' या 'ट्रैप' का उपयोग करता है। "
        "कम से कम 2 प्रश्नों के लिए '15-सेकंड/45-सेकंड नियम' के अनुसार बताओ कि वह छोड़ने योग्य था या नहीं।"
    )
    prompt_en = (
        f"# Chapter: {topic_en}, Level: {level}, Type: {rtype} Reasoning\n\n"
        f"@pyq_agent lang=en level={level} "
        f"'Analyze 10-year PYQs for {topic_en}. "
        "Provide: yearly frequency, sub-topic weightage, exam-wise distribution, top 10 high-yield questions with solutions. "
        "For each question, explain the psychological hook or trap used. "
        "For at least 2 questions, indicate whether they should be skipped according to the 15-sec/45-sec rule."
    )
    return prompt_hi, prompt_en

def create_prompts_short_tricks(topic_hi, topic_en, level, rtype):
    prompt_hi = (
        f"# Chapter: {topic_hi}, Level: {level}, Type: {rtype} Reasoning\n\n"
        f"@content_agent lang=hi level={level} role='स्मृति-सहायक तकनीक विशेषज्ञ' "
        f"'{topic_hi}' के सभी मुख्य नियमों/विधियों के लिए 10-15 मज़ेदार और अजीबोगरीब म्नेमोनिक ट्रिक्स तैयार करो। "
        "हर ट्रिक एक अलग बॉक्स में। "
        "अंत में 2-3 'Skip Strategy' टिप्स ज़रूर दो — बताओ कि कब प्रश्न छोड़ देना चाहिए (जैसे 'यदि 15 सेकंड में पैटर्न न समझ आए तो छोड़ें')।"
    )
    prompt_en = (
        f"# Chapter: {topic_en}, Level: {level}, Type: {rtype} Reasoning\n\n"
        f"@content_agent lang=en level={level} role='mnemonic specialist' "
        f"'Create 10-15 fun/outrageous mnemonics for {topic_en} rules/methods. Each in a separate box. "
        "At the end, give 2-3 'Skip Strategy' tips — when to skip a question (e.g., 'If pattern not understood in 15 sec, skip')."
    )
    return prompt_hi, prompt_en

# ----------------------------------------------------------
# 4. मुख्य फ़ोल्डर निर्माण फ़ंक्शन
# ----------------------------------------------------------
def create_reasoning_book(level_key):
    config = LEVELS[level_key]
    base_dir = config["base_dir"]
    level = level_key
    chapters = config["chapters"]

    os.makedirs(base_dir, exist_ok=True)

    # Book introductions
    with open(os.path.join(base_dir, "00_Book_Introduction_hi.txt"), 'w', encoding='utf-8') as f:
        f.write(config["book_intro_hi"])
    with open(os.path.join(base_dir, "00_Book_Introduction_en.txt"), 'w', encoding='utf-8') as f:
        f.write(config["book_intro_en"])

    for folder_suffix, topic_hi, topic_en, rtype in chapters:
        chapter_dir = os.path.join(base_dir, f"Chapter_{folder_suffix}")
        prompts_dir = os.path.join(chapter_dir, "Prompts")
        os.makedirs(prompts_dir, exist_ok=True)

        # Chapter Intro Prompt
        level_labels = {"foundation": "Foundation (10वीं)", "intermediate": "Intermediate (12वीं)", "advanced": "Advanced (Graduation)"}
        intro_prompt = (
            "🚨 **सख्त निर्देश (STRICT RULE):**\n"
            "- आप जो भी सेक्शन जनरेट करें, केवल वही सामग्री दें जो किताब के लिए आवश्यक है।\n"
            "- कोई भी अतिरिक्त शब्द, संदर्भ, नमस्कार, परिचय, समापन टिप्पणी, या \"यह रहा आपका उत्तर\" जैसा मेटा-टेक्स्ट न लिखें।\n"
            "- आउटपुट सीधे किताब में चिपकाने लायक होना चाहिए — बिना एक भी अनावश्यक शब्द के।\n"
            "- इस नियम का पालन हर प्रतिक्रिया में सख्ती से करें।\n\n"
            "--------------------------------------------\n\n"
            f"👉 आज हम \"स्टूडेंट स्टेशन\" नाम की एक हिंदी-अंग्रेजी द्विभाषी पुस्तक शृंखला का {level_labels[level]} स्तर का अध्याय तैयार कर रहे हैं।\n"
            "यह तर्कशक्ति (Reasoning) की पुस्तक है, जो SSC, Banking, Railway, UPSC जैसी प्रतियोगी परीक्षाओं के लिए है।\n"
            f"इस सत्र में अध्याय: **\"{topic_hi} / {topic_en}\"** ({rtype} Reasoning) ।\n\n"
            "अध्याय 8 खंडों में बनेगा:\n"
            "1. 📖 Content (मुख्य सामग्री + परीक्षक का जाल बॉक्स)\n"
            "2. 📋 Important Rules & Approaches (नियम, समय नियम, सूत्र)\n"
            "3. 🧒 Feynman (फेनमैन तकनीक + ब्लर्टिंग शीट)\n"
            "4. 🗺️ Mind Map\n"
            "5. 🃏 Flashcards (15-20, परीक्षक के जाल वाले प्रश्न सहित)\n"
            "6. 📊 PYQ विश्लेषण (समय नियम की समीक्षा के साथ)\n"
            "7. 🪄 Short Tricks + Skip Strategy\n"
            "8. 📝 Practice (150 MCQs, 6 सेट, परीक्षक के जाल वाले प्रश्न सहित)\n\n"
            "➡️ मैं अब बारी-बारी से सेक्शन माँगूँगा। कृपया हर बार केवल वही खंड generate करें और पूरी quality बनाए रखें。"
        )
        with open(os.path.join(prompts_dir, "Chapter_Intro_Prompt.txt"), 'w', encoding='utf-8') as f:
            f.write(intro_prompt)

        # Content
        content_hi, content_en = create_prompts_content(topic_hi, topic_en, level, rtype)
        with open(os.path.join(prompts_dir, "Content_hi.txt"), 'w', encoding='utf-8') as f:
            f.write(content_hi)
        with open(os.path.join(prompts_dir, "Content_en.txt"), 'w', encoding='utf-8') as f:
            f.write(content_en)

        # Important Rules
        rules_hi, rules_en = create_prompts_rules(topic_hi, topic_en, level, rtype)
        with open(os.path.join(prompts_dir, "Important_Rules_hi.txt"), 'w', encoding='utf-8') as f:
            f.write(rules_hi)
        with open(os.path.join(prompts_dir, "Important_Rules_en.txt"), 'w', encoding='utf-8') as f:
            f.write(rules_en)

        # Feynman
        feynman_hi, feynman_en = create_prompts_feynman(topic_hi, topic_en, level, rtype)
        with open(os.path.join(prompts_dir, "Feynman_hi.txt"), 'w', encoding='utf-8') as f:
            f.write(feynman_hi)
        with open(os.path.join(prompts_dir, "Feynman_en.txt"), 'w', encoding='utf-8') as f:
            f.write(feynman_en)

        # Mind Map
        mindmap = create_prompts_mindmap(topic_en, level, rtype)
        with open(os.path.join(prompts_dir, "Mind_Map.txt"), 'w', encoding='utf-8') as f:
            f.write(mindmap)

        # Flashcards
        flash_hi, flash_en = create_prompts_flashcards(topic_hi, topic_en, level, rtype)
        with open(os.path.join(prompts_dir, "Flashcards_hi.txt"), 'w', encoding='utf-8') as f:
            f.write(flash_hi)
        with open(os.path.join(prompts_dir, "Flashcards_en.txt"), 'w', encoding='utf-8') as f:
            f.write(flash_en)

        # PYQ
        pyq_hi, pyq_en = create_prompts_pyq(topic_hi, topic_en, level, rtype)
        with open(os.path.join(prompts_dir, "PYQ_hi.txt"), 'w', encoding='utf-8') as f:
            f.write(pyq_hi)
        with open(os.path.join(prompts_dir, "PYQ_en.txt"), 'w', encoding='utf-8') as f:
            f.write(pyq_en)

        # Short Tricks
        tricks_hi, tricks_en = create_prompts_short_tricks(topic_hi, topic_en, level, rtype)
        with open(os.path.join(prompts_dir, "Short_Tricks_hi.txt"), 'w', encoding='utf-8') as f:
            f.write(tricks_hi)
        with open(os.path.join(prompts_dir, "Short_Tricks_en.txt"), 'w', encoding='utf-8') as f:
            f.write(tricks_en)

        # Practice Sets (6 sets × 25 MCQs)
        for set_num in range(1, 7):
            start_q = (set_num - 1) * 25 + 1
            end_q = set_num * 25
            diff_hi = get_practice_difficulty_instruction(set_num, 'hi')
            diff_en = get_practice_difficulty_instruction(set_num, 'en')

            practice_hi = (
                f"# Chapter: {topic_hi}, Level: {level}, Set: {set_num}/6, Type: {rtype} Reasoning\n\n"
                f"@content_agent +mcq_generator_bilingual lang=hi level={level} "
                f"'{topic_hi}' के लिए 25 बहुविकल्पीय प्रश्न (MCQs) तैयार करो। "
                f"यह सेट {set_num} है (कुल 6 सेट, 150 प्रश्न)। प्रश्न संख्या {start_q} से {end_q} तक। "
                f"{diff_hi} "
                "हर प्रश्न में 4 विकल्प, सही उत्तर, चरण-दर-चरण हल, और स्रोत (परीक्षा का नाम/वर्ष) ज़रूर दो। "
                "कम से कम 2 प्रश्नों में 'परीक्षक का जाल' (जैसे दोहरे संबंध, भ्रामक विकल्प) शामिल करो।"
            )
            practice_en = (
                f"# Chapter: {topic_en}, Level: {level}, Set: {set_num}/6, Type: {rtype} Reasoning\n\n"
                f"@content_agent +mcq_generator_bilingual lang=en level={level} "
                f"'Generate 25 MCQs for {topic_en}. "
                f"This is Set {set_num} (total 6 sets, 150 questions). Questions numbered {start_q} to {end_q}. "
                f"{diff_en} "
                "Each with 4 options, correct answer, step-by-step solution, and source (exam name/year). "
                "Include at least 2 questions with an examiner's trap (e.g., double relationship, misleading options).'"
            )
            with open(os.path.join(prompts_dir, f"Practice_hi_Set_{set_num:02d}.txt"), 'w', encoding='utf-8') as f:
                f.write(practice_hi)
            with open(os.path.join(prompts_dir, f"Practice_en_Set_{set_num:02d}.txt"), 'w', encoding='utf-8') as f:
                f.write(practice_en)

        # README
        readme = (
            f"# {topic_hi} / {topic_en}\n\n"
            f"**Level:** {level}\n"
            f"**Type:** {rtype} Reasoning\n\n"
            "## ⚠️ सबसे पहले `Prompts/Chapter_Intro_Prompt.txt` का प्रयोग करें!\n\n"
            "##  फ़ाइलें (सभी प्रॉम्प्ट `Prompts/` फोल्डर में)\n"
            "| फ़ाइल | विवरण |\n"
            "|--------|--------|\n"
            "| Prompts/Chapter_Intro_Prompt.txt | प्री-प्रॉम्प्ट (सख्त नियम) |\n"
            "| Prompts/Content_hi/en | मुख्य पाठ + परीक्षक का जाल |\n"
            "| Prompts/Important_Rules_hi/en | नियम, समय प्रबंधन, सूत्र |\n"
            "| Prompts/Feynman_hi/en | फ़ेनमैन तकनीक + ब्लर्टिंग शीट |\n"
            "| Prompts/Mind_Map.txt | माइंड मैप (Mermaid) |\n"
            "| Prompts/Flashcards_hi/en | फ़्लैशकार्ड (15-20, जाल वाले प्रश्न) |\n"
            "| Prompts/PYQ_hi/en | PYQ विश्लेषण (समय नियम सहित) |\n"
            "| Prompts/Short_Tricks_hi/en | म्नेमोनिक ट्रिक्स + Skip Strategy |\n"
            "| Prompts/Practice_hi/en_Set_01..06 | 150 MCQs (6×25, जाल वाले प्रश्न) |\n"
            "\n## उपयोग विधि\n"
            "1. `Prompts/Chapter_Intro_Prompt.txt` को AI चैट में पेस्ट करें।\n"
            "2. फिर एक-एक सेक्शन के लिए छोटे निर्देश दें (जैसे \"Content हिंदी बनाओ\")।\n"
            "3. प्राप्त शुद्ध सामग्री को संबंधित फ़ाइल में सेव करें।\n"
        )
        with open(os.path.join(chapter_dir, "README.md"), 'w', encoding='utf-8') as f:
            f.write(readme)

    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    print(f"✅ '{config['base_dir']}' सफलतापूर्वक तैयार हो गया।")

# ----------------------------------------------------------
# 5. एक्जीक्यूशन: तीनों स्तर बनाएँ
# ----------------------------------------------------------
if __name__ == "__main__":
    for lvl in ["foundation", "intermediate", "advanced"]:
        create_reasoning_book(lvl)