"""
⏱️ Adaptive Timeframe Selector — Auto-Pick Best TF for Current Market

Different markets suit different timeframes:
  - Trending → 15m or 1H (ride the trend)
  - Choppy → 1m or 5m (quick scalps)
  - Volatile → 15m (avoid noise)
  - Quiet → 5m (catch small moves)
"""

import numpy as np


class AdaptiveTimeframeSelector:
    """
    Auto-selects optimal trading timeframe.
    
    Usage:
        selector = AdaptiveTimeframeSelector()
        best_tf = selector.select(df_1m, regime='BULL_TREND', adx=35)
        # {'timeframe': '15m', 'reason': 'Strong trend — use higher TF'}
    """
    
    TIMEFRAMES = ['1m', '5m', '15m', '1H']
    
    REGIME_TF_MAP = {
        'BULL_TREND':       '15m',
        'BEAR_TREND':       '15m',
        'SIDEWAYS_QUIET':   '5m',
        'SIDEWAYS_VOLATILE':'5m',
        'TRANSITION':       '5m',
    }
    
    def select(self, df_1m=None, regime='UNKNOWN', adx=20, volatility=None):
        """Select optimal timeframe based on market conditions."""
        scores = {tf: 0 for tf in self.TIMEFRAMES}
        reasons = []
        
        # 1. Regime-based selection
        preferred = self.REGIME_TF_MAP.get(regime, '5m')
        scores[preferred] += 3
        reasons.append(f'Regime {regime} favors {preferred}')
        
        # 2. ADX-based (trend strength)
        if adx > 30:
            scores['15m'] += 2
            scores['1H'] += 2
            reasons.append('Strong trend (ADX>30) → higher TFs')
        elif adx < 15:
            scores['1m'] += 2
            scores['5m'] += 2
            reasons.append('No trend (ADX<15) → lower TFs for scalping')
        
        # 3. Volatility-based
        if df_1m is not None and len(df_1m) > 30:
            returns = np.diff(df_1m['close'].values) / df_1m['close'].values[:-1]
            vol = np.std(returns) * 100
            
            if vol > 0.5:
                scores['15m'] += 2
                scores['1H'] += 1
                reasons.append(f'High volatility ({vol:.2f}%) → avoid noise')
            elif vol < 0.1:
                scores['1m'] += 2
                scores['5m'] += 1
                reasons.append(f'Low volatility ({vol:.2f}%) → need quick TF')
        
        # 4. Time of day
        from datetime import datetime
        hour = datetime.now().hour
        minute = datetime.now().minute
        
        if 9 <= hour < 10:
            scores['1m'] += 1
            scores['5m'] += 1
            reasons.append('Opening hour → faster TFs')
        elif 14 <= hour < 15:
            scores['5m'] += 1
            scores['15m'] += 1
            reasons.append('Power hour → medium TFs')
        elif 11 <= hour < 14:
            scores['15m'] += 1
            reasons.append('Midday → avoid overtrading')
        
        best_tf = max(scores, key=scores.get)
        
        return {
            'timeframe': best_tf,
            'scores': scores,
            'reasons': reasons,
            'recommendation': f"Use {best_tf} for current conditions"
        }
