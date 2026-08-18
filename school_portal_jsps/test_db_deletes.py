import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'school.db')

def test_deletions():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 1. Insert dummy data
    c.execute("INSERT INTO notices (title, content) VALUES ('Test Notice', 'Test Content')")
    notice_id = c.lastrowid
    
    c.execute("INSERT INTO feedbacks (name, email, message) VALUES ('Test', 'test@test.com', 'Msg')")
    feedback_id = c.lastrowid
    
    c.execute("INSERT INTO admissions (student_name, parent_name, phone, class_applied) VALUES ('Test', 'Test', '123', '1')")
    admission_id = c.lastrowid
    
    c.execute("INSERT INTO careers (name, email, phone, position) VALUES ('Test', 'test@test.com', '123', 'Teacher')")
    career_id = c.lastrowid
    
    conn.commit()
    print(f"Inserted Dummy Data: Notice {notice_id}, Feedback {feedback_id}, Admission {admission_id}, Career {career_id}")
    
    # 2. Verify existence
    assert c.execute(f"SELECT COUNT(*) FROM notices WHERE id={notice_id}").fetchone()[0] == 1
    
    # 3. Test Deletions
    print("Testing delete operations via direct SQL (simulating app.py delete routes)...")
    
    c.execute("DELETE FROM notices WHERE id=?", (notice_id,))
    c.execute("DELETE FROM feedbacks WHERE id=?", (feedback_id,))
    c.execute("DELETE FROM admissions WHERE id=?", (admission_id,))
    c.execute("DELETE FROM careers WHERE id=?", (career_id,))
    
    conn.commit()
    
    # 4. Verify deletion
    assert c.execute(f"SELECT COUNT(*) FROM notices WHERE id={notice_id}").fetchone()[0] == 0
    assert c.execute(f"SELECT COUNT(*) FROM feedbacks WHERE id={feedback_id}").fetchone()[0] == 0
    assert c.execute(f"SELECT COUNT(*) FROM admissions WHERE id={admission_id}").fetchone()[0] == 0
    assert c.execute(f"SELECT COUNT(*) FROM careers WHERE id={career_id}").fetchone()[0] == 0
    
    print("All direct DB deletion tests passed successfully!")
    conn.close()

if __name__ == '__main__':
    test_deletions()
