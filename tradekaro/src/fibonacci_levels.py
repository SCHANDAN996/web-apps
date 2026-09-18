"""
📐 Fibonacci Auto-Levels — Support/Resistance Using Fibonacci Retracements

Auto-detects swing high/low and draws:
  - Retracement levels: 23.6%, 38.2%, 50%, 61.8%, 78.6%
  - Extension levels: 127.2%, 161.8%, 261.8%
  - Pivot clusters (confluence zones)

Used for:
  - Entry targets (buy at 61.8% retracement)
  - Exit targets (sell at 161.8% extension)
  - Stop-loss placement (below 78.6%)
"""

import numpy as np


class FibonacciLevels:
    """
    Auto-calculate Fibonacci retracement and extension levels.
    
    Usage:
        fib = FibonacciLevels()
        levels = fib.calculate(df_ohlcv, lookback=100)
        # {'0.236': 22450, '0.382': 22200, '0.5': 22000, '0.618': 21800, ...}
    """
    
    RETRACEMENT_RATIOS = [0.0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0]
    EXTENSION_RATIOS = [1.272, 1.618, 2.0, 2.618]
    
    def calculate(self, df, lookback=100):
        """
        Auto-detect swing high/low and calculate Fibonacci levels.
        """
        if df is None or len(df) < lookback:
            return None
        
        recent = df.tail(lookback)
        high = recent['high'].max()
        low = recent['low'].min()
        
        high_idx = recent['high'].idxmax()
        low_idx = recent['low'].idxmin()
        
        # Determine trend direction
        if hasattr(high_idx, '__gt__'):
            is_uptrend = low_idx < high_idx
        else:
            is_uptrend = True
        
        diff = high - low
        
        # Retracement levels
        levels = {}
        for ratio in self.RETRACEMENT_RATIOS:
            if is_uptrend:
                # Retracing from high
                price = high - diff * ratio
            else:
                # Retracing from low
                price = low + diff * ratio
            levels[f'R_{ratio}'] = round(price, 2)
        
        # Extension levels
        for ratio in self.EXTENSION_RATIOS:
            if is_uptrend:
                price = high + diff * (ratio - 1)
            else:
                price = low - diff * (ratio - 1)
            levels[f'E_{ratio}'] = round(price, 2)
        
        return {
            'swing_high': round(high, 2),
            'swing_low': round(low, 2),
            'trend': 'UPTREND' if is_uptrend else 'DOWNTREND',
            'range': round(diff, 2),
            'levels': levels,
            'key_support': levels.get('R_0.618', low),
            'key_resistance': levels.get('R_0.382', high),
            'golden_ratio': levels.get('R_0.618', 0),
        }
    
    def find_confluence_zones(self, df, timeframes_data=None):
        """
        Find price zones where multiple Fibonacci levels cluster.
        Confluence = stronger S/R level.
        """
        levels_list = []
        
        # Multiple lookback periods
        for lb in [50, 100, 200]:
            if len(df) >= lb:
                result = self.calculate(df, lookback=lb)
                if result:
                    levels_list.extend(result['levels'].values())
        
        if not levels_list:
            return []
        
        # Cluster levels within 0.5% of each other
        levels_sorted = sorted(levels_list)
        clusters = []
        current_cluster = [levels_sorted[0]]
        
        for i in range(1, len(levels_sorted)):
            if abs(levels_sorted[i] - current_cluster[-1]) / current_cluster[-1] < 0.005:
                current_cluster.append(levels_sorted[i])
            else:
                if len(current_cluster) >= 2:
                    clusters.append({
                        'price': round(np.mean(current_cluster), 2),
                        'strength': len(current_cluster),
                        'type': 'CONFLUENCE'
                    })
                current_cluster = [levels_sorted[i]]
        
        if len(current_cluster) >= 2:
            clusters.append({
                'price': round(np.mean(current_cluster), 2),
                'strength': len(current_cluster),
                'type': 'CONFLUENCE'
            })
        
        return sorted(clusters, key=lambda x: x['strength'], reverse=True)
    
    def get_trade_levels(self, df, current_price):
        """
        Get actionable trade levels based on current price position.
        """
        result = self.calculate(df)
        if not result:
            return None
        
        levels = result['levels']
        
        # Find nearest support and resistance
        supports = [v for v in levels.values() if v < current_price]
        resistances = [v for v in levels.values() if v > current_price]
        
        nearest_support = max(supports) if supports else result['swing_low']
        nearest_resistance = min(resistances) if resistances else result['swing_high']
        
        return {
            'current_price': current_price,
            'nearest_support': nearest_support,
            'nearest_resistance': nearest_resistance,
            'risk_reward': round(
                (nearest_resistance - current_price) / 
                max(current_price - nearest_support, 0.01), 2
            ),
            'position_in_range': round(
                (current_price - result['swing_low']) / max(result['range'], 0.01), 3
            ),
            'buy_zone': current_price <= result['golden_ratio'],
            'all_levels': levels
        }
