"""
🔬 Market Microstructure Analyzer — Tick-Level Pattern Detection

Analyzes fine-grained market behavior:
  - Bid-ask spread patterns (widening = uncertainty)
  - Tick direction analysis (uptick/downtick ratio)
  - Large block trade detection
  - Intraday volume profile (when does volume spike?)
  - Opening range breakout detection
"""

import numpy as np
import pandas as pd
from datetime import datetime, time as dt_time


class MicrostructureAnalyzer:
    """
    Analyzes market microstructure patterns for edge detection.
    
    Usage:
        micro = MicrostructureAnalyzer()
        profile = micro.intraday_volume_profile(df_1m)
        orb = micro.opening_range_breakout(df_1m, range_minutes=15)
    """
    
    # Standard Indian market session times
    MARKET_OPEN = dt_time(9, 15)
    MARKET_CLOSE = dt_time(15, 30)
    
    # Key intraday windows
    OPEN_RANGE = (dt_time(9, 15), dt_time(9, 30))   # First 15 min
    MID_MORNING = (dt_time(10, 0), dt_time(11, 30))  # Mid-morning
    LUNCH_LULL = (dt_time(12, 0), dt_time(13, 30))   # Lunch = low volume
    POWER_HOUR = (dt_time(14, 30), dt_time(15, 15))  # Last hour = action
    CLOSE_RANGE = (dt_time(15, 15), dt_time(15, 30)) # Closing auction
    
    def intraday_volume_profile(self, df_1m):
        """
        Analyze volume distribution across the trading day.
        Returns volume % by 30-min buckets.
        """
        if df_1m is None or len(df_1m) < 100:
            return {}
        
        df = df_1m.copy()
        if not isinstance(df.index, pd.DatetimeIndex):
            return {}
        
        df['hour_min'] = df.index.hour * 100 + df.index.minute
        
        buckets = {
            '09:15-09:45': (915, 945),
            '09:45-10:15': (945, 1015),
            '10:15-11:00': (1015, 1100),
            '11:00-12:00': (1100, 1200),
            '12:00-13:00': (1200, 1300),
            '13:00-14:00': (1300, 1400),
            '14:00-14:30': (1400, 1430),
            '14:30-15:00': (1430, 1500),
            '15:00-15:30': (1500, 1530),
        }
        
        total_vol = df['volume'].sum()
        profile = {}
        
        for label, (start, end) in buckets.items():
            mask = (df['hour_min'] >= start) & (df['hour_min'] < end)
            bucket_vol = df.loc[mask, 'volume'].sum()
            profile[label] = {
                'volume': int(bucket_vol),
                'pct': round(bucket_vol / max(total_vol, 1) * 100, 1)
            }
        
        return profile
    
    def opening_range_breakout(self, df_1m, range_minutes=15):
        """
        Opening Range Breakout (ORB) strategy.
        
        After first 15 minutes:
          Price > OR High → BUY signal
          Price < OR Low  → SELL signal
          
        Returns:
            dict: {high, low, breakout_direction, breakout_candle}
        """
        if df_1m is None or len(df_1m) < range_minutes + 5:
            return None
        
        df = df_1m.copy()
        if not isinstance(df.index, pd.DatetimeIndex):
            return None
        
        # Get today's data
        today = df.index[-1].date()
        today_data = df[df.index.date == today]
        
        if len(today_data) < range_minutes:
            return None
        
        # Opening range (first N minutes)
        or_data = today_data.head(range_minutes)
        or_high = or_data['high'].max()
        or_low = or_data['low'].min()
        or_range = or_high - or_low
        
        # Check for breakout after OR period
        post_or = today_data.iloc[range_minutes:]
        breakout = None
        
        for idx, row in post_or.iterrows():
            if row['close'] > or_high:
                breakout = {
                    'direction': 'BULLISH',
                    'breakout_price': row['close'],
                    'breakout_time': idx.strftime('%H:%M'),
                    'target': or_high + or_range,
                    'stoploss': or_low
                }
                break
            elif row['close'] < or_low:
                breakout = {
                    'direction': 'BEARISH',
                    'breakout_price': row['close'],
                    'breakout_time': idx.strftime('%H:%M'),
                    'target': or_low - or_range,
                    'stoploss': or_high
                }
                break
        
        return {
            'or_high': round(or_high, 2),
            'or_low': round(or_low, 2),
            'or_range': round(or_range, 2),
            'or_range_pct': round(or_range / or_high * 100, 3),
            'breakout': breakout,
            'date': str(today)
        }
    
    def tick_direction_ratio(self, df):
        """
        Calculate uptick/downtick ratio.
        >1.0 = bullish pressure, <1.0 = bearish pressure
        """
        if df is None or len(df) < 10:
            return 1.0
        
        closes = df['close'].values
        upticks = sum(1 for i in range(1, len(closes)) if closes[i] > closes[i-1])
        downticks = sum(1 for i in range(1, len(closes)) if closes[i] < closes[i-1])
        
        ratio = upticks / max(downticks, 1)
        
        return {
            'ratio': round(ratio, 3),
            'upticks': upticks,
            'downticks': downticks,
            'signal': 'BULLISH' if ratio > 1.3 else 'BEARISH' if ratio < 0.7 else 'NEUTRAL'
        }
    
    def detect_block_trades(self, df, threshold_multiplier=5.0):
        """
        Detect unusually large trades (blocks).
        A block = volume > threshold_multiplier * average volume.
        """
        if df is None or len(df) < 20:
            return []
        
        avg_vol = df['volume'].mean()
        threshold = avg_vol * threshold_multiplier
        
        blocks = []
        for idx, row in df.iterrows():
            if row['volume'] > threshold:
                blocks.append({
                    'time': idx.strftime('%H:%M') if hasattr(idx, 'strftime') else str(idx),
                    'volume': int(row['volume']),
                    'multiplier': round(row['volume'] / avg_vol, 1),
                    'direction': 'BUY' if row['close'] > row['open'] else 'SELL',
                    'price': row['close']
                })
        
        return blocks
    
    def session_momentum(self, df_1m):
        """
        Calculate momentum across different session windows.
        """
        if df_1m is None or not isinstance(df_1m.index, pd.DatetimeIndex):
            return {}
        
        today = df_1m.index[-1].date()
        today_data = df_1m[df_1m.index.date == today]
        
        sessions = {
            'opening': self.OPEN_RANGE,
            'mid_morning': self.MID_MORNING,
            'lunch': self.LUNCH_LULL,
            'power_hour': self.POWER_HOUR,
        }
        
        momentum = {}
        for name, (start, end) in sessions.items():
            mask = (today_data.index.time >= start) & (today_data.index.time <= end)
            session_data = today_data[mask]
            
            if len(session_data) >= 2:
                ret = (session_data['close'].iloc[-1] / session_data['close'].iloc[0] - 1) * 100
                momentum[name] = {
                    'return_pct': round(ret, 3),
                    'volume': int(session_data['volume'].sum()),
                    'signal': 'BUY' if ret > 0.1 else 'SELL' if ret < -0.1 else 'FLAT'
                }
        
        return momentum
