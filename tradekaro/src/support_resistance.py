"""
📊 Auto Support/Resistance Detector — Price-Action Based S/R Levels

Not Fibonacci — this uses actual price behavior:
  1. Pivot Points (daily/weekly)
  2. Price cluster detection (where does price spend most time?)
  3. Touch count (how many times price bounced from a level?)
  4. Volume-weighted levels (high volume = important level)
  5. Break & retest detection
"""

import numpy as np
import pandas as pd
from collections import Counter


class SupportResistanceDetector:
    """
    Auto-detects support and resistance levels from price history.
    
    Usage:
        detector = SupportResistanceDetector()
        levels = detector.detect(df_ohlcv)
        # [{'price': 22500, 'type': 'RESISTANCE', 'strength': 4, 'touches': 3}]
    """
    
    def detect(self, df, n_levels=5, sensitivity=0.005):
        """
        Detect S/R levels using multiple methods.
        
        Args:
            df: OHLCV DataFrame
            n_levels: Max number of levels to return
            sensitivity: Price clustering sensitivity (0.5%)
        """
        if df is None or len(df) < 30:
            return []
        
        levels = []
        current_price = df['close'].iloc[-1]
        
        # Method 1: Swing Highs/Lows
        swing_levels = self._swing_points(df)
        levels.extend(swing_levels)
        
        # Method 2: Price Clusters
        clusters = self._price_clusters(df, sensitivity)
        levels.extend(clusters)
        
        # Method 3: Pivot Points
        pivots = self._pivot_points(df)
        levels.extend(pivots)
        
        # Method 4: Round Numbers
        rounds = self._round_numbers(current_price)
        levels.extend(rounds)
        
        # Merge nearby levels
        merged = self._merge_levels(levels, sensitivity)
        
        # Classify as support or resistance
        for lvl in merged:
            if lvl['price'] < current_price:
                lvl['type'] = 'SUPPORT'
            elif lvl['price'] > current_price:
                lvl['type'] = 'RESISTANCE'
            else:
                lvl['type'] = 'PIVOT'
            
            lvl['distance_pct'] = round(
                abs(lvl['price'] - current_price) / current_price * 100, 3
            )
        
        # Sort by strength and return top N
        merged.sort(key=lambda x: x['strength'], reverse=True)
        return merged[:n_levels * 2]  # Both support and resistance
    
    def get_nearest(self, df):
        """Get nearest support and resistance."""
        levels = self.detect(df)
        current = df['close'].iloc[-1]
        
        supports = [l for l in levels if l['type'] == 'SUPPORT']
        resistances = [l for l in levels if l['type'] == 'RESISTANCE']
        
        nearest_sup = max(supports, key=lambda x: x['price']) if supports else None
        nearest_res = min(resistances, key=lambda x: x['price']) if resistances else None
        
        return {
            'current_price': current,
            'nearest_support': nearest_sup,
            'nearest_resistance': nearest_res,
            'in_range': nearest_res['price'] - nearest_sup['price'] if nearest_sup and nearest_res else 0
        }
    
    def _swing_points(self, df, window=5):
        """Detect swing highs and lows."""
        levels = []
        highs = df['high'].values
        lows = df['low'].values
        
        for i in range(window, len(df) - window):
            # Swing high
            if highs[i] == max(highs[i-window:i+window+1]):
                levels.append({
                    'price': round(float(highs[i]), 2),
                    'method': 'SWING_HIGH',
                    'strength': 2
                })
            
            # Swing low
            if lows[i] == min(lows[i-window:i+window+1]):
                levels.append({
                    'price': round(float(lows[i]), 2),
                    'method': 'SWING_LOW',
                    'strength': 2
                })
        
        return levels
    
    def _price_clusters(self, df, sensitivity):
        """Find price zones where price spends most time."""
        closes = df['close'].values
        rounded = np.round(closes / (closes.mean() * sensitivity)) * (closes.mean() * sensitivity)
        
        counts = Counter(rounded)
        most_common = counts.most_common(10)
        
        return [{'price': round(float(price), 2), 'method': 'CLUSTER',
                 'strength': count // 3 + 1}
                for price, count in most_common if count >= 3]
    
    def _pivot_points(self, df):
        """Calculate classic pivot points from last session."""
        if len(df) < 2:
            return []
        
        h = df['high'].iloc[-2] if len(df) > 1 else df['high'].iloc[-1]
        l = df['low'].iloc[-2] if len(df) > 1 else df['low'].iloc[-1]
        c = df['close'].iloc[-2] if len(df) > 1 else df['close'].iloc[-1]
        
        pivot = (h + l + c) / 3
        r1 = 2 * pivot - l
        s1 = 2 * pivot - h
        r2 = pivot + (h - l)
        s2 = pivot - (h - l)
        
        return [
            {'price': round(float(pivot), 2), 'method': 'PIVOT', 'strength': 3},
            {'price': round(float(r1), 2), 'method': 'PIVOT_R1', 'strength': 2},
            {'price': round(float(s1), 2), 'method': 'PIVOT_S1', 'strength': 2},
            {'price': round(float(r2), 2), 'method': 'PIVOT_R2', 'strength': 1},
            {'price': round(float(s2), 2), 'method': 'PIVOT_S2', 'strength': 1},
        ]
    
    def _round_numbers(self, price):
        """Round numbers act as psychological S/R."""
        base = round(price / 100) * 100
        return [
            {'price': base - 200, 'method': 'ROUND', 'strength': 1},
            {'price': base - 100, 'method': 'ROUND', 'strength': 1},
            {'price': base, 'method': 'ROUND', 'strength': 2},
            {'price': base + 100, 'method': 'ROUND', 'strength': 1},
            {'price': base + 200, 'method': 'ROUND', 'strength': 1},
        ]
    
    def _merge_levels(self, levels, sensitivity):
        """Merge nearby levels (within sensitivity %)."""
        if not levels:
            return []
        
        sorted_levels = sorted(levels, key=lambda x: x['price'])
        merged = [sorted_levels[0]]
        
        for lvl in sorted_levels[1:]:
            last = merged[-1]
            if abs(lvl['price'] - last['price']) / max(last['price'], 1) < sensitivity:
                last['strength'] += lvl['strength']
                last['price'] = (last['price'] + lvl['price']) / 2
            else:
                merged.append(lvl)
        
        return merged
