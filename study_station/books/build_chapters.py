"""
build_chapters.py — Generate per-chapter HTML files from raw .txt content
Run: python books/build_chapters.py

Reads books/Foundation_10th_Math_WorldClass/Chapter_XX_*/
Outputs website/books/competitive-exams/10th-level/math/{slug}.html
"""
import os, re, json, sys, html

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WEBSITE_DIR = os.path.join(SCRIPT_DIR, "..", "website")
WEBSITE_BOOKS = os.path.join(WEBSITE_DIR, "books", "competitive-exams")

# Filled while building — every standalone SEO page emitted, used for the hub
# index and (via chapters/_pages.json) the sitemap in build_website.py.
SEO_PAGES = []

MATH_CHAPTERS = [
    ("01", "number-system",         "Number_System",           "संख्या प्रणाली",           "Number System"),
    ("02", "lcm-hcf",              "LCM_HCF",                "ल.स.प. और म.स.प.",         "LCM & HCF"),
    ("03", "simplification",       "Simplification",          "सरलीकरण",                  "Simplification"),
    ("04", "fractions-decimals",   "Fractions_Decimals",       "भिन्न और दशमलव",           "Fractions & Decimals"),
    ("05", "percentage",           "Percentage",               "प्रतिशत",                   "Percentage"),
    ("06", "average",              "Average",                  "औसत",                       "Average"),
    ("07", "ratio-proportion",     "Ratio_Proportion",         "अनुपात और समानुपात",        "Ratio & Proportion"),
    ("08", "profit-loss",          "Profit_Loss",              "लाभ और हानि",              "Profit & Loss"),
    ("09", "simple-interest",      "Simple_Interest",          "साधारण ब्याज",              "Simple Interest"),
    ("10", "compound-interest",    "Compound_Interest",        "चक्रवृद्धि ब्याज",         "Compound Interest"),
    ("11", "time-work",            "Time_Work",                "समय और कार्य",             "Time & Work"),
    ("12", "time-distance",        "Time_Distance",            "समय और दूरी",              "Time & Distance"),
    ("13", "mixture-alligation",   "Mixture_Alligation",       "मिश्रण और पृथ्थीकरण",      "Mixture & Alligation"),
    ("14", "mensuration",          "Mensuration",              "क्षेत्रमिति",               "Mensuration"),
    ("15", "geometry",             "Geometry",                 "ज्यामिति",                  "Geometry"),
    ("16", "algebra",              "Algebra",                  "बीजगणित",                   "Algebra"),
    ("17", "data-interpretation",  "Data_Interpretation",      "डेटा व्याख्या",            "Data Interpretation"),
    ("18", "trigonometry",         "Trigonometry",             "त्रिकोणमिति",               "Trigonometry"),
    ("19", "statistics",           "Statistics",               "सांख्यिकी",                "Statistics"),
    ("20", "number-series",        "Number_Series",            "संख्या श्रेणी",             "Number Series"),
    ("21", "probability",          "Probability",              "प्रायिकता",                 "Probability"),
    ("22", "permutation-combination","Permutation_Combination","क्रमचय और संचय",           "Permutation & Combination"),
]

REASONING_CHAPTERS = [
    ("01", "analogy",              "Analogy",                 "सादृश्यता",                "Analogy"),
    ("02", "classification",       "Classification",          "वर्गीकरण",                 "Classification"),
    ("03", "coding-decoding",      "Coding_Decoding",         "कूट भाषा",                 "Coding-Decoding"),
    ("04", "blood-relations",      "Blood_Relations",         "रक्त संबंध",               "Blood Relations"),
    ("05", "direction-sense",      "Direction_Sense",         "दिशा ज्ञान",               "Direction Sense"),
    ("06", "order-ranking",        "Order_Ranking",           "क्रम और रैंकिंग",          "Order & Ranking"),
    ("07", "sitting-arrangement",  "Sitting_Arrangement",     "बैठक व्यवस्था",            "Sitting Arrangement"),
    ("08", "puzzles-basic",        "Puzzles_Basic",           "पहेलियाँ (आधार)",          "Puzzles (Basic)"),
    ("09", "venn-diagrams",        "Venn_Diagrams",           "वेन आरेख",                 "Venn Diagrams"),
    ("10", "clock-calendar",       "Clock_Calendar",          "घड़ी और कैलेंडर",          "Clock & Calendar"),
    ("11", "series",               "Series",                  "श्रेणी",                   "Series"),
    ("12", "missing-term",         "Missing_Term",            "लुप्त पद",                 "Missing Term"),
    ("13", "dictionary-order",     "Dictionary_Order",        "शब्दकोश क्रम",             "Dictionary Order"),
    ("14", "alphabet-questions",   "Alphabet_Questions",      "वर्णमाला प्रश्न",          "Alphabet Questions"),
    ("15", "mathematical-operations","Mathematical_Operations","गणितीय संक्रियाएँ",       "Mathematical Operations"),
    ("16", "statement-conclusion", "Statement_Conclusion",    "कथन और निष्कर्ष",          "Statement & Conclusion"),
    ("17", "course-of-action",     "Course_of_Action",        "कार्यवाही",                "Course of Action"),
    ("18", "inequality",           "Inequality",              "असमानता",                  "Inequality"),
    ("19", "cubes-dice",           "Cubes_Dice",              "घन और पासा",               "Cubes & Dice"),
    ("20", "mirror-water-images",  "Mirror_Water_Images",     "दर्पण और जल प्रतिबिंब",    "Mirror & Water Images"),
    ("21", "paper-folding-cutting","Paper_Folding_Cutting",   "कागज़ मोड़ना-काटना",       "Paper Folding & Cutting"),
    ("22", "figure-series",        "Figure_Series",           "आकृति श्रेणी",             "Figure Series"),
]

ENGLISH_CHAPTERS = [
    ("01", "noun",                 "Noun",                 "संज्ञा",                  "Noun"),
    ("02", "pronoun",              "Pronoun",              "सर्वनाम",                 "Pronoun"),
    ("03", "adjective",            "Adjective",            "विशेषण",                  "Adjective"),
    ("04", "verb",                 "Verb",                 "क्रिया",                  "Verb"),
    ("05", "tense",                "Tense",                "काल",                     "Tense"),
    ("06", "adverb",               "Adverb",               "क्रिया-विशेषण",           "Adverb"),
    ("07", "preposition",          "Preposition",          "संबंधसूचक अव्यय",         "Preposition"),
    ("08", "conjunction",          "Conjunction",          "समुच्चयबोधक",             "Conjunction"),
    ("09", "articles",             "Articles",             "आर्टिकल (A, An, The)",   "Articles"),
    ("10", "voice",                "Voice",                "वाच्य",                   "Voice"),
    ("11", "narration",            "Narration",            "कथन (Narration)",        "Narration"),
    ("12", "sentence-structure",   "Sentence_Structure",   "वाक्य संरचना",            "Sentence Structure"),
    ("13", "synonyms",             "Synonyms",             "समानार्थी शब्द",          "Synonyms"),
    ("14", "antonyms",             "Antonyms",             "विलोम शब्द",              "Antonyms"),
    ("15", "one-word-substitution","One_Word_Substitution","एक शब्द प्रतिस्थापन",     "One Word Substitution"),
    ("16", "idioms-phrases",       "Idioms_Phrases",       "मुहावरे और वाक्यांश",     "Idioms & Phrases"),
    ("17", "spelling",             "Spelling",             "वर्तनी",                  "Spelling"),
    ("18", "error-spotting",       "Error_Spotting_Basic", "त्रुटि पहचान",            "Error Spotting"),
    ("19", "fill-in-blanks",       "Fill_in_Blanks_Basic", "रिक्त स्थान भरो",         "Fill in the Blanks"),
    ("20", "sentence-improvement", "Sentence_Improvement_Basic", "वाक्य सुधार",       "Sentence Improvement"),
]

# Subject registry — add a subject here and its chapters compile automatically.
# base: raw-content folder under books/{level_dir}/{subj_dir}/{book_folder}/
# out_slug: website folder under books/competitive-exams/{level_slug}/{out_slug}/
SUBJECTS = [
    {
        "subject": "math", "subject_hi": "गणित", "subject_en": "Mathematics",
        "level_slug": "10th-level", "level_label": "10th Level",
        "base": os.path.join(SCRIPT_DIR, "10th_Level", "Maths", "Foundation_10th_Math_WorldClass"),
        "out_slug": "math",
        "chapters": MATH_CHAPTERS,
    },
    {
        "subject": "reasoning", "subject_hi": "तर्कशक्ति", "subject_en": "Reasoning",
        "level_slug": "10th-level", "level_label": "10th Level",
        "base": os.path.join(SCRIPT_DIR, "10th_Level", "Reasoning"),
        "out_slug": "reasoning",
        "chapters": REASONING_CHAPTERS,
    },
    {
        "subject": "english", "subject_hi": "अंग्रेज़ी", "subject_en": "English",
        "level_slug": "10th-level", "level_label": "10th Level",
        "base": os.path.join(SCRIPT_DIR, "10th_Level", "English",
                             "Foundation_10th_English_WorldClass"),
        "out_slug": "english",
        "chapters": ENGLISH_CHAPTERS,
    },
]

# ========== DATA CLEANING ==========

AI_LEAK_PATTERNS = [
    r"(?i)\bI'll\s+(set|edit|keep|just|make|add|put|write|use|check|try|need)",
    r"(?i)\bI\s+should\b",
    r"(?i)\bI\s+need\s+to\b",
    r"(?i)\bLet\s+me\s+(recalculate|think|check|try|verify|re-?read|re-?do|start|set)",
    r"(?i)\bWait,\s",
    r"(?i)\bThat\s+would\s+(match|give|make|be)",
    r"(?i)\bI\s+have\s+to\b",
    r"(?i)\bI'd\s+need\b",
    r"(?i)\bBut\s+that's\s+not\b",
    r"(?i)\bHmm,?\s",
    r"(?i)\bOkay,?\s+so\b",
    r"(?i)\bActually,?\s+let\b",
]

def fix_katex_artifacts(text):
    """Repair math expressions shattered by copying KaTeX-rendered chat output.

    Copying rendered math duplicates each expression as stacked lines:
      fraction a/b  →  a \n b \n b \n a \n <tab+zwsp junk>
      root √n      →  n \n n \n <tab+zwsp junk>
      power a^b    →  a \n b \n a \n b
    Also drops lines made only of Unicode math-italic letters (𝑛, 𝑥 …) which
    duplicate the following ASCII text.
    """
    lines = text.split('\n')

    def tok(i):
        return lines[i].strip() if 0 <= i < len(lines) else None

    def is_num(s):
        return s is not None and re.fullmatch(r'[0-9]{1,6}', s) is not None

    def is_junk(s):
        if s is None:
            return False
        return re.fullmatch(r'[\s\t​‌‍⁡-⁤﻿]*', s) is not None \
            and re.search(r'[\t​⁡-⁤]', s) is not None

    out = []
    i = 0
    n = len(lines)
    while i < n:
        s = tok(i)
        # Math-italic-only line (duplicate of adjacent ASCII text) — drop it
        if s and all(0x1D400 <= ord(c) <= 0x1D7FF for c in s):
            i += 1
            continue
        # Fraction: a, b, b, a (+ junk lines)
        if is_num(s) and is_num(tok(i + 1)) and tok(i + 2) == tok(i + 1) and tok(i + 3) == s:
            a, b = s, tok(i + 1)
            j = i + 4
            while j < n and (is_junk(lines[j]) or lines[j].strip() == ''):
                if lines[j].strip() == '' and not (j + 1 < n and is_junk(lines[j + 1])):
                    break
                j += 1
            out.append(f'{a}/{b}')
            i = j
            continue
        # Root: n, n (+ junk)
        if is_num(s) and tok(i + 1) == s and is_junk(lines[i + 2] if i + 2 < n else None):
            j = i + 2
            while j < n and (is_junk(lines[j]) or lines[j].strip() == ''):
                if lines[j].strip() == '' and not (j + 1 < n and is_junk(lines[j + 1])):
                    break
                j += 1
            out.append(f'√{s}')
            i = j
            continue
        # Power: a, b, a, b (no junk marker)
        if is_num(s) and is_num(tok(i + 1)) and tok(i + 2) == s and tok(i + 3) == tok(i + 1):
            out.append(f'{s}^{tok(i + 1)}')
            i += 4
            continue
        out.append(lines[i])
        i += 1
    return '\n'.join(out)


# Matches a fenced block, allowing an optional language tag + caption text on
# the opening line (e.g. ```svg My caption\n...\n```).
FENCE_RE = re.compile(r'```[a-zA-Z]*[^\n]*\n.*?\n```', re.DOTALL)


def clean_text(text):
    """Remove AI self-talk, double blanks, and fix common issues.

    Fenced code blocks (```mermaid, ```svg) are protected from all cleaning so
    diagram markup — path data, attributes, coordinates — is never corrupted.
    """

    # 0. Pull out fenced diagram/code blocks; restore them verbatim at the end.
    protected = []

    def _stash(m):
        protected.append(m.group(0))
        return f"\x00FENCE{len(protected) - 1}\x00"

    text = FENCE_RE.sub(_stash, text)

    # 0a. Repair KaTeX copy artifacts BEFORE stripping invisible chars
    #     (the zero-width junk is the signature we detect)
    text = fix_katex_artifacts(text)

    # 0b. Strip invisible characters (zero-width space/joiner, BOM, soft hyphen, word joiner)
    text = re.sub('[​‌‍﻿­⁠]', '', text)

    # 1. Fix encoding glitches — ONLY between digits, so that a real letter "A"
    #    (node ids, "A and B", "If A can do…") is never corrupted
    text = re.sub(r'(\d)\s*A[-—]\s*(\d)', r'\1 × \2', text)
    text = re.sub(r'(\d)\s+A÷?\s+(\d)', r'\1 ÷ \2', text)
    # NOTE: '?"' and '??' replacements removed — they corrupted legitimate
    # text like `है?"]` (question mark before a closing quote)
    text = text.replace("+'", '→')
    text = text.replace('?o', '"').replace('?T', "'").replace('', '')

    # 2. Un-smush text (add newlines)
    # Generic Un-smusher for missing spaces/newlines
    text = re.sub(r'([a-z0-9\)])([A-Z])', r'\1\n\n\2', text)
    text = re.sub(r'(\.)([A-Z])', r'\1\n\n\2', text)
    text = re.sub(r'(\?)(If|The|What|How|Why|[A-Z])', r'\1\n\n\2', text)

    # Safely extract question numbers without breaking paragraphs
    text = re.sub(r'(Source:.*?(?:20\d{2}|Class\s*\d{1,2}|Exams?))(\d{1,2}\.)', r'\1\n\n\2', text, flags=re.I)
    text = re.sub(r'(Questions\s+\d+[^0-9]+\d+)(\d{1,2}\.)', r'\1\n\n\2', text, flags=re.I)
    # Hindi equivalents: "स्रोत: NCERT कक्षा 62." → new question "2." starts after "कक्षा 6"
    text = re.sub(r'(स्रोत\s*:.*?(?:20\d{2}|कक्षा\s*\d{1,2}))(\d{1,2}\.)', r'\1\n\n\2', text)
    text = re.sub(r'(?<!\n)(प्रश्न\s*\d{1,3}\.\s)', r'\n\n\1', text)
    text = re.sub(r'(आसान|मध्यम|कठिन)\)?(\d{1,2}\.)', r'\1\n\n\2', text)
    
    text = re.sub(r'(?<!\n)(?<!^)(\([a-dA-D]\)\s)', r'\n\1', text)
    text = re.sub(r'(?i)(?<!\n)(?<!^)(Answer|Ans|उत्तर)\s*:', r'\n\1:', text)
    
    # Fix Answer: \n(a) back to Answer: (a)
    text = re.sub(r'(?i)(Answer|Ans|उत्तर)\s*:\s*\n\s*\(([a-d])\)', r'\1: (\2)', text)
    
    text = re.sub(r'(?i)(?<!\n)(?<!^)(Solution|Sol|हल|व्याख्या)\s*:', r'\n\1:', text)
    text = re.sub(r'(?i)(?<!\n)(?<!^)(Source|Src|स्रोत)\s*:', r'\n\1:', text)
    
    # Flashcards fixing (Flashcard 1Q: ... A: ...)
    text = re.sub(r'(?i)Flashcard\s+(\d+)Q:', r'\nCard \1\nFront:', text)
    text = re.sub(r'(?i)(?<!\n)(?<!^)(A:|Back:)', r'\nBack:', text)
    text = re.sub(r'(?i)(?<!\n)(?<!^)Front:', r'\nFront:', text)

    lines = text.split('\n')
    cleaned = []
    prev_blank = False
    for line in lines:
        stripped = line.strip()
        # Skip pure AI self-talk lines
        is_leak = False
        for pat in AI_LEAK_PATTERNS:
            if re.search(pat, stripped):
                # Only skip if the line is primarily self-talk (< 100 chars and starts with pattern)
                if len(stripped) < 150 and re.match(pat, stripped):
                    is_leak = True
                    break
        if is_leak:
            continue
        # Remove double blank lines
        if stripped == '':
            if prev_blank:
                continue
            prev_blank = True
        else:
            prev_blank = False
        # Fix **Answer:** markdown bold leaking into answers
        line = re.sub(r'\*\*Answer:\*\*', 'Answer:', line)
        line = re.sub(r'\*\*उत्तर:\*\*', 'उत्तर:', line)
        cleaned.append(line)
    result = '\n'.join(cleaned).strip()

    # Restore protected fenced blocks verbatim.
    def _unstash(m):
        return protected[int(m.group(1))]

    result = re.sub(r'\x00FENCE(\d+)\x00', _unstash, result)
    return result

def read_file(path):
    """Read a text file, return cleaned content or empty string."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            text = f.read().strip()
        if text.startswith("# Chapter:") and len(text) < 2000:
            return ""
        return clean_text(text)
    except:
        return ""

# ========== HTML CONVERTERS ==========

def esc(text):
    """HTML escape text."""
    return html.escape(text, quote=True)

def is_heading_candidate(stripped):
    """Determine if a short line should be treated as a heading.
    Returns False for lines that are clearly NOT headings."""
    # Too short — likely a broken fraction digit or stray word
    if len(stripped) < 5:
        return False
    # Too long — not a heading
    if len(stripped) >= 80:
        return False
    # Ends with Hindi purna viram, visarg, or common sentence-enders
    if stripped.endswith('।') or stripped.endswith('|') or stripped.endswith('.'):
        return False
    if stripped.endswith(':') or stripped.endswith(',') or stripped.endswith(';'):
        return False
    if stripped.endswith(')') or stripped.endswith('"') or stripped.endswith("'"):
        return False
    # Contains a question mark — it's a recall prompt, not heading
    if '?' in stripped:
        return False
    # Starts with parenthesis — likely an answer/note
    if stripped.startswith('(') or stripped.startswith('*'):
        return False
    # Contains Hindi sentence markers suggesting it's prose
    hindi_sentence_markers = ['है', 'हैं', 'था', 'थे', 'थी', 'होता', 'होती', 'होते',
                               'करो', 'करें', 'सकते', 'सकता', 'सकती', 'चाहिए',
                               'जाता', 'जाती', 'जाते', 'रहता', 'रहती']
    for marker in hindi_sentence_markers:
        if stripped.endswith(marker) or stripped.endswith(marker + '।'):
            return False
    # Must look like a title: starts with number+dot, or is Title Case, or short bold phrase
    if re.match(r'^\d+\.\s', stripped):
        return True  # e.g. "1. Natural Numbers"
    if re.match(r'^[A-Z][a-z]', stripped) and len(stripped) < 60:
        return True  # Title Case English
    # Hindi heading-like lines (short, no verb ending)
    if len(stripped) < 50:
        return True
    return False


def text_to_html(text):
    """Convert markdown-ish text to semantic HTML."""
    if not text:
        return ""
    lines = text.split('\n')
    out = []
    in_list = False
    in_table = False
    in_mermaid = False
    mermaid_lines = []
    in_svg = False
    svg_lines = []
    svg_caption = ''

    for line in lines:
        stripped = line.strip()

        # --- Inline SVG diagram block: ```svg [optional caption] ... ``` ---
        if stripped.startswith('```svg'):
            in_svg = True
            svg_lines = []
            svg_caption = stripped[6:].strip()  # text after ```svg = caption
            continue
        if in_svg:
            if stripped == '```':
                in_svg = False
                svg_code = '\n'.join(svg_lines).strip()
                cap = f'<figcaption>{esc(svg_caption)}</figcaption>' if svg_caption else ''
                out.append(f'<figure class="chapter-figure">{svg_code}{cap}</figure>')
                svg_lines = []
                svg_caption = ''
            else:
                svg_lines.append(line.rstrip())
            continue

        if not stripped:
            if in_list:
                out.append('</ul>')
                in_list = False
            if in_table:
                out.append('</table>')
                in_table = False
            continue

        # --- Mermaid code block detection ---
        if stripped.startswith('```mermaid') or stripped == '```mermaid':
            in_mermaid = True
            mermaid_lines = []
            continue
        if in_mermaid:
            if stripped == '```':
                in_mermaid = False
                mermaid_code = '\n'.join(mermaid_lines)
                out.append(f'<div class="mermaid">{esc(mermaid_code)}</div>')
                mermaid_lines = []
            else:
                mermaid_lines.append(line.rstrip())
            continue

        # --- Markdown headings (explicit # markers) ---
        if stripped.startswith('### '):
            if in_list: out.append('</ul>'); in_list = False
            out.append(f'<h4>{esc(stripped[4:])}</h4>')
        elif stripped.startswith('## '):
            if in_list: out.append('</ul>'); in_list = False
            out.append(f'<h3>{esc(stripped[3:])}</h3>')
        elif stripped.startswith('# '):
            if in_list: out.append('</ul>'); in_list = False
            out.append(f'<h2>{esc(stripped[2:])}</h2>')
        # Horizontal rule
        elif re.match(r'^-{3,}$', stripped):
            if in_list: out.append('</ul>'); in_list = False
            out.append('<hr>')
        # Recall box (🧠)
        elif stripped.startswith('🧠'):
            if in_list: out.append('</ul>'); in_list = False
            out.append(f'<div class="recall-box">🧠 {esc(stripped[2:].strip())}</div>')
        # Emoji section headers
        elif re.match(r'^[📌💡🎯📊🔑⚡✅❌⭐🏆📝🧮📐🔢🎓🃏🪄📖🧒🗺️]\s', stripped):
            if in_list: out.append('</ul>'); in_list = False
            emoji = stripped[0] if ord(stripped[0]) > 127 else stripped[:2]
            rest = stripped[len(emoji):].strip()
            out.append(f'<div class="emoji-section"><span class="emoji-section__icon">{emoji}</span><strong>{esc(rest)}</strong></div>')
        # Bullet lists
        elif re.match(r'^[·•\-]\s', stripped):
            if not in_list:
                out.append('<ul>')
                in_list = True
            item = re.sub(r'^[·•\-]\s+', '', stripped)
            out.append(f'  <li>{format_inline(item)}</li>')
        # Table-like lines
        elif '\t' in stripped and not stripped.startswith('('):
            if not in_table:
                out.append('<table class="content-table">')
                in_table = True
            cols = [c.strip() for c in stripped.split('\t') if c.strip()]
            out.append('<tr>' + ''.join(f'<td>{esc(c)}</td>' for c in cols) + '</tr>')
        # Tricks & Shortcuts
        elif re.match(r'^(Trick|Shortcut|Tip)\b', stripped, re.I):
            if in_list: out.append('</ul>'); in_list = False
            out.append(f'<div class="card card--trick"><div class="card__icon">🪄</div><div class="card__content">{format_inline(stripped)}</div></div>')
        # Rules & Important Concepts
        elif re.match(r'^(Rule|Formula|Concept|Important|Note)\b', stripped, re.I):
            if in_list: out.append('</ul>'); in_list = False
            out.append(f'<div class="card card--rule"><div class="card__icon">🔑</div><div class="card__content">{format_inline(stripped)}</div></div>')
        # Step-by-Step
        elif re.match(r'^(Step\s*\d+|Step-by-Step)\b', stripped, re.I):
            if in_list: out.append('</ul>'); in_list = False
            out.append(f'<div class="step-card">{format_inline(stripped)}</div>')
        # Definitions (परिभाषा / Definition)
        elif re.match(r'^(परिभाषा|Definition)\s*:', stripped, re.I):
            if in_list: out.append('</ul>'); in_list = False
            out.append(f'<div class="card card--definition"><div class="card__icon">📋</div><div class="card__content">{format_inline(stripped)}</div></div>')
        # Recall Boxes (questions)
        elif '?' in stripped or 'Recall:' in stripped:
            if in_list: out.append('</ul>'); in_list = False
            text_clean = stripped.replace('🧠', '').strip()
            out.append(f'<div class="card card--recall"><div class="card__icon">🧠</div><div class="card__content">{format_inline(text_clean)}</div></div>')
        # Smart Heading Detection (with strict rules)
        elif is_heading_candidate(stripped):
            if in_list: out.append('</ul>'); in_list = False
            # Numbered headings get <h3>, others get <h4>
            if re.match(r'^\d+\.\s', stripped):
                out.append(f'<h3>{esc(stripped)}</h3>')
            else:
                out.append(f'<h4>{esc(stripped)}</h4>')
        # Standard Paragraphs (default)
        else:
            if in_list: out.append('</ul>'); in_list = False
            out.append(f'<p>{format_inline(stripped)}</p>')

    if in_list: out.append('</ul>')
    if in_table: out.append('</table>')
    return '\n'.join(out)

def format_inline(text):
    """Format bold, italic, and inline code."""
    t = esc(text)
    t = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', t)
    t = re.sub(r'\*(.+?)\*', r'<em>\1</em>', t)
    t = re.sub(r'`(.+?)`', r'<code>\1</code>', t)
    return t

# ========== MCQ CONVERTER ==========

ANSWER_LABEL = r'(?:सही\s*उत्तर|उत्तर|Answer|Ans)'
SOLUTION_LABEL = r'(?:(?:चरण-दर-चरण\s*)?हल|Solution|Sol|व्याख्या)'
SOURCE_LABEL = r'(?:Source|स्रोत|Src)'
QNUM_RE = r'(?:Q\d+|प्रश्न\s*\d+|\d+)\.(?!\d)\s*'


def _parse_question_fields(qblock, numbered=True):
    """Extract question/options/answer/solution/source from one MCQ block.

    numbered=False handles sets whose questions carry no number at all
    (the first lines before the options are treated as the question).
    """
    lines = qblock.split('\n')
    question_text = ''
    options_line = ''
    correct_answer = ''
    correct_text = ''
    solution_text = ''
    source_text = ''
    current_field = 'question'

    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Question line
        if numbered and re.match(r'^' + QNUM_RE, line) and not question_text:
            question_text = line
            current_field = 'question'
        # Options line
        elif re.match(r'^\([a-d]\)', line, re.I):
            options_line += ' ' + line
            current_field = 'options'
        # Answer
        elif re.match(r'^' + ANSWER_LABEL + r'\s*[:\-]', line, re.I):
            correct_text = re.sub(r'^' + ANSWER_LABEL + r'\s*[:\-]\s*', '', line, flags=re.I).strip()
            letter_m = re.search(r'\(([A-D])\)', correct_text, re.I)
            if letter_m:
                correct_answer = letter_m.group(1).upper()
            current_field = 'answer'
        # Solution (start)
        elif re.match(r'^' + SOLUTION_LABEL + r'\s*[:\-]', line, re.I):
            solution_text = re.sub(r'^' + SOLUTION_LABEL + r'\s*[:\-]\s*', '', line, flags=re.I).strip()
            current_field = 'solution'
        # Source
        elif re.match(r'^' + SOURCE_LABEL + r'\s*[:\-]', line, re.I):
            source_text = re.sub(r'^' + SOURCE_LABEL + r'\s*[:\-]\s*', '', line, flags=re.I).strip()
            current_field = 'source'
        # Continuation of current field
        elif current_field == 'solution':
            solution_text += ' ' + line if solution_text else line
        elif current_field == 'options' and options_line:
            options_line += ' ' + line
        elif current_field == 'question' and not options_line:
            if question_text:
                question_text += ' ' + line
            elif not numbered:
                question_text = line

    return question_text, options_line, correct_answer, correct_text, solution_text, source_text


def parse_mcqs(text):
    """Convert raw MCQ text to pre-rendered HTML cards."""
    if not text or len(text) < 20:
        return ""

    # Strip markdown bold and chat-UI junk lines that break field detection
    text = text.replace('**', '')
    text = '\n'.join(l for l in text.split('\n') if not JUNK_LINES.match(l.strip()))

    # Inline-HTML variant: answers wrapped in <details> blocks
    if '<details>' in text:
        text = re.sub(r'<br\s*/?>', '\n', text)
        text = re.sub(r'</?(?:details|summary|strong|b|em|i|u|span|p|div)[^>]*>', '\n', text)
        text = re.sub(r'\n{3,}', '\n\n', text)

    out = []
    questions = re.split(r'\n(?=' + QNUM_RE + r')', text)
    set_num = 0
    q_counter = 0

    # Answer-key mode: some sets list bare questions first and a separate key
    # ("25. उत्तर: (A) 1 …") afterwards — pair them up by question number.
    answer_key = {}
    remaining = []
    for qblock in questions:
        m = re.match(r'^\s*(\d+)\.\s*' + ANSWER_LABEL + r'\s*[:\-]?\s*(.*)', qblock.strip(), re.S)
        if m:
            num = int(m.group(1))
            body = m.group(2).strip()
            letter_m = re.search(r'\(([A-D])\)', body, re.I)
            key_lines = body.split('\n', 1)
            answer_key[num] = {
                'letter': letter_m.group(1).upper() if letter_m else '',
                'text': key_lines[0].strip(),
                'solution': re.sub(r'\s+', ' ', key_lines[1]).strip() if len(key_lines) > 1 else '',
            }
        else:
            remaining.append(qblock)
    if answer_key:
        questions = remaining

    # Fallback for numberless sets: each blank-line block holding an answer
    # label is one complete question card.
    n_answers = len(re.findall(r'(?:^|\n)\s*' + ANSWER_LABEL + r'\s*[:\-]', text))
    if len(questions) < 5 and n_answers >= 8:
        questions = []
        current = []
        for line in text.split('\n'):
            if line.strip() == '':
                if current:
                    questions.append('\n'.join(current))
                    current = []
            else:
                current.append(line)
        if current:
            questions.append('\n'.join(current))
        numbered = False
    else:
        numbered = True

    for qblock in questions:
        qblock = qblock.strip()
        if not qblock or len(qblock) < 5:
            continue

        # Check for set headers
        set_match = re.search(r'---\s*Set\s*(\d+)\s*---', qblock, re.I)
        if set_match:
            set_num = int(set_match.group(1))
            out.append(f'<h2 class="mcq-set-title">📝 Set {set_num}</h2>')
            qblock = re.sub(r'---\s*Set\s*\d+\s*---', '', qblock, flags=re.I).strip()
            if not qblock or len(qblock) < 5:
                continue

        question_text, options_line, correct_answer, correct_text, solution_text, source_text = \
            _parse_question_fields(qblock, numbered=numbered)

        # Pair with the answer key when the question itself carried no answer
        if question_text and not (correct_text or correct_answer) and answer_key:
            num_m = re.match(r'^(?:Q|प्रश्न\s*)?(\d+)\.', question_text)
            if num_m and int(num_m.group(1)) in answer_key:
                key = answer_key[int(num_m.group(1))]
                correct_answer = key['letter']
                correct_text = key['text']
                if key['solution'] and not solution_text:
                    solution_text = key['solution']

        # A card without a question plus some answer/solution is header noise — skip
        if not question_text or not (correct_text or correct_answer or solution_text):
            continue

        # Parse options using position-based approach
        opts = []
        if options_line:
            for letter in ['A', 'B', 'C', 'D']:
                pattern = re.compile(r'\(' + letter + r'\)\s*', re.I)
                m = pattern.search(options_line)
                if m:
                    opts.append({'letter': letter, 'idx': m.start()})
            opts.sort(key=lambda x: x['idx'])
            for i, o in enumerate(opts):
                start = o['idx'] + 3  # skip "(X)"
                end = opts[i+1]['idx'] if i+1 < len(opts) else len(options_line)
                o['text'] = options_line[start:end].strip()

        q_counter += 1
        qid = f"q{q_counter}"

        card_html = f'<div class="mcq-card" id="card_{qid}" data-correct="{correct_answer}">\n'
        card_html += f'  <div class="mcq-question">{esc(question_text)}</div>\n'

        if opts:
            card_html += '  <div class="mcq-options">\n'
            for o in opts:
                is_correct = '1' if o['letter'] == correct_answer else '0'
                card_html += (
                    f'    <div class="mcq-opt" data-letter="{o["letter"]}" '
                    f'data-correct="{is_correct}" onclick="selectMcqOption(this, \'{qid}\')">\n'
                    f'      <span class="mcq-opt__letter">{o["letter"]}</span>\n'
                    f'      <span class="mcq-opt__text">{esc(o.get("text",""))}</span>\n'
                    f'    </div>\n'
                )
            card_html += '  </div>\n'

        # Answer section (hidden toggle)
        card_html += f'  <details class="mcq-answer" id="ans_{qid}">\n'
        card_html += f'    <summary>Show Solution</summary>\n'
        card_html += f'    <div class="mcq-answer__inner">\n'
        card_html += f'      <div class="mcq-answer__label">✅ Answer: <strong>{esc(correct_text or correct_answer)}</strong></div>\n'
        if solution_text:
            card_html += f'      <div class="mcq-answer__solution">💡 {esc(solution_text)}</div>\n'
        if source_text:
            card_html += f'      <div class="mcq-answer__source">📚 {esc(source_text)}</div>\n'
        card_html += f'    </div>\n'
        card_html += '  </details>\n'
        card_html += '</div>\n'

        out.append(card_html)

    return '\n'.join(out)

# ========== FLASHCARD CONVERTER ==========

JUNK_LINES = re.compile(r'^(plaintext|Copy|Download|Diagram|Code|Fullscreen|markdown|text)$', re.I)


def parse_flashcards(text):
    """Convert raw flashcard text to pre-rendered HTML cards.

    Handles three source formats:
      1. "Card 1 / Flashcard 1" headers followed by Front:/Back:
      2. Bare "Front:/Back:" (or सामने:/पीछे:) pairs separated by blank lines
      3. Numbered items ("1." on its own line) followed by labelled pairs
    """
    if not text or len(text) < 20:
        return ""

    # Strip copy-paste junk lines from AI chat UIs
    text = '\n'.join(l for l in text.split('\n') if not JUNK_LINES.match(l.strip()))

    # Primary split: explicit card headers
    cards = re.split(r'\n(?=(?:Card|कार्ड|Flashcard|फ्लैशकार्ड)\s*\d+)', text, flags=re.I)

    # Fallback splits when header-split found (almost) nothing but multiple
    # Front labels exist in the text
    if len(cards) <= 2:
        n_fronts = len(re.findall(r'(?:^|\n)\s*(?:Front|सामने)\s*:', text, re.I))
        if n_fronts >= 2:
            cards = re.split(r'\n\s*(?=(?:Front|सामने)\s*:)', text, flags=re.I)
        else:
            # Numbered flashcards: "1." alone on a line
            cards = re.split(r'\n(?=\d{1,2}\.\s*$)', text, flags=re.M)

    out = ['<div class="flashcard-grid">']
    card_num = 0

    for card in cards:
        card = card.strip()
        if not card or len(card) < 10:
            continue

        # Extract front and back with multiple patterns
        front_match = re.search(r'(?:Front|सामने|Q|प्रश्न)\s*:\s*(.+)', card, re.I)
        back_match = re.search(r'(?:Back|पीछे|A|उत्तर|Ans)\s*:\s*(.+(?:\n(?!\s*(?:Front|सामने|Card|कार्ड|\d{1,2}\.)).+)*)', card, re.I)

        # Fallback: if no Front/Back labels, split by newline
        if not front_match:
            card_lines = [l.strip() for l in card.split('\n') if l.strip()]
            content_lines = [l for l in card_lines if not re.match(r'^(?:Card|कार्ड|Flashcard|फ्लैशकार्ड)\s*\d+|^\d{1,2}\.\s*$', l, re.I)]
            if len(content_lines) >= 2:
                front = content_lines[0]
                back = ' '.join(content_lines[1:])
            elif len(content_lines) == 1:
                front = content_lines[0]
                back = '—'
            else:
                continue
        else:
            front = front_match.group(1).strip()
            back = re.sub(r'\s*\n\s*', ' ', back_match.group(1)).strip() if back_match else '—'

        card_num += 1
        out.append(
            f'<div class="flashcard" onclick="this.classList.toggle(\'flipped\')">\n'
            f'  <div class="flashcard__inner">\n'
            f'    <div class="flashcard__front"><span class="flashcard__num">{card_num}</span>{esc(front)}</div>\n'
            f'    <div class="flashcard__back">{esc(back)}</div>\n'
            f'  </div>\n'
            f'</div>'
        )

    out.append('</div>')
    if card_num == 0:
        return ""
    return '\n'.join(out)

# ========== MIND MAP CONVERTER ==========

MERMAID_KEYWORDS = ('mindmap', 'graph ', 'graph\n', 'flowchart', 'graph TD', 'graph LR')


def parse_mindmap(text):
    """Render Mind_Map.txt as a Mermaid diagram.

    Handles: fenced ```mermaid blocks, raw unfenced mermaid code, and
    copy-paste garbage ("Diagram Code Download... Mermaid rendering failed").
    Returns "" when no usable diagram exists (empty-state shows instead).
    """
    if not text:
        return ""

    # Drop junk lines that came from copying an AI chat UI
    lines = [l for l in text.split('\n') if not JUNK_LINES.match(l.strip())]
    cleaned = '\n'.join(lines).strip()
    cleaned = cleaned.replace('Mermaid rendering failed.', '').strip()
    if len(cleaned) < 30:
        return ""

    # Case 1: proper fenced block(s) — reuse the standard text pipeline
    if '```mermaid' in cleaned:
        return text_to_html(cleaned)

    # Case 2: raw mermaid code without fences
    stripped = cleaned.lstrip()
    if stripped.startswith(MERMAID_KEYWORDS):
        return f'<div class="mermaid">{esc(cleaned)}</div>'

    # Case 3: mermaid code buried after a title line
    m = re.search(r'^(mindmap|graph\s+(?:TD|LR|BT|RL)|flowchart\s+\w+)\s*$', cleaned, re.M)
    if m:
        code = cleaned[m.start():]
        return f'<div class="mermaid">{esc(code)}</div>'

    # No usable diagram
    return ""


# ========== CHAPTER HTML GENERATOR ==========

def generate_chapter_html(num, slug, folder_name, name_hi, name_en, base, subject, level_slug):
    """Generate a complete chapter HTML file with all 14 sections."""
    folder = os.path.join(base, f"Chapter_{num}_{folder_name}")

    # Read all content files
    data = {}
    file_map = {
        'content_hi': 'Content_hi.txt',  'content_en': 'Content_en.txt',
        'feynman_hi': 'Feynman_hi.txt',  'feynman_en': 'Feynman_en.txt',
        'mind_map':   'Mind_Map.txt',
        'flashcards_hi': 'Flashcards_hi.txt', 'flashcards_en': 'Flashcards_en.txt',
        'pyq_hi':     'PYQ_hi.txt',       'pyq_en':     'PYQ_en.txt',
        'tricks_hi':  'Short_Tricks_hi.txt', 'tricks_en': 'Short_Tricks_en.txt',
    }
    for key, fname in file_map.items():
        data[key] = read_file(os.path.join(folder, fname))

    # Practice MCQs — combine sets
    for lang in ['hi', 'en']:
        parts = []
        for s in range(1, 7):
            txt = read_file(os.path.join(folder, f"Practice_{lang}_Set_{s:02d}.txt"))
            if txt:
                parts.append(f"--- Set {s} ---\n{txt}")
        data[f'practice_{lang}'] = '\n\n'.join(parts)

    # Build HTML sections
    sections = []
    rendered_map = {}

    # Tab mappings: (tab_id, content_key_hi, content_key_en, renderer)
    tab_map = [
        ('content',    'content_hi',    'content_en',    'text'),
        ('feynman',    'feynman_hi',    'feynman_en',    'text'),
        ('mindmap',    'mind_map',      'mind_map',      'mindmap'),
        ('flashcards', 'flashcards_hi', 'flashcards_en', 'flashcard'),
        ('pyq',        'pyq_hi',        'pyq_en',        'mcq'),
        ('tricks',     'tricks_hi',     'tricks_en',     'text'),
        ('practice',   'practice_hi',   'practice_en',   'mcq'),
    ]

    for tab_id, key_hi, key_en, renderer in tab_map:
        for lang, key in [('hi', key_hi), ('en', key_en)]:
            raw = data.get(key, '')
            if renderer == 'mcq':
                rendered = parse_mcqs(raw) if raw else ''
            elif renderer == 'flashcard':
                rendered = parse_flashcards(raw) if raw else ''
            elif renderer == 'mindmap':
                rendered = parse_mindmap(raw) if raw else ''
            else:
                rendered = text_to_html(raw) if raw else ''

            if not rendered:
                rendered = '<div class="empty-state"><div class="empty-state__icon">📝</div><div class="empty-state__title">Content being prepared</div></div>'

            rendered_map[(tab_id, lang)] = rendered
            sections.append(
                f'  <section data-tab="{tab_id}" data-lang="{lang}" style="display:none">\n'
                f'{rendered}\n'
                f'  </section>\n'
            )

    chapter_html = (
        f'<!--\n'
        f'  Chapter: {name_en} | {name_hi}\n'
        f'  Level: {level_slug} | Subject: {subject} | Chapter: {int(num)}\n'
        f'  Auto-generated by build_chapters.py — DO NOT EDIT\n'
        f'-->\n'
        f'<article class="chapter-data"\n'
        f'  data-slug="{slug}"\n'
        f'  data-num="{int(num)}"\n'
        f'  data-name-en="{esc(name_en)}"\n'
        f'  data-name-hi="{esc(name_hi)}"\n'
        f'  data-subject="{subject}"\n'
        f'  data-level="{level_slug}">\n\n'
        + '\n'.join(sections) +
        f'\n</article>\n'
    )

    return chapter_html, rendered_map


# ========== STANDALONE SEO PAGES ==========
# The fragment above is what the SPA fetches — it has no <head>, so search
# engines can neither crawl nor understand it. For every chapter we also emit a
# real, server-rendered page per language: crawlable, linked from a hub, and
# listed in the sitemap. The SPA is unaffected.

SITE_URL = os.environ.get('SITE_URL', '').rstrip('/')

SEO_TAB_ORDER = [
    ('content',    {'hi': 'पाठ',              'en': 'Chapter Notes'}),
    ('feynman',    {'hi': 'आसान भाषा में',    'en': 'In Simple Words'}),
    ('tricks',     {'hi': 'शॉर्ट ट्रिक्स',   'en': 'Short Tricks'}),
    ('mindmap',    {'hi': 'माइंड मैप',        'en': 'Mind Map'}),
    ('pyq',        {'hi': 'पिछले वर्ष के प्रश्न', 'en': 'Previous Year Questions'}),
    ('practice',   {'hi': 'अभ्यास प्रश्न',    'en': 'Practice Questions'}),
]


def _plain_text(html_str, limit=155):
    """Strip tags to build a meta description."""
    txt = re.sub(r'<[^>]+>', ' ', html_str or '')
    txt = html.unescape(txt)
    txt = re.sub(r'\s+', ' ', txt).strip()
    return txt[:limit].rsplit(' ', 1)[0] if len(txt) > limit else txt


def seo_page_rel(lang, level_slug, out_slug, slug):
    """Site-relative path of a chapter's standalone SEO page."""
    return f"chapters/{lang}/{level_slug}/{out_slug}/{slug}.html"


def generate_seo_page(lang, num, slug, name_hi, name_en, subject_label, level_label,
                      level_slug, out_slug, rendered_map):
    """Render one crawlable, standalone page for a chapter in one language."""
    is_hi = lang == 'hi'
    title = name_hi if is_hi else name_en
    other = 'en' if is_hi else 'hi'
    root = '../../../../'          # chapters/{lang}/{level}/{subject}/x.html
    rel = seo_page_rel(lang, level_slug, out_slug, slug)
    canonical = f"{SITE_URL}/{rel}" if SITE_URL else None
    alt_rel = seo_page_rel(other, level_slug, out_slug, slug)

    body_parts = []
    for tab_id, labels in SEO_TAB_ORDER:
        chunk = rendered_map.get((tab_id, lang), '')
        if not chunk or 'empty-state' in chunk:
            continue
        body_parts.append(
            f'<section class="seo-section" id="{tab_id}">\n'
            f'  <h2>{esc(labels[lang])}</h2>\n{chunk}\n</section>'
        )
    body = '\n'.join(body_parts)

    desc_src = rendered_map.get(('content', lang), '')
    desc = _plain_text(desc_src) or (
        f"{title} — {subject_label} अध्याय {int(num)}" if is_hi
        else f"{title} — {subject_label} chapter {int(num)}")

    heading = (f"{title} — {subject_label} अध्याय {int(num)}" if is_hi
               else f"{title} — {subject_label} Chapter {int(num)}")
    intro = ("मुफ़्त पाठ, माइंड मैप, शॉर्ट ट्रिक्स और अभ्यास प्रश्न — हिंदी में।" if is_hi
             else "Free notes, mind map, short tricks and practice questions.")
    reader_cta = ("इंटरैक्टिव रीडर में खोलें" if is_hi else "Open in interactive reader")
    other_lang_label = "English" if is_hi else "हिंदी"

    ld = {
        "@context": "https://schema.org",
        "@type": "LearningResource",
        "name": heading,
        "description": desc,
        "inLanguage": "hi-IN" if is_hi else "en-IN",
        "educationalLevel": level_label,
        "about": subject_label,
        "isAccessibleForFree": True,
        "learningResourceType": "Chapter",
    }
    if canonical:
        ld["url"] = canonical

    return f'''<!DOCTYPE html>
<html lang="{'hi' if is_hi else 'en'}" data-theme="dark">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(heading)} | Study Station</title>
<meta name="description" content="{esc(desc)}">
<meta name="robots" content="index, follow">
<meta name="theme-color" content="#8B5CF6">
{f'<link rel="canonical" href="{canonical}">' if canonical else ''}
{f'<link rel="alternate" hreflang="{other}" href="{SITE_URL}/{alt_rel}">' if SITE_URL else ''}
{f'<link rel="alternate" hreflang="{lang}" href="{canonical}">' if canonical else ''}
<meta property="og:type" content="article">
<meta property="og:title" content="{esc(heading)}">
<meta property="og:description" content="{esc(desc)}">
{f'<meta property="og:url" content="{canonical}">' if canonical else ''}
<link rel="manifest" href="{root}manifest.webmanifest">
<link rel="icon" type="image/svg+xml" href="{root}assets/icon.svg">
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&family=Outfit:wght@600;700;800&family=Noto+Sans+Devanagari:wght@400;600;700&display=swap" rel="stylesheet">
<script type="module" src="https://unpkg.com/ionicons@7.1.0/dist/ionicons/ionicons.esm.js"></script>
<link rel="stylesheet" href="{root}css/style.css">
<link rel="stylesheet" href="{root}css/components.css">
<script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
<script>mermaid.initialize({{startOnLoad:true,theme:'dark',securityLevel:'loose'}});</script>
<style>
.seo-wrap{{max-width:820px;margin:0 auto;padding:5.5rem 1rem 4rem}}
.seo-section{{margin:2.5rem 0}}
.seo-section h2{{font-family:'Outfit',sans-serif;font-size:1.4rem;margin-bottom:1rem;padding-bottom:.5rem;border-bottom:2px solid var(--accent-surface);color:var(--accent-light)}}
.seo-head h1{{font-family:'Outfit',sans-serif;font-size:clamp(1.5rem,4vw,2.1rem);line-height:1.3}}
.seo-actions{{display:flex;gap:.6rem;flex-wrap:wrap;margin:1.25rem 0}}
.seo-toc{{background:var(--bg-secondary);border:1px solid var(--glass-border);border-radius:var(--radius-lg);padding:1rem 1.25rem;margin:1.5rem 0}}
.seo-toc a{{color:var(--accent-light);margin-right:1rem;font-size:.9rem;white-space:nowrap}}
</style>
</head>
<body>
<nav class="navbar"><div class="container navbar__inner">
<a href="{root}index.html" class="navbar__brand"><div class="navbar__logo"><ion-icon name="book-sharp"></ion-icon></div><span>Study Station</span></a>
<ul class="navbar__links">
<li><a href="{root}index.html" class="navbar__link">Home</a></li>
<li><a href="{root}chapters/index.html" class="navbar__link active">Chapters</a></li>
<li><a href="{root}jobs.html" class="navbar__link">Jobs</a></li>
</ul>
</div></nav>

<main class="seo-wrap">
<nav class="breadcrumb" aria-label="breadcrumb">
<a href="{root}index.html">Home</a> <span class="breadcrumb__sep">/</span>
<a href="{root}chapters/index.html">Chapters</a> <span class="breadcrumb__sep">/</span>
<span class="breadcrumb__current">{esc(subject_label)}</span>
</nav>

<header class="seo-head">
<span class="section__badge">{esc(level_label)} · {esc(subject_label)}</span>
<h1>{esc(heading)}</h1>
<p style="color:var(--text-secondary);margin-top:.5rem">{esc(intro)}</p>
<div class="seo-actions">
<a class="btn btn--primary" href="{root}index.html#books"><ion-icon name="book-outline"></ion-icon>{esc(reader_cta)}</a>
<a class="btn" style="background:var(--bg-tertiary);color:var(--text-primary)" href="{root}{alt_rel}" hreflang="{other}">{esc(other_lang_label)}</a>
</div>
</header>

<nav class="seo-toc">{''.join(f'<a href="#{t}">{esc(l[lang])}</a>' for t, l in SEO_TAB_ORDER if rendered_map.get((t, lang)) and 'empty-state' not in rendered_map.get((t, lang), ''))}</nav>

{body}
</main>

<footer class="ssg-footer" style="border-top:1px solid var(--glass-border);padding:2rem 1rem 4rem;text-align:center;color:var(--text-secondary);font-size:.85rem">
<p><strong>Study Station</strong> — {'मुफ़्त अध्ययन सामग्री और सरकारी नौकरी अलर्ट' if is_hi else 'Free study material &amp; sarkari job alerts'}.</p>
</footer>
<script src="{root}js/theme.js"></script>
</body>
</html>
'''

# ========== MAIN ==========

def build_subject(cfg):
    """Compile one subject's chapters and write its _index.json."""
    base = cfg["base"]
    out_dir = os.path.join(WEBSITE_BOOKS, cfg["level_slug"], cfg["out_slug"])
    os.makedirs(out_dir, exist_ok=True)

    index_data = []
    generated = 0
    print(f"\n▶ Subject: {cfg['subject_en']} ({cfg['level_slug']})")

    for num, slug, folder_name, name_hi, name_en in cfg["chapters"]:
        folder = os.path.join(base, f"Chapter_{num}_{folder_name}")
        hi_path = os.path.join(folder, "Content_hi.txt")
        is_ready = os.path.exists(hi_path) and os.path.getsize(hi_path) > 2000

        index_data.append({
            "num": int(num),
            "slug": slug,
            "name_hi": name_hi,
            "name_en": name_en,
            "status": "ready" if is_ready else "coming_soon"
        })

        if is_ready:
            print(f"  📖 Generating {slug}.html ...", end=" ")
            chapter_html, rendered_map = generate_chapter_html(
                num, slug, folder_name, name_hi, name_en,
                base, cfg["subject"], cfg["level_slug"])

            out_path = os.path.join(out_dir, f"{slug}.html")
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(chapter_html)

            # Crawlable standalone page per language (the SPA keeps using the
            # fragment above; these exist purely so search engines can read us).
            for lang in ('hi', 'en'):
                page = generate_seo_page(
                    lang, num, slug, name_hi, name_en,
                    cfg['subject_hi'] if lang == 'hi' else cfg['subject_en'],
                    cfg['level_label'], cfg['level_slug'], cfg['out_slug'],
                    rendered_map)
                rel = seo_page_rel(lang, cfg['level_slug'], cfg['out_slug'], slug)
                seo_path = os.path.join(WEBSITE_DIR, rel)
                os.makedirs(os.path.dirname(seo_path), exist_ok=True)
                with open(seo_path, 'w', encoding='utf-8') as f:
                    f.write(page)
                SEO_PAGES.append({
                    'rel': rel, 'lang': lang, 'num': int(num), 'slug': slug,
                    'name': name_hi if lang == 'hi' else name_en,
                    'subject': cfg['subject_hi'] if lang == 'hi' else cfg['subject_en'],
                    'level': cfg['level_label'],
                })

            size_kb = os.path.getsize(out_path) / 1024
            print(f"✅ ({size_kb:.1f} KB + 2 SEO pages)")
            generated += 1

    index_path = os.path.join(out_dir, "_index.json")
    with open(index_path, 'w', encoding='utf-8') as f:
        json.dump({
            "subject": cfg["subject"],
            "subject_hi": cfg["subject_hi"],
            "subject_en": cfg["subject_en"],
            "level": cfg["level_slug"],
            "chapters": index_data
        }, f, ensure_ascii=False, indent=2)

    print(f"  → {generated}/{len(cfg['chapters'])} chapters ready in {cfg['out_slug']}/")
    return generated


def build_chapters_hub():
    """Write chapters/index.html linking every SEO page.

    Without this hub nothing links to the chapter pages, so a crawler could
    never discover them. It also lets build_website.py pick them up for the
    sitemap via chapters/_pages.json.
    """
    hub_dir = os.path.join(WEBSITE_DIR, 'chapters')
    os.makedirs(hub_dir, exist_ok=True)

    # Group by subject for a readable hub
    groups = {}
    for p in SEO_PAGES:
        groups.setdefault((p['level'], p['subject'], p['lang']), []).append(p)

    blocks = []
    for (level, subject, lang), pages in sorted(groups.items()):
        pages.sort(key=lambda x: x['num'])
        links = ''.join(
            f'<li><a class="footer__link" href="{p["rel"].replace("chapters/", "", 1)}">'
            f'{p["num"]}. {esc(p["name"])}</a></li>' for p in pages)
        blocks.append(
            f'<section class="seo-section"><h2>{esc(subject)} — {esc(level)} '
            f'({"हिंदी" if lang == "hi" else "English"})</h2>'
            f'<ul class="footer__links" style="columns:2;gap:1rem">{links}</ul></section>')

    canonical = f"{SITE_URL}/chapters/index.html" if SITE_URL else None
    html_doc = f'''<!DOCTYPE html>
<html lang="hi" data-theme="dark">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>All Chapters — Free Notes, Tricks &amp; Practice | Study Station</title>
<meta name="description" content="सभी अध्याय एक जगह — गणित और तर्कशक्ति के मुफ़्त नोट्स, माइंड मैप, शॉर्ट ट्रिक्स और अभ्यास प्रश्न (हिंदी + English).">
<meta name="robots" content="index, follow">
<meta name="theme-color" content="#8B5CF6">
{f'<link rel="canonical" href="{canonical}">' if canonical else ''}
<link rel="manifest" href="../manifest.webmanifest">
<link rel="icon" type="image/svg+xml" href="../assets/icon.svg">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&family=Outfit:wght@600;700;800&family=Noto+Sans+Devanagari:wght@400;600;700&display=swap" rel="stylesheet">
<script type="module" src="https://unpkg.com/ionicons@7.1.0/dist/ionicons/ionicons.esm.js"></script>
<link rel="stylesheet" href="../css/style.css">
<link rel="stylesheet" href="../css/components.css">
<style>.seo-wrap{{max-width:900px;margin:0 auto;padding:5.5rem 1rem 4rem}}
.seo-section{{margin:2rem 0}}
.seo-section h2{{font-family:'Outfit',sans-serif;font-size:1.25rem;margin-bottom:.9rem;padding-bottom:.4rem;border-bottom:2px solid var(--accent-surface);color:var(--accent-light)}}</style>
</head>
<body>
<nav class="navbar"><div class="container navbar__inner">
<a href="../index.html" class="navbar__brand"><div class="navbar__logo"><ion-icon name="book-sharp"></ion-icon></div><span>Study Station</span></a>
<ul class="navbar__links">
<li><a href="../index.html" class="navbar__link">Home</a></li>
<li><a href="index.html" class="navbar__link active">Chapters</a></li>
<li><a href="../jobs.html" class="navbar__link">Jobs</a></li>
</ul>
</div></nav>
<main class="seo-wrap">
<header>
<span class="section__badge"><ion-icon name="library-outline"></ion-icon> All Chapters</span>
<h1 style="font-family:'Outfit',sans-serif;font-size:clamp(1.5rem,4vw,2.1rem)">सभी अध्याय / All Chapters</h1>
<p style="color:var(--text-secondary);margin-top:.5rem">गणित और तर्कशक्ति — मुफ़्त नोट्स, माइंड मैप, शॉर्ट ट्रिक्स और अभ्यास प्रश्न। Free notes, mind maps, short tricks and practice questions.</p>
</header>
{''.join(blocks)}
</main>
<footer class="ssg-footer" style="border-top:1px solid var(--glass-border);padding:2rem 1rem 4rem;text-align:center;color:var(--text-secondary);font-size:.85rem">
<p><strong>Study Station</strong> — मुफ़्त अध्ययन सामग्री और सरकारी नौकरी अलर्ट।</p>
</footer>
<script src="../js/theme.js"></script>
</body>
</html>
'''
    with open(os.path.join(hub_dir, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(html_doc)

    # Handoff for the sitemap builder in build_website.py
    with open(os.path.join(hub_dir, '_pages.json'), 'w', encoding='utf-8') as f:
        json.dump(['chapters/index.html'] + [p['rel'] for p in SEO_PAGES], f, indent=1)

    print(f"\n🔎 SEO: {len(SEO_PAGES)} standalone chapter pages + hub (chapters/index.html)")


def main():
    total = 0
    for cfg in SUBJECTS:
        total += build_subject(cfg)

    build_chapters_hub()

    print(f"\n{'='*50}")
    print(f"✅ Done! {total} chapter HTML files generated across {len(SUBJECTS)} subjects")
    print(f"{'='*50}")

if __name__ == "__main__":
    main()
