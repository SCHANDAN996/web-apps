"""
🔄 Regime Ensemble — Combine Multiple Regime Detectors

Single regime detector can be wrong. Combine 4 methods:
  1. Volatility-based (HV percentile)
  2. Trend-based (ADX + EMA slope)
  3. Mean-reversion (RSI range behavior)
  4. Volume-based (volume trend)
"""

import numpy as np


class RegimeEnsemble:
    
    REGIMES = ['STRONG_BULL', 'BULL', 'SIDEWAYS', 'BEAR', 'STRONG_BEAR', 'HIGH_VOL']
    
    def detect(self, df, lookback=60):
        if df is None or len(df) < lookback:
            return {'regime': 'UNKNOWN', 'confidence': 0}
        
        recent = df.tail(lookback)
        votes = {}
        
        votes['volatility'] = self._vol_regime(recent)
        votes['trend'] = self._trend_regime(recent)
        votes['meanrev'] = self._meanrev_regime(recent)
        votes['volume'] = self._volume_regime(recent)
        
        regime_scores = {r: 0 for r in self.REGIMES}
        for method, result in votes.items():
            regime_scores[result['regime']] += result['confidence']
        
        best = max(regime_scores, key=regime_scores.get)
        total_conf = sum(v['confidence'] for v in votes.values())
        confidence = regime_scores[best] / max(total_conf, 0.01)
        
        agreement = sum(1 for v in votes.values() if v['regime'] == best)
        
        return {
            'regime': best,
            'confidence': round(confidence, 3),
            'agreement': f'{agreement}/{len(votes)}',
            'votes': {k: v['regime'] for k, v in votes.items()},
            'strategy': self._strategy(best)
        }
    
    def _vol_regime(self, df):
        returns = df['close'].pct_change().dropna()
        hv = returns.std() * np.sqrt(252) * 100
        if hv > 30: return {'regime': 'HIGH_VOL', 'confidence': 0.8}
        if hv > 20: return {'regime': 'SIDEWAYS', 'confidence': 0.5}
        if hv < 10: return {'regime': 'SIDEWAYS', 'confidence': 0.6}
        return {'regime': 'BULL', 'confidence': 0.4}
    
    def _trend_regime(self, df):
        close = df['close'].values
        ret = (close[-1] - close[0]) / close[0] * 100
        adx = df['ADX'].iloc[-1] if 'ADX' in df.columns else 20
        
        if ret > 5 and adx > 25: return {'regime': 'STRONG_BULL', 'confidence': 0.9}
        if ret > 2: return {'regime': 'BULL', 'confidence': 0.7}
        if ret < -5 and adx > 25: return {'regime': 'STRONG_BEAR', 'confidence': 0.9}
        if ret < -2: return {'regime': 'BEAR', 'confidence': 0.7}
        return {'regime': 'SIDEWAYS', 'confidence': 0.6}
    
    def _meanrev_regime(self, df):
        rsi = df['RSI_14'].values if 'RSI_14' in df.columns else np.full(len(df), 50)
        rsi_std = np.std(rsi[-20:])
        if rsi_std < 8: return {'regime': 'SIDEWAYS', 'confidence': 0.7}
        if np.mean(rsi[-10:]) > 60: return {'regime': 'BULL', 'confidence': 0.6}
        if np.mean(rsi[-10:]) < 40: return {'regime': 'BEAR', 'confidence': 0.6}
        return {'regime': 'SIDEWAYS', 'confidence': 0.4}
    
    def _volume_regime(self, df):
        vol = df['volume'].values
        recent_avg = np.mean(vol[-10:])
        older_avg = np.mean(vol[-30:-10]) if len(vol) > 30 else np.mean(vol)
        ratio = recent_avg / max(older_avg, 1)
        
        if ratio > 1.5: return {'regime': 'HIGH_VOL', 'confidence': 0.6}
        if ratio < 0.6: return {'regime': 'SIDEWAYS', 'confidence': 0.5}
        return {'regime': 'BULL', 'confidence': 0.3}
    
    def _strategy(self, regime):
        strategies = {
            'STRONG_BULL': 'Aggressive longs, trail stops, add on dips',
            'BULL': 'Buy dips, moderate position size',
            'SIDEWAYS': 'Mean reversion, sell options, tight ranges',
            'BEAR': 'Reduce longs, hedge with puts, short rallies',
            'STRONG_BEAR': 'Cash/short only, max risk reduction',
            'HIGH_VOL': 'Reduce size, wider stops, sell premium'
        }
        return strategies.get(regime, '')
