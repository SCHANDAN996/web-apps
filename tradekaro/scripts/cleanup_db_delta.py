import sqlite3
import datetime

DB_PATH = 'trading_data.db'

def cleanup_database_delta_only():
    print(f"[{datetime.datetime.now()}] Starting Database Cleanup for Delta Options Wide...")
    conn = sqlite3.connect(DB_PATH)
    
    # Increase timeout to handle locks during long deletes
    conn.execute("PRAGMA busy_timeout = 60000;")
    cursor = conn.cursor()

    try:
        # 5. Trim delta_options_wide (Older than 3 days)
        print("Trimming old delta_options_wide snapshots...")
        cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM delta_options_wide")
        min_ts, max_ts = cursor.fetchone()
        if max_ts:
            try:
                if isinstance(max_ts, str):
                    # Trying to parse string timestamp '2026-02-21 00:51:43.007503'
                    try:
                        max_dt = datetime.datetime.fromisoformat(max_ts)
                    except ValueError:
                        # Fallback for simpler '2026-02-21' format or similar
                        max_dt = datetime.datetime.strptime(max_ts[:19], '%Y-%m-%d %H:%M:%S')
                    
                    cutoff_dt = max_dt - datetime.timedelta(days=3)
                    cutoff_str = cutoff_dt.strftime('%Y-%m-%d %H:%M:%S')
                    
                    cursor.execute("""
                        DELETE FROM delta_options_wide 
                        WHERE timestamp < ?
                    """, (cutoff_str,))
                else:
                    # Int format (UNIX timestamp)
                    max_ts = int(max_ts)
                    three_days_sec = 3 * 24 * 60 * 60
                    cutoff_ts = max_ts - three_days_sec
                    cursor.execute("""
                        DELETE FROM delta_options_wide 
                        WHERE timestamp < ?
                    """, (cutoff_ts,))
                
                print(f"  -> Deleted {cursor.rowcount} old Delta option logic rows.")
            except Exception as parse_e:
                print(f"  -> Could not parse delta_options_wide timestamp: {parse_e}")
        else:
            print("  -> No Delta data found.")
            
        conn.commit()
        print("Data deletion committed successfully.")
        
        # 7. VACUUM to reclaim space
        print("Running VACUUM to reclaim storage space. This may take a while (10-30 mins)...")
        # Ensure we are in a safe state for vacuum
        conn.execute("VACUUM;")
        print("VACUUM complete. Storage reclaimed.")
        
    except Exception as e:
        print(f"Error during cleanup: {e}")
        conn.rollback()
    finally:
        conn.close()
        print(f"[{datetime.datetime.now()}] Cleanup Finished.")

if __name__ == "__main__":
    cleanup_database_delta_only()
