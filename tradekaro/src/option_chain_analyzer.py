"""
📊 Option Chain Analyzer — PCR, Max Pain, OI Analysis

Extracts edge from option chain data:
  PCR: Put-Call Ratio (>1.2=bullish, <0.8=bearish)
  Max Pain: Strike where option writers lose least
  OI Buildup: Where is new position concentration?
  Change in OI: Fresh positions vs unwinding
"""

import numpy as np


class OptionChainAnalyzer:
    
    def analyze(self, chain_data, spot_price):
        if not chain_data or spot_price <= 0:
            return {'signal': 'NO_DATA'}
        
        pcr = self._pcr(chain_data)
        max_pain = self._max_pain(chain_data)
        oi_analysis = self._oi_concentration(chain_data, spot_price)
        
        signal = 'NEUTRAL'
        if pcr['ratio'] > 1.2 and spot_price < max_pain['strike']:
            signal = 'BULLISH'
        elif pcr['ratio'] < 0.8 and spot_price > max_pain['strike']:
            signal = 'BEARISH'
        
        return {
            'pcr': pcr, 'max_pain': max_pain, 'oi_analysis': oi_analysis,
            'signal': signal, 'spot': spot_price
        }
    
    def _pcr(self, chain):
        total_put_oi = sum(d.get('pe_oi', 0) for d in chain)
        total_call_oi = sum(d.get('ce_oi', 0) for d in chain)
        ratio = total_put_oi / max(total_call_oi, 1)
        
        return {
            'ratio': round(ratio, 3),
            'put_oi': total_put_oi, 'call_oi': total_call_oi,
            'interpretation': 'BULLISH' if ratio > 1.2 else 'BEARISH' if ratio < 0.8 else 'NEUTRAL'
        }
    
    def _max_pain(self, chain):
        strikes = [d['strike'] for d in chain]
        min_pain = float('inf')
        pain_strike = strikes[0] if strikes else 0
        
        for test_strike in strikes:
            pain = 0
            for d in chain:
                ce_pain = max(0, test_strike - d['strike']) * d.get('ce_oi', 0)
                pe_pain = max(0, d['strike'] - test_strike) * d.get('pe_oi', 0)
                pain += ce_pain + pe_pain
            if pain < min_pain:
                min_pain = pain
                pain_strike = test_strike
        
        return {'strike': pain_strike, 'pain_value': round(min_pain, 0)}
    
    def _oi_concentration(self, chain, spot):
        max_ce = max(chain, key=lambda x: x.get('ce_oi', 0))
        max_pe = max(chain, key=lambda x: x.get('pe_oi', 0))
        
        return {
            'max_call_oi_strike': max_ce['strike'],
            'max_call_oi': max_ce.get('ce_oi', 0),
            'max_put_oi_strike': max_pe['strike'],
            'max_put_oi': max_pe.get('pe_oi', 0),
            'expected_range': f"{max_pe['strike']} — {max_ce['strike']}",
            'range_width': max_ce['strike'] - max_pe['strike']
        }
