"""
🤖 Book Agents — Multi-Agent AI Content Pipeline
Uses Gemini API to generate psychology-driven educational content

Agents:
1. Content Agent — Feynman + Active Recall based chapter writing
2. PYQ Mapper — Maps previous year questions to topics
3. QA Agent — Cognitive load analysis and quality check

All content is bilingual (Hindi + English)
"""
import json
import re
import google.generativeai as genai

def get_gemini_model():
    """Get configured Gemini model from system settings"""
    try:
        from models import SystemSettings
        from app import app
        with app.app_context():
            api_key_setting = SystemSettings.query.filter_by(setting_key='gemini_api_keys').first()
            if not api_key_setting:
                api_key_setting = SystemSettings.query.filter_by(setting_key='gemini_api_key').first()
            
            if not api_key_setting or not api_key_setting.setting_value:
                return None, "No API key configured"
            
            keys = [k.strip() for k in api_key_setting.setting_value.split('\n') if k.strip()]
            if not keys:
                return None, "No valid API keys found"
            
            model_setting = SystemSettings.query.filter_by(setting_key='ai_model_name').first()
            model_name = model_setting.setting_value if model_setting else 'gemini-2.0-flash'
            
            genai.configure(api_key=keys[0])
            model = genai.GenerativeModel(model_name)
            return model, None
    except Exception as e:
        return None, str(e)


def generate_full_chapter(topic, topic_hi, subject, target_exam, target_level, difficulty='intermediate'):
    """
    🧠 Master function: Generates a complete chapter with all cognitive science modules
    
    Returns: {
        'success': True/False,
        'data': {
            'content_en', 'content_hi',
            'feynman_en', 'feynman_hi',
            'mind_map', 'retrieval_prompts_en/hi',
            'spaced_cards_en/hi', 'key_formulas',
            'pyq_inline', 'pyq_weightage',
            'cognitive_load_score'
        }
    }
    """
    model, error = get_gemini_model()
    if not model:
        return {'success': False, 'error': f'Gemini not configured: {error}'}
    
    result_data = {}
    
    # === STEP 1: Generate Main Content (English) ===
    try:
        content_en = _generate_content(model, topic, subject, target_exam, target_level, difficulty, 'English')
        result_data['content_en'] = content_en
    except Exception as e:
        return {'success': False, 'error': f'Content generation (EN) failed: {str(e)}'}
    
    # === STEP 2: Generate Main Content (Hindi) ===
    try:
        content_hi = _generate_content(model, topic_hi or topic, subject, target_exam, target_level, difficulty, 'Hindi')
        result_data['content_hi'] = content_hi
    except Exception as e:
        result_data['content_hi'] = ''  # Non-fatal
    
    # === STEP 3: Feynman Technique Explanation ===
    try:
        feynman_en, feynman_hi = _generate_feynman(model, topic, subject)
        result_data['feynman_en'] = feynman_en
        result_data['feynman_hi'] = feynman_hi
    except Exception as e:
        result_data['feynman_en'] = ''
        result_data['feynman_hi'] = ''
    
    # === STEP 4: Active Recall Prompts ===
    try:
        prompts_en, prompts_hi = _generate_recall_prompts(model, topic, subject, content_en)
        result_data['retrieval_prompts_en'] = prompts_en
        result_data['retrieval_prompts_hi'] = prompts_hi
    except Exception as e:
        result_data['retrieval_prompts_en'] = []
        result_data['retrieval_prompts_hi'] = []
    
    # === STEP 5: Spaced Repetition Flashcards ===
    try:
        cards_en, cards_hi = _generate_flashcards(model, topic, subject, content_en)
        result_data['spaced_cards_en'] = cards_en
        result_data['spaced_cards_hi'] = cards_hi
    except Exception as e:
        result_data['spaced_cards_en'] = []
        result_data['spaced_cards_hi'] = []
    
    # === STEP 6: Key Formulas (Math-specific) ===
    try:
        formulas = _generate_formulas(model, topic, subject)
        result_data['key_formulas'] = formulas
    except Exception as e:
        result_data['key_formulas'] = []
    
    # === STEP 7: Mind Map Data ===
    try:
        mind_map = _generate_mind_map(model, topic, subject)
        result_data['mind_map'] = mind_map
    except Exception as e:
        result_data['mind_map'] = {}
    
    # === STEP 8: PYQ Data (Mock weightage) ===
    try:
        pyq_inline, pyq_weightage = _generate_pyq_data(model, topic, subject, target_exam)
        result_data['pyq_inline'] = pyq_inline
        result_data['pyq_weightage'] = pyq_weightage
    except Exception as e:
        result_data['pyq_inline'] = []
        result_data['pyq_weightage'] = {}
    
    # === STEP 9: Cognitive Load Score ===
    word_count = len((result_data.get('content_en', '') + result_data.get('content_hi', '')).split())
    # Score 1-10: Based on word count, formula density, etc.
    result_data['cognitive_load_score'] = min(10.0, max(1.0, word_count / 500.0))
    
    return {'success': True, 'data': result_data}


# ==========================================
# AGENT 1: Content Writer Agent
# ==========================================
def _generate_content(model, topic, subject, target_exam, target_level, difficulty, language):
    """Generates structured chapter content using Feynman + Active Recall principles"""
    
    lang_instruction = "Write entirely in Hindi (Devanagari script)." if language == 'Hindi' else "Write in clear, simple English."
    
    prompt = f"""You are an expert educational content writer specializing in {subject} for {target_exam} competitive exam preparation.

TOPIC: {topic}
TARGET LEVEL: {target_level}
DIFFICULTY: {difficulty}
{lang_instruction}

Write a comprehensive chapter following these COGNITIVE SCIENCE principles:

1. **CHUNKING RULE**: Break information into groups of 5-7 items maximum. Use clear headings and subheadings.

2. **DUAL CODING**: For every key concept, provide BOTH:
   - A text explanation
   - A visual description (describe a diagram, table, or analogy that can be visualized)

3. **ACTIVE RECALL MARKERS**: After every 2-3 paragraphs, insert a line that says:
   "🤔 **Pause & Think**: [question about what was just taught]"

4. **SCAFFOLDING**: Start from the most basic concept and build up gradually. Never assume prior knowledge.

5. **EXAMPLES FIRST**: For {subject}, always show a solved example BEFORE explaining the theory/formula.

6. **MNEMONIC AIDS**: Include memory tricks, acronyms, or rhymes where possible.

FORMAT: Use Markdown with:
- `##` for main sections
- `###` for subsections  
- `**bold**` for key terms (first occurrence)
- `> ` for important notes/tips
- Tables where comparison is needed
- Numbered steps for procedures

Keep the content between 1500-2500 words. Make it exam-focused but deeply understanding-oriented.
Do NOT add any meta commentary. Just write the chapter content directly."""

    response = model.generate_content(prompt)
    return response.text.strip()


# ==========================================
# AGENT 2: Feynman Technique Agent
# ==========================================
def _generate_feynman(model, topic, subject):
    """Generates Feynman-style simple explanations in both languages"""
    
    prompt = f"""You are explaining "{topic}" ({subject}) to a 12-year-old child using the Feynman Technique.

Rules:
1. Use everyday analogies (kitchen, playground, shopping, cricket)
2. NO jargon or technical terms without immediate simple definition
3. Use "Imagine..." or "Think of it like..." style
4. Maximum 300 words
5. Make it fun and engaging with emojis

Write TWO versions:

=== ENGLISH ===
[Write the Feynman explanation in English]

=== HINDI ===
[Write the same explanation in Hindi (Devanagari script)]

Separate the two versions clearly."""

    response = model.generate_content(prompt)
    text = response.text.strip()
    
    # Parse English and Hindi sections
    en_part = ''
    hi_part = ''
    
    if '=== ENGLISH ===' in text and '=== HINDI ===' in text:
        parts = text.split('=== HINDI ===')
        en_part = parts[0].replace('=== ENGLISH ===', '').strip()
        hi_part = parts[1].strip() if len(parts) > 1 else ''
    else:
        en_part = text
        hi_part = ''
    
    return en_part, hi_part


# ==========================================
# AGENT 3: Active Recall Generator
# ==========================================
def _generate_recall_prompts(model, topic, subject, content):
    """Generates Active Recall questions based on chapter content"""
    
    prompt = f"""Based on this {subject} chapter about "{topic}", create 6 Active Recall questions.

Chapter content (summary):
{content[:2000]}

For each question, provide:
1. The question itself (testing recall, not recognition)
2. A hint (subtle clue)
3. The answer (concise)

Return as a JSON array with this EXACT format (no other text):
```json
[
  {{
    "question": "...",
    "hint": "...",
    "answer": "...",
    "after_section": "section name where this should appear"
  }}
]
```

Make 6 questions covering different sections of the chapter.
Questions should test UNDERSTANDING, not just memorization.
For math: include calculation-based questions."""

    response = model.generate_content(prompt)
    prompts_en = _extract_json_array(response.text)
    
    # Generate Hindi versions
    prompt_hi = f"""Translate these Active Recall questions to Hindi (Devanagari script).
Keep the JSON format exactly the same, just translate the text values.

{json.dumps(prompts_en, ensure_ascii=False)}

Return ONLY the JSON array, no other text:"""

    try:
        response_hi = model.generate_content(prompt_hi)
        prompts_hi = _extract_json_array(response_hi.text)
    except:
        prompts_hi = []
    
    return prompts_en, prompts_hi


# ==========================================
# AGENT 4: Flashcard Generator (Spaced Repetition)
# ==========================================
def _generate_flashcards(model, topic, subject, content):
    """Generates spaced repetition flashcards"""
    
    prompt = f"""Create 10 flashcards for spaced repetition study of "{topic}" ({subject}).

Each card should have:
- Front: A question or prompt
- Back: The answer (concise, memorable)
- Tags: Related concepts

For Math topics, include formula cards.

Return as JSON array:
```json
[
  {{
    "front": "What is the formula for...?",
    "back": "Formula: ...",
    "tags": ["algebra", "basics"]
  }}
]
```

Return ONLY the JSON array."""

    response = model.generate_content(prompt)
    cards_en = _extract_json_array(response.text)
    
    # Hindi version
    try:
        prompt_hi = f"""Translate these flashcards to Hindi. Keep JSON format.
{json.dumps(cards_en[:5], ensure_ascii=False)}

Return ONLY JSON array:"""
        response_hi = model.generate_content(prompt_hi)
        cards_hi = _extract_json_array(response_hi.text)
    except:
        cards_hi = []
    
    return cards_en, cards_hi


# ==========================================
# AGENT 5: Formula Extractor (Math-specific)
# ==========================================
def _generate_formulas(model, topic, subject):
    """Extracts and formats key formulas for the topic"""
    
    if subject.lower() not in ['mathematics', 'math', 'maths', 'quantitative aptitude', 'गणित']:
        return []
    
    prompt = f"""List all important formulas for the Math topic: "{topic}"

Return as JSON array:
```json
[
  {{
    "name": "Area of Triangle",
    "formula": "A = ½ × base × height",
    "formula_latex": "A = \\\\frac{{1}}{{2}} \\\\times b \\\\times h",
    "when_to_use": "When base and height are given",
    "example": "If base = 6cm, height = 4cm, then A = ½ × 6 × 4 = 12 cm²"
  }}
]
```

Include ALL formulas related to this topic. Return ONLY JSON."""

    response = model.generate_content(prompt)
    return _extract_json_array(response.text)


# ==========================================
# AGENT 6: Mind Map Generator
# ==========================================
def _generate_mind_map(model, topic, subject):
    """Generates mind map node/edge data for visualization"""
    
    prompt = f"""Create a mind map structure for "{topic}" ({subject}).

Return as JSON with this format:
```json
{{
  "center": "{topic}",
  "branches": [
    {{
      "label": "Main concept 1",
      "color": "#4CAF50",
      "children": [
        {{"label": "Sub-concept 1a"}},
        {{"label": "Sub-concept 1b"}}
      ]
    }},
    {{
      "label": "Main concept 2", 
      "color": "#2196F3",
      "children": [
        {{"label": "Sub-concept 2a"}},
        {{"label": "Sub-concept 2b"}}
      ]
    }}
  ]
}}
```

Create 4-6 main branches, each with 2-4 children. Use distinct colors.
Return ONLY JSON."""

    response = model.generate_content(prompt)
    return _extract_json_object(response.text)


# ==========================================
# AGENT 7: PYQ Data Generator
# ==========================================
def _generate_pyq_data(model, topic, subject, target_exam):
    """Generates mock PYQ data and weightage analysis"""
    
    prompt = f"""For the {subject} topic "{topic}" in {target_exam} exams:

1. Create 4 sample Previous Year Questions (PYQ) that are commonly asked.
2. Create weightage data showing how frequently this topic appears.

Return as JSON:
```json
{{
  "pyq_inline": [
    {{
      "question": "If x + y = 10 and xy = 21, find x² + y²",
      "year": 2023,
      "exam": "SSC CGL",
      "options": ["A) 58", "B) 56", "C) 52", "D) 48"],
      "answer": "A",
      "explanation": "x² + y² = (x+y)² - 2xy = 100 - 42 = 58"
    }}
  ],
  "pyq_weightage": {{
    "SSC CGL": {{"2020": 3, "2021": 4, "2022": 2, "2023": 5, "2024": 3}},
    "SSC CHSL": {{"2020": 2, "2021": 3, "2022": 2, "2023": 4, "2024": 2}},
    "Banking": {{"2020": 1, "2021": 2, "2022": 1, "2023": 2, "2024": 1}}
  }}
}}
```

Make the questions realistic and exam-level. Return ONLY JSON."""

    response = model.generate_content(prompt)
    data = _extract_json_object(response.text)
    
    pyq_inline = data.get('pyq_inline', [])
    pyq_weightage = data.get('pyq_weightage', {})
    
    return pyq_inline, pyq_weightage


# ==========================================
# UTILITY: JSON Extraction Helpers
# ==========================================

def _extract_json_array(text):
    """Safely extract a JSON array from AI response text"""
    try:
        # Try direct parse
        text = text.strip()
        if text.startswith('['):
            return json.loads(text)
        
        # Try extracting from markdown code block
        match = re.search(r'```(?:json)?\s*(\[[\s\S]*?\])\s*```', text)
        if match:
            return json.loads(match.group(1))
        
        # Try finding array in text
        match = re.search(r'\[[\s\S]*\]', text)
        if match:
            return json.loads(match.group(0))
    except (json.JSONDecodeError, AttributeError):
        pass
    return []

def _extract_json_object(text):
    """Safely extract a JSON object from AI response text"""
    try:
        text = text.strip()
        if text.startswith('{'):
            return json.loads(text)
        
        match = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', text)
        if match:
            return json.loads(match.group(1))
        
        match = re.search(r'\{[\s\S]*\}', text)
        if match:
            return json.loads(match.group(0))
    except (json.JSONDecodeError, AttributeError):
        pass
    return {}
