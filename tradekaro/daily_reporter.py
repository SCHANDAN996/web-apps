"""
📊 Daily Trade Summary Reporter
Sends automated daily P&L report to Telegram every evening at 4:00 PM IST.
Also provides on-demand summary via /report command.
"""

import sqlite3
import threading
import time
import schedule
import os
import pytz
from datetime import datetime, timedelta
from src.notifier import TelegramNotifier

IST = pytz.timezone('Asia/Kolkata')


def get_daily_summary(date_str=None):
    """Generate daily trade summary from DB."""
    if not date_str:
        date_str = datetime.now(IST).strftime('%Y-%m-%d')
    
    db_path = 'trading_data.db'
    if not os.path.exists(db_path):
        return None
    
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Today's trades
    c.execute('''SELECT 
        COUNT(*) as total,
        SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as wins,
        SUM(CASE WHEN pnl <= 0 THEN 1 ELSE 0 END) as losses,
        ROUND(SUM(pnl), 2) as total_pnl,
        ROUND(AVG(pnl), 2) as avg_pnl,
        ROUND(MAX(pnl), 2) as best_trade,
        ROUND(MIN(pnl), 2) as worst_trade,
        ROUND(AVG(confidence), 2) as avg_confidence
    FROM trade_journal 
    WHERE status='CLOSED' AND entry_time LIKE ?''', (f'{date_str}%',))
    
    row = c.fetchone()
    total, wins, losses, total_pnl, avg_pnl, best, worst, avg_conf = row
    
    # Per symbol breakdown
    c.execute('''SELECT symbol, COUNT(*), 
        SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END),
        ROUND(SUM(pnl), 2)
    FROM trade_journal 
    WHERE status='CLOSED' AND entry_time LIKE ?
    GROUP BY symbol ORDER BY SUM(pnl) DESC''', (f'{date_str}%',))
    symbols = c.fetchall()
    
    # Open positions
    c.execute('''SELECT COUNT(*) FROM trade_journal 
    WHERE status='OPEN' ''')
    open_count = c.fetchone()[0]
    
    # All-time stats
    c.execute('''SELECT COUNT(*), ROUND(SUM(pnl), 2),
        ROUND(SUM(CASE WHEN pnl>0 THEN 1.0 ELSE 0 END)/COUNT(*)*100, 1)
    FROM trade_journal WHERE status='CLOSED' ''')
    all_total, all_pnl, all_wr = c.fetchone()
    
    conn.close()
    
    return {
        'date': date_str,
        'total': total or 0,
        'wins': wins or 0,
        'losses': losses or 0,
        'total_pnl': total_pnl or 0,
        'avg_pnl': avg_pnl or 0,
        'best': best or 0,
        'worst': worst or 0,
        'avg_confidence': avg_conf or 0,
        'symbols': symbols,
        'open_positions': open_count or 0,
        'all_time_trades': all_total or 0,
        'all_time_pnl': all_pnl or 0,
        'all_time_wr': all_wr or 0
    }


def format_report(data):
    """Format summary into Telegram-friendly HTML message."""
    if not data or data['total'] == 0:
        return f"""📊 <b>TradeKaro Daily Report</b>
📅 {data['date'] if data else 'Today'}

❌ <b>Aaj koi trade nahi hua.</b>

ℹ️ Market band tha ya brain ne koi signal nahi diya.
Open Positions: {data.get('open_positions', 0) if data else 0}

— TradeKaro AI 🧠"""
    
    win_rate = round(data['wins'] / data['total'] * 100, 1) if data['total'] > 0 else 0
    pnl_emoji = "🟢" if data['total_pnl'] >= 0 else "🔴"
    
    # Symbol breakdown
    sym_lines = ""
    for sym_row in (data.get('symbols') or []):
        sym, count, wins, pnl = sym_row
        s_emoji = "✅" if pnl >= 0 else "❌"
        sym_lines += f"  {s_emoji} {sym}: {count} trades, ₹{pnl:,.0f}\n"
    
    report = f"""📊 <b>TradeKaro Daily Report</b>
📅 {data['date']}
━━━━━━━━━━━━━━━━━━

{pnl_emoji} <b>Today's P&L: ₹{data['total_pnl']:,.0f}</b>

📈 Trades: {data['total']} ({data['wins']}W / {data['losses']}L)
🎯 Win Rate: {win_rate}%
💰 Avg P&L: ₹{data['avg_pnl']:,.0f}
🏆 Best: ₹{data['best']:,.0f}
💀 Worst: ₹{data['worst']:,.0f}
🧠 Avg Confidence: {data['avg_confidence']}

<b>Per Symbol:</b>
{sym_lines}
📂 Open Positions: {data['open_positions']}
━━━━━━━━━━━━━━━━━━
<b>All-Time:</b>
📊 {data['all_time_trades']:,} trades | WR: {data['all_time_wr']}%
💰 Total P&L: ₹{data['all_time_pnl']:,.0f}

— TradeKaro AI 🧠"""
    
    return report


def send_daily_report():
    """Send the daily report to Telegram."""
    try:
        notifier = TelegramNotifier()
        data = get_daily_summary()
        report = format_report(data)
        result = notifier.send_message(report)
        if result and result.get('ok'):
            print(f"[REPORT] ✅ Daily report sent for {data['date']}")
        else:
            print(f"[REPORT] ❌ Failed to send: {result}")
    except Exception as e:
        print(f"[REPORT] ❌ Error: {e}")


def start_daily_reporter():
    """Start background scheduler for daily report at 4:00 PM IST."""
    def _scheduler_loop():
        # Schedule at 4:00 PM IST (after market close at 3:30)
        schedule.every().monday.at("16:00").do(send_daily_report)
        schedule.every().tuesday.at("16:00").do(send_daily_report)
        schedule.every().wednesday.at("16:00").do(send_daily_report)
        schedule.every().thursday.at("16:00").do(send_daily_report)
        schedule.every().friday.at("16:00").do(send_daily_report)
        
        print("[REPORT] 📊 Daily Reporter scheduled (Mon-Fri 4:00 PM IST)")
        
        while True:
            schedule.run_pending()
            time.sleep(30)
    
    t = threading.Thread(target=_scheduler_loop, daemon=True)
    t.start()
    return t


if __name__ == '__main__':
    # Test: Send report now
    print("Sending test report...")
    send_daily_report()
