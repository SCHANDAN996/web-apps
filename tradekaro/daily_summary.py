"""
Evening Telegram summary for TradeKaro.

Runs from cron after NSE close (deploy/tradekaro-daily-summary.cron). It says
what the bot did today even when it did nothing: Telegram only ever heard
about opened and closed trades, so a quiet phone looked the same whether the
bot was running and declining every trade or not running at all.

It replaces the report daily_reporter.py sent from inside the bot. That one
was scheduled for "16:00" in server time, which is UTC -- 21:30 IST, not the
4 PM its docstring promised -- and it could never say the bot was down,
because it only ran while the bot did. Its trade and all-time P&L lines are
carried over here.

    venv/bin/python daily_summary.py              # send today's summary
    venv/bin/python daily_summary.py --dry-run    # print it instead
    venv/bin/python daily_summary.py --date 2026-09-15
"""
import argparse
import html
import json
import os
import sqlite3
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.decision_stats import ist_today, stats_path

DB_PATH = 'trading_data.db'

# TheCouncil vetoes anything under 0.60 final confidence, and confidence starts
# as |score - 0.5| * 2 (agents can lift it at most x1.3). So in practice the
# model has to reach about 0.80 or 0.20 before a trade can happen.
TRADE_LOW, TRADE_HIGH = 0.20, 0.80

MONTHS = ['जनवरी', 'फ़रवरी', 'मार्च', 'अप्रैल', 'मई', 'जून', 'जुलाई',
          'अगस्त', 'सितंबर', 'अक्टूबर', 'नवंबर', 'दिसंबर']

REASON_LABELS = {
    'No direction': 'कोई दिशा नहीं (0.45–0.55)',
    'Low confidence veto': 'confidence 0.60 से कम',
    'Approved': 'मंज़ूर',
}


def load_stats(day, stats_dir='logs'):
    try:
        with open(stats_path(day, stats_dir), encoding='utf-8') as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def load_trades(day, db_path=DB_PATH):
    con = sqlite3.connect(f'file:{db_path}?mode=ro', uri=True, timeout=30)
    try:
        opened = con.execute(
            "SELECT symbol, side, entry_price FROM trade_journal "
            "WHERE entry_time LIKE ? ORDER BY entry_time", (f'{day}%',)).fetchall()
        closed = con.execute(
            "SELECT COUNT(*), COALESCE(SUM(pnl), 0), "
            "COALESCE(SUM(pnl > 0), 0), COALESCE(SUM(pnl <= 0), 0) FROM trade_journal "
            "WHERE status = 'CLOSED' AND exit_time LIKE ?", (f'{day}%',)).fetchone()
        open_now = con.execute(
            "SELECT COUNT(*) FROM trade_journal WHERE status = 'OPEN'").fetchone()[0]
        all_time = con.execute(
            "SELECT COUNT(*), COALESCE(SUM(pnl), 0), COALESCE(SUM(pnl > 0), 0) "
            "FROM trade_journal WHERE status = 'CLOSED'").fetchone()
    finally:
        con.close()
    return {'opened': opened, 'closed': closed[0], 'pnl': closed[1],
            'wins': closed[2], 'losses': closed[3], 'open_now': open_now,
            'all_trades': all_time[0], 'all_pnl': all_time[1], 'all_wins': all_time[2]}


def bot_status():
    try:
        out = subprocess.run(['systemctl', 'is-active', 'tradekaro-bot'],
                             capture_output=True, text=True, timeout=10)
        return out.stdout.strip() or 'unknown'
    except Exception:
        return 'unknown'


def _n(x):
    return f"{x:,}"


def _rupees(x):
    x = x or 0
    return f"₹{'+' if x > 0 else ''}{x:,.0f}"


def build_message(day, stats, trades, status):
    """The summary as Telegram HTML. Everything dynamic is escaped."""
    esc = html.escape
    y, m, d = day.split('-')
    lines = [f"📊 <b>TradeKaro — {int(d)} {MONTHS[int(m) - 1]}</b>", ""]

    if status == 'active':
        lines.append("बॉट: ✅ चालू")
    else:
        lines.append(f"बॉट: ⚠️ बंद ({esc(status)})")

    decisions = (stats or {}).get('decisions', 0)
    lines.append(f"फ़ैसले: {_n(decisions)}  |  नए ट्रेड: {len(trades['opened'])}")
    pnl = trades['pnl'] or 0
    closed_line = f"आज बंद हुए: {trades['closed']}"
    if trades['closed']:
        closed_line += f" ({trades.get('wins', 0)} जीते / {trades.get('losses', 0)} हारे)"
    lines.append(f"{closed_line}  |  P&amp;L: {_rupees(pnl)}")
    lines.append(f"खुली positions: {trades['open_now']}")

    for symbol, side, price in trades['opened'][:5]:
        lines.append(f"  • {esc(str(side))} {esc(str(symbol))} @ {price}")

    all_trades = trades.get('all_trades', 0)
    if all_trades:
        win_rate = trades.get('all_wins', 0) / all_trades * 100
        lines.append(f"अब तक कुल: {_n(all_trades)} trades  |  जीत {win_rate:.0f}%  |  "
                     f"P&amp;L: {_rupees(trades.get('all_pnl', 0))}")

    if not decisions:
        lines += ["", "⚠️ <b>आज एक भी फ़ैसला दर्ज नहीं हुआ।</b>",
                  "बॉट की जाँच करें: <code>journalctl -u tradekaro-bot -n 50</code>"]
        return "\n".join(lines)

    scored = [(sym, s['strongest']) for sym, s in stats.get('symbols', {}).items()
              if s.get('strongest') is not None]
    scored.sort(key=lambda t: abs(t[1] - 0.5), reverse=True)
    if scored:
        lines += ["", "🧠 <b>सबसे मज़बूत संकेत</b>"]
        for sym, score in scored[:3]:
            arrow = '↑' if score > 0.5 else '↓' if score < 0.5 else '–'
            lines.append(f"  {esc(sym)}  {score:.2f} {arrow}")
        best = abs(scored[0][1] - 0.5)
        if best < TRADE_HIGH - 0.5:
            lines.append(f"ट्रेड के लिए model को लगभग {TRADE_HIGH:.2f} से ऊपर "
                         f"या {TRADE_LOW:.2f} से नीचे जाना होगा।")

    reasons = sorted(stats.get('reasons', {}).items(), key=lambda t: t[1], reverse=True)
    if reasons:
        lines += ["", "⏸️ <b>फ़ैसलों का हाल</b>"]
        for reason, count in reasons[:3]:
            lines.append(f"  {_n(count)} × {esc(REASON_LABELS.get(reason, reason))}")

    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument('--date', default=None, help='IST date, YYYY-MM-DD')
    parser.add_argument('--dry-run', action='store_true', help='print, do not send')
    args = parser.parse_args(argv)

    day = args.date or ist_today()
    message = build_message(day, load_stats(day), load_trades(day), bot_status())

    if args.dry_run:
        print(message)
        return 0

    from src.notifier import TelegramNotifier
    response = TelegramNotifier().send_message(message)
    if not response or not response.get('ok'):
        print(f"[SUMMARY] {day}: Telegram did not accept the message: {response}")
        return 1
    print(f"[SUMMARY] {day}: sent")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
