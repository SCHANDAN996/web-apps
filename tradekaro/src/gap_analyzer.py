"""
📊 Gap Analyzer — Opening Gap Classification + Fill Probability

Gap types:
  COMMON: Small gap that fills within the day (70% fill rate)
  BREAKAWAY: Gap at start of new trend (30% fill rate)
  RUNAWAY: Gap during strong trend (20% fill rate)
  EXHAUSTION: Gap near trend end, then reversal (80% fill rate)
"""

import numpy as np
from datetime import datetime


class GapAnalyzer:
    
    def __init__(self):
        self.gap_history = []
    
    def detect_gap(self, prev_close, today_open, avg_range, trend_days=0, volume_ratio=1.0):
        gap = today_open - prev_close
        gap_pct = gap / prev_close * 100
        gap_size = abs(gap_pct)
        
        if gap_size < 0.1:
            return {'type': 'NO_GAP', 'gap_pct': 0}
        
        direction = 'UP' if gap > 0 else 'DOWN'
        gap_type = self._classify(gap_size, trend_days, volume_ratio, avg_range, abs(gap))
        fill_prob = self._fill_probability(gap_type, gap_size)
        
        result = {
            'type': gap_type, 'direction': direction,
            'gap_pct': round(gap_pct, 3), 'gap_points': round(gap, 2),
            'fill_probability': fill_prob,
            'target_fill': round(prev_close, 2),
            'strategy': self._strategy(gap_type, direction, fill_prob)
        }
        self.gap_history.append(result)
        return result
    
    def analyze_daily(self, df):
        if df is None or len(df) < 5:
            return []
        gaps = []
        for i in range(1, len(df)):
            prev_c = df['close'].iloc[i-1]
            curr_o = df['open'].iloc[i]
            avg_r = df['high'].iloc[max(0,i-20):i].mean() - df['low'].iloc[max(0,i-20):i].mean()
            gap = self.detect_gap(prev_c, curr_o, avg_r)
            if gap['type'] != 'NO_GAP':
                gaps.append(gap)
        return gaps
    
    def gap_fill_rate(self):
        if not self.gap_history:
            return 0
        filled = sum(1 for g in self.gap_history if g.get('filled', False))
        return round(filled / len(self.gap_history) * 100, 1)
    
    def _classify(self, size, trend_days, vol_ratio, avg_range, gap_abs):
        if size > 2.0 and abs(trend_days) < 3:
            return 'BREAKAWAY'
        if size > 1.0 and abs(trend_days) > 10:
            return 'EXHAUSTION'
        if size > 1.0 and 3 < abs(trend_days) < 10 and vol_ratio > 1.5:
            return 'RUNAWAY'
        return 'COMMON'
    
    def _fill_probability(self, gap_type, size):
        probs = {'COMMON': 75, 'BREAKAWAY': 30, 'RUNAWAY': 20, 'EXHAUSTION': 80}
        base = probs.get(gap_type, 50)
        if size > 3:
            base -= 15
        return min(95, max(5, base))
    
    def _strategy(self, gap_type, direction, fill_prob):
        if fill_prob > 65:
            return f'FADE the gap — trade AGAINST {direction} for gap fill'
        elif fill_prob < 35:
            return f'FOLLOW the gap — trade WITH {direction} for continuation'
        return 'WAIT for first 15 min to confirm direction'
