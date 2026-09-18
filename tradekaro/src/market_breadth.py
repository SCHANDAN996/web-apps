"""
📈 Market Breadth Analyzer — Internal Market Health Metrics

Price alone doesn't tell the full story. Breadth reveals:
  - How many stocks are participating in the rally?
  - Advance/Decline ratio
  - New 52-week Highs vs Lows
  - Breadth Thrust (sudden extreme breadth = strong trend start)
  - McClellan Oscillator (smoothed A/D difference)
"""

import numpy as np
from collections import deque
from datetime import datetime


class MarketBreadthAnalyzer:
    """
    Analyzes internal market breadth for health assessment.
    
    Usage:
        breadth = MarketBreadthAnalyzer()
        breadth.update(advances=35, declines=15, unchanged=0,
                      new_highs=12, new_lows=3)
        health = breadth.get_health()
    """
    
    def __init__(self, lookback=50):
        self.lookback = lookback
        self.history = deque(maxlen=lookback)
        self.ad_line = 0  # Cumulative A/D line
    
    def update(self, advances, declines, unchanged=0,
              new_highs=0, new_lows=0):
        """Update with daily breadth data."""
        total = advances + declines + unchanged
        
        entry = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'advances': advances,
            'declines': declines,
            'unchanged': unchanged,
            'total': total,
            'ad_ratio': round(advances / max(declines, 1), 3),
            'ad_diff': advances - declines,
            'new_highs': new_highs,
            'new_lows': new_lows,
            'hl_ratio': round(new_highs / max(new_lows, 1), 3),
            'pct_advancing': round(advances / max(total, 1) * 100, 1)
        }
        
        self.ad_line += (advances - declines)
        entry['ad_line'] = self.ad_line
        
        self.history.append(entry)
        return entry
    
    def update_from_stocks(self, stock_returns):
        """
        Auto-calculate breadth from individual stock returns.
        
        Args:
            stock_returns: dict {symbol: daily_return_pct}
        """
        advances = sum(1 for r in stock_returns.values() if r > 0)
        declines = sum(1 for r in stock_returns.values() if r < 0)
        unchanged = sum(1 for r in stock_returns.values() if r == 0)
        
        return self.update(advances, declines, unchanged)
    
    def get_health(self):
        """Get composite market health assessment."""
        if not self.history:
            return {'health': 'UNKNOWN', 'score': 50}
        
        latest = self.history[-1]
        
        # Component scores (0-100 each)
        ad_score = min(100, latest['ad_ratio'] * 40)
        if ad_score > 80: ad_score = 80 + (ad_score - 80) * 0.5
        
        hl_score = min(100, latest['hl_ratio'] * 30) if latest['new_highs'] + latest['new_lows'] > 0 else 50
        
        pct_score = latest['pct_advancing']
        
        # Trend of A/D line
        if len(self.history) >= 5:
            recent_ad = [h['ad_line'] for h in list(self.history)[-5:]]
            ad_trend = 1 if recent_ad[-1] > recent_ad[0] else -1
            trend_score = 70 if ad_trend > 0 else 30
        else:
            trend_score = 50
        
        # McClellan-style: smoothed A/D diff
        mcclellan = self._mcclellan()
        
        # Breadth thrust check
        thrust = self._check_thrust()
        
        composite = (ad_score * 0.30 + pct_score * 0.25 + 
                    trend_score * 0.25 + hl_score * 0.20)
        
        if composite > 70:
            health = 'STRONG_BULL'
        elif composite > 55:
            health = 'HEALTHY'
        elif composite > 45:
            health = 'NEUTRAL'
        elif composite > 30:
            health = 'WEAK'
        else:
            health = 'BEARISH'
        
        return {
            'health': health,
            'score': round(composite, 1),
            'ad_ratio': latest['ad_ratio'],
            'pct_advancing': latest['pct_advancing'],
            'ad_line': self.ad_line,
            'mcclellan': mcclellan,
            'thrust': thrust,
            'details': latest
        }
    
    def _mcclellan(self):
        """McClellan Oscillator: 19-day EMA - 39-day EMA of A/D diff."""
        if len(self.history) < 20:
            return 0
        
        diffs = [h['ad_diff'] for h in self.history]
        
        ema19 = self._ema(diffs, 19)
        ema39 = self._ema(diffs, min(39, len(diffs)))
        
        return round(ema19 - ema39, 2)
    
    def _check_thrust(self):
        """
        Breadth Thrust: >61.5% of stocks advancing for 10+ days = rare bullish signal.
        """
        if len(self.history) < 10:
            return None
        
        recent = list(self.history)[-10:]
        thrust_days = sum(1 for h in recent if h['pct_advancing'] > 61.5)
        
        if thrust_days >= 8:
            return {
                'detected': True,
                'strength': 'STRONG',
                'message': f'🚀 BREADTH THRUST — {thrust_days}/10 days >61.5% advancing!'
            }
        return {'detected': False}
    
    def _ema(self, data, period):
        if not data:
            return 0
        multiplier = 2 / (period + 1)
        ema = data[0]
        for d in data[1:]:
            ema = d * multiplier + ema * (1 - multiplier)
        return ema
