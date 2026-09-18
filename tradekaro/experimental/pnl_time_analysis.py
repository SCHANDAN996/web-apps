"""
⏰ P&L Time Analysis — When Do You Make/Lose Money?

Tracks P&L by:
  Hour of day, Day of week, Session phase
  Identifies best/worst trading times
"""

from collections import defaultdict
from datetime import datetime
import numpy as np


class PnLTimeAnalysis:
    
    def __init__(self):
        self.by_hour = defaultdict(list)
        self.by_day = defaultdict(list)
        self.by_session = defaultdict(list)
    
    def record(self, pnl, timestamp=None):
        dt = timestamp or datetime.now()
        self.by_hour[dt.hour].append(pnl)
        self.by_day[dt.strftime('%A')].append(pnl)
        
        h = dt.hour
        if 9 <= h < 10: session = 'OPENING'
        elif 10 <= h < 12: session = 'MORNING'
        elif 12 <= h < 14: session = 'LUNCH'
        elif 14 <= h < 15: session = 'POWER_HOUR'
        else: session = 'OTHER'
        self.by_session[session].append(pnl)
    
    def analyze(self):
        hourly = {h: {'avg': round(np.mean(pnls), 0), 'total': round(sum(pnls), 0), 'trades': len(pnls)}
                  for h, pnls in self.by_hour.items()}
        daily = {d: {'avg': round(np.mean(pnls), 0), 'total': round(sum(pnls), 0), 'trades': len(pnls)}
                 for d, pnls in self.by_day.items()}
        session = {s: {'avg': round(np.mean(pnls), 0), 'total': round(sum(pnls), 0), 
                       'win_rate': round(sum(1 for p in pnls if p > 0) / max(len(pnls), 1) * 100, 1)}
                   for s, pnls in self.by_session.items()}
        
        best_hour = max(hourly, key=lambda h: hourly[h]['avg']) if hourly else None
        worst_hour = min(hourly, key=lambda h: hourly[h]['avg']) if hourly else None
        
        return {
            'by_hour': hourly, 'by_day': daily, 'by_session': session,
            'best_hour': best_hour, 'worst_hour': worst_hour,
            'recommendation': f'Best: {best_hour}:00, Avoid: {worst_hour}:00' if best_hour else 'Need more data'
        }
