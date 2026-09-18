import sqlite3
import datetime
import pytz
import os
import sys
import subprocess

# Add src to path
sys.path.append(os.path.abspath('src'))
from database import TradingDB
from executor import OrderExecutor
from connector import ShoonyaConnector

def exit_all(restart_bot=True):
    """Close every open position.

    With restart_bot=False the bot is left stopped, which is what an emergency
    stop needs — a human decides when trading resumes. Returns the number of
    positions that were closed.
    """
    print("1. Stopping tradekaro-bot service...")
    subprocess.run(["systemctl", "stop", "tradekaro-bot.service"])

    db = TradingDB()
    api = ShoonyaConnector()
    # Login to set session mode
    api.login()
    executor = OrderExecutor(api)

    cursor = db.conn.cursor()
    cursor.execute("SELECT id, symbol, side, qty, entry_price, instrument, sl_price, entry_time FROM trade_journal WHERE status = 'OPEN'")
    rows = cursor.fetchall()
    
    if not rows:
        print("No open positions found in the database.")
        if restart_bot:
            subprocess.run(["systemctl", "start", "tradekaro-bot.service"])
        return 0

    ist = pytz.timezone('Asia/Kolkata')
    exit_time = datetime.datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')

    print(f"2. Exiting {len(rows)} active trades...")
    for row in rows:
        journal_id, trade_symbol, side, qty, entry_price, instrument, sl_price, entry_time = row
        print(f"   -> Exiting trade #{journal_id}: {trade_symbol} | Side: {side} | Qty: {qty}")
        
        # Determine exit side
        exit_side = 'S' if side == 'BUY' else 'B'
        
        # Use entry_price as the exit price for simulation
        exit_price = entry_price
        
        # Determine exchange
        exchange = 'NFO' if instrument in ['CE', 'PE'] else 'NSE'
        
        try:
            executor.place_smart_order(trade_symbol, exchange, qty, exit_side, exit_price, is_exit=True)
            executor.send_exit_notification(
                symbol=trade_symbol,
                side=side,
                entry_price=entry_price,
                exit_price=exit_price,
                qty=qty,
                exit_reason='MANUAL_FORCE_EXIT',
                sl_price=sl_price,
                entry_time=entry_time
            )
        except Exception as e:
            print(f"      Error placing exit order: {e}")
            
        # Update trade journal status to CLOSED
        db.update_trade_journal_exit(journal_id, exit_price, 'MANUAL_FORCE_EXIT', exit_time)

    if restart_bot:
        print("3. Starting tradekaro-bot service...")
        subprocess.run(["systemctl", "start", "tradekaro-bot.service"])
        print("All open positions have been closed and the bot restarted fresh!")
    else:
        print("All open positions have been closed. Bot left stopped deliberately.")

    return len(rows)

if __name__ == "__main__":
    exit_all()
