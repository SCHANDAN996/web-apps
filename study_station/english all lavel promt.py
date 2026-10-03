import os

# ------------------------------------------------------------------
# 1. कॉन्फ़िगरेशन: स्तर और अध्याय
# ------------------------------------------------------------------
LEVELS = {
    "foundation": {
        "base_dir": "Foundation_10th_English_WorldClass",
        "chapters": [
            ("01_Noun", "संज्ञा (Noun)", "Noun", "Grammar"),
            ("02_Pronoun", "सर्वनाम (Pronoun)", "Pronoun", "Grammar"),
            ("03_Adjective", "विशेषण (Adjective)", "Adjective", "Grammar"),
            ("04_Verb", "क्रिया (Verb)", "Verb", "Grammar"),
            ("05_Tense", "काल (Tense)", "Tense", "Grammar"),
            ("06_Adverb", "क्रियाविशेषण (Adverb)", "Adverb", "Grammar"),
            ("07_Preposition", "संबंधसूचक (Preposition)", "Preposition", "Grammar"),
            ("08_Conjunction", "संयोजक (Conjunction)", "Conjunction", "Grammar"),
            ("09_Articles", "लेख (Articles)", "Articles", "Grammar"),
            ("10_Voice", "वाच्य (Voice)", "Active-Passive Voice", "Grammar"),
            ("11_Narration", "कथन (Narration)", "Direct-Indirect Speech", "Grammar"),
            ("12_Sentence_Structure", "वाक्य संरचना", "Sentence Structure", "Grammar"),
            ("13_Synonyms", "पर्यायवाची (Synonyms)", "Synonyms", "Vocabulary"),
            ("14_Antonyms", "विलोम (Antonyms)", "Antonyms", "Vocabulary"),
            ("15_One_Word_Substitution", "एक शब्द प्रतिस्थापन", "One-word Substitution", "Vocabulary"),
            ("16_Idioms_Phrases", "मुहावरे एवं वाक्यांश", "Idioms & Phrases", "Vocabulary"),
            ("17_Spelling", "वर्तनी जाँच", "Spelling Check", "Vocabulary"),
            ("18_Error_Spotting_Basic", "त्रुटि पहचान (सरल)", "Error Spotting (Basic)", "Application"),
            ("19_Fill_in_Blanks_Basic", "रिक्त स्थान भरें (सरल)", "Fill in the Blanks (Basic)", "Application"),
            ("20_Sentence_Improvement_Basic", "वाक्य सुधार (सरल)", "Sentence Improvement (Basic)", "Application"),
        ]
    },
    "intermediate": {
        "base_dir": "Intermediate_12th_English_WorldClass",
        "chapters": [
            ("01_Noun", "संज्ञा (Noun)", "Noun", "Grammar"),
            ("02_Pronoun", "सर्वनाम (Pronoun)", "Pronoun", "Grammar"),
            ("03_Adjective", "विशेषण (Adjective)", "Adjective", "Grammar"),
            ("04_Verb", "क्रिया (Verb)", "Verb", "Grammar"),
            ("05_Tense", "काल (Tense)", "Tense", "Grammar"),
            ("06_Adverb", "क्रियाविशेषण (Adverb)", "Adverb", "Grammar"),
            ("07_Preposition", "संबंधसूचक (Preposition)", "Preposition", "Grammar"),
            ("08_Conjunction", "संयोजक (Conjunction)", "Conjunction", "Grammar"),
            ("09_Articles", "लेख (Articles)", "Articles", "Grammar"),
            ("10_Voice", "वाच्य (Voice)", "Active-Passive Voice", "Grammar"),
            ("11_Narration", "कथन (Narration)", "Direct-Indirect Speech", "Grammar"),
            ("12_Sentence_Structure", "वाक्य संरचना", "Sentence Structure", "Grammar"),
            ("13_Synonyms", "पर्यायवाची (Synonyms)", "Synonyms", "Vocabulary"),
            ("14_Antonyms", "विलोम (Antonyms)", "Antonyms", "Vocabulary"),
            ("15_One_Word_Substitution", "एक शब्द प्रतिस्थापन", "One-word Substitution", "Vocabulary"),
            ("16_Idioms_Phrases", "मुहावरे एवं वाक्यांश", "Idioms & Phrases", "Vocabulary"),
            ("17_Spelling", "वर्तनी जाँच", "Spelling Check", "Vocabulary"),
            ("18_Error_Spotting_Adv", "त्रुटि पहचान (उन्नत)", "Error Spotting (Advanced)", "Application"),
            ("19_Fill_in_Blanks_Adv", "रिक्त स्थान भरें (उन्नत)", "Fill in the Blanks (Advanced)", "Application"),
            ("20_Sentence_Improvement_Adv", "वाक्य सुधार (उन्नत)", "Sentence Improvement (Advanced)", "Application"),
            ("21_Cloze_Test", "क्लोज़ टेस्ट", "Cloze Test", "Application"),
            ("22_Para_Jumbles", "पैरा जम्बल्स", "Para Jumbles", "Application"),
            ("23_Sentence_Arrangement", "वाक्य क्रम", "Sentence Arrangement", "Application"),
            ("24_RC_Basic", "पठन बोध (आसान)", "Reading Comprehension (Basic)", "Comprehension"),
            ("25_Word_Roots", "शब्द मूल (Roots)", "Word Roots & Morphology", "Vocabulary"),
        ]
    },
    "advanced": {
        "base_dir": "Advanced_Graduation_English_WorldClass",
        "chapters": [
            ("01_Noun", "संज्ञा (Noun)", "Noun", "Grammar"),
            ("02_Pronoun", "सर्वनाम (Pronoun)", "Pronoun", "Grammar"),
            ("03_Adjective", "विशेषण (Adjective)", "Adjective", "Grammar"),
            ("04_Verb", "क्रिया (Verb)", "Verb", "Grammar"),
            ("05_Tense", "काल (Tense)", "Tense", "Grammar"),
            ("06_Adverb", "क्रियाविशेषण (Adverb)", "Adverb", "Grammar"),
            ("07_Preposition", "संबंधसूचक (Preposition)", "Preposition", "Grammar"),
            ("08_Conjunction", "संयोजक (Conjunction)", "Conjunction", "Grammar"),
            ("09_Articles", "लेख (Articles)", "Articles", "Grammar"),
            ("10_Voice", "वाच्य (Voice)", "Active-Passive Voice", "Grammar"),
            ("11_Narration", "कथन (Narration)", "Direct-Indirect Speech", "Grammar"),
            ("12_Sentence_Structure", "वाक्य संरचना", "Sentence Structure", "Grammar"),
            ("13_Synonyms", "पर्यायवाची (Synonyms)", "Synonyms", "Vocabulary"),
            ("14_Antonyms", "विलोम (Antonyms)", "Antonyms", "Vocabulary"),
            ("15_One_Word_Substitution", "एक शब्द प्रतिस्थापन", "One-word Substitution", "Vocabulary"),
            ("16_Idioms_Phrases", "मुहावरे एवं वाक्यांश", "Idioms & Phrases", "Vocabulary"),
            ("17_Spelling", "वर्तनी जाँच", "Spelling Check", "Vocabulary"),
            ("18_Error_Spotting_Adv", "त्रुटि पहचान (उन्नत)", "Error Spotting (Advanced)", "Application"),
            ("19_Fill_in_Blanks_Adv", "रिक्त स्थान भरें (उन्नत)", "Fill in the Blanks (Advanced)", "Application"),
            ("20_Sentence_Improvement_Adv", "वाक्य सुधार (उन्नत)", "Sentence Improvement (Advanced)", "Application"),
            ("21_Cloze_Test_Adv", "उन्नत क्लोज़ टेस्ट", "Advanced Cloze Test", "Application"),
            ("22_Para_Jumbles_Adv", "उन्नत पैरा जम्बल्स", "Advanced Para Jumbles", "Application"),
            ("23_Sentence_Arrangement", "वाक्य क्रम", "Sentence Arrangement", "Application"),
            ("24_RC_Adv", "उन्नत पठन बोध", "Advanced Reading Comprehension", "Comprehension"),
            ("25_Word_Roots", "शब्द मूल (Roots)", "Word Roots & Morphology", "Vocabulary"),
            ("26_Critical_Reading", "आलोचनात्मक पठन", "Critical Reading", "Comprehension"),
            ("27_Precis_Writing", "संक्षेपण (Precis Writing)", "Precis Writing", "Writing"),
            ("28_Error_Log", "त्रुटि लॉग टेम्पलेट", "Error Log Template", "Meta"),
            ("29_Placement_Test", "प्लेसमेंट टेस्ट", "Placement Test", "Meta"),
            ("30_Revision_Tracker", "रिवीजन ट्रैकर", "Revision Tracker", "Meta"),
        ]
    }
}

# ------------------------------------------------------------------
# 2. संशोधित मास्टर प्रॉम्प्ट (हिंदी और अंग्रेज़ी)
# ------------------------------------------------------------------
MASTER_PROMPT_HI = """तुम एक विश्व-स्तरीय द्विभाषी (हिंदी-अंग्रेज़ी) अंग्रेज़ी भाषा की पुस्तक के लेखक हो। अध्याय: "{topic_hi} / {topic_en}", स्तर: {level}, प्रकार: {type}।

निम्न 8 खंडों में उत्तर दो। हर खंड में केवल शुद्ध सामग्री दो — कोई अतिरिक्त शब्द, संदर्भ या मेटा-टेक्स्ट नहीं।

1. 📖 Content: 
- शक्तिशाली हुक, सीखने के उद्देश्य, छोटे-छोटे खंड, हर 2-3 पैरा पर Active Recall (🧠), 1 Mnemonic ट्रिक, सारांश तालिका, "2 दिन बाद दोहराएँ"।
- ⚠️ परीक्षक का जाल: 2-3 आम जालों का बॉक्स। व्याकरण के लिए "12 स्वर्ण नियमों" पर विशेष ध्यान।
- 🔁 भाषाई कंट्रास्ट (Linguistic Bridge): एक छोटा बॉक्स "हिंदी में ऐसा, अंग्रेज़ी में वैसा" जो हिंदी भाषी छात्रों की सामान्य गलतियाँ (जैसे "What you are doing?") दर्शाए और सही अंग्रेज़ी रूप बताए।
- शब्दावली के लिए 5-10 ग्रीक/लैटिन मूल शब्द (roots) और उनसे बने शब्दों की तालिका। इन्हीं मूल शब्दों का उपयोग करते हुए पठन बोध (Reading Comprehension) का एक छोटा गद्यांश बनाओ ताकि छात्र शब्दों को संदर्भ में देख सके।
- पठन बोध के लिए AI, जलवायु, अर्थव्यवस्था जैसे आधुनिक विषय, टोन मैपिंग और अनुमान रणनीति (Detective Approach)।

2. 📋 Important Grammar Rules & Tips:
- तीन भागों में तालिका: 
  (क) 12 हाई-यील्ड नियम — नियम | उदाहरण | परीक्षक का जाल।
  (ख) समय प्रबंधन: 15/45 सेकंड नियम का स्पष्ट वर्गीकरण — कौन से प्रश्न 'तथ्यात्मक' (Fact-based) हैं जो 15 सेकंड में हल होने चाहिए, और कौन से 'तार्किक' (Inference-based) हैं जिन्हें 45 सेकंड देने हैं।
  (ग) रूपात्मक सूत्र (Morphology) — मूल शब्द, प्रत्यय, उदाहरण।

3. 🧒 Feynman (फेनमैन तकनीक):
- सबसे कठिन अवधारणा को 12 वर्षीय बच्चे जैसी भाषा में समझाओ। दैनिक जीवन का ठोस उदाहरण, अविस्मरणीय ट्रिक। अंत में "ब्लर्टिंग शीट" निर्देश और एक प्रश्न।

4. 🗺️ Mind Map: Mermaid कोड में अवधारणाओं, नियमों, जालों और रणनीतियों का मानचित्र।

5. 🃏 Flashcards (15-20): प्रश्न-उत्तर, जिनमें 2 म्नेमोनिक और 2 परीक्षक-जाल वाले प्रश्न शामिल हों। विभिन्न उप-विषयों को इंटरलीव (मिलाएँ) करें।

6. 📊 PYQ Analysis: पिछले 10 वर्षों का विश्लेषण। वर्षवार आवृत्ति, भार, परीक्षा-वार वितरण, शीर्ष 10 हाई-यील्ड प्रश्न (समाधान सहित)। हर प्रश्न का जाल-प्रकार (Intervening Phrase, Collective Noun, Sound-Right, Over-thinking) बताओ। 2 प्रश्नों पर 15/45-सेकंड नियम लागू करो।

7. 🪄 Short Tricks + Skip Strategy:
- 10-15 म्नेमोनिक ट्रिक्स (बॉक्स में)। 2-3 Skip Strategy टिप्स (कब प्रश्न छोड़ें)।

8. 📝 Practice (150 MCQs, 6 सेट × 25):
- वितरण: 50 Easy (सीधी याद), 50 Medium (संदर्भ-आधारित), 50 Hard (जटिल त्रुटि, टोन/अनुमान)।
- हर सेट में निर्दिष्ट कठिनाई। प्रश्न संख्या 1-25, 26-50,... 126-150। हर प्रश्न में 4 विकल्प, सही उत्तर, चरण-दर-चरण हल, स्रोत। 2 प्रश्नों में परीक्षक-जाल शामिल करो।"""

MASTER_PROMPT_EN = """You are the author of a world-class bilingual (Hindi-English) English language book. Chapter: "{topic_hi} / {topic_en}", Level: {level}, Type: {type}.

Provide the following 8 sections. Only pure content, no meta-text, greetings, or filler.

1. 📖 Content:
- Powerful hook, learning objectives, chunked paragraphs, Active Recall (🧠) after every 2-3 paras, 1 Mnemonic, summary table, "Review after 2 days".
- ⚠️ Examiner's Trap: box with 2-3 common traps. For grammar, highlight "12 Golden Rules".
- 🔁 Linguistic Bridge: a small box "In Hindi we say this, but in English we say that" showing common Hindi-speaker errors (e.g., "What you are doing?") and the correct English form.
- For vocabulary, include 5-10 Greek/Latin roots with derived words table. Use these same roots in a short Reading Comprehension passage so learners see the words in context.
- For comprehension, use modern topics (AI, climate, economy), tone mapping, and Detective Approach for inference.

2. 📋 Important Grammar Rules & Tips:
- Three-part table: 
  (a) 12 High-Yield Rules — Rule | Example | Examiner's Trap.
  (b) Time Management: clear classification of 15/45-sec rule — which questions are Fact-based (15 sec) and which are Inference-based (45 sec).
  (c) Morphology: root, affix, example.

3. 🧒 Feynman Technique:
- Explain the hardest concept as if to a 12-year-old. Use a concrete daily-life example, unforgettable trick. End with "Blurting Sheet" instruction and a question.

4. 🗺️ Mind Map: Mermaid code showing concepts, rules, traps, and strategies.

5. 🃏 Flashcards (15-20): Q&A, include 2 mnemonic and 2 examiner-trap questions. Interleave different sub-topics.

6. 📊 PYQ Analysis: Last 10 years analysis. Yearly frequency, weightage, exam distribution, top 10 high-yield Qs with solutions. Classify each Q's trap type (Intervening Phrase, Collective Noun, Sound-Right, Over-thinking). Apply 15/45-sec rule on 2 Qs.

7. 🪄 Short Tricks + Skip Strategy:
- 10-15 mnemonics (in boxes). 2-3 Skip Strategy tips.

8. 📝 Practice (150 MCQs, 6 sets × 25):
- Distribution: 50 Easy (recall), 50 Medium (application), 50 Hard (complex error, tone/inference).
- Specified difficulty per set. Question numbers 1-25, 26-50,... 126-150. Each Q: 4 options, correct answer, step-by-step solution, source. Include 2 examiner-trap Qs per set."""

# ------------------------------------------------------------------
# 3. प्रैक्टिस सेट कठिनाई वितरण (50-50-50)
# ------------------------------------------------------------------
def get_practice_difficulty(set_num):
    if set_num == 1:
        return (20, 5, 0)   # 20 Easy, 5 Medium
    elif set_num == 2:
        return (15, 10, 0)  # 15 Easy, 10 Medium
    elif set_num == 3:
        return (10, 15, 0)  # 10 Easy, 15 Medium
    elif set_num == 4:
        return (0, 20, 5)   # 20 Medium, 5 Hard
    elif set_num == 5:
        return (0, 15, 10)  # 15 Medium, 10 Hard
    else:
        return (0, 10, 15)  # 10 Medium, 15 Hard

# ------------------------------------------------------------------
# 4. फ़ाइल निर्माण फ़ंक्शन
# ------------------------------------------------------------------
def create_english_book(level_key):
    config = LEVELS[level_key]
    base_dir = config["base_dir"]
    chapters = config["chapters"]

    os.makedirs(base_dir, exist_ok=True)

    for folder_suffix, topic_hi, topic_en, chapter_type in chapters:
        chapter_dir = os.path.join(base_dir, f"Chapter_{folder_suffix}")
        prompts_dir = os.path.join(chapter_dir, "Prompts")
        os.makedirs(prompts_dir, exist_ok=True)

        # Chapter Intro
        intro_prompt = (
            "🚨 **सख्त निर्देश:** कोई अतिरिक्त शब्द, संदर्भ, नमस्कार, या \"यह रहा आपका उत्तर\" जैसा मेटा-टेक्स्ट न लिखें। केवल शुद्ध सामग्री दें जो सीधे किताब में चिपकाई जा सके।\n\n"
            f"👉 स्टूडेंट स्टेशन अंग्रेज़ी पुस्तक, स्तर: {level_key}, अध्याय: \"{topic_hi} / {topic_en}\", प्रकार: {chapter_type}\n"
            "अध्याय 8 खंडों में बनेगा: Content, Important Rules, Feynman, Mind Map, Flashcards, PYQ, Short Tricks, Practice (150 MCQs)।\n"
            "➡️ अब मैं बारी-बारी से सेक्शन माँगूँगा।"
        )
        with open(os.path.join(prompts_dir, "Chapter_Intro_Prompt.txt"), 'w', encoding='utf-8') as f:
            f.write(intro_prompt)

        # मास्टर प्रॉम्प्ट
        master_hi = MASTER_PROMPT_HI.format(topic_hi=topic_hi, topic_en=topic_en, level=level_key, type=chapter_type)
        master_en = MASTER_PROMPT_EN.format(topic_hi=topic_hi, topic_en=topic_en, level=level_key, type=chapter_type)
        with open(os.path.join(prompts_dir, "Master_Prompt_hi.txt"), 'w', encoding='utf-8') as f:
            f.write(master_hi)
        with open(os.path.join(prompts_dir, "Master_Prompt_en.txt"), 'w', encoding='utf-8') as f:
            f.write(master_en)

        # सेक्शन फ़ाइलें
        sections = ["Content", "Important_Rules", "Feynman", "Mind_Map", "Flashcards", "PYQ", "Short_Tricks"]
        for sec in sections:
            with open(os.path.join(prompts_dir, f"{sec}_hi.txt"), 'w', encoding='utf-8') as f:
                f.write(f"# {sec} (हिंदी) for {topic_hi}\nकृपया मास्टर प्रॉम्प्ट के अनुसार केवल {sec} खंड तैयार करें।")
            with open(os.path.join(prompts_dir, f"{sec}_en.txt"), 'w', encoding='utf-8') as f:
                f.write(f"# {sec} (English) for {topic_en}\nPlease generate only the {sec} section as per the master prompt.")

        # प्रैक्टिस सेट
        for set_num in range(1, 7):
            easy, med, hard = get_practice_difficulty(set_num)
            start_q = (set_num - 1) * 25 + 1
            end_q = set_num * 25

            practice_hi = (
                f"# {topic_hi}, Set {set_num}/6\n"
                f"25 MCQs (प्रश्न {start_q}-{end_q})। इस सेट में {easy} Easy, {med} Medium, {hard} Hard।\n"
                "प्रत्येक में 4 विकल्प, उत्तर, हल, स्रोत। 2 प्रश्नों में परीक्षक-जाल शामिल करें।"
            )
            practice_en = (
                f"# {topic_en}, Set {set_num}/6\n"
                f"25 MCQs (Questions {start_q}-{end_q}). This set: {easy} Easy, {med} Medium, {hard} Hard.\n"
                "Each with 4 options, answer, solution, source. Include 2 examiner-trap questions."
            )
            with open(os.path.join(prompts_dir, f"Practice_hi_Set_{set_num:02d}.txt"), 'w', encoding='utf-8') as f:
                f.write(practice_hi)
            with open(os.path.join(prompts_dir, f"Practice_en_Set_{set_num:02d}.txt"), 'w', encoding='utf-8') as f:
                f.write(practice_en)

        # README
        readme = (
            f"# {topic_hi} / {topic_en}\nLevel: {level_key}\nType: {chapter_type}\n\n"
            "Use `Prompts/Chapter_Intro_Prompt.txt` first, then individual section files.\n"
            "Master prompts are in `Prompts/Master_Prompt_hi.txt` and `Master_Prompt_en.txt`."
        )
        with open(os.path.join(chapter_dir, "README.md"), 'w', encoding='utf-8') as f:
            f.write(readme)

    print(f"✅ '{base_dir}' तैयार।")

# ------------------------------------------------------------------
# 5. मुख्य एक्जीक्यूशन
# ------------------------------------------------------------------
if __name__ == "__main__":
    for lvl in ["foundation", "intermediate", "advanced"]:
        create_english_book(lvl)