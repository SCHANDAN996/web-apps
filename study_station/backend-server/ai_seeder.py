import os
import time
import json
import google.generativeai as genai
from app import app
from models import db, StudyContent, PracticeQuestion, SystemSettings

def get_setting(key):
    with app.app_context():
        setting = SystemSettings.query.filter_by(setting_key=key).first()
        return setting.setting_value if setting else None

def generate_chapter_data(class_num, subject, chapter_name):
    api_keys_str = get_setting('gemini_api_keys') or get_setting('gemini_api_key')
    
    keys = []
    if api_keys_str:
        keys = [k.strip() for k in api_keys_str.split('\n') if k.strip()]
        
    # Fallback: environment variable (never hardcode secrets)
    api_key = keys[0] if keys else os.environ.get('GEMINI_API_KEY', '')
    
    if not api_key:
        print("Error: No valid Gemini API Key found in settings!")
        return None
        
    model_name = get_setting('ai_model_name') or 'gemini-flash-latest'
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name)
    
    prompt = f"""
    You are an expert, friendly teacher for Class {class_num} students.
    Your task is to generate beautiful, easy-to-understand study materials for the subject '{subject}', chapter '{chapter_name}'.

    Please respond with a JSON object strictly following this structure:
    {{
        "notes": "A string containing the study notes in Markdown format. Use emojis, simple vocabulary, short sentences, and engaging headings. Make it fun and educational for a young student.",
        "questions": [
            {{
                "question_text": "A simple multiple choice question",
                "option_a": "Option 1",
                "option_b": "Option 2",
                "option_c": "Option 3",
                "option_d": "Option 4",
                "correct_answer": "A", 
                "explanation": "A very simple 1-line explanation of why this is correct."
            }}
        ]
    }}
    
    Make sure to provide exactly 3 questions.
    Return ONLY valid JSON. Do not include markdown code block backticks like ```json around the response.
    """
    
    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        
        # Super robust JSON extraction using regex
        import re
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            text = json_match.group(0)
            
        data = json.loads(text)
        return {"success": True, "data": data}
    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}"
        if hasattr(response, 'prompt_feedback') and response.prompt_feedback:
            error_msg += f" | Safety Info: {response.prompt_feedback}"
        print(f"Error generating data for {chapter_name}: {error_msg}")
        return {"success": False, "error": error_msg}

def seed_class(class_num):
    with app.app_context():
        print(f"--- Starting AI Seeding for Class {class_num} ---")
        
        # Find all chapters for this class
        chapters = StudyContent.query.filter_by(class_level=class_num).all()
        
        if not chapters:
            print(f"No chapters found in DB for Class {class_num}. Run seed_syllabus.py first.")
            return
            
        total = len(chapters)
        print(f"Found {total} chapters. This will take approximately {total * 5} seconds.")
        
        success_count = 0
        
        for idx, chapter in enumerate(chapters, 1):
            print(f"[{idx}/{total}] Generating: {chapter.subject} - {chapter.title}...", end=" ")
            
            # Skip if already generated (doesn't contain the placeholder keyword)
            if "⏳" not in chapter.content_text and "Detailed notes" not in chapter.content_text:
                print("Skipped (Already generated).")
                continue
                
            data = generate_chapter_data(class_num, chapter.subject, chapter.title)
            
            if data and 'notes' in data and 'questions' in data:
                # Update Notes
                chapter.content_text = data['notes']
                
                # Delete old dummy questions for this chapter
                PracticeQuestion.query.filter_by(
                    class_level=class_num, 
                    subject=chapter.subject, 
                    chapter_number=chapter.chapter_number
                ).delete()
                
                # Insert new AI questions
                for q in data['questions']:
                    new_q = PracticeQuestion(
                        class_level=class_num,
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
                        exam_name=f"Class {class_num} Test",
                        year=2024
                    )
                    db.session.add(new_q)
                
                db.session.commit()
                success_count += 1
                print("Done! [OK]")
            else:
                print("Failed! [FAIL]")
                
            # Respect API Rate Limits (15 requests per minute -> 1 request every 4 seconds)
            time.sleep(4)
            
        print(f"--- Finished! Successfully generated {success_count} chapters. ---")

if __name__ == '__main__':
    # You can change the class number here
    seed_class(1)
