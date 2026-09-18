import sqlite3
import os
import glob
import subprocess

DB_PATH = 'trading_data.db'

def reset_all():
    print("1. Stopping tradekaro-bot service...")
    subprocess.run(["systemctl", "stop", "tradekaro-bot.service"])

    print("2. Clearing database tables (trades, trade_journal, signals, ai_thoughts)...")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("DELETE FROM trades")
        c.execute("DELETE FROM trade_journal")
        c.execute("DELETE FROM signals")
        c.execute("DELETE FROM ai_thoughts")
        conn.commit()
        print("   Database tables cleared successfully.")
    except Exception as e:
        print(f"   Error clearing tables: {e}")
    finally:
        conn.close()

    print("3. Truncating log files...")
    log_files = [
        'logs/trading.log',
        'logs/ai_thoughts.log',
        'app_web.log',
        'bot_output.txt'
    ]
    for log_file in log_files:
        if os.path.exists(log_file):
            try:
                with open(log_file, 'w') as f:
                    f.truncate(0)
                print(f"   Cleared log: {log_file}")
            except Exception as e:
                print(f"   Error clearing {log_file}: {e}")

    # Remove rotated log files
    for pat in ['logs/trading.log.*', 'logs/ai_thoughts.log.*']:
        for rotated in glob.glob(pat):
            try:
                os.remove(rotated)
                print(f"   Removed rotated file: {rotated}")
            except Exception as e:
                print(f"   Error removing {rotated}: {e}")

    print("4. Starting tradekaro-bot service...")
    subprocess.run(["systemctl", "start", "tradekaro-bot.service"])
    print("Reset complete! Bot is now running with a fresh slate today.")

if __name__ == "__main__":
    reset_all()
