"""
📚 Math Book Seeder — Populates all 3 levels of Math books with chapters
Based on Study Station's complete competitive exam syllabus
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from app import app
from models import db, Book, BookChapter

def seed_math_books():
    with app.app_context():
        # Delete old test chapters from book 1
        BookChapter.query.filter_by(book_id=1).delete()
        
        # Update existing book 1 as 10th level
        book1 = Book.query.get(1)
        if book1:
            book1.title = "Mathematics - 10th Level"
            book1.subtitle = "SSC MTS, GD Constable, Railway Group D"
            book1.slug = "math-10th-level"
            book1.target_exam = "SSC MTS / GD / Railway"
            book1.target_level = "10th"
            book1.subject = "Mathematics"
            book1.icon = "📐"
            book1.cover_color = "#4CAF50"
        
        # === BOOK 1: 10th Level Chapters ===
        chapters_10th = [
            ("Number System", "संख्या प्रणाली", "basic"),
            ("Simplification (BODMAS)", "सरलीकरण (BODMAS)", "basic"),
            ("Average", "औसत", "basic"),
            ("Percentage", "प्रतिशत", "basic"),
            ("Profit and Loss", "लाभ और हानि", "basic"),
            ("Ratio and Proportion", "अनुपात और समानुपात", "basic"),
            ("Time and Work", "समय और कार्य", "intermediate"),
            ("Speed, Time and Distance", "दूरी, समय और चाल", "intermediate"),
            ("Mensuration 2D", "क्षेत्रमिति (2D)", "intermediate"),
        ]
        
        for i, (en, hi, diff) in enumerate(chapters_10th, 1):
            ch = BookChapter(book_id=1, order=i, title_en=en, title_hi=hi, difficulty_level=diff)
            db.session.add(ch)
        
        if book1:
            book1.total_chapters = len(chapters_10th)
        
        # === BOOK 2: 12th Level ===
        book2 = Book.query.filter_by(slug='math-12th-level').first()
        if not book2:
            book2 = Book(
                title="Mathematics - 12th Level",
                subtitle="SSC CHSL, Stenographer, Delhi Police SI",
                slug="math-12th-level",
                target_exam="SSC CHSL / Steno / Police SI",
                target_level="12th",
                subject="Mathematics",
                icon="📊",
                cover_color="#2196F3",
                status="draft"
            )
            db.session.add(book2)
            db.session.flush()
        
        # Delete existing chapters
        BookChapter.query.filter_by(book_id=book2.id).delete()
        
        chapters_12th = [
            ("Number System (Advanced)", "संख्या प्रणाली (उन्नत)", "intermediate"),
            ("Simplification & Approximation", "सरलीकरण और सन्निकटन", "intermediate"),
            ("Average (Advanced Problems)", "औसत (उन्नत)", "intermediate"),
            ("Percentage (Advanced)", "प्रतिशत (उन्नत)", "intermediate"),
            ("Profit, Loss and Discount", "लाभ, हानि और छूट", "intermediate"),
            ("Ratio, Proportion & Partnership", "अनुपात, समानुपात और साझेदारी", "intermediate"),
            ("Time and Work (Pipes & Cisterns)", "समय और कार्य (पाइप और टंकी)", "intermediate"),
            ("Speed, Time & Distance (Trains, Boats)", "चाल, समय और दूरी (ट्रेन, नाव)", "intermediate"),
            ("Algebra (Identities & Equations)", "बीजगणित (सर्वसमिकाएँ और समीकरण)", "intermediate"),
            ("Geometry (Triangles & Properties)", "ज्यामिति (त्रिभुज और गुण)", "intermediate"),
            ("Trigonometry (Basic)", "त्रिकोणमिति (आधारभूत)", "intermediate"),
            ("Data Interpretation", "डेटा व्याख्या", "intermediate"),
        ]
        
        for i, (en, hi, diff) in enumerate(chapters_12th, 1):
            ch = BookChapter(book_id=book2.id, order=i, title_en=en, title_hi=hi, difficulty_level=diff)
            db.session.add(ch)
        book2.total_chapters = len(chapters_12th)
        
        # === BOOK 3: Graduate Level ===
        book3 = Book.query.filter_by(slug='math-graduate-level').first()
        if not book3:
            book3 = Book(
                title="Mathematics - Graduate Level",
                subtitle="SSC CGL, Banking PO/Clerk, UPSC CSAT",
                slug="math-graduate-level",
                target_exam="SSC CGL / Banking / UPSC",
                target_level="Graduate",
                subject="Mathematics",
                icon="🎓",
                cover_color="#673AB7",
                status="draft"
            )
            db.session.add(book3)
            db.session.flush()
        
        BookChapter.query.filter_by(book_id=book3.id).delete()
        
        chapters_grad = [
            ("Number System (Competition Level)", "संख्या प्रणाली (प्रतियोगिता स्तर)", "advanced"),
            ("Advanced Algebra", "उन्नत बीजगणित", "advanced"),
            ("Quadratic Equations", "द्विघात समीकरण", "advanced"),
            ("Advanced Geometry (Circles & Tangents)", "उन्नत ज्यामिति (वृत्त और स्पर्शरेखा)", "advanced"),
            ("Mensuration 3D", "क्षेत्रमिति (3D)", "advanced"),
            ("Advanced Trigonometry", "उन्नत त्रिकोणमिति", "advanced"),
            ("Coordinate Geometry", "निर्देशांक ज्यामिति", "advanced"),
            ("Statistics & Probability", "सांख्यिकी और संभाव्यता", "advanced"),
            ("Simple & Compound Interest", "साधारण और चक्रवृद्धि ब्याज", "intermediate"),
            ("Mixtures and Alligation", "मिश्रण और एलिगेशन", "advanced"),
            ("Number Series (Missing/Wrong)", "संख्या श्रृंखला", "advanced"),
            ("Advanced Data Interpretation", "उन्नत डेटा व्याख्या", "advanced"),
            ("Surds and Indices", "करणी और घातांक", "advanced"),
            ("Logarithms", "लघुगणक", "advanced"),
            ("Set Theory & Venn Diagrams", "सेट सिद्धांत और वेन आरेख", "advanced"),
        ]
        
        for i, (en, hi, diff) in enumerate(chapters_grad, 1):
            ch = BookChapter(book_id=book3.id, order=i, title_en=en, title_hi=hi, difficulty_level=diff)
            db.session.add(ch)
        book3.total_chapters = len(chapters_grad)
        
        db.session.commit()
        
        total = len(chapters_10th) + len(chapters_12th) + len(chapters_grad)
        print(f"Done! Created 3 books with {total} total chapters:")
        print(f"  Book 1 (10th): {len(chapters_10th)} chapters")
        print(f"  Book 2 (12th): {len(chapters_12th)} chapters")  
        print(f"  Book 3 (Grad): {len(chapters_grad)} chapters")

if __name__ == '__main__':
    seed_math_books()
