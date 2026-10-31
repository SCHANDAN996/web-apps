"""
📚 Book Builder API — Study Station
CRUD + AI Generation + Spaced Repetition endpoints
"""
import json
import re
from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request, render_template
from models import db, Book, BookChapter, PYQAnalysis, StudentProgress
from security import rate_limit

book_bp = Blueprint('book', __name__)

# ==========================================
# HELPER: Slug generator
# ==========================================
def generate_slug(title):
    slug = re.sub(r'[^a-zA-Z0-9\s-]', '', title.lower())
    slug = re.sub(r'[\s]+', '-', slug.strip())
    return slug

# ==========================================
# ADMIN: Book Builder Dashboard
# ==========================================
@book_bp.route('/admin/books')
def admin_books():
    books = Book.query.order_by(Book.created_at.desc()).all()
    return render_template('book_builder.html', books=books)

@book_bp.route('/admin/books/<int:book_id>')
def admin_book_detail(book_id):
    book = Book.query.get_or_404(book_id)
    return render_template('book_builder.html', books=Book.query.all(), active_book=book)

# ==========================================
# API: Book CRUD
# ==========================================

@book_bp.route('/api/books', methods=['GET'])
def list_books():
    status = request.args.get('status')
    query = Book.query
    if status:
        query = query.filter_by(status=status)
    books = query.order_by(Book.created_at.desc()).all()
    
    result = []
    for b in books:
        result.append({
            'id': b.id,
            'title': b.title,
            'subtitle': b.subtitle,
            'slug': b.slug,
            'description': b.description,
            'targetExam': b.target_exam,
            'targetLevel': b.target_level,
            'subject': b.subject,
            'coverColor': b.cover_color,
            'icon': b.icon,
            'status': b.status,
            'totalChapters': b.total_chapters,
            'chaptersDone': len([c for c in b.chapters if c.status == 'ready']),
            'version': b.version,
            'isPremium': b.is_premium,
            'createdAt': b.created_at.isoformat() if b.created_at else None,
        })
    return jsonify({'success': True, 'data': result})

@book_bp.route('/api/books', methods=['POST'])
def create_book():
    data = request.json
    title = data.get('title', '').strip()
    if not title:
        return jsonify({'success': False, 'error': 'Title is required'}), 400
    
    book = Book(
        title=title,
        subtitle=data.get('subtitle', ''),
        slug=generate_slug(title),
        description=data.get('description', ''),
        target_exam=data.get('targetExam', ''),
        target_level=data.get('targetLevel', ''),
        subject=data.get('subject', ''),
        cover_color=data.get('coverColor', '#673AB7'),
        icon=data.get('icon', '📐'),
        is_premium=data.get('isPremium', False),
    )
    db.session.add(book)
    db.session.commit()
    return jsonify({'success': True, 'id': book.id})

@book_bp.route('/api/books/<int:book_id>', methods=['GET'])
def get_book(book_id):
    book = Book.query.get_or_404(book_id)
    chapters = []
    for ch in book.chapters:
        chapters.append({
            'id': ch.id,
            'order': ch.order,
            'titleEn': ch.title_en,
            'titleHi': ch.title_hi,
            'status': ch.status,
            'difficultyLevel': ch.difficulty_level,
            'wordCount': ch.word_count,
            'estimatedReadTime': ch.estimated_read_time,
            'cognitiveLoadScore': ch.cognitive_load_score,
            'hasFeynman': bool(ch.feynman_en),
            'hasMindMap': bool(ch.mind_map_data),
            'hasRecallPrompts': bool(ch.retrieval_prompts_en),
            'hasSpacedCards': bool(ch.spaced_cards_en),
            'hasPYQ': bool(ch.pyq_inline),
            'hasPracticeEn': bool(ch.practice_questions_en),
            'hasPracticeHi': bool(ch.practice_questions_hi),
            'practiceCountEn': len(json.loads(ch.practice_questions_en)) if ch.practice_questions_en else 0,
            'practiceCountHi': len(json.loads(ch.practice_questions_hi)) if ch.practice_questions_hi else 0,
        })
    
    return jsonify({
        'success': True,
        'data': {
            'id': book.id,
            'title': book.title,
            'subtitle': book.subtitle,
            'slug': book.slug,
            'description': book.description,
            'targetExam': book.target_exam,
            'targetLevel': book.target_level,
            'subject': book.subject,
            'coverColor': book.cover_color,
            'icon': book.icon,
            'status': book.status,
            'totalChapters': book.total_chapters,
            'version': book.version,
            'isPremium': book.is_premium,
            'chapters': chapters
        }
    })

@book_bp.route('/api/books/<int:book_id>', methods=['PUT'])
def update_book(book_id):
    book = Book.query.get_or_404(book_id)
    data = request.json
    
    if 'title' in data: book.title = data['title']
    if 'subtitle' in data: book.subtitle = data['subtitle']
    if 'description' in data: book.description = data['description']
    if 'targetExam' in data: book.target_exam = data['targetExam']
    if 'targetLevel' in data: book.target_level = data['targetLevel']
    if 'subject' in data: book.subject = data['subject']
    if 'coverColor' in data: book.cover_color = data['coverColor']
    if 'icon' in data: book.icon = data['icon']
    if 'status' in data: book.status = data['status']
    if 'isPremium' in data: book.is_premium = data['isPremium']
    
    db.session.commit()
    return jsonify({'success': True})

@book_bp.route('/api/books/<int:book_id>', methods=['DELETE'])
def delete_book(book_id):
    book = Book.query.get_or_404(book_id)
    # Delete all chapters first
    BookChapter.query.filter_by(book_id=book_id).delete()
    db.session.delete(book)
    db.session.commit()
    return jsonify({'success': True})

# ==========================================
# API: Chapter CRUD
# ==========================================

@book_bp.route('/api/books/<int:book_id>/chapters', methods=['POST'])
def add_chapter(book_id):
    book = Book.query.get_or_404(book_id)
    data = request.json
    
    # Get next order number
    max_order = db.session.query(db.func.max(BookChapter.order)).filter_by(book_id=book_id).scalar() or 0
    
    ch = BookChapter(
        book_id=book_id,
        order=max_order + 1,
        title_en=data.get('titleEn', 'Untitled Chapter'),
        title_hi=data.get('titleHi', ''),
        difficulty_level=data.get('difficultyLevel', 'intermediate'),
    )
    db.session.add(ch)
    book.total_chapters = max_order + 1
    db.session.commit()
    return jsonify({'success': True, 'id': ch.id})

@book_bp.route('/api/chapters/<int:chapter_id>', methods=['GET'])
def get_chapter(chapter_id):
    ch = BookChapter.query.get_or_404(chapter_id)
    
    return jsonify({
        'success': True,
        'data': {
            'id': ch.id,
            'bookId': ch.book_id,
            'order': ch.order,
            'titleEn': ch.title_en,
            'titleHi': ch.title_hi,
            'contentEn': ch.content_en,
            'contentHi': ch.content_hi,
            'feynmanEn': ch.feynman_en,
            'feynmanHi': ch.feynman_hi,
            'mindMapData': json.loads(ch.mind_map_data) if ch.mind_map_data else None,
            'retrievalPromptsEn': json.loads(ch.retrieval_prompts_en) if ch.retrieval_prompts_en else [],
            'retrievalPromptsHi': json.loads(ch.retrieval_prompts_hi) if ch.retrieval_prompts_hi else [],
            'spacedCardsEn': json.loads(ch.spaced_cards_en) if ch.spaced_cards_en else [],
            'spacedCardsHi': json.loads(ch.spaced_cards_hi) if ch.spaced_cards_hi else [],
            'keyFormulas': json.loads(ch.key_formulas) if ch.key_formulas else [],
            'pyqInline': json.loads(ch.pyq_inline) if ch.pyq_inline else [],
            'pyqWeightage': json.loads(ch.pyq_weightage) if ch.pyq_weightage else {},
            'practiceQuestionsEn': json.loads(ch.practice_questions_en) if ch.practice_questions_en else [],
            'practiceQuestionsHi': json.loads(ch.practice_questions_hi) if ch.practice_questions_hi else [],
            'difficultyLevel': ch.difficulty_level,
            'wordCount': ch.word_count,
            'estimatedReadTime': ch.estimated_read_time,
            'cognitiveLoadScore': ch.cognitive_load_score,
            'status': ch.status,
        }
    })

@book_bp.route('/api/chapters/<int:chapter_id>', methods=['PUT'])
def update_chapter(chapter_id):
    ch = BookChapter.query.get_or_404(chapter_id)
    data = request.json
    
    if 'titleEn' in data: ch.title_en = data['titleEn']
    if 'titleHi' in data: ch.title_hi = data['titleHi']
    if 'contentEn' in data: ch.content_en = data['contentEn']
    if 'contentHi' in data: ch.content_hi = data['contentHi']
    if 'feynmanEn' in data: ch.feynman_en = data['feynmanEn']
    if 'feynmanHi' in data: ch.feynman_hi = data['feynmanHi']
    if 'mindMapData' in data: ch.mind_map_data = json.dumps(data['mindMapData'])
    if 'retrievalPromptsEn' in data: ch.retrieval_prompts_en = json.dumps(data['retrievalPromptsEn'])
    if 'retrievalPromptsHi' in data: ch.retrieval_prompts_hi = json.dumps(data['retrievalPromptsHi'])
    if 'spacedCardsEn' in data: ch.spaced_cards_en = json.dumps(data['spacedCardsEn'])
    if 'spacedCardsHi' in data: ch.spaced_cards_hi = json.dumps(data['spacedCardsHi'])
    if 'keyFormulas' in data: ch.key_formulas = json.dumps(data['keyFormulas'])
    if 'pyqInline' in data: ch.pyq_inline = json.dumps(data['pyqInline'])
    if 'pyqWeightage' in data: ch.pyq_weightage = json.dumps(data['pyqWeightage'])
    if 'practiceQuestionsEn' in data: ch.practice_questions_en = json.dumps(data['practiceQuestionsEn'])
    if 'practiceQuestionsHi' in data: ch.practice_questions_hi = json.dumps(data['practiceQuestionsHi'])
    if 'difficultyLevel' in data: ch.difficulty_level = data['difficultyLevel']
    if 'status' in data: ch.status = data['status']
    
    # Auto-compute word count and read time
    content = (ch.content_en or '') + (ch.content_hi or '')
    ch.word_count = len(content.split())
    ch.estimated_read_time = max(1, ch.word_count // 200)  # ~200 words/min reading speed
    
    db.session.commit()
    return jsonify({'success': True})

@book_bp.route('/api/chapters/<int:chapter_id>', methods=['DELETE'])
def delete_chapter(chapter_id):
    ch = BookChapter.query.get_or_404(chapter_id)
    book = Book.query.get(ch.book_id)
    db.session.delete(ch)
    if book:
        book.total_chapters = BookChapter.query.filter_by(book_id=book.id).count() - 1
    db.session.commit()
    return jsonify({'success': True})

# ==========================================
# API: AI Chapter Generation
# ==========================================

@book_bp.route('/api/chapters/<int:chapter_id>/generate', methods=['POST'])
def generate_chapter(chapter_id):
    """AI-powered chapter content generation using Gemini"""
    ch = BookChapter.query.get_or_404(chapter_id)
    book = Book.query.get(ch.book_id)
    
    try:
        from book_agents import generate_full_chapter
        result = generate_full_chapter(
            topic=ch.title_en,
            topic_hi=ch.title_hi or ch.title_en,
            subject=book.subject if book else 'Mathematics',
            target_exam=book.target_exam if book else 'SSC',
            target_level=book.target_level if book else 'Graduate',
            difficulty=ch.difficulty_level
        )
        
        if result and result.get('success'):
            data = result['data']
            ch.content_en = data.get('content_en', '')
            ch.content_hi = data.get('content_hi', '')
            ch.feynman_en = data.get('feynman_en', '')
            ch.feynman_hi = data.get('feynman_hi', '')
            ch.mind_map_data = json.dumps(data.get('mind_map', {}))
            ch.retrieval_prompts_en = json.dumps(data.get('retrieval_prompts_en', []))
            ch.retrieval_prompts_hi = json.dumps(data.get('retrieval_prompts_hi', []))
            ch.spaced_cards_en = json.dumps(data.get('spaced_cards_en', []))
            ch.spaced_cards_hi = json.dumps(data.get('spaced_cards_hi', []))
            ch.key_formulas = json.dumps(data.get('key_formulas', []))
            ch.pyq_inline = json.dumps(data.get('pyq_inline', []))
            ch.pyq_weightage = json.dumps(data.get('pyq_weightage', {}))
            ch.cognitive_load_score = data.get('cognitive_load_score', 5.0)
            
            content = (ch.content_en or '') + (ch.content_hi or '')
            ch.word_count = len(content.split())
            ch.estimated_read_time = max(1, ch.word_count // 200)
            ch.status = 'ready'
            
            db.session.commit()
            return jsonify({'success': True, 'message': 'Chapter generated successfully'})
        else:
            return jsonify({'success': False, 'error': result.get('error', 'AI generation failed')})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@book_bp.route('/api/books/<int:book_id>/generate-all', methods=['POST'])
def generate_all_chapters(book_id):
    """Generate all draft chapters for a book"""
    book = Book.query.get_or_404(book_id)
    chapters = BookChapter.query.filter_by(book_id=book_id, status='draft').all()
    
    results = []
    for ch in chapters:
        ch.status = 'generating'
        db.session.commit()
        
        try:
            from book_agents import generate_full_chapter
            result = generate_full_chapter(
                topic=ch.title_en,
                topic_hi=ch.title_hi or ch.title_en,
                subject=book.subject or 'Mathematics',
                target_exam=book.target_exam or 'SSC',
                target_level=book.target_level or 'Graduate',
                difficulty=ch.difficulty_level
            )
            
            if result and result.get('success'):
                data = result['data']
                ch.content_en = data.get('content_en', '')
                ch.content_hi = data.get('content_hi', '')
                ch.feynman_en = data.get('feynman_en', '')
                ch.feynman_hi = data.get('feynman_hi', '')
                ch.mind_map_data = json.dumps(data.get('mind_map', {}))
                ch.retrieval_prompts_en = json.dumps(data.get('retrieval_prompts_en', []))
                ch.retrieval_prompts_hi = json.dumps(data.get('retrieval_prompts_hi', []))
                ch.spaced_cards_en = json.dumps(data.get('spaced_cards_en', []))
                ch.spaced_cards_hi = json.dumps(data.get('spaced_cards_hi', []))
                ch.key_formulas = json.dumps(data.get('key_formulas', []))
                ch.pyq_inline = json.dumps(data.get('pyq_inline', []))
                ch.pyq_weightage = json.dumps(data.get('pyq_weightage', {}))
                ch.cognitive_load_score = data.get('cognitive_load_score', 5.0)
                content = (ch.content_en or '') + (ch.content_hi or '')
                ch.word_count = len(content.split())
                ch.estimated_read_time = max(1, ch.word_count // 200)
                ch.status = 'ready'
                results.append({'chapter': ch.title_en, 'status': 'success'})
            else:
                ch.status = 'draft'
                results.append({'chapter': ch.title_en, 'status': 'failed', 'error': result.get('error', '')})
        except Exception as e:
            ch.status = 'draft'
            results.append({'chapter': ch.title_en, 'status': 'failed', 'error': str(e)})
        
        db.session.commit()
    
    # Update book status
    ready_count = BookChapter.query.filter_by(book_id=book_id, status='ready').count()
    total = BookChapter.query.filter_by(book_id=book_id).count()
    if ready_count == total and total > 0:
        book.status = 'review'
    
    db.session.commit()
    return jsonify({'success': True, 'results': results})

# ==========================================
# API: Spaced Repetition (SM-2)
# ==========================================

@book_bp.route('/api/progress', methods=['POST'])
@rate_limit('progress', [(60, 60)])
def update_progress():
    """Update student's spaced repetition progress using SM-2 algorithm"""
    data = request.get_json(silent=True) or {}
    student_id = str(data.get('studentId') or 'anonymous')[:100]
    try:
        chapter_id = int(data.get('chapterId'))
        quality = int(data.get('quality', 3))  # 0-5 scale
        score = data.get('score')
        score = None if score is None else float(score)
        time_spent = max(0, min(int(data.get('timeSpent', 0)), 24 * 60 * 60))
    except (TypeError, ValueError):
        return jsonify({'success': False, 'error': 'chapterId, quality, score and timeSpent must be numbers'}), 400
    if not 0 <= quality <= 5:
        return jsonify({'success': False, 'error': 'quality must be between 0 and 5'}), 400
    if not db.session.get(BookChapter, chapter_id):
        return jsonify({'success': False, 'error': 'Chapter not found'}), 404
    
    progress = StudentProgress.query.filter_by(
        student_id=student_id, chapter_id=chapter_id
    ).first()
    
    if not progress:
        # Column defaults only apply on flush — set them now so SM-2 math works.
        progress = StudentProgress(student_id=student_id, chapter_id=chapter_id,
                                   easiness_factor=2.5, interval_days=1,
                                   repetition_count=0, score=0.0, total_time_spent=0)
        db.session.add(progress)
    
    # SM-2 Algorithm
    if quality >= 3:
        if progress.repetition_count == 0:
            progress.interval_days = 1
        elif progress.repetition_count == 1:
            progress.interval_days = 6
        else:
            progress.interval_days = round(progress.interval_days * progress.easiness_factor)
        progress.repetition_count += 1
    else:
        progress.repetition_count = 0
        progress.interval_days = 1
    
    # Update easiness factor (min 1.3)
    progress.easiness_factor = max(1.3,
        progress.easiness_factor + 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)
    )
    
    progress.last_reviewed = datetime.utcnow()
    progress.next_review = datetime.utcnow() + timedelta(days=progress.interval_days)
    if score is not None:
        progress.score = score
    progress.total_time_spent = (progress.total_time_spent or 0) + time_spent
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'nextReview': progress.next_review.isoformat(),
        'intervalDays': progress.interval_days,
        'easinessFactor': round(progress.easiness_factor, 2),
        'repetitionCount': progress.repetition_count
    })

@book_bp.route('/api/progress/<string:student_id>', methods=['GET'])
def get_progress(student_id):
    """Get all progress for a student"""
    progress_list = StudentProgress.query.filter_by(student_id=student_id).all()
    result = []
    for p in progress_list:
        result.append({
            'chapterId': p.chapter_id,
            'lastReviewed': p.last_reviewed.isoformat() if p.last_reviewed else None,
            'nextReview': p.next_review.isoformat() if p.next_review else None,
            'intervalDays': p.interval_days,
            'repetitionCount': p.repetition_count,
            'score': p.score,
            'totalTimeSpent': p.total_time_spent
        })
    return jsonify({'success': True, 'data': result})

# ==========================================
# API: Practice Questions Import
# ==========================================

@book_bp.route('/api/chapters/<int:chapter_id>/questions', methods=['POST'])
def import_questions(chapter_id):
    """Import practice questions — accepts JSON array or raw text"""
    ch = BookChapter.query.get_or_404(chapter_id)
    data = request.json
    
    questions = data.get('questions', [])
    raw_text = data.get('rawText', '')
    
    if raw_text and not questions:
        # Smart text parser for formatted questions
        questions = _parse_questions_text(raw_text)
    
    if not questions:
        return jsonify({'success': False, 'error': 'No questions provided'}), 400
    
    lang = request.args.get('lang', 'en')
    
    if lang == 'hi':
        existing = json.loads(ch.practice_questions_hi) if ch.practice_questions_hi else []
        existing.extend(questions)
        ch.practice_questions_hi = json.dumps(existing, ensure_ascii=False)
    else:
        existing = json.loads(ch.practice_questions_en) if ch.practice_questions_en else []
        existing.extend(questions)
        ch.practice_questions_en = json.dumps(existing, ensure_ascii=False)
    
    db.session.commit()
    return jsonify({'success': True, 'count': len(questions), 'total': len(existing)})

@book_bp.route('/api/chapters/<int:chapter_id>/questions', methods=['GET'])
def get_questions(chapter_id):
    ch = BookChapter.query.get_or_404(chapter_id)
    lang = request.args.get('lang', 'en')
    
    if lang == 'hi':
        questions = json.loads(ch.practice_questions_hi) if ch.practice_questions_hi else []
    else:
        questions = json.loads(ch.practice_questions_en) if ch.practice_questions_en else []
        
    return jsonify({'success': True, 'data': questions, 'total': len(questions)})

@book_bp.route('/api/chapters/<int:chapter_id>/questions', methods=['DELETE'])
def clear_questions(chapter_id):
    ch = BookChapter.query.get_or_404(chapter_id)
    lang = request.args.get('lang', 'en')
    
    if lang == 'hi':
        ch.practice_questions_hi = None
    else:
        ch.practice_questions_en = None
        
    db.session.commit()
    return jsonify({'success': True})

def _parse_questions_text(text):
    """Smart parser: Converts formatted MCQ text to structured JSON"""
    questions = []
    current_q = None
    lines = text.strip().split('\n')
    section = 'General'
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Detect section headers
        if line.startswith('### ') or line.startswith('## '):
            section = line.lstrip('#').strip().split('(')[0].strip()
            continue
        
        # Detect question start: **1. ... or **101. ...
        q_match = re.match(r'\*\*(?:Q\.?\s*)?([\d]+)[.\)\s]\s*(.+?)\*\*', line)
        if q_match:
            if current_q and current_q.get('question'):
                questions.append(current_q)
            current_q = {
                'id': int(q_match.group(1)),
                'question': q_match.group(2).strip(),
                'options': [],
                'answer': '',
                'solution': '',
                'section': section
            }
            continue
        
        if not current_q:
            continue
        
        # Detect options: A) ... or A. ...
        opt_match = re.match(r'^([A-D])\s*[)\.]\s*(.+)', line)
        if opt_match:
            current_q['options'].append(opt_match.group(2).strip())
            continue
        
        # Detect answer: **Answer: B** or **Ans: B**
        ans_match = re.match(r'\*\*(?:Answer|Ans|Uttar)[:\s]*([A-D])\s*\*\*', line, re.IGNORECASE)
        if ans_match:
            current_q['answer'] = ans_match.group(1)
            continue
        
        # Simple answer line
        ans_match2 = re.match(r'\*\*(?:उत्तर|Answer)[:\s]*([A-D])\s*\*\*', line)
        if ans_match2:
            current_q['answer'] = ans_match2.group(1)
            continue
        
        # Detect solution
        sol_match = re.match(r'\*\*(?:Solution|समाधान|Explanation)[:\s]*\*\*\s*(.*)', line, re.IGNORECASE)
        if sol_match:
            current_q['solution'] = sol_match.group(1).strip()
            continue
        
        # If we're after answer, remaining text is solution continuation
        if current_q.get('answer') and line and not line.startswith('**'):
            if current_q['solution']:
                current_q['solution'] += ' ' + line
            else:
                current_q['solution'] = line
    
    # Don't forget the last question
    if current_q and current_q.get('question'):
        questions.append(current_q)
    
    return questions

# ==========================================
# PUBLIC: Book Reader Routes
# ==========================================

@book_bp.route('/book/<slug>')
def read_book(slug):
    book = Book.query.filter_by(slug=slug).first_or_404()
    return render_template('book_reader.html', book=book)
