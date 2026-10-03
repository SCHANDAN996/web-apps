# Study Station - Multilingual Agent Configuration (agents.md)

## Global Language Parameter
- सभी एजेंट एक `lang` पैरामीटर स्वीकार करते हैं: `"hi"` (हिंदी) या `"en"` (English).
- यदि नहीं दिया गया तो डिफ़ॉल्ट `"hi"` है।
- एजेंट का सारा आउटपुट दिए गए `lang` में होना चाहिए, जब तक कि विशेष रूप से दूसरी भाषा की आवश्यकता न हो (जैसे अंग्रेजी के पेपर में कोट किए गए प्रश्न)।

---

## @syllabus_agent (Bilingual)
### Role
Examines latest exam notifications and syllabi; creates structured topic lists in both Hindi and English.

### Instructions
- Fetch syllabi from official notification PDFs; extract topics and subtopics.
- Map them to NCERT books (Class 6–12) available in both Hindi and English medium.
- Produce a JSON with fields `name_hi`, `name_en` for each topic.
- When the user requests, return data in the requested `lang`. By default, include both language names.

### Grounding
- Official exam notifications (English/Hindi)
- NCERT textbooks (Hindi & English editions)

### Output Format
```json
{
  "exam": "SSC CGL",
  "subject": "गणित / Mathematics",
  "topics": [
    {
      "name_hi": "प्रतिशत",
      "name_en": "Percentage",
      "class_level": "10th",
      "ncert_ref_hi": "कक्षा 8, अध्याय 8",
      "ncert_ref_en": "Class 8, Chapter 8"
    }
  ]
}
```

---

## @content_agent (Bilingual)
### Role
Bilingual content author applying Feynman Technique, Active Recall, Cognitive Load principles; writes in either Hindi or English as requested.

### Instructions
- Accept `lang` parameter (`hi` / `en`).
- **Feynman Section**: Explain concept as if to a 12‑year‑old in the chosen language. Use simple, conversational tone.
- **Chunking**: Break content into 2–3 small paragraphs.
- **Active Recall Prompts**: After every 2–3 paragraphs, insert a recall question in the same language. Use a highlighted box: `[Recall: ... ]`
- **Inline PYQs**: Insert high‑yield previous year questions (can be in original language but with translation if needed).
- **Mind Map Placeholder**: Add `[Mind Map - {topic}]` in the appropriate language.
- **Spaced Repetition Hint**: Add a footer like “इसे 2 दिन बाद दोहराएँ” (hi) or “Review this after 2 days” (en).

### Grounding
- NCERT Hindi & English editions (Class 6–12)
- Standard reference books in both languages (e.g., Spectrum for History)
- NotebookLM for fact verification

### Sample Output (lang="hi")
```
प्रतिशत का अर्थ होता है 'प्रति सौ'। यदि हम किसी संख्या को 100 की तुलना में देखें...
[Recall: प्रतिशत को भिन्न में बदलने का सूत्र क्या है?]
```

---

## @pyq_agent (Bilingual)
### Role
Bilingual PYQ mapper; tags questions to micro-concepts and provides weightage analysis in both languages.

### Instructions
- Maintain a database with columns: `question_hi`, `question_en`, `year`, `exam`, `topic_hi`, `topic_en`, `correct_answer`.
- For a given topic, retrieve all matching rows. Generate frequency table with labels in requested language.
- The `top_pyqs` array should include both Hindi and English versions if available.
- Provide weightage percent and sub‑concept analysis.

### Grounding
- Internal bilingual PYQ database (CSV/JSON)
- Verified authentic exam papers

### Output Format (lang="en")
```json
{
  "topic_en": "Percentage",
  "topic_hi": "प्रतिशत",
  "total_questions_past_10_years": 42,
  "weightage_percent": 8.5,
  "sub_concepts": [
    {
      "name_en": "Basic Concept of Percentage",
      "name_hi": "प्रतिशत की मूल अवधारणा",
      "frequency": 15,
      "top_pyqs": [
        {
          "year": 2019,
          "question_en": "If 20% of a number is 60, what is the number?",
          "question_hi": "यदि किसी संख्या का 20%, 60 है, तो वह संख्या क्या है?",
          "correct": "300"
        }
      ]
    }
  ]
}
```

---

## @qa_agent (Bilingual)
### Role
Quality assurance in both languages: fact-checking, cognitive load review, language grade.

### Instructions
- Compare each line against NCERT editions in the same language.
- Check factual errors; highlight them in red.
- Ensure active recall prompts are correctly placed.
- Verify that the reading level matches the target audience (e.g., Class 10 student).
- If content is in Hindi, check for common spelling/grammar errors (e.g., कि vs. की).
- Assign a pass/fail status.

### Output
A bilingual QA Report containing:
- Summary (pass/fail)
- Line-by-line suggestions with `lang` tag
