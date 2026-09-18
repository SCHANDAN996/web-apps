"""
🕐 Intraday Session Classifier — Detect Market Phases (Wyckoff)

Wyckoff Theory phases:
  ACCUMULATION → Smart money buying quietly (low vol, tight range)
  MARKUP       → Price trending up aggressively
  DISTRIBUTION → Smart money selling quietly (high vol, no progress)
  MARKDOWN     → Price trending down aggressively

Also detects intraday phases:
  OPENING_DRIVE (9:15-9:45)
  MID_DAY_DRIFT (11:00-13:30)
  POWER_HOUR (14:30-15:15)
"""

import numpy as np
from datetime import datetime, time as dt_time


class SessionClassifier:
    """
    Classifies current market phase for strategy selection.
    
    Usage:
        classifier = SessionClassifier()
        phase = classifier.classify(df_ohlcv)
        # {'phase': 'ACCUMULATION', 'confidence': 0.78}
    """
    
    INTRADAY_SESSIONS = {
        'PRE_OPEN':      (dt_time(9, 0), dt_time(9, 15)),
        'OPENING_DRIVE': (dt_time(9, 15), dt_time(9, 45)),
        'MORNING_TREND': (dt_time(9, 45), dt_time(11, 0)),
        'MID_DAY_DRIFT': (dt_time(11, 0), dt_time(13, 30)),
        'AFTERNOON':     (dt_time(13, 30), dt_time(14, 30)),
        'POWER_HOUR':    (dt_time(14, 30), dt_time(15, 15)),
        'CLOSING':       (dt_time(15, 15), dt_time(15, 30)),
    }
    
    SESSION_TRAITS = {
        'OPENING_DRIVE': 'High volatility, gap fills, initial trend setting',
        'MORNING_TREND': 'Strongest trends, follow breakout direction',
        'MID_DAY_DRIFT': 'Low volume chop, avoid new entries',
        'POWER_HOUR':    'Institutional activity, strong moves, trend resumption',
        'CLOSING':       'Closing auction, avoid new positions',
    }
    
    def classify_wyckoff(self, df, lookback=50):
        """Classify into Wyckoff phase."""
        if df is None or len(df) < lookback:
            return {'phase': 'UNKNOWN', 'confidence': 0}
        
        recent = df.tail(lookback)
        
        close = recent['close'].values
        volume = recent['volume'].values
        high = recent['high'].values
        low = recent['low'].values
        
        # Metrics
        price_trend = (close[-1] - close[0]) / close[0] * 100
        vol_trend = np.mean(volume[-10:]) / max(np.mean(volume[:10]), 1)
        range_pct = np.mean((high - low) / close) * 100
        
        # Range contraction/expansion
        early_range = np.mean((high[:lookback//2] - low[:lookback//2]) / close[:lookback//2])
        late_range = np.mean((high[lookback//2:] - low[lookback//2:]) / close[lookback//2:])
        range_ratio = late_range / max(early_range, 0.001)
        
        # Classify
        if abs(price_trend) < 2 and vol_trend < 0.8 and range_ratio < 0.8:
            phase = 'ACCUMULATION'
            confidence = min(0.9, (2 - abs(price_trend)) / 2)
            advice = 'Smart money buying quietly — prepare for breakout UP'
        elif price_trend > 3 and vol_trend > 1.2:
            phase = 'MARKUP'
            confidence = min(0.9, price_trend / 10)
            advice = 'Strong uptrend — follow the trend, buy dips'
        elif abs(price_trend) < 2 and vol_trend > 1.3 and range_ratio > 1.2:
            phase = 'DISTRIBUTION'
            confidence = min(0.9, vol_trend / 2)
            advice = 'Smart money selling — prepare for breakdown DOWN'
        elif price_trend < -3 and vol_trend > 1.0:
            phase = 'MARKDOWN'
            confidence = min(0.9, abs(price_trend) / 10)
            advice = 'Strong downtrend — avoid longs, short rallies'
        else:
            phase = 'TRANSITION'
            confidence = 0.4
            advice = 'Phase transition — wait for clarity'
        
        return {
            'phase': phase,
            'confidence': round(confidence, 2),
            'advice': advice,
            'metrics': {
                'price_trend': round(price_trend, 2),
                'vol_trend': round(vol_trend, 2),
                'range_ratio': round(range_ratio, 2)
            }
        }
    
    def get_intraday_session(self):
        """Get current intraday session."""
        now = datetime.now().time()
        
        for name, (start, end) in self.INTRADAY_SESSIONS.items():
            if start <= now <= end:
                return {
                    'session': name,
                    'traits': self.SESSION_TRAITS.get(name, ''),
                    'should_trade': name not in ['PRE_OPEN', 'CLOSING', 'MID_DAY_DRIFT']
                }
        
        return {'session': 'MARKET_CLOSED', 'should_trade': False}
    
    def get_strategy_for_session(self):
        """Recommend strategy based on current session."""
        session = self.get_intraday_session()
        name = session['session']
        
        strategies = {
            'OPENING_DRIVE': {'style': 'ORB_BREAKOUT', 'risk': 'HIGH', 'tip': 'Wait for ORB, trade breakout'},
            'MORNING_TREND': {'style': 'TREND_FOLLOW', 'risk': 'MEDIUM', 'tip': 'Follow established direction'},
            'MID_DAY_DRIFT': {'style': 'AVOID', 'risk': 'LOW', 'tip': 'No new entries, manage existing'},
            'AFTERNOON':     {'style': 'SCALPING', 'risk': 'MEDIUM', 'tip': 'Small quick trades'},
            'POWER_HOUR':    {'style': 'MOMENTUM', 'risk': 'HIGH', 'tip': 'Strong moves, follow big volume'},
            'CLOSING':       {'style': 'EXIT_ONLY', 'risk': 'LOW', 'tip': 'Close intraday, no new entries'},
            'MARKET_CLOSED': {'style': 'NONE', 'risk': 'NONE', 'tip': 'Market closed'},
        }
        
        return {**session, **strategies.get(name, strategies['MARKET_CLOSED'])}
