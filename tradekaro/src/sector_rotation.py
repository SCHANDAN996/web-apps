"""
🔄 Sector Rotation Engine — Auto-Rotate Capital Between Sectors

Market Cycle Theory:
  Early Bull  → IT, Financials (rate-sensitive)
  Mid Bull    → Auto, Consumer (demand growth)
  Late Bull   → Metals, Energy (commodities boom)
  Bear Market → Pharma, FMCG (defensive)
  Recovery    → Infra, Real Estate (govt spending)

Uses regime + macro data to auto-shift sector weights.
"""

from datetime import datetime
from collections import defaultdict


class SectorRotationEngine:
    """
    Auto-rotates capital allocation across sectors based on market cycle.
    
    Usage:
        engine = SectorRotationEngine()
        weights = engine.get_sector_weights('BULL_TREND', iv_percentile=30)
        # {'IT': 0.25, 'BANKS': 0.20, 'AUTO': 0.15, ...}
    """
    
    # Sector classification for Indian market
    SECTOR_STOCKS = {
        'IT':        ['TCS', 'INFY', 'WIPRO', 'HCLTECH', 'TECHM', 'LTIM'],
        'BANKS':     ['HDFCBANK', 'ICICIBANK', 'SBIN', 'KOTAKBANK', 'AXISBANK', 'INDUSINDBK'],
        'AUTO':      ['TATAMOTORS', 'MARUTI', 'BAJAJ-AUTO', 'M&M', 'HEROMOTOCO', 'EICHERMOT'],
        'PHARMA':    ['SUNPHARMA', 'DRREDDY', 'CIPLA', 'DIVISLAB', 'APOLLOHOSP'],
        'METALS':    ['TATASTEEL', 'JSWSTEEL', 'HINDALCO', 'ADANIENT', 'COALINDIA'],
        'OIL':       ['RELIANCE', 'ONGC', 'BPCL', 'IOC'],
        'FMCG':      ['HINDUNILVR', 'ITC', 'NESTLEIND', 'BRITANNIA', 'TATACONSUM'],
        'INFRA':     ['LTIM', 'ADANIPORTS', 'ULTRACEMCO', 'GRASIM', 'SHREECEM'],
    }
    
    # Regime → Sector weight matrix
    ROTATION_MATRIX = {
        'BULL_TREND': {
            'IT': 0.20, 'BANKS': 0.25, 'AUTO': 0.15, 'PHARMA': 0.05,
            'METALS': 0.15, 'OIL': 0.10, 'FMCG': 0.05, 'INFRA': 0.05
        },
        'BEAR_TREND': {
            'IT': 0.10, 'BANKS': 0.05, 'AUTO': 0.05, 'PHARMA': 0.25,
            'METALS': 0.05, 'OIL': 0.05, 'FMCG': 0.30, 'INFRA': 0.15
        },
        'SIDEWAYS_QUIET': {
            'IT': 0.15, 'BANKS': 0.15, 'AUTO': 0.10, 'PHARMA': 0.15,
            'METALS': 0.10, 'OIL': 0.10, 'FMCG': 0.15, 'INFRA': 0.10
        },
        'SIDEWAYS_VOLATILE': {
            'IT': 0.10, 'BANKS': 0.10, 'AUTO': 0.05, 'PHARMA': 0.20,
            'METALS': 0.10, 'OIL': 0.10, 'FMCG': 0.25, 'INFRA': 0.10
        },
        'TRANSITION': {
            'IT': 0.15, 'BANKS': 0.15, 'AUTO': 0.10, 'PHARMA': 0.15,
            'METALS': 0.10, 'OIL': 0.10, 'FMCG': 0.15, 'INFRA': 0.10
        },
    }
    
    # IV adjustment: High IV → more defensive
    IV_ADJUSTMENT = {
        'high_iv': {'PHARMA': 0.05, 'FMCG': 0.05, 'BANKS': -0.05, 'AUTO': -0.05},
        'low_iv':  {'BANKS': 0.05, 'IT': 0.05, 'PHARMA': -0.05, 'FMCG': -0.05}
    }
    
    def __init__(self):
        self.current_weights = {}
        self.rotation_history = []
    
    def get_sector_weights(self, regime, iv_percentile=50, momentum_data=None):
        """
        Get optimal sector weights for current market conditions.
        
        Args:
            regime: Market regime string
            iv_percentile: Current IV percentile (0-100)
            momentum_data: Optional dict {sector: momentum_score}
        """
        base = self.ROTATION_MATRIX.get(regime, self.ROTATION_MATRIX['SIDEWAYS_QUIET']).copy()
        
        # IV adjustment
        if iv_percentile > 60:
            adj = self.IV_ADJUSTMENT['high_iv']
        elif iv_percentile < 40:
            adj = self.IV_ADJUSTMENT['low_iv']
        else:
            adj = {}
        
        for sector, delta in adj.items():
            if sector in base:
                base[sector] = max(0, min(0.40, base[sector] + delta))
        
        # Momentum tilt (increase weight for strong momentum sectors)
        if momentum_data:
            for sector, mom in momentum_data.items():
                if sector in base and mom > 0.6:
                    base[sector] = min(0.35, base[sector] + 0.05)
                elif sector in base and mom < 0.4:
                    base[sector] = max(0.02, base[sector] - 0.05)
        
        # Normalize to sum = 1.0
        total = sum(base.values())
        if total > 0:
            base = {k: round(v / total, 3) for k, v in base.items()}
        
        self.current_weights = base
        self.rotation_history.append({
            'time': datetime.now().isoformat(),
            'regime': regime,
            'weights': base
        })
        
        return base
    
    def get_stocks_for_sector(self, sector):
        """Get stocks in a sector."""
        return self.SECTOR_STOCKS.get(sector, [])
    
    def get_top_sectors(self, n=3):
        """Get top N sectors by current weight."""
        sorted_sectors = sorted(self.current_weights.items(), 
                              key=lambda x: x[1], reverse=True)
        return sorted_sectors[:n]
    
    def get_rotation_signal(self, prev_regime, curr_regime):
        """Detect if a sector rotation should happen."""
        if prev_regime == curr_regime:
            return None
        
        prev_w = self.ROTATION_MATRIX.get(prev_regime, {})
        curr_w = self.ROTATION_MATRIX.get(curr_regime, {})
        
        increases = {s: curr_w.get(s, 0) - prev_w.get(s, 0) 
                    for s in set(list(prev_w.keys()) + list(curr_w.keys()))
                    if curr_w.get(s, 0) - prev_w.get(s, 0) > 0.05}
        
        decreases = {s: prev_w.get(s, 0) - curr_w.get(s, 0)
                    for s in set(list(prev_w.keys()) + list(curr_w.keys()))
                    if prev_w.get(s, 0) - curr_w.get(s, 0) > 0.05}
        
        if increases or decreases:
            return {
                'action': 'ROTATE',
                'from': prev_regime,
                'to': curr_regime,
                'increase': increases,
                'decrease': decreases,
                'message': f"🔄 Rotate: Add {list(increases.keys())}, Reduce {list(decreases.keys())}"
            }
        return None
