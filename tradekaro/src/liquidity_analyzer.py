"""
💧 Liquidity Analyzer — Detect Low Liquidity Traps

Institutional traders check liquidity BEFORE entering:
  - Spread analysis (tight spread = liquid = safe)
  - Volume depth (is volume drying up? = trap)
  - Impact cost estimation (how much will my order move price?)
  - Liquidity score per stock (0-100)
"""

import numpy as np
import pandas as pd
from datetime import datetime


class LiquidityAnalyzer:
    """
    Measures market liquidity and warns about low-liquidity traps.
    
    Usage:
        analyzer = LiquidityAnalyzer()
        score = analyzer.get_liquidity_score(df_ohlcv)
        cost = analyzer.estimate_impact_cost(symbol, order_qty, avg_volume)
    """
    
    # Liquidity tiers
    TIERS = {
        (80, 100): {'label': 'ULTRA_LIQUID', 'emoji': '🟢', 'safe_pct': 5.0},
        (60, 80):  {'label': 'LIQUID',       'emoji': '🟡', 'safe_pct': 3.0},
        (40, 60):  {'label': 'MODERATE',     'emoji': '🟠', 'safe_pct': 1.5},
        (20, 40):  {'label': 'ILLIQUID',     'emoji': '🔴', 'safe_pct': 0.5},
        (0, 20):   {'label': 'DANGER',       'emoji': '⛔', 'safe_pct': 0.0},
    }
    
    def __init__(self):
        self.cache = {}
    
    def get_liquidity_score(self, df, lookback=20):
        """
        Calculate composite liquidity score (0-100).
        
        Components:
          1. Volume consistency (40%)
          2. Spread tightness (30%)
          3. Volume trend (20%)
          4. Price impact (10%)
        """
        if df is None or len(df) < lookback:
            return 50  # Default moderate
        
        recent = df.tail(lookback)
        
        # 1. Volume consistency (low CV = consistent = liquid)
        vol = recent['volume'].values
        vol_mean = np.mean(vol)
        vol_std = np.std(vol)
        vol_cv = vol_std / max(vol_mean, 1)
        vol_score = max(0, min(100, (1 - vol_cv) * 100))
        
        # 2. Spread tightness (high-low range as % of close)
        spreads = (recent['high'] - recent['low']) / recent['close']
        avg_spread = spreads.mean()
        spread_score = max(0, min(100, (1 - avg_spread * 20) * 100))
        
        # 3. Volume trend (increasing volume = improving liquidity)
        vol_first = np.mean(vol[:lookback//2])
        vol_last = np.mean(vol[lookback//2:])
        vol_trend = vol_last / max(vol_first, 1)
        trend_score = max(0, min(100, vol_trend * 50))
        
        # 4. Price impact (big candles on low volume = high impact)
        returns = np.abs(np.diff(recent['close'].values) / recent['close'].values[:-1])
        vol_normalized = vol[1:] / max(vol_mean, 1)
        impact = np.mean(returns / np.maximum(vol_normalized, 0.01))
        impact_score = max(0, min(100, (1 - impact * 100) * 100))
        
        # Weighted composite
        score = (vol_score * 0.40 + spread_score * 0.30 + 
                trend_score * 0.20 + impact_score * 0.10)
        
        return round(score, 1)
    
    def get_liquidity_tier(self, score):
        """Get tier label and safety limits for a liquidity score."""
        for (low, high), info in self.TIERS.items():
            if low <= score < high:
                return info
        return self.TIERS[(0, 20)]
    
    def estimate_impact_cost(self, order_qty, avg_daily_volume, avg_spread_pct=0.1):
        """
        Estimate market impact cost of an order.
        
        Rule of thumb: Impact ≈ sqrt(order_size / ADV) * constant
        """
        if avg_daily_volume <= 0:
            return float('inf')
        
        participation_rate = order_qty / avg_daily_volume
        
        # Square root impact model (standard in quant finance)
        impact_pct = np.sqrt(participation_rate) * 0.5 + avg_spread_pct / 2
        
        return {
            'impact_pct': round(impact_pct, 4),
            'participation_rate': round(participation_rate, 4),
            'recommendation': 'TWAP' if participation_rate > 0.05 else 'MARKET',
            'safe': participation_rate < 0.10
        }
    
    def scan_stocks(self, stock_data_dict):
        """
        Scan multiple stocks and rank by liquidity.
        
        Args:
            stock_data_dict: {symbol: df_ohlcv}
        Returns:
            sorted list of (symbol, score, tier)
        """
        results = []
        for sym, df in stock_data_dict.items():
            score = self.get_liquidity_score(df)
            tier = self.get_liquidity_tier(score)
            results.append({
                'symbol': sym,
                'score': score,
                'tier': tier['label'],
                'emoji': tier['emoji'],
                'safe_position_pct': tier['safe_pct']
            })
        
        return sorted(results, key=lambda x: x['score'], reverse=True)
