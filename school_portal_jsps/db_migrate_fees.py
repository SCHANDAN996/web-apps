import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'school.db')

def migrate_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    try:
        c.execute('ALTER TABLE global_settings ADD COLUMN admission_fee INTEGER DEFAULT 0')
        print("Added admission_fee column successfully.")
    except sqlite3.OperationalError as e:
        print(f"Column admission_fee might already exist. Error: {e}")
        
    try:
        c.execute('ALTER TABLE global_settings ADD COLUMN payment_upi_id TEXT DEFAULT ""')
        print("Added payment_upi_id column successfully.")
    except sqlite3.OperationalError as e:
        print(f"Column payment_upi_id might already exist. Error: {e}")

    conn.commit()
    conn.close()
    print("Migration finished.")

if __name__ == '__main__':
    migrate_db()
