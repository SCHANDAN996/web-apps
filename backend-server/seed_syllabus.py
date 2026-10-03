import os
from app import app
from models import db, StudyContent, PracticeQuestion
from syllabus_data import SYLLABUS

def get_subject_icon(subject):
    icons = {
        "Science": "🔬",
        "Physics": "⚛️",
        "Chemistry": "🧪",
        "Biology": "🧬",
        "Maths": "📐"
    }
    return icons.get(subject, "📚")

def seed_syllabus_structure():
    with app.app_context():
        print("Starting syllabus auto-filler...")
        
        # Check if we should clear existing or just append
        # Let's not drop_all to preserve practice questions and existing detailed notes
        # Instead, we will check if the chapter already exists to prevent duplicates
        
        added_count = 0
        
        for class_level, subjects in SYLLABUS.items():
            class_num = int(class_level)
            for subject, chapters in subjects.items():
                icon = get_subject_icon(subject)
                
                for i, chapter_name in enumerate(chapters):
                    chapter_num = i + 1
                    
                    # Check if this exact chapter already exists
                    exists = StudyContent.query.filter_by(
                        class_level=class_num, 
                        subject=subject, 
                        chapter_number=chapter_num
                    ).first()
                    
                    if not exists:
                        placeholder_content = f"# Chapter {chapter_num}: {chapter_name}\n\n### ⏳ Detailed notes for this chapter are currently being updated.\n\n*Please check back later or use the Admin Panel to add notes manually!*"
                        
                        new_chapter = StudyContent(
                            title=chapter_name,
                            description=f"Class {class_level} {subject} Chapter {chapter_num}",
                            category="NOTES",
                            class_level=class_num,
                            board="CBSE",
                            subject=subject,
                            subject_icon=icon,
                            chapter_number=chapter_num,
                            chapter_name=chapter_name,
                            content_text=placeholder_content,
                            difficulty="MEDIUM"
                        )
                        db.session.add(new_chapter)
                        
                        # Also add a dummy practice question for this chapter so the Practice UI is full
                        pq_exists = PracticeQuestion.query.filter_by(
                            class_level=class_num,
                            subject=subject,
                            chapter_number=chapter_num
                        ).first()
                        
                        if not pq_exists:
                            dummy_q = PracticeQuestion(
                                class_level=class_num,
                                subject=subject,
                                chapter_number=chapter_num,
                                chapter=chapter_name,
                                question_text=f"Sample Question for {chapter_name}",
                                option_a="Option A",
                                option_b="Option B",
                                option_c="Option C",
                                option_d="Option D",
                                correct_answer="A",
                                explanation=f"This is a placeholder question for Class {class_level} {subject} Chapter {chapter_num}.",
                                exam_name="Practice Exam",
                                year=2024
                            )
                            db.session.add(dummy_q)
                            
                        added_count += 1
                        
        db.session.commit()
        print(f"Successfully added {added_count} new syllabus chapters and practice sets to the database!")

if __name__ == '__main__':
    seed_syllabus_structure()
