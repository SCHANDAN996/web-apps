# Skill: MCQ_Generator_Bilingual (Bilingual MCQs for Competitive Exams)

## Description
Generates high‑quality, cognitively layered MCQs in Hindi or English, strictly grounded in NCERT and standard exam syllabus.

## Syntax
Activate with `+mcq_generator lang=<hi|en> topic="..." num=5`

## Generation Instructions
When called, the agent must follow these steps for the specified language:

### 1. Understand the Target Language
- If `lang=hi`, the stem, all options, and explanation must be in **pure, standard Hindi** (no Hinglish unless the term is universally used, like “बैंक”, “सिविल”)।
- If `lang=en`, use **simple, clear English** suitable for Indian learners.

### 2. Stem Construction
- एक पूरा, स्पष्ट वाक्य जो प्रश्न पूछता है। (hi)
- A complete, clear sentence that asks the question. (en)
- अंत में प्रश्नवाचक चिह्न (?) लगाएँ। (hi) / End with question mark (?). (en)

### 3. Options (A/B/C/D)
- चार विकल्प दें। (hi) / Give exactly four options. (en)
- सही उत्तर केवल एक ही हो। (hi) / Only one correct answer. (en)
- भ्रामक विकल्प (distractors) सामान्य गलतियों पर आधारित हों। (hi) / Distractors based on common misconceptions. (en)
- सभी विकल्पों की लंबाई और संरचना समान हो। (hi) / All options parallel in length and grammar. (en)
- "उपरोक्त सभी" / "All of the above" से बचें जब तक विशेष निर्देश न हों। (hi) / Avoid "All of the above" unless specified. (en)

### 4. Cognitive Levels (Bloom’s Taxonomy)
सुनिश्चित करें कि प्रश्न विभिन्न स्तरों को मापें:
- **Remembering** (स्मरण)
- **Understanding** (समझ)
- **Applying** (अनुप्रयोग)
- **Analyzing** (विश्लेषण)

प्रतियोगी परीक्षाओं के लिए “Applying” और “Analyzing” स्तर के प्रश्न अधिक हों।

### 5. Explanation
- प्रत्येक प्रश्न के लिए सही उत्तर का स्पष्ट, चरण-दर-चरण स्पष्टीकरण उसी भाषा में दें। (hi/en)
- स्रोत का संदर्भ अवश्य दें: कक्षा, अध्याय, पृष्ठ (यदि उपलब्ध हो)।

### 6. Language Quality Check
- Hindi: वर्तनी, व्याकरण (लिंग, वचन, कारक), और मानक शब्दावली की जाँच करें। (hi)
- English: Spelling, grammar, subject‑verb agreement, standard terminology. (en)

### Output JSON Format
```json
{
  "lang": "hi",
  "topic": "प्रतिशत",
  "total_questions": 5,
  "questions": [
    {
      "id": 1,
      "stem": "एक परीक्षा में 75% छात्र उत्तीर्ण हुए। यदि अनुत्तीर्ण छात्रों की संख्या 150 है, तो कुल छात्र कितने थे?",
      "options": {
        "A": "400",
        "B": "500",
        "C": "600",
        "D": "700"
      },
      "correct": "C",
      "explanation": "अनुत्तीर्ण प्रतिशत = 100% - 75% = 25%\n25% = 150\nकुल छात्र = (150 / 25) * 100 = 600",
      "cognitive_level": "Applying",
      "source": "NCERT कक्षा 8 गणित, अध्याय 8"
    }
  ]
}
```
