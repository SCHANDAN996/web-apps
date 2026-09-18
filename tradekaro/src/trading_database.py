"""
🗄️ Trading Database — SQLite Persistence for Trades/Signals/Market Data

Persistent storage for:
  Trades, signals, daily summaries, model predictions, system events
"""

import sqlite3, os, json
from datetime import datetime


class TradingDatabase:
    
    def __init__(self, db_path='data/tradekaro.db'):
        os.makedirs(os.path.dirname(db_path) or 'data', exist_ok=True)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._create_tables()
    
    def _create_tables(self):
        self.conn.executescript('''
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY, symbol TEXT, side TEXT, qty INTEGER,
                entry_price REAL, exit_price REAL, pnl REAL,
                entry_time TEXT, exit_time TEXT, strategy TEXT, meta TEXT
            );
            CREATE TABLE IF NOT EXISTS signals (
                id INTEGER PRIMARY KEY, symbol TEXT, direction TEXT,
                confidence REAL, source TEXT, timestamp TEXT, meta TEXT
            );
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY, event_type TEXT, message TEXT,
                severity TEXT, timestamp TEXT
            );
            CREATE TABLE IF NOT EXISTS daily_summary (
                date TEXT PRIMARY KEY, total_trades INTEGER, total_pnl REAL,
                win_rate REAL, max_drawdown REAL, meta TEXT
            );
        ''')
        self.conn.commit()
    
    def save_trade(self, symbol, side, qty, entry, exit_p, pnl, strategy='', meta=None):
        self.conn.execute(
            'INSERT INTO trades (symbol,side,qty,entry_price,exit_price,pnl,entry_time,exit_time,strategy,meta) VALUES (?,?,?,?,?,?,?,?,?,?)',
            (symbol, side, qty, entry, exit_p, pnl, datetime.now().isoformat(), datetime.now().isoformat(), strategy, json.dumps(meta or {}))
        )
        self.conn.commit()
    
    def save_signal(self, symbol, direction, confidence, source=''):
        self.conn.execute(
            'INSERT INTO signals (symbol,direction,confidence,source,timestamp,meta) VALUES (?,?,?,?,?,?)',
            (symbol, direction, confidence, source, datetime.now().isoformat(), '{}')
        )
        self.conn.commit()
    
    def save_event(self, event_type, message, severity='INFO'):
        self.conn.execute(
            'INSERT INTO events (event_type,message,severity,timestamp) VALUES (?,?,?,?)',
            (event_type, message, severity, datetime.now().isoformat())
        )
        self.conn.commit()
    
    def get_trades(self, limit=50):
        cur = self.conn.execute('SELECT * FROM trades ORDER BY id DESC LIMIT ?', (limit,))
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]
    
    def get_today_pnl(self):
        today = datetime.now().strftime('%Y-%m-%d')
        cur = self.conn.execute("SELECT SUM(pnl) FROM trades WHERE entry_time LIKE ?", (f'{today}%',))
        result = cur.fetchone()[0]
        return round(result or 0, 2)
    
    def get_trade_count(self):
        cur = self.conn.execute('SELECT COUNT(*) FROM trades')
        return cur.fetchone()[0]
    
    def close(self):
        self.conn.close()
