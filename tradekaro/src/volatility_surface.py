"""
📈 Volatility Surface Analyzer — IV Smile/Skew for Options Edge

Options traders' secret weapon:
  - IV Smile: ATM options have low IV, OTM options have high IV
  - IV Skew: Puts have higher IV than calls (fear premium)
  - Term Structure: How IV changes across expiries
  - IV Percentile: Is current IV cheap or expensive vs history?

Trade signals:
  - Flat smile → sell straddle (market stable)
  - Steep skew → buy puts (market expects crash)
  - IV < 20th percentile → buy options (cheap volatility)
"""

import numpy as np
from datetime import datetime
from collections import deque


class VolatilitySurfaceAnalyzer:
    """
    Analyzes implied volatility patterns for options trading edge.
    
    Usage:
        vol = VolatilitySurfaceAnalyzer()
        vol.update_chain(strike_iv_data)
        analysis = vol.analyze()
    """
    
    def __init__(self, history_size=252):
        self.iv_history = deque(maxlen=history_size)
        self.current_chain = {}
        self.atm_strike = 0
    
    def update_chain(self, chain_data, spot_price):
        """
        Update with current option chain IV data.
        
        Args:
            chain_data: list of {strike, iv_ce, iv_pe}
            spot_price: current underlying price
        """
        self.atm_strike = self._find_atm(chain_data, spot_price)
        self.current_chain = {
            'data': chain_data,
            'spot': spot_price,
            'atm': self.atm_strike,
            'timestamp': datetime.now().isoformat()
        }
        
        # Track ATM IV history
        atm_data = next((d for d in chain_data if d['strike'] == self.atm_strike), None)
        if atm_data:
            avg_iv = (atm_data.get('iv_ce', 15) + atm_data.get('iv_pe', 15)) / 2
            self.iv_history.append(avg_iv)
    
    def analyze(self):
        """Full volatility surface analysis."""
        if not self.current_chain:
            return {'status': 'NO_DATA'}
        
        smile = self._analyze_smile()
        skew = self._analyze_skew()
        percentile = self._iv_percentile()
        
        # Trading recommendation
        if percentile < 20:
            recommendation = 'BUY_OPTIONS — IV is cheap, expect expansion'
        elif percentile > 80:
            recommendation = 'SELL_OPTIONS — IV is expensive, expect contraction'
        elif skew['skew_value'] > 5:
            recommendation = 'PROTECTIVE_PUTS — Market pricing in downside risk'
        else:
            recommendation = 'NEUTRAL — IV at fair value'
        
        return {
            'smile': smile,
            'skew': skew,
            'iv_percentile': percentile,
            'recommendation': recommendation,
            'atm_iv': self._get_atm_iv()
        }
    
    def _analyze_smile(self):
        """Analyze IV smile pattern."""
        data = self.current_chain.get('data', [])
        spot = self.current_chain.get('spot', 0)
        
        if not data or spot == 0:
            return {'shape': 'UNKNOWN'}
        
        otm_put_ivs = []
        atm_ivs = []
        otm_call_ivs = []
        
        for d in data:
            moneyness = (d['strike'] - spot) / spot * 100
            avg_iv = (d.get('iv_ce', 0) + d.get('iv_pe', 0)) / 2
            
            if moneyness < -3:
                otm_put_ivs.append(avg_iv)
            elif moneyness > 3:
                otm_call_ivs.append(avg_iv)
            else:
                atm_ivs.append(avg_iv)
        
        atm_avg = np.mean(atm_ivs) if atm_ivs else 15
        put_avg = np.mean(otm_put_ivs) if otm_put_ivs else atm_avg
        call_avg = np.mean(otm_call_ivs) if otm_call_ivs else atm_avg
        
        if put_avg > atm_avg * 1.1 and call_avg > atm_avg * 1.1:
            shape = 'SMILE'
        elif put_avg > atm_avg * 1.1 > call_avg:
            shape = 'SKEW'
        elif call_avg > atm_avg * 1.1 > put_avg:
            shape = 'REVERSE_SKEW'
        else:
            shape = 'FLAT'
        
        return {
            'shape': shape,
            'atm_iv': round(atm_avg, 2),
            'otm_put_iv': round(put_avg, 2),
            'otm_call_iv': round(call_avg, 2)
        }
    
    def _analyze_skew(self):
        """Analyze put-call skew (fear gauge)."""
        data = self.current_chain.get('data', [])
        if not data:
            return {'skew_value': 0}
        
        atm = self.atm_strike
        atm_data = next((d for d in data if d['strike'] == atm), None)
        
        if not atm_data:
            return {'skew_value': 0}
        
        skew = atm_data.get('iv_pe', 15) - atm_data.get('iv_ce', 15)
        
        return {
            'skew_value': round(skew, 2),
            'interpretation': 'FEAR_PREMIUM' if skew > 3 else 'NORMAL' if skew > 0 else 'CALL_DEMAND',
            'put_iv': atm_data.get('iv_pe', 0),
            'call_iv': atm_data.get('iv_ce', 0)
        }
    
    def _iv_percentile(self):
        """Current IV vs historical — is it cheap or expensive?"""
        if len(self.iv_history) < 20:
            return 50
        
        current = self.iv_history[-1]
        history = sorted(self.iv_history)
        rank = sum(1 for h in history if h <= current)
        
        return round(rank / len(history) * 100, 1)
    
    def _get_atm_iv(self):
        data = self.current_chain.get('data', [])
        atm_data = next((d for d in data if d['strike'] == self.atm_strike), None)
        if atm_data:
            return round((atm_data.get('iv_ce', 15) + atm_data.get('iv_pe', 15)) / 2, 2)
        return 15
    
    def _find_atm(self, chain, spot):
        if not chain:
            return 0
        return min(chain, key=lambda x: abs(x['strike'] - spot))['strike']
