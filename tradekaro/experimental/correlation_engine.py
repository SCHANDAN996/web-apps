"""
🌐 Cross-Asset Correlation Engine

Detects inter-market relationships and trades them:
  Gold ↑ → Banks ↓ (negative correlation)
  USD/INR ↑ → IT stocks ↑ (positive — export earnings)
  VIX ↑ → NIFTY ↓ (fear gauge)
  Oil ↑ → Paint/Aviation ↓ (cost pressure)

Features:
  - Rolling correlation matrix (30/60/90 day windows)
  - Lead-lag detection (which asset moves first?)
  - Regime-specific correlations
  - Alert when correlation breaks (regime change signal)
"""

import numpy as np
import pandas as pd
from collections import defaultdict


class CorrelationEngine:
    """
    Cross-asset correlation analyzer.
    
    Usage:
        engine = CorrelationEngine()
        engine.add_data('NIFTY', nifty_prices)
        engine.add_data('GOLD', gold_prices)
        
        corr = engine.get_correlation('NIFTY', 'GOLD')
        # -0.45 (negative — gold is hedge)
        
        leads = engine.detect_lead_lag('GOLD', 'NIFTY', max_lag=5)
        # {'lag': 2, 'corr': -0.52} → Gold leads NIFTY by 2 days
    """
    
    # Known macro relationships (prior knowledge)
    KNOWN_CORRELATIONS = {
        ('NIFTY', 'VIX'):      {'expected': -0.80, 'type': 'inverse'},
        ('NIFTY', 'GOLD'):     {'expected': -0.30, 'type': 'mild_inverse'},
        ('NIFTY', 'USD_INR'):  {'expected': -0.40, 'type': 'inverse'},
        ('USD_INR', 'TCS'):    {'expected':  0.50, 'type': 'positive'},
        ('USD_INR', 'INFY'):   {'expected':  0.50, 'type': 'positive'},
        ('OIL', 'ONGC'):       {'expected':  0.60, 'type': 'positive'},
        ('OIL', 'INDIGO'):     {'expected': -0.40, 'type': 'inverse'},
        ('GOLD', 'HDFCBANK'):  {'expected': -0.25, 'type': 'mild_inverse'},
    }
    
    def __init__(self, window=60):
        self.window = window
        self.data = {}  # {symbol: pd.Series of daily returns}
        self.correlation_cache = {}
    
    def add_data(self, symbol, prices):
        """Add price series for an asset."""
        if isinstance(prices, pd.Series):
            self.data[symbol] = prices.pct_change().dropna()
        elif isinstance(prices, (list, np.ndarray)):
            s = pd.Series(prices)
            self.data[symbol] = s.pct_change().dropna()
    
    def add_from_db(self, db, symbols):
        """Load data from TradingDB."""
        for sym in symbols:
            try:
                df = db.get_market_data(sym, '1d', limit=200)
                if not df.empty and 'close' in df.columns:
                    self.add_data(sym, df['close'])
            except:
                pass
    
    def get_correlation(self, sym1, sym2, window=None):
        """Get rolling correlation between two assets."""
        w = window or self.window
        
        if sym1 not in self.data or sym2 not in self.data:
            return 0
        
        s1 = self.data[sym1]
        s2 = self.data[sym2]
        
        # Align dates
        combined = pd.concat([s1, s2], axis=1, keys=[sym1, sym2]).dropna()
        
        if len(combined) < w:
            return combined[sym1].corr(combined[sym2])
        
        # Rolling correlation
        return combined[sym1].tail(w).corr(combined[sym2].tail(w))
    
    def get_correlation_matrix(self, symbols=None):
        """Get full NxN correlation matrix."""
        syms = symbols or list(self.data.keys())
        n = len(syms)
        
        matrix = np.zeros((n, n))
        for i in range(n):
            for j in range(n):
                if i == j:
                    matrix[i][j] = 1.0
                else:
                    matrix[i][j] = self.get_correlation(syms[i], syms[j])
        
        return pd.DataFrame(matrix, index=syms, columns=syms)
    
    def detect_lead_lag(self, sym1, sym2, max_lag=10):
        """
        Detect if sym1 leads or lags sym2.
        
        Returns:
            dict: {lag: int, correlation: float, leader: str}
            Positive lag = sym1 leads
        """
        if sym1 not in self.data or sym2 not in self.data:
            return {'lag': 0, 'correlation': 0, 'leader': 'none'}
        
        s1 = self.data[sym1]
        s2 = self.data[sym2]
        
        best_lag = 0
        best_corr = 0
        
        for lag in range(-max_lag, max_lag + 1):
            if lag == 0:
                corr = s1.corr(s2)
            elif lag > 0:
                corr = s1.iloc[:-lag].reset_index(drop=True).corr(
                    s2.iloc[lag:].reset_index(drop=True))
            else:
                corr = s1.iloc[-lag:].reset_index(drop=True).corr(
                    s2.iloc[:lag].reset_index(drop=True))
            
            if abs(corr) > abs(best_corr):
                best_corr = corr
                best_lag = lag
        
        leader = sym1 if best_lag > 0 else sym2 if best_lag < 0 else 'simultaneous'
        
        return {
            'lag': best_lag,
            'correlation': round(best_corr, 4),
            'leader': leader,
            'description': f"{leader} leads by {abs(best_lag)} periods"
        }
    
    def detect_correlation_breaks(self, threshold=0.3):
        """
        Find pairs where current correlation diverges from expected.
        This signals a regime change.
        """
        breaks = []
        
        for (sym1, sym2), info in self.KNOWN_CORRELATIONS.items():
            if sym1 in self.data and sym2 in self.data:
                current = self.get_correlation(sym1, sym2)
                expected = info['expected']
                deviation = abs(current - expected)
                
                if deviation > threshold:
                    breaks.append({
                        'pair': f"{sym1}-{sym2}",
                        'expected': expected,
                        'current': round(current, 3),
                        'deviation': round(deviation, 3),
                        'signal': 'REGIME_CHANGE'
                    })
        
        return breaks
    
    def get_hedge_suggestions(self, symbol):
        """Suggest hedging instruments for a given position."""
        if symbol not in self.data:
            return []
        
        hedges = []
        for sym in self.data:
            if sym == symbol:
                continue
            corr = self.get_correlation(symbol, sym)
            if corr < -0.3:  # Negative correlation = hedge
                hedges.append({
                    'symbol': sym,
                    'correlation': round(corr, 3),
                    'hedge_ratio': round(abs(1 / corr), 2)
                })
        
        return sorted(hedges, key=lambda x: x['correlation'])
