"""
📈 Trend Strength Index — Composite Trend Quality Score

Combines multiple trend indicators into ONE strength number (0-100):
  ADX contribution, EMA alignment, Momentum, Higher highs/lows count
"""

import numpy as np


class TrendStrengthIndex:
    
    def calculate(self, df, lookback=50):
        if df is None or len(df) < lookback:
            return {'score': 50, 'trend': 'UNKNOWN'}
        
        recent = df.tail(lookback)
        scores = {}
        
        # 1. ADX (0-30)
        adx = recent['ADX'].iloc[-1] if 'ADX' in recent.columns else 20
        scores['adx'] = min(30, adx)
        
        # 2. EMA Alignment (0-25)
        close = recent['close'].iloc[-1]
        sma20 = recent['SMA_20'].iloc[-1] if 'SMA_20' in recent.columns else close
        ema50 = recent['EMA_50'].iloc[-1] if 'EMA_50' in recent.columns else close
        if close > sma20 > ema50: scores['ema'] = 25
        elif close < sma20 < ema50: scores['ema'] = 20
        elif close > sma20: scores['ema'] = 15
        else: scores['ema'] = 5
        
        # 3. Momentum (0-25)
        closes = recent['close'].values
        ret_20 = (closes[-1] - closes[-20]) / closes[-20] * 100 if len(closes) >= 20 else 0
        scores['momentum'] = min(25, max(0, 12.5 + ret_20 * 2))
        
        # 4. Higher Highs/Lows (0-20)
        hh = sum(1 for i in range(1, min(10, len(closes))) if closes[-i] > closes[-i-1])
        scores['hh_hl'] = hh * 2
        
        total = sum(scores.values())
        
        if total > 70: trend = 'STRONG_UPTREND'
        elif total > 55: trend = 'UPTREND'
        elif total > 45: trend = 'SIDEWAYS'
        elif total > 30: trend = 'DOWNTREND'
        else: trend = 'STRONG_DOWNTREND'
        
        return {
            'score': round(total, 1), 'trend': trend,
            'components': scores,
            'tradeable': total > 55 or total < 35
        }
