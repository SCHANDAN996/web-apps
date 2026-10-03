from app import app, db
from models import PreviousYearPaper

def seed_pyq():
    with app.app_context():
        # Clear existing
        PreviousYearPaper.query.delete()
        
        sample_papers = [
            # SSC
            {"exam": "SSC CGL", "year": "2023", "title": "Tier 1 Shift 1", "cat": "SSC", "q": "https://example.com/q1.pdf", "a": "https://example.com/a1.pdf"},
            {"exam": "SSC CHSL", "year": "2022", "title": "Tier 1 All Shifts", "cat": "SSC", "q": "https://example.com/q2.pdf", "a": "https://example.com/a2.pdf"},
            {"exam": "SSC MTS", "year": "2021", "title": "Paper 1", "cat": "SSC", "q": "https://example.com/q3.pdf", "a": "https://example.com/a3.pdf"},
            
            # BANKING
            {"exam": "SBI PO", "year": "2023", "title": "Prelims", "cat": "BANKING", "q": "https://example.com/q4.pdf", "a": "https://example.com/a4.pdf"},
            {"exam": "IBPS Clerk", "year": "2022", "title": "Mains", "cat": "BANKING", "q": "https://example.com/q5.pdf", "a": "https://example.com/a5.pdf"},
            
            # UPSC
            {"exam": "UPSC Civil Services", "year": "2023", "title": "Prelims GS Paper 1", "cat": "UPSC", "q": "https://example.com/q6.pdf", "a": "https://example.com/a6.pdf"},
            {"exam": "UPSC NDA", "year": "2022", "title": "Maths & GAT", "cat": "UPSC", "q": "https://example.com/q7.pdf", "a": "https://example.com/a7.pdf"},
            
            # RAILWAY
            {"exam": "RRB NTPC", "year": "2021", "title": "CBT 1", "cat": "RAILWAY", "q": "https://example.com/q8.pdf", "a": "https://example.com/a8.pdf"}
        ]
        
        for p in sample_papers:
            paper = PreviousYearPaper(
                exam_name=p["exam"],
                year=p["year"],
                paper_title=p["title"],
                question_pdf_url=p["q"],
                answer_key_url=p["a"],
                category=p["cat"]
            )
            db.session.add(paper)
            
        db.session.commit()
        print("Successfully seeded Previous Year Papers!")

if __name__ == "__main__":
    seed_pyq()
