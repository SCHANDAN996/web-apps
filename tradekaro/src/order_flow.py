"""
📊 Order Flow Imbalance Detector — Buy/Sell Pressure from Price Action

Without Level 2 data, infer order flow from:
  - Delta (close vs midpoint of range → buying/selling pressure)
  - Cumulative delta
  - Volume-weighted direction
  - Absorption detection (high volume but no price move = big player absorbing)
"""

import numpy as np
import pandas as pd
from collections import deque


class OrderFlowAnalyzer:
    """
    Infers buy/sell pressure from OHLCV data.
    
    Usage:
        flow = OrderFlowAnalyzer()
        analysis = flow.analyze(df_ohlcv)
        # {'delta': 1250, 'pressure': 'BUY', 'absorption': False}
    """
    
    def __init__(self):
        self.cumulative_delta = 0
        self.delta_history = deque(maxlen=500)
    
    def analyze(self, df, lookback=20):
        """Full order flow analysis."""
        if df is None or len(df) < lookback:
            return {'pressure': 'NEUTRAL', 'delta': 0}
        
        recent = df.tail(lookback)
        
        delta = self._calculate_delta(recent)
        cum_delta = self._cumulative_delta(recent)
        absorption = self._detect_absorption(recent)
        divergence = self._delta_price_divergence(recent)
        aggression = self._aggression_ratio(recent)
        
        # Aggregate signal
        if cum_delta > 0 and aggression['ratio'] > 1.3:
            pressure = 'STRONG_BUY'
        elif cum_delta > 0:
            pressure = 'BUY'
        elif cum_delta < 0 and aggression['ratio'] < 0.7:
            pressure = 'STRONG_SELL'
        elif cum_delta < 0:
            pressure = 'SELL'
        else:
            pressure = 'NEUTRAL'
        
        return {
            'delta': round(delta, 0),
            'cumulative_delta': round(cum_delta, 0),
            'pressure': pressure,
            'absorption': absorption,
            'divergence': divergence,
            'aggression': aggression,
        }
    
    def _calculate_delta(self, df):
        """
        Estimate buy/sell delta from price action.
        Delta = Volume * (Close - Low) / (High - Low) — buy volume
              - Volume * (High - Close) / (High - Low) — sell volume
        """
        deltas = []
        for _, row in df.iterrows():
            rng = row['high'] - row['low']
            if rng > 0:
                buy_vol = row['volume'] * (row['close'] - row['low']) / rng
                sell_vol = row['volume'] * (row['high'] - row['close']) / rng
                deltas.append(buy_vol - sell_vol)
            else:
                deltas.append(0)
        
        return sum(deltas[-5:])  # Last 5 candles
    
    def _cumulative_delta(self, df):
        """Running cumulative delta over the period."""
        total = 0
        for _, row in df.iterrows():
            rng = row['high'] - row['low']
            if rng > 0:
                buy_pct = (row['close'] - row['low']) / rng
                delta = row['volume'] * (2 * buy_pct - 1)
                total += delta
        return total
    
    def _detect_absorption(self, df, vol_threshold=1.5):
        """
        Absorption: High volume but small price move = big player absorbing.
        """
        if len(df) < 5:
            return None
        
        avg_vol = df['volume'].mean()
        last = df.iloc[-1]
        body_pct = abs(last['close'] - last['open']) / max(last['open'], 1) * 100
        
        if last['volume'] > avg_vol * vol_threshold and body_pct < 0.3:
            direction = 'BUY_ABSORPTION' if last['close'] >= last['open'] else 'SELL_ABSORPTION'
            return {
                'detected': True,
                'type': direction,
                'volume_ratio': round(last['volume'] / avg_vol, 2),
                'body_pct': round(body_pct, 3),
                'message': f'🔍 {direction}: High volume ({last["volume"]:,.0f}) but tiny move ({body_pct:.2f}%)'
            }
        
        return {'detected': False}
    
    def _delta_price_divergence(self, df):
        """
        Price going up but delta going down = weakening rally (bearish divergence)
        Price going down but delta going up = selling exhaustion (bullish divergence)
        """
        if len(df) < 10:
            return None
        
        half = len(df) // 2
        first_half = df.iloc[:half]
        second_half = df.iloc[half:]
        
        price_change = second_half['close'].iloc[-1] - first_half['close'].iloc[0]
        
        delta_first = self._cumulative_delta(first_half)
        delta_second = self._cumulative_delta(second_half)
        delta_change = delta_second - delta_first
        
        if price_change > 0 and delta_change < 0:
            return {
                'type': 'BEARISH_DIVERGENCE',
                'message': '⚠️ Price rising but buying pressure declining — rally weakening'
            }
        elif price_change < 0 and delta_change > 0:
            return {
                'type': 'BULLISH_DIVERGENCE',
                'message': '📈 Price falling but selling pressure declining — reversal possible'
            }
        return {'type': 'NONE'}
    
    def _aggression_ratio(self, df):
        """
        Ratio of aggressive buyers vs sellers.
        Close near high = aggressive buying, close near low = aggressive selling.
        """
        if len(df) < 5:
            return {'ratio': 1.0}
        
        buy_aggression = 0
        sell_aggression = 0
        
        for _, row in df.tail(10).iterrows():
            rng = row['high'] - row['low']
            if rng > 0:
                buy_pct = (row['close'] - row['low']) / rng
                buy_aggression += buy_pct * row['volume']
                sell_aggression += (1 - buy_pct) * row['volume']
        
        ratio = buy_aggression / max(sell_aggression, 1)
        
        return {
            'ratio': round(ratio, 3),
            'signal': 'AGGRESSIVE_BUY' if ratio > 1.5 else 'AGGRESSIVE_SELL' if ratio < 0.67 else 'BALANCED'
        }
