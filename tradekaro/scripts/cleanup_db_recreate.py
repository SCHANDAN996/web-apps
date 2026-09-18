import sqlite3
import datetime

DB_PATH = 'trading_data.db'

def recreate_large_tables():
    print(f"[{datetime.datetime.now()}] Starting Database Recreate Cleanup...")
    conn = sqlite3.connect(DB_PATH)
    
    # Increase timeout to handle locks
    conn.execute("PRAGMA busy_timeout = 60000;")
    cursor = conn.cursor()

    try:
        # Instead of generic DELETE which takes hours for 93M rows, 
        # we create a fresh table with only the recent data.
        print("Recreating delta_options_wide...")
        
        cursor.execute("SELECT MAX(timestamp) FROM delta_options_wide")
        max_ts_raw = cursor.fetchone()[0]
        
        if max_ts_raw:
            try:
                # Handle both string and int timestamp formats
                if isinstance(max_ts_raw, str):
                    try:
                        max_dt = datetime.datetime.fromisoformat(max_ts_raw)
                    except ValueError:
                        max_dt = datetime.datetime.strptime(max_ts_raw[:19], '%Y-%m-%d %H:%M:%S')
                    
                    cutoff_dt = max_dt - datetime.timedelta(days=3)
                    cutoff_val = cutoff_dt.strftime('%Y-%m-%d %H:%M:%S')
                    condition = "timestamp >= ?"
                else:
                    max_ts = int(max_ts_raw)
                    cutoff_val = max_ts - (3 * 24 * 60 * 60)
                    condition = "timestamp >= ?"

                # 1. Create a temporary table with the exact schema
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS delta_options_wide_new (
                        timestamp INTEGER, expiry TEXT, strike REAL, underlying TEXT, 
                        underlying_price REAL, ce_ltp REAL, ce_oi INTEGER, ce_iv REAL, 
                        pe_ltp REAL, pe_oi INTEGER, pe_iv REAL,
                        PRIMARY KEY (underlying, expiry, strike, timestamp)
                    )
                """)
                
                # 2. Insert ONLY the data we want to keep
                print(f"  -> Copying recent data since {cutoff_val}...")
                cursor.execute(f"""
                    INSERT INTO delta_options_wide_new 
                    SELECT * FROM delta_options_wide WHERE {condition}
                """, (cutoff_val,))
                
                print(f"  -> Copied {cursor.rowcount} rows into new table.")
                
                # 3. Drop the old massive table entirely
                print("  -> Dropping old 90M+ rows table...")
                cursor.execute("DROP TABLE delta_options_wide")
                
                # 4. Rename new table to original name
                print("  -> Renaming new table...")
                cursor.execute("ALTER TABLE delta_options_wide_new RENAME TO delta_options_wide")
                
            except Exception as e:
                print(f"  -> Recreate Error: {e}")
        else:
            print("  -> No data found.")
            
        conn.commit()
        print("Table rebuild committed successfully.")
        
        # Finally, VACUUM to shrink the actual file size
        print("Running VACUUM to reclaim storage space. This may take a while (10-30 mins)...")
        conn.execute("VACUUM;")
        print("VACUUM complete. Storage reclaimed.")
        
    except Exception as e:
        print(f"Error during cleanup: {e}")
        conn.rollback()
    finally:
        conn.close()
        print(f"[{datetime.datetime.now()}] Cleanup Finished.")

if __name__ == "__main__":
    recreate_large_tables()
