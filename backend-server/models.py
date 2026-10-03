from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class StudyContent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50)) # NOTES, SUMMARY, FORMULA
    class_level = db.Column(db.Integer)
    board = db.Column(db.String(50))
    subject = db.Column(db.String(100))
    subject_icon = db.Column(db.String(10))
    chapter_number = db.Column(db.Integer)
    chapter_name = db.Column(db.String(200))
    content_text = db.Column(db.Text)
    pdf_url = db.Column(db.String(500))
    difficulty = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class PracticeQuestion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_text = db.Column(db.Text, nullable=False)
    option_a = db.Column(db.String(255))
    option_b = db.Column(db.String(255))
    option_c = db.Column(db.String(255))
    option_d = db.Column(db.String(255))
    correct_answer = db.Column(db.String(1)) # A, B, C, or D
    explanation = db.Column(db.Text)
    class_level = db.Column(db.Integer)
    subject = db.Column(db.String(100))
    chapter_number = db.Column(db.Integer)
    chapter = db.Column(db.String(100))
    exam_name = db.Column(db.String(100))
    year = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class JobAlert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_type = db.Column(db.String(50), default="LATEST_JOB") # LATEST_JOB, ADMIT_CARD, RESULT, SYLLABUS, ANSWER_KEY
    title = db.Column(db.String(255), nullable=False)
    organization = db.Column(db.String(255))
    post_name = db.Column(db.String(255))
    vacancies = db.Column(db.String(100))
    eligibility = db.Column(db.Text)
    last_date = db.Column(db.String(100))
    
    # New Detailed Fields (SarkariResult style)
    application_fee = db.Column(db.Text) # JSON string: {"General/OBC": "100", "SC/ST": "0"}
    important_dates = db.Column(db.Text) # JSON string: {"Start Date": "01/01/2026", "Last Date": "31/01/2026"}
    age_limit = db.Column(db.Text) # String: "18 to 27 Years"
    vacancy_details = db.Column(db.Text) # JSON array of dicts for category-wise vacancy
    
    application_url = db.Column(db.String(500))
    official_url = db.Column(db.String(500))
    description = db.Column(db.Text)
    category = db.Column(db.String(100)) # GOVT, PRIVATE, BANKING
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class SystemSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    setting_key = db.Column(db.String(100), unique=True, nullable=False)
    setting_value = db.Column(db.String(500))
    description = db.Column(db.String(255))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class PreviousYearPaper(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    exam_name = db.Column(db.String(200), nullable=False) # e.g., "SSC CGL"
    year = db.Column(db.String(50)) # e.g., "2023"
    paper_title = db.Column(db.String(255)) # e.g., "Tier 1 Shift 1"
    question_pdf_url = db.Column(db.String(500))
    answer_key_url = db.Column(db.String(500))
    category = db.Column(db.String(100)) # e.g., SSC, BANKING, UPSC, STATE_PSC
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ==========================================
# 📚 BOOK CREATION SYSTEM MODELS
# ==========================================

class Book(db.Model):
    """एक पूरी पुस्तक (e.g., Math Master Book for SSC)"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    subtitle = db.Column(db.String(255))
    slug = db.Column(db.String(255), unique=True)           # URL-friendly name
    description = db.Column(db.Text)
    target_exam = db.Column(db.String(100))                 # SSC CGL, UPSC, Banking, Board
    target_level = db.Column(db.String(50))                 # 10th, 12th, Graduate
    subject = db.Column(db.String(100))
    cover_color = db.Column(db.String(7), default='#673AB7') # Hex color for cover
    icon = db.Column(db.String(10), default='📐')
    status = db.Column(db.String(20), default='draft')      # draft, generating, review, published
    total_chapters = db.Column(db.Integer, default=0)
    version = db.Column(db.String(10), default='1.0')
    is_premium = db.Column(db.Boolean, default=False)       # Subscription-gated
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    chapters = db.relationship('BookChapter', backref='book', lazy=True, order_by='BookChapter.order')

class BookChapter(db.Model):
    """पुस्तक का एक अध्याय — Cognitive Science modules embedded"""
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    order = db.Column(db.Integer, nullable=False)
    title_en = db.Column(db.String(255), nullable=False)    # English title
    title_hi = db.Column(db.String(255))                    # Hindi title

    # === मुख्य सामग्री (Core Content) ===
    content_en = db.Column(db.Text)                         # English content (Markdown)
    content_hi = db.Column(db.Text)                         # Hindi content (Markdown)

    # === मनोवैज्ञानिक मॉड्यूल (Cognitive Science Modules) ===
    feynman_en = db.Column(db.Text)                         # Feynman Technique — simple explanation (EN)
    feynman_hi = db.Column(db.Text)                         # Feynman Technique — simple explanation (HI)
    mind_map_data = db.Column(db.Text)                      # JSON — nodes/edges for mind map SVG
    retrieval_prompts_en = db.Column(db.Text)               # JSON — Active Recall questions (EN)
    retrieval_prompts_hi = db.Column(db.Text)               # JSON — Active Recall questions (HI)
    spaced_cards_en = db.Column(db.Text)                    # JSON — Flashcards for spaced repetition (EN)
    spaced_cards_hi = db.Column(db.Text)                    # JSON — Flashcards for spaced repetition (HI)
    key_formulas = db.Column(db.Text)                       # JSON — Math formulas (LaTeX/rendered)

    # === PYQ एकीकरण ===
    pyq_inline = db.Column(db.Text)                         # JSON — [{question, year, exam, answer}]
    pyq_weightage = db.Column(db.Text)                      # JSON — {exam: count} chart data
    practice_questions_en = db.Column(db.Text)              # JSON — [{question, options, answer, solution, section}]
    practice_questions_hi = db.Column(db.Text)              # JSON — [{question, options, answer, solution, section}]
    difficulty_level = db.Column(db.String(20), default='intermediate')  # basic, intermediate, advanced

    # === मेटाडेटा ===
    word_count = db.Column(db.Integer, default=0)
    estimated_read_time = db.Column(db.Integer)             # minutes
    cognitive_load_score = db.Column(db.Float)              # 1-10 scale (low = better)
    status = db.Column(db.String(20), default='draft')      # draft, generating, ready, published
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class PYQAnalysis(db.Model):
    """PYQ विश्लेषण — विषय-वार भार (Topic Weightage Analysis)"""
    id = db.Column(db.Integer, primary_key=True)
    exam_name = db.Column(db.String(100), nullable=False)   # SSC CGL, UPSC, etc.
    subject = db.Column(db.String(100), nullable=False)     # Mathematics
    topic = db.Column(db.String(200), nullable=False)       # Profit & Loss, Trigonometry
    year = db.Column(db.Integer)
    frequency = db.Column(db.Integer, default=0)            # How many times asked
    difficulty = db.Column(db.String(20))                   # Easy, Medium, Hard
    question_type = db.Column(db.String(50))                # MCQ, Calculation, Data Interp.
    priority_score = db.Column(db.Float, default=50.0)      # AI-computed 1-100
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class StudentProgress(db.Model):
    """छात्र प्रगति — SM-2 Spaced Repetition Tracking"""
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(100), nullable=False)  # Browser fingerprint / login ID
    chapter_id = db.Column(db.Integer, db.ForeignKey('book_chapter.id'), nullable=False)
    last_reviewed = db.Column(db.DateTime)
    next_review = db.Column(db.DateTime)
    easiness_factor = db.Column(db.Float, default=2.5)      # SM-2 EF (min 1.3)
    interval_days = db.Column(db.Integer, default=1)
    repetition_count = db.Column(db.Integer, default=0)
    score = db.Column(db.Float, default=0.0)                # 0-100 last quiz score
    total_time_spent = db.Column(db.Integer, default=0)     # seconds
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
