import sqlite3
import os

DB_PATH = 'trading_data.db'

try:
    if not os.path.exists(DB_PATH):
        print(f"Error: {DB_PATH} not found!")
    else:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check Signals
        cursor.execute("SELECT count(*) FROM signals")
        count = cursor.fetchone()[0]
        print(f"Signals Count: {count}")
        
        if count > 0:
            cursor.execute("SELECT * FROM signals ORDER BY time DESC LIMIT 5")
            print("Recent Signals:", cursor.fetchall())
            
        # Check News
        cursor.execute("SELECT count(*) FROM news")
        print(f"News Count: {cursor.fetchone()[0]}")
        
        conn.close()

except Exception as e:
    print(f"Db Error: {e}")
