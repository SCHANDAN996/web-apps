"""
📊 Pair Trading Engine — Statistical Arbitrage Between Correlated Stocks

Find 2 stocks that move together (HDFCBANK-ICICIBANK, TCS-INFY):
  1. Calculate spread (price ratio)
  2. When spread deviates > 2σ → trade the convergence
  3. Buy the cheap one, sell the expensive one
  4. Profit when spread reverts to mean

Market-neutral strategy: makes money regardless of market direction.
"""

import numpy as np
import pandas as pd
from datetime import datetime
from collections import deque


class PairTradingEngine:
    """
    Statistical arbitrage via pairs trading.
    
    Usage:
        engine = PairTradingEngine()
        engine.add_pair('HDFCBANK', 'ICICIBANK', hdfc_prices, icici_prices)
        signal = engine.get_signal('HDFCBANK', 'ICICIBANK')
        # {'action': 'BUY_A_SELL_B', 'z_score': -2.3, 'spread': 0.85}
    """
    
    KNOWN_PAIRS = [
        ('HDFCBANK', 'ICICIBANK'),
        ('TCS', 'INFY'),
        ('TATASTEEL', 'JSWSTEEL'),
        ('SUNPHARMA', 'DRREDDY'),
        ('RELIANCE', 'ONGC'),
        ('MARUTI', 'TATAMOTORS'),
        ('SBIN', 'KOTAKBANK'),
    ]
    
    def __init__(self, lookback=60, entry_z=2.0, exit_z=0.5):
        self.lookback = lookback
        self.entry_z = entry_z
        self.exit_z = exit_z
        self.pairs = {}
        self.active_trades = {}
    
    def add_pair(self, sym_a, sym_b, prices_a, prices_b):
        """Register a tradeable pair."""
        key = f"{sym_a}_{sym_b}"
        
        a = np.array(prices_a[-self.lookback:])
        b = np.array(prices_b[-self.lookback:])
        
        if len(a) != len(b) or len(a) < 20:
            return
        
        ratio = a / np.maximum(b, 0.01)
        
        self.pairs[key] = {
            'sym_a': sym_a, 'sym_b': sym_b,
            'ratio': ratio,
            'mean': np.mean(ratio),
            'std': np.std(ratio),
            'correlation': float(np.corrcoef(a, b)[0, 1]),
            'last_a': float(a[-1]),
            'last_b': float(b[-1]),
        }
    
    def get_signal(self, sym_a, sym_b):
        """Get pair trading signal."""
        key = f"{sym_a}_{sym_b}"
        if key not in self.pairs:
            return {'action': 'NO_DATA'}
        
        pair = self.pairs[key]
        current_ratio = pair['last_a'] / max(pair['last_b'], 0.01)
        z_score = (current_ratio - pair['mean']) / max(pair['std'], 0.001)
        
        if z_score > self.entry_z:
            action = 'SELL_A_BUY_B'  # A is expensive, B is cheap
            reason = f'{sym_a} overvalued vs {sym_b}'
        elif z_score < -self.entry_z:
            action = 'BUY_A_SELL_B'  # A is cheap, B is expensive
            reason = f'{sym_a} undervalued vs {sym_b}'
        elif abs(z_score) < self.exit_z and key in self.active_trades:
            action = 'CLOSE_PAIR'
            reason = 'Spread reverted to mean'
        else:
            action = 'HOLD'
            reason = f'Z-score {z_score:.2f} within range'
        
        return {
            'action': action,
            'z_score': round(z_score, 3),
            'current_ratio': round(current_ratio, 4),
            'mean_ratio': round(pair['mean'], 4),
            'correlation': pair['correlation'],
            'reason': reason,
            'pair': f'{sym_a}/{sym_b}'
        }
    
    def scan_all_pairs(self):
        """Scan all registered pairs for signals."""
        signals = []
        for key, pair in self.pairs.items():
            sig = self.get_signal(pair['sym_a'], pair['sym_b'])
            if sig['action'] not in ['HOLD', 'NO_DATA']:
                signals.append(sig)
        return sorted(signals, key=lambda x: abs(x['z_score']), reverse=True)
    
    def cointegration_test(self, prices_a, prices_b):
        """Simple cointegration check (are they truly mean-reverting?)."""
        a = np.array(prices_a)
        b = np.array(prices_b)
        if len(a) != len(b) or len(a) < 30:
            return {'cointegrated': False}
        
        ratio = a / np.maximum(b, 0.01)
        # ADF-like: check if ratio crosses mean frequently
        mean = np.mean(ratio)
        crossings = sum(1 for i in range(1, len(ratio))
                       if (ratio[i-1] - mean) * (ratio[i] - mean) < 0)
        
        expected_crossings = len(ratio) * 0.15
        is_coint = crossings > expected_crossings
        
        return {
            'cointegrated': is_coint,
            'crossings': crossings,
            'expected': round(expected_crossings, 0),
            'correlation': round(float(np.corrcoef(a, b)[0, 1]), 3)
        }
