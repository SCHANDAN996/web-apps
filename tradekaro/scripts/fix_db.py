import sqlite3

def create_table_fix():
    print("Fixing Database...")
    try:
        conn = sqlite3.connect('trading_data.db')
        # Agent Registry (The Council Memory)
        conn.execute('''CREATE TABLE IF NOT EXISTS agent_registry
                          (agent_name TEXT PRIMARY KEY,
                           status TEXT,
                           confidence REAL,
                           last_update TIMESTAMP,
                           details TEXT)''')
        conn.commit()
        print("✅ Table 'agent_registry' Created Successfully.")
        conn.close()
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    create_table_fix()
