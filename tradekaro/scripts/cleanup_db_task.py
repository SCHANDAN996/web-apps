import sqlite3
import datetime
import time

DB_PATH = 'trading_data.db'

def cleanup_database():
    print(f"[{datetime.datetime.now()}] Starting Database Cleanup...")
    conn = sqlite3.connect(DB_PATH)
    
    # Increase timeout to handle locks during long deletes
    conn.execute("PRAGMA busy_timeout = 60000;")
    cursor = conn.cursor()

    try:
        # 1. Trim ai_thoughts (Keep latest 10,000)
        print("Trimming ai_thoughts...")
        cursor.execute("SELECT COUNT(*) FROM ai_thoughts")
        count = cursor.fetchone()[0]
        if count > 10000:
            cursor.execute("""
                DELETE FROM ai_thoughts 
                WHERE id NOT IN (
                    SELECT id FROM ai_thoughts ORDER BY time DESC LIMIT 10000
                )
            """)
            print(f"  -> Deleted {cursor.rowcount} old thoughts.")
        else:
            print("  -> No trimming needed.")
            
        # 2. Trim signals (Keep latest 10,000)
        print("Trimming signals...")
        cursor.execute("SELECT COUNT(*) FROM signals")
        count = cursor.fetchone()[0]
        if count > 10000:
            cursor.execute("""
                DELETE FROM signals 
                WHERE id NOT IN (
                    SELECT id FROM signals ORDER BY time DESC LIMIT 10000
                )
            """)
            print(f"  -> Deleted {cursor.rowcount} old signals.")
        else:
            print("  -> No trimming needed.")

        # 3. Trim market_data 1m intervals (Older than 7 days)
        print("Trimming old 1m market_data...")
        seven_days_ago = (datetime.datetime.now() - datetime.timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("""
            DELETE FROM market_data 
            WHERE interval = '1m' AND timestamp < ?
        """, (seven_days_ago,))
        print(f"  -> Deleted {cursor.rowcount} old 1m candles.")
        
        # 4. Trim nse_option_chain (Older than 3 days)
        print("Trimming old nse_option_chain snapshots...")
        three_days_ago = (datetime.datetime.now() - datetime.timedelta(days=3)).strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("""
            DELETE FROM nse_option_chain 
            WHERE timestamp < ?
        """, (three_days_ago,))
        print(f"  -> Deleted {cursor.rowcount} old NSE option chain rows.")

        # 5. Trim delta_options_wide (Older than 3 days)
        print("Trimming old delta_options_wide snapshots...")
        cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM delta_options_wide")
        min_ts, max_ts = cursor.fetchone()
        if max_ts:
            # Ensure max_ts is treated as int if it was saved as string
            try:
                max_ts = int(max_ts)
                # delta_options_wide uses UNIX epoch integer timestamps
                three_days_sec = 3 * 24 * 60 * 60
                cutoff_ts = max_ts - three_days_sec
                cursor.execute("""
                    DELETE FROM delta_options_wide 
                    WHERE CAST(timestamp AS INTEGER) < ?
                """, (cutoff_ts,))
                print(f"  -> Deleted {cursor.rowcount} old Delta option logic rows.")
            except Exception as parse_e:
                print(f"  -> Could not parse delta_options_wide timestamp: {parse_e}")
        else:
            print("  -> No Delta data found.")

        # 6. Optimize high-precision decimal storage in delta_futures JSON
        print("Optimizing delta_futures precision...")
        # Since sqlite json values are stored directly, rounding the mark_price standardizes numeric width.
        cursor.execute("""
            UPDATE delta_futures 
            SET mark_price = ROUND(mark_price, 2)
        """)
        print(f"  -> Rounded {cursor.rowcount} mark_price records.")
            
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
    cleanup_database()
