import os
import requests
import time
from app import app, db
from models import StudyContent

# NCERT Class Prefix Mapping
CLASS_PREFIX = {
    1: 'a', 2: 'b', 3: 'c', 4: 'd', 5: 'e', 6: 'f',
    7: 'g', 8: 'h', 9: 'i', 10: 'j', 11: 'k', 12: 'l'
}

# Book codes (Subject -> NCERT book code part)
# This is a sample catalog that covers the most popular books.
CATALOG = {
    "Maths": ["ema1", "mh1", "emh1"],
    "Science": ["esc1", "sc1"],
    "Physics": ["eph1", "eph2"],
    "Chemistry": ["ech1", "ech2"],
    "Biology": ["ebo1"],
    "History": ["ess1", "his1"],
    "Geography": ["ess2", "geo1"],
    "English": ["een1", "eng1"],
    "Hindi": ["ehn1", "hin1"]
}

def download_book(class_level, subject, book_code_suffix):
    prefix = CLASS_PREFIX.get(class_level)
    if not prefix:
        return
        
    book_code = f"{prefix}{book_code_suffix}"
    
    # Setup directories
    basedir = os.path.abspath(os.path.dirname(__file__))
    website_dir = os.path.abspath(os.path.join(basedir, '../website'))
    local_pdf_dir = os.path.join(website_dir, f"class-{class_level}", "books", subject.lower(), "pdfs")
    os.makedirs(local_pdf_dir, exist_ok=True)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/pdf'
    }

    print(f"\n--- Checking Book Code: {book_code} for Class {class_level} {subject} ---")
    
    for chapter_num in range(1, 20): # Max 20 chapters usually
        ch_str = str(chapter_num).zfill(2)
        pdf_filename = f"{book_code}{ch_str}.pdf"
        url = f"https://ncert.nic.in/textbook/pdf/{pdf_filename}"
        
        local_path = os.path.join(local_pdf_dir, f"chapter-{chapter_num}.pdf")
        
        if os.path.exists(local_path):
            print(f"[SKIP] Chapter {chapter_num} already downloaded.")
            save_to_db(class_level, subject, chapter_num, local_path)
            continue
            
        print(f"[*] Downloading {url} ...")
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                with open(local_path, 'wb') as f:
                    f.write(response.content)
                print(f"[SUCCESS] Saved Chapter {chapter_num}!")
                save_to_db(class_level, subject, chapter_num, local_path)
            elif response.status_code == 404:
                print(f"[END] Chapter {chapter_num} not found. Assuming end of book.")
                time.sleep(1)
                break # No more chapters in this book
            else:
                print(f"[ERROR] HTTP {response.status_code}")
                time.sleep(1)
                break
            
            time.sleep(1) # Prevent getting banned
        except Exception as e:
            print(f"[FAILED] Error downloading {url}: {e}")
            time.sleep(2)
            break

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

def run_all():
    print("Starting Massive NCERT Download (Class 1 to 12)...")
    
    # We loop class 1 to 12
    for c in range(1, 13):
        for subject, codes in CATALOG.items():
            for code in codes:
                download_book(c, subject, code)
                
    print("\nALL DOWNLOADS FINISHED! Run build_website.py next.")

if __name__ == '__main__':
    run_all()
