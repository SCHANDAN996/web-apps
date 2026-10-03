import os
import shutil
from app import app, db
from models import StudyContent

SUBJECTS = [
    "Maths", "Science", "Physics", "Chemistry", "Biology", 
    "History", "Geography", "English", "Hindi"
]

def save_to_db(class_level, subject, chapter_num, local_path):
    with app.app_context():
        # Clean relative path for the frontend (from main_pdf/chapter-X.html to pdfs/)
        rel_path = f"../pdfs/chapter-{chapter_num}.pdf"
        
        # Check if exists
        chapter = StudyContent.query.filter_by(
            class_level=class_level, 
            subject=subject, 
            chapter_number=chapter_num
        ).first()
        
        if chapter:
            chapter.pdf_url = rel_path
        else:
            chapter = StudyContent(
                title=f"Chapter {chapter_num}",
                category="NOTES",
                class_level=class_level,
                board="CBSE",
                subject=subject,
                subject_icon="📚",
                chapter_number=chapter_num,
                chapter_name=f"Chapter {chapter_num}",
                pdf_url=rel_path
            )
            db.session.add(chapter)
        db.session.commit()

def run_mock():
    print("Starting Rapid PDF Population for All Classes (1 to 12)...")
    basedir = os.path.abspath(os.path.dirname(__file__))
    website_dir = os.path.abspath(os.path.join(basedir, '../website'))
    
    # We use an already successfully downloaded PDF as a placeholder to bypass NCERT server blocks
    src_pdf = os.path.join(website_dir, "class-8", "books", "maths", "pdfs", "chapter-1.pdf")
    
    if not os.path.exists(src_pdf):
        print(f"ERROR: Source PDF {src_pdf} not found. Ensure at least one PDF is downloaded to use as placeholder.")
        return
        
    for c in range(1, 13):
        print(f"Populating Class {c}...")
        for subject in SUBJECTS:
            local_pdf_dir = os.path.join(website_dir, f"class-{c}", "books", subject.lower(), "pdfs")
            os.makedirs(local_pdf_dir, exist_ok=True)
            
            # Assuming 15 chapters max for all books to have a complete UI experience
            for ch in range(1, 16):
                local_path = os.path.join(local_pdf_dir, f"chapter-{ch}.pdf")
                if not os.path.exists(local_path):
                    shutil.copy2(src_pdf, local_path)
                    
                # Save into the database
                save_to_db(c, subject, ch, local_path)

    print("\nALL PDFS SUCCESSFULLY POPULATED! You can now run build_website.py")

if __name__ == '__main__':
    run_mock()
