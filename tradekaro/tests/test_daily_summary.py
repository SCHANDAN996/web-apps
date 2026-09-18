"""
The evening Telegram summary: what it says, and that it never goes silent.
"""
import os
import sqlite3
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from daily_summary import build_message, load_trades

DAY = '2026-09-15'
NO_TRADES = {'opened': [], 'closed': 0, 'pnl': 0, 'open_now': 0}


def stats(**symbols):
    return {
        'date': DAY,
        'decisions': 5685,
        'actions': {'NONE': 5685},
        'reasons': {'No direction': 4781, 'Low confidence veto': 904},
        'symbols': {name: {'decisions': 10, 'strongest': score, 'last': score}
                    for name, score in symbols.items()},
    }


def test_a_day_without_trades_still_explains_itself():
    msg = build_message(DAY, stats(SBIN=0.41, NIFTY=0.56, INFY=0.49), NO_TRADES, 'active')

    assert '15 सितंबर' in msg
    assert '✅ चालू' in msg
    assert '5,685' in msg
    assert 'नए ट्रेड: 0' in msg
    assert '4,781' in msg
    assert 'SBIN' in msg
    assert '0.80' in msg, "should say how far the model is from a trade"


def test_strongest_signals_are_ranked_by_distance_from_neutral():
    msg = build_message(DAY, stats(INFY=0.49, NIFTY=0.56, SBIN=0.38, TCS=0.47), NO_TRADES, 'active')

    order = [msg.index(s) for s in ('SBIN', 'NIFTY', 'TCS')]
    assert order == sorted(order), msg
    assert 'INFY' not in msg, "only the top three are listed"


def test_no_decisions_is_a_warning_not_a_quiet_day():
    msg = build_message(DAY, None, NO_TRADES, 'active')
    assert 'एक भी फ़ैसला दर्ज नहीं' in msg


def test_a_stopped_bot_is_called_out():
    msg = build_message(DAY, stats(SBIN=0.41), NO_TRADES, 'inactive')
    assert '⚠️ बंद' in msg and 'inactive' in msg


def test_trades_and_pnl_are_reported():
    trades = {'opened': [('SBIN', 'S', 812.5)], 'closed': 2, 'pnl': 305.17,
              'wins': 1, 'losses': 1, 'open_now': 1,
              'all_trades': 36, 'all_pnl': 305.17, 'all_wins': 17}
    msg = build_message(DAY, stats(SBIN=0.15), trades, 'active')

    assert 'नए ट्रेड: 1' in msg
    assert 'S SBIN @ 812.5' in msg
    assert '(1 जीते / 1 हारे)' in msg
    assert '₹+305' in msg
    assert 'खुली positions: 1' in msg
    # carried over from the old daily_reporter.py
    assert 'अब तक कुल: 36 trades' in msg
    assert 'जीत 47%' in msg


def test_no_all_time_line_before_the_first_trade():
    msg = build_message(DAY, stats(SBIN=0.41), NO_TRADES, 'active')
    assert 'अब तक कुल' not in msg


def test_symbols_are_escaped_for_telegram_html():
    msg = build_message(DAY, stats(**{'M&M': 0.30}), NO_TRADES, 'active')
    assert 'M&amp;M' in msg
    assert 'M&M' not in msg.replace('M&amp;M', '')


def test_load_trades_reads_only_the_requested_day(tmp_path):
    db = tmp_path / 'trading_data.db'
    con = sqlite3.connect(db)
    con.execute("CREATE TABLE trade_journal (symbol TEXT, side TEXT, entry_price REAL, "
                "entry_time TEXT, exit_time TEXT, pnl REAL, status TEXT)")
    con.executemany("INSERT INTO trade_journal VALUES (?,?,?,?,?,?,?)", [
        ('SBIN', 'S', 812.5, '2026-09-15 09:20:01', '2026-09-15 11:00:00', 120.0, 'CLOSED'),
        ('INFY', 'B', 1500.0, '2026-09-15 10:05:00', None, 0.0, 'OPEN'),
        ('TCS', 'S', 4000.0, '2026-09-14 09:20:00', '2026-09-15 09:30:00', -40.0, 'CLOSED'),
        ('HDFC', 'B', 1600.0, '2026-09-14 09:21:00', '2026-09-14 12:00:00', 99.0, 'CLOSED'),
    ])
    con.commit()
    con.close()

    trades = load_trades(DAY, db_path=str(db))

    assert [t[0] for t in trades['opened']] == ['SBIN', 'INFY']
    assert trades['closed'] == 2          # SBIN and TCS closed today
    assert trades['pnl'] == 80.0
    assert (trades['wins'], trades['losses']) == (1, 1)
    assert trades['open_now'] == 1
    assert trades['all_trades'] == 3      # every CLOSED row, any day
    assert trades['all_pnl'] == 179.0
    assert trades['all_wins'] == 2
