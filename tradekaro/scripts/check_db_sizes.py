import sqlite3
import pandas as pd
import sys

def get_table_sizes(db_path):
    conn = sqlite3.connect(db_path)
    
    # Enable memory mapping for faster reads
    conn.execute("PRAGMA mmap_size=30000000000")
    
    query = """
    SELECT name, sum(pgsize) as bytes 
    FROM dbstat 
    GROUP BY name 
    ORDER BY bytes DESC 
    """
    
    print("Executing dbstat query...")
    try:
        df = pd.read_sql_query(query, conn)
        df['mb'] = df['bytes'] / (1024 * 1024)
        print("\n--- Table Sizes ---")
        print(df.head(15).to_string())
    except Exception as e:
        print(f"Error reading dbstat: {e}")
        
        print("\nTrying alternative method (page count estimation)...")
        # Alternative method if dbstat is too slow or locked
        cursor = conn.cursor()
        cursor.execute("SELECT name, rootpage FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        for table, root in tables:
            print(f"Table: {table}")
            try:
                # Count pages for each table's rootpage tree (simplified, may not be 100% accurate but fast)
                # Just doing a fast row count for now if dbstat fails
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"  Rows: {count}")
            except Exception as ex:
                print(f"  Error: {ex}")

if __name__ == "__main__":
    get_table_sizes('trading_data.db')
