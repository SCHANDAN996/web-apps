# -*- coding: utf-8 -*-
import os
import sys

# Safe stdout reconfigure (Python 3.7+)
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# ----------------------------------------------------------
# 1. Configuration
# ----------------------------------------------------------
LEVELS = {
    "foundation": {
        "base_dir": os.path.join(SCRIPT_DIR, "10th_Level", "GK", "Foundation_10th_GK_WorldClass"),
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
            ("01_Ancient_History", "प्राचीन भारतीय इतिहास", "Ancient Indian History", "Static"),
            ("02_Medieval_History", "मध्यकालीन भारतीय इतिहास", "Medieval Indian History", "Static"),
            ("03_Modern_History", "आधुनिक भारतीय इतिहास", "Modern Indian History", "Static"),
            ("04_Constitution_Basic", "भारतीय संविधान (मूल)", "Indian Constitution (Basic)", "Static"),
            ("05_Polity", "भारतीय राजनीतिक व्यवस्था", "Indian Polity", "Static"),
            ("06_Physical_Geography", "भारत का भौतिक भूगोल", "Physical Geography of India", "Static"),
            ("07_States_Rivers", "राज्य एवं नदियाँ", "States & Rivers", "Static"),
            ("08_World_Geography", "विश्व भूगोल (बुनियादी)", "World Geography (Basic)", "Static"),
            ("09_Economy_Basic", "भारतीय अर्थव्यवस्था (बुनियादी)", "Indian Economy (Basic)", "Static"),
            ("10_Physics_Daily", "भौतिकी – दैनिक जीवन", "Physics in Everyday Life", "Static"),
            ("11_Chemistry", "सामान्य रसायन", "General Chemistry", "Static"),
            ("12_Biology", "जीवविज्ञान – मानव शरीर", "Biology – Human Body", "Static"),
            ("13_Awards", "पुरस्कार और सम्मान", "Awards & Honours", "Static"),
            ("14_Sports", "खेल और प्रतियोगिताएँ", "Sports & Competitions", "Static"),
            ("15_Days_Dates", "महत्वपूर्ण दिवस और तिथियाँ", "Important Days & Dates", "Static"),
            ("16_Books_Authors", "पुस्तकें और लेखक", "Books & Authors", "Static"),
            ("17_Culture_Art", "भारतीय संस्कृति और कला", "Indian Culture & Art", "Static"),
            ("18_Science_Tech", "विज्ञान और प्रौद्योगिकी (बुनियादी)", "Science & Technology (Basic)", "Static"),
            ("19_Environment", "पर्यावरण और पारिस्थितिकी (बुनियादी)", "Environment & Ecology (Basic)", "Static"),
            ("20_Current_Affairs_6M", "करंट अफेयर्स (पिछले 6 माह)", "Current Affairs (Last 6 months)", "Dynamic"),
        ],
    },
    "intermediate": {
        "base_dir": os.path.join(SCRIPT_DIR, "12th_Level", "GK", "Intermediate_12th_GK_WorldClass"),
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
            ("01_Ancient_History", "प्राचीन भारतीय इतिहास", "Ancient Indian History", "Static"),
            ("02_Medieval_History", "मध्यकालीन भारतीय इतिहास", "Medieval Indian History", "Static"),
            ("03_Modern_History", "आधुनिक भारतीय इतिहास", "Modern Indian History", "Static"),
            ("04_Constitution_Basic", "भारतीय संविधान (मूल)", "Indian Constitution (Basic)", "Static"),
            ("05_Polity", "भारतीय राजनीतिक व्यवस्था", "Indian Polity", "Static"),
            ("06_Physical_Geography", "भारत का भौतिक भूगोल", "Physical Geography of India", "Static"),
            ("07_States_Rivers", "राज्य एवं नदियाँ", "States & Rivers", "Static"),
            ("08_World_Geography", "विश्व भूगोल (बुनियादी)", "World Geography (Basic)", "Static"),
            ("09_Economy_Basic", "भारतीय अर्थव्यवस्था (बुनियादी)", "Indian Economy (Basic)", "Static"),
            ("10_Physics_Daily", "भौतिकी – दैनिक जीवन", "Physics in Everyday Life", "Static"),
            ("11_Chemistry", "सामान्य रसायन", "General Chemistry", "Static"),
            ("12_Biology", "जीवविज्ञान – मानव शरीर", "Biology – Human Body", "Static"),
            ("13_Awards", "पुरस्कार और सम्मान", "Awards & Honours", "Static"),
            ("14_Sports", "खेल और प्रतियोगिताएँ", "Sports & Competitions", "Static"),
            ("15_Days_Dates", "महत्वपूर्ण दिवस और तिथियाँ", "Important Days & Dates", "Static"),
            ("16_Books_Authors", "पुस्तकें और लेखक", "Books & Authors", "Static"),
            ("17_Culture_Art", "भारतीय संस्कृति और कला", "Indian Culture & Art", "Static"),
            ("18_Science_Tech", "विज्ञान और प्रौद्योगिकी (बुनियादी)", "Science & Technology (Basic)", "Static"),
            ("19_Environment", "पर्यावरण और पारिस्थितिकी (बुनियादी)", "Environment & Ecology (Basic)", "Static"),
            ("20_Current_Affairs_6M", "करंट अफेयर्स (पिछले 6 माह)", "Current Affairs (Last 6 months)", "Dynamic"),
            ("21_International_Orgs", "अंतर्राष्ट्रीय संगठन", "International Organizations", "Static"),
            ("22_Defence", "भारतीय रक्षा और सुरक्षा", "Indian Defence & Security", "Static"),
            ("23_Economic_Terms", "आर्थिक शब्दावली और अवधारणाएँ", "Economic Terms & Concepts", "Static"),
            ("24_Reports_Indices", "रिपोर्ट और सूचकांक", "Reports & Indices", "Dynamic/Static"),
            ("25_Govt_Schemes", "सरकारी योजनाएँ और पहल", "Government Schemes & Initiatives", "Dynamic"),
        ],
    },
    "advanced": {
        "base_dir": os.path.join(SCRIPT_DIR, "Graduation_Level", "GK", "Advanced_Graduation_GK_WorldClass"),
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
            ("01_Ancient_History", "प्राचीन भारतीय इतिहास", "Ancient Indian History", "Static"),
            ("02_Medieval_History", "मध्यकालीन भारतीय इतिहास", "Medieval Indian History", "Static"),
            ("03_Modern_History", "आधुनिक भारतीय इतिहास", "Modern Indian History", "Static"),
            ("04_Constitution_Basic", "भारतीय संविधान (मूल)", "Indian Constitution (Basic)", "Static"),
            ("05_Polity", "भारतीय राजनीतिक व्यवस्था", "Indian Polity", "Static"),
            ("06_Physical_Geography", "भारत का भौतिक भूगोल", "Physical Geography of India", "Static"),
            ("07_States_Rivers", "राज्य एवं नदियाँ", "States & Rivers", "Static"),
            ("08_World_Geography", "विश्व भूगोल (बुनियादी)", "World Geography (Basic)", "Static"),
            ("09_Economy_Basic", "भारतीय अर्थव्यवस्था (बुनियादी)", "Indian Economy (Basic)", "Static"),
            ("10_Physics_Daily", "भौतिकी – दैनिक जीवन", "Physics in Everyday Life", "Static"),
            ("11_Chemistry", "सामान्य रसायन", "General Chemistry", "Static"),
            ("12_Biology", "जीवविज्ञान – मानव शरीर", "Biology – Human Body", "Static"),
            ("13_Awards", "पुरस्कार और सम्मान", "Awards & Honours", "Static"),
            ("14_Sports", "खेल और प्रतियोगिताएँ", "Sports & Competitions", "Static"),
            ("15_Days_Dates", "महत्वपूर्ण दिवस और तिथियाँ", "Important Days & Dates", "Static"),
            ("16_Books_Authors", "पुस्तकें और लेखक", "Books & Authors", "Static"),
            ("17_Culture_Art", "भारतीय संस्कृति और कला", "Indian Culture & Art", "Static"),
            ("18_Science_Tech", "विज्ञान और प्रौद्योगिकी (बुनियादी)", "Science & Technology (Basic)", "Static"),
            ("19_Environment", "पर्यावरण और पारिस्थितिकी (बुनियादी)", "Environment & Ecology (Basic)", "Static"),
            ("20_Current_Affairs_6M", "करंट अफेयर्स (पिछले 6 माह)", "Current Affairs (Last 6 months)", "Dynamic"),
            ("21_International_Orgs", "अंतर्राष्ट्रीय संगठन", "International Organizations", "Static"),
            ("22_Defence", "भारतीय रक्षा और सुरक्षा", "Indian Defence & Security", "Static"),
            ("23_Economic_Terms", "आर्थिक शब्दावली और अवधारणाएँ", "Economic Terms & Concepts", "Static"),
            ("24_Reports_Indices", "रिपोर्ट और सूचकांक", "Reports & Indices", "Dynamic/Static"),
            ("25_Govt_Schemes", "सरकारी योजनाएँ और पहल", "Government Schemes & Initiatives", "Dynamic"),
            ("26_Advanced_Polity", "उन्नत भारतीय राजव्यवस्था", "Advanced Indian Polity", "Static"),
            ("27_Budget_Economic_Survey", "बजट और आर्थिक सर्वेक्षण", "Budget & Economic Survey", "Dynamic"),
            ("28_Advanced_Science_Tech", "उन्नत विज्ञान-प्रौद्योगिकी", "Advanced Science & Tech", "Static"),
            ("29_Environment_Conventions", "पर्यावरणीय सम्मेलन और प्रोटोकॉल", "Environment Conventions", "Static"),
            ("30_Current_Affairs_12M", "करंट अफेयर्स (पिछले 12 माह)", "Current Affairs (12 months)", "Dynamic"),
        ],
    },
}

# ----------------------------------------------------------
# 2. Practice difficulty distribution
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
# 3. Prompt templates
# ----------------------------------------------------------
def create_prompts_content(topic_hi, topic_en, level, chapter_type):
    trap_instruction = (
        "⚠️ परीक्षक का जाल (Examiner's Trap):\n"
        "- इस अध्याय के अंत में एक अलग बॉक्स बनाओ जिसका शीर्षक हो \"⚠️ सावधान: परीक्षक का जाल\"।\n"
        "- इसमें इस अध्याय के 2-3 सबसे आम जाल बताओ, और हर जाल का **प्रकार (Trap Type)** स्पष्ट करो, जैसे:\n"
        "  * \"लगभग सही कथन\" (90% सही जानकारी, एक छोटी गलती)\n"
        "  * \"विपरीत कार्य-कारण\" (Reverse Causation)\n"
        "  * \"कालानुक्रमिक भ्रम\" (Chronological Confusion)\n"
        "  * \"नकारात्मक वाक्यांश\" (प्रश्न में 'नहीं', 'छोड़कर' छिपाना)\n"
        "  * \"समान नाम/वर्ष\" (मिलते-जुलते नामों या तिथियों का भ्रम)\n"
    )

    linguistic_bridge = (
        "🔁 भाषाई कंट्रास्ट (Linguistic Bridge):\n"
        "- यदि इस अध्याय में ऐसे तथ्य हैं जो हिंदी और अंग्रेज़ी में भिन्न नामों/शब्दों से जाने जाते हैं, तो एक छोटा बॉक्स \"हिंदी में ऐसा, अंग्रेज़ी में वैसा\" बनाओ।\n"
        "- उदाहरण: 'लाल किला' (Red Fort), 'संविधान सभा' (Constituent Assembly) आदि।\n"
    )

    prompt_hi = (
        f"# Chapter: {topic_hi}, Level: {level}, Type: {chapter_type}\n\n"
        f"@content_agent lang=hi level={level} role='अनुभवी GK शिक्षक और संज्ञानात्मक मनोवैज्ञानिक' "
        f"'{topic_hi} ({topic_en})' पर एक ऐसा अध्याय लिखो जो पाठक को शुरू करने के बाद छोड़ने न दे।\n"
        "चरण-दर-चरण (Chain-of-Thought) लिखो:\n"
        "1. एक शक्तिशाली और यादगार कहानी/हुक से शुरुआत करो (कोई ऐतिहासिक घटना, रोचक तथ्य, या वर्तमान से जुड़ा उदाहरण)।\n"
        "2. सीखने के उद्देश्य स्पष्ट रूप से लिखो।\n"
        "3. मुख्य सामग्री को छोटे-छोटे खंडों (Chunking) में बाँटो, हर खंड का उप-शीर्षक हो।\n"
        "4. हर 2-3 पैराग्राफ बाद एक Active Recall Prompt (🧠) रखो।\n"
        "5. कम से कम 2-3 विषय-विशिष्ट Mnemonics (स्मृति-सहायक सूत्र) दो।\n"
        "6. अंत में एक सारांश तालिका (Summary Table) और 'इसे 2 दिन बाद दोहराएँ' का निर्देश दो।\n"
        f"{trap_instruction}\n"
        f"{linguistic_bridge}\n"
        "🔗 Static-Dynamic Link: यदि कोई स्थैतिक तथ्य हाल की किसी घटना/रिपोर्ट से जुड़ता है, तो एक छोटे बॉक्स में समझाओ।\n"
        "📅 रिवीजन प्लानर: अध्याय के अंत में तीन स्तरीय दोहराव (2 दिन, साप्ताहिक, मासिक ब्लर्टिंग) का निर्देश दो।\n"
        "यदि स्थैतिक विषय है, तो 5-10 हाई-यील्ड तथ्यों/आँकड़ों की एक तालिका बनाओ।\n"
        "भाषा अत्यंत सरल, संवादात्मक और प्रेरक रखो।"
    )

    trap_instruction_en = trap_instruction.replace('⚠️ परीक्षक का जाल', "⚠️ Examiner's Trap") \
                                         .replace('सावधान: परीक्षक का जाल', "Caution: Examiner's Trap")
    linguistic_bridge_en = linguistic_bridge.replace('🔁 भाषाई कंट्रास्ट (Linguistic Bridge):', '🔁 Linguistic Bridge:') \
                                           .replace('हिंदी में ऐसा, अंग्रेज़ी में वैसा', 'In Hindi we say this, in English we say that')
    prompt_en = (
        f"# Chapter: {topic_en}, Level: {level}, Type: {chapter_type}\n\n"
        f"@content_agent lang=en level={level} role='experienced GK educator and cognitive psychologist' "
        f"'Write a chapter on {topic_en} that becomes unputdownable. "
        "Follow Chain-of-Thought:\n"
        "1. Start with a powerful hook (historical anecdote, surprising fact, current event).\n"
        "2. Clearly state learning objectives.\n"
        "3. Break content into small chunks with sub-headings.\n"
        "4. Insert Active Recall Prompt (🧠) after every 2-3 paragraphs.\n"
        "5. Provide at least 2-3 topic-specific mnemonics.\n"
        "6. End with a summary table and 'Review after 2 days' instruction.\n"
        f"{trap_instruction_en}\n"
        f"{linguistic_bridge_en}\n"
        "🔗 Static-Dynamic Link: If any static fact has a recent connection, explain in a small box.\n"
        "📅 Revision Planner: At the end, include three-level review instructions (2-day, weekly, monthly blurting).\n"
        "If static topic, include a table of 5-10 high-yield facts/figures.\n"
        "Keep language extremely simple, conversational, and motivational."
    )
    return prompt_hi, prompt_en

def create_prompts_key_facts(topic_hi, topic_en, level, chapter_type):
    prompt_hi = (
        f"# Chapter: {topic_hi}, Level: {level}, Type: {chapter_type}\n\n"
        f"@content_agent lang=hi level={level} "
        f"'{topic_hi}' के सबसे महत्वपूर्ण तथ्यों, आँकड़ों और परीक्षा-उपयोगी सूचनाओं की एक साफ़ तालिका बनाओ।\n"
        "निर्देश:\n"
        "- तालिका के तीन भाग हों:\n"
        "  1. \"हाई-यील्ड तथ्य\" – तथ्य | विवरण | परीक्षक का जाल | जाल का प्रकार\n"
        "  2. \"समय प्रबंधन (15/45 सेकंड नियम)\" – कौन से तथ्य 'तथ्यात्मक' (15 सेकंड) हैं और कौन से 'विश्लेषणात्मक' (45 सेकंड)। 'स्कोर मैक्सिमाइज़र' विषयों (जैसे इतिहास, विज्ञान) को चिह्नित करें।\n"
        "  3. \"आँकड़े एवं सूत्र\" – यदि कोई संख्यात्मक डेटा, रैंकिंग, या सूत्र महत्वपूर्ण हो तो उसे अलग से दें।\n"
        "- कोई व्याख्या नहीं, केवल सारणीबद्ध जानकारी।\n"
        "- भाषा सरल और सटीक।"
    )
    prompt_en = (
        f"# Chapter: {topic_en}, Level: {level}, Type: {chapter_type}\n\n"
        f"@content_agent lang=en level={level} "
        f"'List all high-yield facts, figures, and exam-critical information for {topic_en} in a clean table.\n"
        "Instructions:\n"
        "- Table has three parts:\n"
        "  1. \"High-Yield Facts\" – Fact | Description | Examiner's Trap | Trap Type\n"
        "  2. \"Time Management (15/45-sec rule)\" – classify facts as fact-based (15 sec) or analytical (45 sec). Mark 'Score Maximizer' subjects.\n"
        "  3. \"Data & Formulas\" – if any numerical data, rankings, or formulas are important, list separately.\n"
        "- No explanation, just tabular data.\n"
        "- Keep language simple and precise."
    )
    return prompt_hi, prompt_en

def create_prompts_feynman(topic_hi, topic_en, level, chapter_type):
    prompt_hi = (
        f"# Chapter: {topic_hi}, Level: {level}, Type: {chapter_type}\n\n"
        f"@content_agent lang=hi level={level} role='रिचर्ड फेनमैन जैसा शिक्षक' "
        f"'{topic_hi}' की सबसे कठिन अवधारणा या सबसे भ्रमित करने वाले तथ्य को चुनो। "
        "इसे 12 वर्ष के बच्चे को समझाने जैसी अत्यंत सरल भाषा में समझाओ। "
        "दैनिक जीवन का एक ठोस और मज़ेदार उदाहरण दो। "
        "एक अविस्मरणीय ट्रिक या नियम बताओ। "
        "अंत में \"ब्लर्टिंग शीट\" (Blurting Sheet) का निर्देश दो: \"अब बिना ऊपर देखे, इस अवधारणा के बारे में जो याद है, लिख डालो।\" "
        "अंत में एक प्रश्न पूछो।"
    )
    prompt_en = (
        f"# Chapter: {topic_en}, Level: {level}, Type: {chapter_type}\n\n"
        f"@content_agent lang=en level={level} role='a teacher like Richard Feynman' "
        f"'Pick the hardest concept or most confusing fact from {topic_en}. "
        "Explain it as simply as if to a 12-year-old. "
        "Use a concrete daily-life example. "
        "Give an unforgettable trick. "
        "End with a 'Blurting Sheet' instruction: \"Now write down everything you remember about this concept without looking up.\" "
        "End with a question."
    )
    return prompt_hi, prompt_en

def create_prompts_mindmap(topic_en, level, chapter_type):
    return (
        f"# Chapter: {topic_en}, Level: {level}, Type: {chapter_type}\n\n"
        f"@content_agent 'Create a detailed mind map (Mermaid code) for the chapter \"{topic_en}\". "
        "Show main concepts, key facts, examiner's traps, and strategies clearly.'"
    )

def create_prompts_flashcards(topic_hi, topic_en, level, chapter_type):
    prompt_hi = (
        f"# Chapter: {topic_hi}, Level: {level}, Type: {chapter_type}\n\n"
        f"@content_agent lang=hi level={level} "
        f"'{topic_hi}' के लिए 15-20 फ्लैशकार्ड बनाओ। "
        "हर कार्ड में सामने एक प्रश्न (जिज्ञासा पैदा करे) और पीछे संक्षिप्त उत्तर। "
        "कम से कम 2 कार्ड में कोई म्नेमोनिक ट्रिक पूछो। "
        "1-2 कार्ड में परीक्षक के जाल से संबंधित प्रश्न पूछो।"
    )
    prompt_en = (
        f"# Chapter: {topic_en}, Level: {level}, Type: {chapter_type}\n\n"
        f"@content_agent lang=en level={level} "
        f"'Create 15-20 flashcards for {topic_en}. "
        "Each card: front a curiosity-invoking question, back concise answer. "
        "At least 2 cards ask about a mnemonic trick. "
        "1-2 cards ask about an examiner's trap related to this topic."
    )
    return prompt_hi, prompt_en

def create_prompts_pyq(topic_hi, topic_en, level, chapter_type):
    prompt_hi = (
        f"# Chapter: {topic_hi}, Level: {level}, Type: {chapter_type}\n\n"
        f"@pyq_agent lang=hi level={level} "
        f"'{topic_hi}' के पिछले 10 वर्षों के PYQ (UPSC, SSC, Banking, Railway आदि) का विश्लेषण करो। "
        "दो: वर्ष-वार आवृत्ति तालिका, उप-विषय भार, परीक्षा-वार वितरण, शीर्ष 10 हाई-यील्ड प्रश्न (समाधान सहित)। "
        "प्रत्येक प्रश्न का जाल-प्रकार (जैसे 'लगभग सही कथन', 'कालानुक्रमिक भ्रम', 'नकारात्मक वाक्यांश') स्पष्ट करो। "
        "कम से कम 2 प्रश्नों पर 15/45 सेकंड नियम लागू करो।"
    )
    prompt_en = (
        f"# Chapter: {topic_en}, Level: {level}, Type: {chapter_type}\n\n"
        f"@pyq_agent lang=en level={level} "
        f"'Analyze 10-year PYQs for {topic_en} (UPSC, SSC, Banking, Railway, etc.). "
        "Provide: yearly frequency table, sub-topic weightage, exam-wise distribution, top 10 high-yield questions with solutions. "
        "For each question, specify the trap type (e.g., Almost Correct, Chronological Confusion, Negative Phrasing). "
        "Apply the 15/45-second rule on at least 2 questions."
    )
    return prompt_hi, prompt_en

def create_prompts_memory_hooks(topic_hi, topic_en, level, chapter_type):
    prompt_hi = (
        f"# Chapter: {topic_hi}, Level: {level}, Type: {chapter_type}\n\n"
        f"@content_agent lang=hi level={level} role='स्मृति-सहायक तकनीक विशेषज्ञ' "
        f"'{topic_hi}' के सभी मुख्य तथ्यों के लिए 10-15 मज़ेदार और अजीबोगरीब Mnemonics तैयार करो। "
        "हर Mnemonic एक अलग बॉक्स में। "
        "अंत में 2-3 'Skip Strategy' टिप्स ज़रूर दो — बताओ कि परीक्षा में किस प्रकार के प्रश्न को देखते ही छोड़ देना चाहिए (जैसे 'यदि चार राजवंशों के संस्थापक पूछे गए और एक भी याद नहीं, तो तुरंत छोड़ें')।"
    )
    prompt_en = (
        f"# Chapter: {topic_en}, Level: {level}, Type: {chapter_type}\n\n"
        f"@content_agent lang=en level={level} role='mnemonic specialist' "
        f"'Create 10-15 fun/outrageous mnemonics for {topic_en} facts. Each in a separate box. "
        "At the end, give 2-3 'Skip Strategy' tips — when to skip a question (e.g., 'If asked about founders of four dynasties and you can't recall one, skip immediately')."
    )
    return prompt_hi, prompt_en

# ----------------------------------------------------------
# 4. Main function to create book structure
# ----------------------------------------------------------
def create_gk_book(level_key):
    config = LEVELS[level_key]
    base_dir = config["base_dir"]
    level = level_key
    chapters = config["chapters"]

    os.makedirs(base_dir, exist_ok=True)

    with open(os.path.join(base_dir, "00_Book_Introduction_hi.txt"), 'w', encoding='utf-8') as f:
        f.write(config["book_intro_hi"])
    with open(os.path.join(base_dir, "00_Book_Introduction_en.txt"), 'w', encoding='utf-8') as f:
        f.write(config["book_intro_en"])

    for folder_suffix, topic_hi, topic_en, chapter_type in chapters:
        chapter_dir = os.path.join(base_dir, f"Chapter_{folder_suffix}")
        prompts_dir = os.path.join(chapter_dir, "Prompts")
        os.makedirs(prompts_dir, exist_ok=True)

        level_labels = {"foundation": "Foundation (10वीं)", "intermediate": "Intermediate (12वीं)", "advanced": "Advanced (Graduation)"}
        intro_prompt = (
            "🚨 **सख्त निर्देश (STRICT RULE):**\n"
            "- आप जो भी सेक्शन जनरेट करें, केवल वही सामग्री दें जो किताब के लिए आवश्यक है।\n"
            "- कोई भी अतिरिक्त शब्द, संदर्भ, नमस्कार, परिचय, समापन टिप्पणी, या \"यह रहा आपका उत्तर\" जैसा मेटा-टेक्स्ट न लिखें।\n"
            "- आउटपुट सीधे किताब में चिपकाने लायक होना चाहिए — बिना एक भी अनावश्यक शब्द के।\n"
            "- इस नियम का पालन हर प्रतिक्रिया में सख्ती से करें।\n\n"
            "--------------------------------------------\n\n"
            f"👉 आज हम \"स्टूडेंट स्टेशन\" नाम की एक हिंदी-अंग्रेजी द्विभाषी पुस्तक शृंखला का {level_labels[level]} स्तर का अध्याय तैयार कर रहे हैं।\n"
            "यह सामान्य ज्ञान (GK) की पुस्तक है, जो UPSC, SSC, Banking, Railway, State PCS जैसी प्रतियोगी परीक्षाओं के लिए है।\n"
            f"इस सत्र में अध्याय: **\"{topic_hi} / {topic_en}\"** ({chapter_type}) ।\n\n"
            "अध्याय 8 खंडों में बनेगा:\n"
            "1. 📖 Content (मुख्य सामग्री + परीक्षक का जाल + भाषाई कंट्रास्ट + रिवीजन प्लानर)\n"
            "2. 📋 Key Facts & Figures (हाई-यील्ड तथ्य, समय प्रबंधन, आँकड़े)\n"
            "3. 🧒 Feynman (फेनमैन तकनीक + ब्लर्टिंग शीट)\n"
            "4. 🗺️ Mind Map\n"
            "5. 🃏 Flashcards (15-20, परीक्षक के जाल वाले प्रश्न सहित)\n"
            "6. 📊 PYQ विश्लेषण (जाल-प्रकार और 15/45 सेकंड नियम के साथ)\n"
            "7. 🪄 Memory Hooks & Short Tricks + Skip Strategy\n"
            "8. 📝 Practice (150 MCQs, 6 सेट, परीक्षक के जाल वाले प्रश्न सहित)\n\n"
            "➡️ मैं अब बारी-बारी से सेक्शन माँगूँगा। कृपया हर बार केवल वही खंड generate करें और पूरी quality बनाए रखें।"
        )
        with open(os.path.join(prompts_dir, "Chapter_Intro_Prompt.txt"), 'w', encoding='utf-8') as f:
            f.write(intro_prompt)

        # Content
        content_hi, content_en = create_prompts_content(topic_hi, topic_en, level, chapter_type)
        with open(os.path.join(prompts_dir, "Content_hi.txt"), 'w', encoding='utf-8') as f:
            f.write(content_hi)
        with open(os.path.join(prompts_dir, "Content_en.txt"), 'w', encoding='utf-8') as f:
            f.write(content_en)

        # Key Facts
        keyfacts_hi, keyfacts_en = create_prompts_key_facts(topic_hi, topic_en, level, chapter_type)
        with open(os.path.join(prompts_dir, "Key_Facts_hi.txt"), 'w', encoding='utf-8') as f:
            f.write(keyfacts_hi)
        with open(os.path.join(prompts_dir, "Key_Facts_en.txt"), 'w', encoding='utf-8') as f:
            f.write(keyfacts_en)

        # Feynman
        feynman_hi, feynman_en = create_prompts_feynman(topic_hi, topic_en, level, chapter_type)
        with open(os.path.join(prompts_dir, "Feynman_hi.txt"), 'w', encoding='utf-8') as f:
            f.write(feynman_hi)
        with open(os.path.join(prompts_dir, "Feynman_en.txt"), 'w', encoding='utf-8') as f:
            f.write(feynman_en)

        # Mind Map
        mindmap = create_prompts_mindmap(topic_en, level, chapter_type)
        with open(os.path.join(prompts_dir, "Mind_Map.txt"), 'w', encoding='utf-8') as f:
            f.write(mindmap)

        # Flashcards
        flash_hi, flash_en = create_prompts_flashcards(topic_hi, topic_en, level, chapter_type)
        with open(os.path.join(prompts_dir, "Flashcards_hi.txt"), 'w', encoding='utf-8') as f:
            f.write(flash_hi)
        with open(os.path.join(prompts_dir, "Flashcards_en.txt"), 'w', encoding='utf-8') as f:
            f.write(flash_en)

        # PYQ
        pyq_hi, pyq_en = create_prompts_pyq(topic_hi, topic_en, level, chapter_type)
        with open(os.path.join(prompts_dir, "PYQ_hi.txt"), 'w', encoding='utf-8') as f:
            f.write(pyq_hi)
        with open(os.path.join(prompts_dir, "PYQ_en.txt"), 'w', encoding='utf-8') as f:
            f.write(pyq_en)

        # Memory Hooks
        memhooks_hi, memhooks_en = create_prompts_memory_hooks(topic_hi, topic_en, level, chapter_type)
        with open(os.path.join(prompts_dir, "Memory_Hooks_hi.txt"), 'w', encoding='utf-8') as f:
            f.write(memhooks_hi)
        with open(os.path.join(prompts_dir, "Memory_Hooks_en.txt"), 'w', encoding='utf-8') as f:
            f.write(memhooks_en)

        # Practice Sets
        for set_num in range(1, 7):
            start_q = (set_num - 1) * 25 + 1
            end_q = set_num * 25
            diff_hi = get_practice_difficulty_instruction(set_num, 'hi')
            diff_en = get_practice_difficulty_instruction(set_num, 'en')

            practice_hi = (
                f"# Chapter: {topic_hi}, Level: {level}, Set: {set_num}/6, Type: {chapter_type}\n\n"
                f"@content_agent +mcq_generator_bilingual lang=hi level={level} "
                f"'{topic_hi}' के लिए 25 बहुविकल्पीय प्रश्न (MCQs) तैयार करो। "
                f"यह सेट {set_num} है (कुल 6 सेट, 150 प्रश्न)। प्रश्न संख्या {start_q} से {end_q} तक। "
                f"{diff_hi} "
                "हर प्रश्न में 4 विकल्प, सही उत्तर, चरण-दर-चरण हल, और स्रोत (परीक्षा का नाम/वर्ष) ज़रूर दो। "
                "कम से कम 2 प्रश्नों में 'परीक्षक का जाल' (जैसे लगभग सही कथन, कालानुक्रमिक भ्रम, समान नाम) शामिल करो।"
            )
            practice_en = (
                f"# Chapter: {topic_en}, Level: {level}, Set: {set_num}/6, Type: {chapter_type}\n\n"
                f"@content_agent +mcq_generator_bilingual lang=en level={level} "
                f"'Generate 25 MCQs for {topic_en}. "
                f"This is Set {set_num} (total 6 sets, 150 questions). Questions numbered {start_q} to {end_q}. "
                f"{diff_en} "
                "Each with 4 options, correct answer, step-by-step solution, and source (exam name/year). "
                "Include at least 2 questions with an examiner's trap (e.g., almost correct statement, chronological confusion, similar names).'"
            )
            with open(os.path.join(prompts_dir, f"Practice_hi_Set_{set_num:02d}.txt"), 'w', encoding='utf-8') as f:
                f.write(practice_hi)
            with open(os.path.join(prompts_dir, f"Practice_en_Set_{set_num:02d}.txt"), 'w', encoding='utf-8') as f:
                f.write(practice_en)

        # README
        readme = (
            f"# {topic_hi} / {topic_en}\n\n"
            f"**Level:** {level}\n"
            f"**Type:** {chapter_type}\n\n"
            "## ⚠️ सबसे पहले `Prompts/Chapter_Intro_Prompt.txt` का प्रयोग करें!\n\n"
            "##  फ़ाइलें (सभी प्रॉम्प्ट `Prompts/` फोल्डर में)\n"
            "| फ़ाइल | विवरण |\n"
            "|--------|--------|\n"
            "| Prompts/Chapter_Intro_Prompt.txt | प्री-प्रॉम्प्ट (सख्त नियम) |\n"
            "| Prompts/Content_hi/en | मुख्य पाठ + परीक्षक का जाल + भाषाई कंट्रास्ट |\n"
            "| Prompts/Key_Facts_hi/en | हाई-यील्ड तथ्य, समय प्रबंधन, आँकड़े |\n"
            "| Prompts/Feynman_hi/en | फ़ेनमैन तकनीक + ब्लर्टिंग शीट |\n"
            "| Prompts/Mind_Map.txt | माइंड मैप (Mermaid) |\n"
            "| Prompts/Flashcards_hi/en | फ़्लैशकार्ड (15-20, जाल वाले प्रश्न) |\n"
            "| Prompts/PYQ_hi/en | PYQ विश्लेषण (जाल-प्रकार, 15/45 सेकंड नियम) |\n"
            "| Prompts/Memory_Hooks_hi/en | Mnemonics + Skip Strategy |\n"
            "| Prompts/Practice_hi/en_Set_01..06 | 150 MCQs (6×25, जाल वाले प्रश्न) |\n"
            "\n## उपयोग विधि\n"
            "1. `Prompts/Chapter_Intro_Prompt.txt` को AI चैट में पेस्ट करें।\n"
            "2. फिर एक-एक सेक्शन के लिए छोटे निर्देश दें (जैसे \"Content हिंदी बनाओ\")।\n"
            "3. प्राप्त शुद्ध सामग्री को संबंधित फ़ाइल में सेव करें।\n"
        )
        with open(os.path.join(chapter_dir, "README.md"), 'w', encoding='utf-8') as f:
            f.write(readme)

    print(f"✅ '{config['base_dir']}' सफलतापूर्वक तैयार हो गया।", flush=True)

# ----------------------------------------------------------
# 5. Execution
# ----------------------------------------------------------
if __name__ == "__main__":
    print("Script started...", flush=True)
    for lvl in ["foundation", "intermediate", "advanced"]:
        print(f"Creating level: {lvl}", flush=True)
        create_gk_book(lvl)
    print("All done!", flush=True)