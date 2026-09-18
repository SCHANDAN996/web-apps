import sqlite3

try:
    conn = sqlite3.connect('trading_data.db')
    cursor = conn.cursor()
    
    # Check if table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='agent_registry'")
    table = cursor.fetchone()
    
    if table:
        print("✅ Table 'agent_registry' EXISTS.")
        # Check rows
        cursor.execute("SELECT * FROM agent_registry")
        rows = cursor.fetchall()
        print(f"   Rows found: {len(rows)}")
    else:
        print("❌ Table 'agent_registry' MISSING.")

    conn.close()
except Exception as e:
    print(f"Error: {e}")
