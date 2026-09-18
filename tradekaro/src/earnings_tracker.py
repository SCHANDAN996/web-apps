"""
📅 Earnings Tracker — Quarterly Results Calendar + Impact Analysis

Tracks upcoming earnings dates and historical impact:
  Which stocks report this week?
  Historical post-earnings move (avg gap % after results)
"""

import json, os
from datetime import datetime, timedelta
from collections import defaultdict


class EarningsTracker:
    
    DATA_FILE = 'data/earnings_calendar.json'
    
    KNOWN_SCHEDULE = {
        'TCS': {'quarter': 'Q4', 'typical_month': 4},
        'INFY': {'quarter': 'Q4', 'typical_month': 4},
        'HDFCBANK': {'quarter': 'Q4', 'typical_month': 4},
        'RELIANCE': {'quarter': 'Q4', 'typical_month': 4},
        'ICICIBANK': {'quarter': 'Q4', 'typical_month': 4},
    }
    
    def __init__(self):
        self.calendar = self._load()
        self.historical_moves = defaultdict(list)
    
    def add_earnings(self, symbol, date, estimate_eps=None):
        self.calendar[symbol] = {
            'date': date, 'estimate_eps': estimate_eps,
            'added': datetime.now().isoformat()
        }
        self._save()
    
    def upcoming(self, days=7):
        today = datetime.now()
        upcoming = []
        for sym, data in self.calendar.items():
            try:
                dt = datetime.strptime(data['date'], '%Y-%m-%d')
                if 0 <= (dt - today).days <= days:
                    upcoming.append({'symbol': sym, 'date': data['date'],
                                    'days_away': (dt - today).days})
            except: pass
        return sorted(upcoming, key=lambda x: x['days_away'])
    
    def record_move(self, symbol, pre_price, post_price):
        move_pct = (post_price - pre_price) / pre_price * 100
        self.historical_moves[symbol].append({
            'move_pct': round(move_pct, 2), 'date': datetime.now().strftime('%Y-%m-%d')
        })
    
    def avg_earnings_move(self, symbol):
        moves = self.historical_moves.get(symbol, [])
        if not moves: return {'avg_move': 0, 'data_points': 0}
        avg = sum(m['move_pct'] for m in moves) / len(moves)
        return {'avg_move': round(avg, 2), 'data_points': len(moves),
                'max_move': round(max(m['move_pct'] for m in moves), 2)}
    
    def _load(self):
        if os.path.exists(self.DATA_FILE):
            try:
                with open(self.DATA_FILE) as f: return json.load(f)
            except: pass
        return {}
    
    def _save(self):
        os.makedirs(os.path.dirname(self.DATA_FILE) or 'data', exist_ok=True)
        with open(self.DATA_FILE, 'w') as f: json.dump(self.calendar, f, indent=2)
