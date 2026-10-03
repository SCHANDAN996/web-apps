import os
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from models import db, StudyContent, PracticeQuestion, JobAlert

app = Flask(__name__)
CORS(app)

# Configure SQLite Database for development
basedir = os.path.abspath(os.path.dirname(__name__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'study_station.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

db.init_app(app)
import json
app.jinja_env.filters['from_json'] = json.loads

# Register Book Builder Blueprint
from book_api import book_bp
app.register_blueprint(book_bp)

# Create tables
with app.app_context():
    db.create_all()

@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response

# ==========================================
# ADMIN PANEL ROUTES (Hostinger Style UI)
# ==========================================

@app.route('/')
def index():
    from flask import send_from_directory
    website_dir = os.path.abspath(os.path.join(basedir, '../website'))
    return send_from_directory(website_dir, 'index.html')

@app.route('/<path:filename>')
def serve_website(filename):
    if filename == 'study.html':
        from flask import redirect
        return redirect('/classes.html')
        
    from flask import send_from_directory
    website_dir = os.path.abspath(os.path.join(basedir, '../website'))
    # Only serve if it exists in the website dir, else 404
    if os.path.exists(os.path.join(website_dir, filename)):
        return send_from_directory(website_dir, filename)
    else:
        from flask import abort
        abort(404)

@app.route('/admin')
def admin_dashboard():
    stats = {
        'notes': StudyContent.query.count(),
        'questions': PracticeQuestion.query.count(),
        'jobs': JobAlert.query.count()
    }
    return render_template('dashboard.html', stats=stats)

@app.route('/admin/settings', methods=['GET', 'POST'])
def admin_settings():
    from models import SystemSettings
    import google.generativeai as genai
    
    if request.method == 'POST':
        # Save settings
        for key, value in request.form.items():
            setting = SystemSettings.query.filter_by(setting_key=key).first()
            if not setting:
                setting = SystemSettings(setting_key=key)
                db.session.add(setting)
            setting.setting_value = value
        db.session.commit()
    
    settings = get_all_settings()
    
    # Fetch available models using the first API key if it exists
    available_models = []
    api_keys_str = settings.get('gemini_api_keys', settings.get('gemini_api_key', ''))
    keys = [k.strip() for k in api_keys_str.split('\n') if k.strip()]
    if keys:
        try:
            genai.configure(api_key=keys[0])
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    available_models.append({'name': m.name, 'display_name': m.display_name})
        except Exception as e:
            print("Error fetching models:", e)
            
    return render_template('settings.html', settings=settings, available_models=available_models, success=(request.method == 'POST'))

@app.route('/admin/check_keys', methods=['GET'])
def check_api_keys():
    import google.generativeai as genai
    settings = get_all_settings()
    api_keys_str = settings.get('gemini_api_keys', settings.get('gemini_api_key', ''))
    keys = [k.strip() for k in api_keys_str.split('\n') if k.strip()]
    
    ai_model_name = settings.get('ai_model_name') or 'gemini-1.5-flash'
    
    if not keys:
        return jsonify({'success': False, 'message': 'No keys configured.'})
        
    status_list = []
    for key in keys:
        try:
            genai.configure(api_key=key)
            # Use the model they selected in settings
            model = genai.GenerativeModel(ai_model_name)
            # Test with a very small prompt
            response = model.generate_content("Say OK")
            status_list.append({'key': key, 'working': True, 'message': 'Active & Working'})
        except Exception as e:
            error_msg = str(e)
            if 'Quota' in error_msg or '429' in error_msg:
                msg = 'Quota Exceeded / Rate Limited'
            elif 'API_KEY_INVALID' in error_msg or '400' in error_msg:
                msg = 'Invalid API Key'
            else:
                msg = f"Error: {error_msg}"
            status_list.append({'key': key, 'working': False, 'message': msg})
            
    return jsonify({'success': True, 'status': status_list})

def get_all_settings():
    from models import SystemSettings
    settings_dict = {}
    for s in SystemSettings.query.all():
        settings_dict[s.setting_key] = s.setting_value
    return settings_dict

@app.route('/admin/automation', methods=['GET', 'POST'])
def admin_automation():
    from automation import trigger_auto_scrape
    if request.method == 'POST':
        url_to_scrape = request.form.get('url')
        result = trigger_auto_scrape(url_to_scrape)
        return render_template('automation.html', result=result)
    return render_template('automation.html')

@app.route('/admin/study')
def admin_study():
    notes = StudyContent.query.order_by(StudyContent.class_level, StudyContent.subject, StudyContent.chapter_number).all()
    return render_template('admin_study.html', notes=notes)

@app.route('/admin/study/update/<int:id>', methods=['POST'])
def admin_study_update(id):
    note = StudyContent.query.get_or_404(id)
    new_content = request.form.get('content_text')
    pdf_url = request.form.get('pdf_url')
    if new_content is not None:
        note.content_text = new_content
    if pdf_url is not None:
        note.pdf_url = pdf_url
    db.session.commit()
    from flask import redirect, url_for
    return redirect(url_for('admin_study'))

@app.route('/admin/publish', methods=['POST'])
def admin_publish():
    try:
        from build_website import build_ssg
        build_ssg()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/admin/study/generate/<int:id>', methods=['POST'])
def admin_study_generate(id):
    from ai_seeder import generate_chapter_data
    from models import PracticeQuestion
    
    chapter = StudyContent.query.get_or_404(id)
    try:
        result = generate_chapter_data(chapter.class_level, chapter.subject, chapter.title)
        
        if result and result.get("success"):
            data = result["data"]
            # Update notes
            chapter.content_text = data.get('notes', '')
            
            # Delete old mock questions for this exact chapter
            PracticeQuestion.query.filter_by(
                class_level=chapter.class_level, 
                subject=chapter.subject, 
                chapter_number=chapter.chapter_number
            ).delete()
            
            # Insert AI generated questions
            for q in data.get('questions', []):
                new_q = PracticeQuestion(
                    class_level=chapter.class_level,
                    subject=chapter.subject,
                    chapter_number=chapter.chapter_number,
                    chapter=chapter.title,
                    question_text=q.get('question_text', ''),
                    option_a=q.get('option_a', ''),
                    option_b=q.get('option_b', ''),
                    option_c=q.get('option_c', ''),
                    option_d=q.get('option_d', ''),
                    correct_answer=q.get('correct_answer', 'A'),
                    explanation=q.get('explanation', ''),
                    exam_name=f"Class {chapter.class_level} AI Test",
                    year=2024
                )
                db.session.add(new_q)
            
            db.session.commit()
            return jsonify({"success": True})
        else:
            error_details = result.get("error") if result else "Unknown AI error"
            return jsonify({"success": False, "error": f"AI Generation Failed: {error_details}"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

# ==========================================
# REST API ENDPOINTS (For Android App)
# ==========================================

@app.route('/api/study/content', methods=['GET'])
def get_study_content():
    class_level = request.args.get('class')
    subject = request.args.get('subject')
    
    query = StudyContent.query
    if class_level:
        query = query.filter_by(class_level=class_level)
    if subject:
        query = query.filter_by(subject=subject)
        
    contents = query.all()
    result = []
    for c in contents:
        result.append({
            'id': c.id,
            'title': c.title,
            'description': c.description,
            'category': c.category,
            'classLevel': c.class_level,
            'board': c.board,
            'subject': c.subject,
            'subjectIcon': c.subject_icon,
            'chapterNumber': c.chapter_number,
            'chapterName': c.chapter_name,
            'contentText': c.content_text,
            'pdfUrl': c.pdf_url,
            'difficulty': c.difficulty
        })
    return jsonify({'success': True, 'data': result})

@app.route('/api/practice/questions', methods=['GET'])
def get_practice_questions():
    exam = request.args.get('exam')
    query = PracticeQuestion.query
    if exam:
        query = query.filter_by(exam_name=exam)
        
    questions = query.all()
    result = []
    for q in questions:
        result.append({
            'id': q.id,
            'questionText': q.question_text,
            'options': {
                'A': q.option_a,
                'B': q.option_b,
                'C': q.option_c,
                'D': q.option_d
            },
            'correctAnswer': q.correct_answer,
            'explanation': q.explanation,
            'subject': q.subject,
            'examName': q.exam_name,
            'classLevel': q.class_level,
            'chapter': q.chapter
        })
    return jsonify({'success': True, 'data': result})

@app.route('/api/jobs/latest', methods=['GET'])
def get_latest_jobs():
    jobs = JobAlert.query.order_by(JobAlert.created_at.desc()).limit(20).all()
    result = []
    for j in jobs:
        result.append({
            'id': j.id,
            'title': j.title,
            'organization': j.organization,
            'postName': j.post_name,
            'vacancies': j.vacancies,
            'eligibility': j.eligibility,
            'lastDate': j.last_date,
            'applicationUrl': j.application_url,
            'category': j.category
        })
    return jsonify({'success': True, 'data': result})

@app.route('/api/chat', methods=['POST'])
def api_chat():
    from ai_seeder import get_setting
    import google.generativeai as genai
    
    data = request.json
    chapter_id = data.get('chapterId')
    user_message = data.get('message')
    
    if not chapter_id or not user_message:
        return jsonify({"success": False, "error": "Missing parameters"})
        
    chapter = StudyContent.query.get(chapter_id)
    if not chapter:
        return jsonify({"success": False, "error": "Chapter not found"})
        
    api_keys_str = get_setting('gemini_api_keys') or get_setting('gemini_api_key')
    if not api_keys_str:
        return jsonify({"success": False, "error": "AI API Key not configured"})
        
    keys = [k.strip() for k in api_keys_str.split('\n') if k.strip()]
    api_key = keys[0] if keys else None
    
    if not api_key:
        return jsonify({"success": False, "error": "Invalid API Key"})
        
    model_name = get_setting('ai_model_name') or 'gemini-flash-latest'
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)
        
        prompt = f"""
        You are an AI Tutor for Class {chapter.class_level} students learning the subject '{chapter.subject}'.
        The current chapter is '{chapter.chapter_name}'.
        
        Here are the official chapter notes for your reference:
        {chapter.content_text}
        
        The student has asked you this question:
        "{user_message}"
        
        Please provide a helpful, encouraging, and easy-to-understand answer suitable for a Class {chapter.class_level} student. Use simple language and emojis.
        """
        
        response = model.generate_content(prompt)
        return jsonify({"success": True, "reply": response.text.strip()})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

# ==========================================
# FRONTEND SSR ROUTES (Proper SEO Indexing)
# ==========================================
import urllib.parse
import re

@app.route('/study')
def frontend_study():
    # Get distinct classes
    classes_tuples = db.session.query(StudyContent.class_level).distinct().order_by(StudyContent.class_level).all()
    classes = [c[0] for c in classes_tuples if c[0] is not None]
    return render_template('frontend/study_classes.html', classes=classes)

@app.route('/study/class-<int:class_level>')
def frontend_subjects(class_level):
    # Get distinct subjects for the class and chapter count
    from sqlalchemy import func
    subjects_data = db.session.query(
        StudyContent.subject, 
        StudyContent.subject_icon, 
        func.count(StudyContent.id).label('count')
    ).filter_by(class_level=class_level).group_by(StudyContent.subject, StudyContent.subject_icon).all()
    
    subjects = []
    for s in subjects_data:
        subjects.append({
            'subject': s.subject,
            'icon': s.subject_icon or '📚',
            'count': s.count
        })
    return render_template('frontend/study_subjects.html', class_level=class_level, subjects=subjects)

@app.route('/study/class-<int:class_level>/<subject>')
def frontend_chapters(class_level, subject):
    decoded_subject = urllib.parse.unquote(subject)
    chapters = StudyContent.query.filter_by(class_level=class_level, subject=decoded_subject).order_by(StudyContent.chapter_number).all()
    if not chapters:
        from flask import abort
        abort(404)
    return render_template('frontend/study_chapters.html', class_level=class_level, subject=decoded_subject, chapters=chapters)

@app.route('/study/class-<int:class_level>/<subject>/chapter-<int:chapter_num>')
def frontend_dashboard(class_level, subject, chapter_num):
    decoded_subject = urllib.parse.unquote(subject)
    chapter = StudyContent.query.filter_by(class_level=class_level, subject=decoded_subject, chapter_number=chapter_num).first_or_404()
    
    # Pre-parse markdown for SEO and immediate rendering
    content = chapter.content_text or 'No AI notes available yet.'
    content = re.sub(r'^### (.*$)', r'<h3 class="text-xl font-bold mt-4 mb-2 text-indigo-700">\1</h3>', content, flags=re.MULTILINE)
    content = re.sub(r'^## (.*$)', r'<h2 class="text-2xl font-bold mt-5 mb-3 text-indigo-800">\1</h2>', content, flags=re.MULTILINE)
    content = re.sub(r'^# (.*$)', r'<h1 class="text-3xl font-bold mt-6 mb-4 text-indigo-900">\1</h1>', content, flags=re.MULTILINE)
    content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content)
    content = re.sub(r'\*(.*?)\*', r'<em>\1</em>', content)
    content = re.sub(r'\n\n', r'</p><p class="mb-4">', content)
    content = re.sub(r'\n', r'<br>', content)
    
    if not content.strip().startswith('<h'):
        content = '<p class="mb-4">' + content + '</p>'
        
    return render_template('frontend/study_dashboard.html', class_level=class_level, subject=decoded_subject, chapter=chapter, parsed_notes=content)

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
