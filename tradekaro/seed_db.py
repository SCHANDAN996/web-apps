import sqlite3
import datetime

def seed_db():
    print("Seeding Database...")
    try:
        conn = sqlite3.connect('trading_data.db')
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        data = [
            ("MACRO", "NEUTRAL", 0.5, timestamp, "System Initializing..."),
            ("SENTIMENT", "NEUTRAL", 0.5, timestamp, "Scanning News..."),
            ("TECHNICAL", "NEUTRAL", 0.5, timestamp, "Waiting for Market Data...")
        ]
        
        conn.executemany("INSERT OR REPLACE INTO agent_registry VALUES (?, ?, ?, ?, ?)", data)
        conn.commit()
        print("✅ Database Seeded with Initial Council State.")
        conn.close()
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    seed_db()
