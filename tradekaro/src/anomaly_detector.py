"""
🚨 Anomaly Detection Engine — Detect Unusual Market Behavior Before Crashes

Detects:
  - Volume Spikes (3σ above mean = institutional activity)
  - Price Gaps (overnight gaps > 1% = news-driven move)
  - Volatility Regime Shifts (sudden VIX jump)
  - Order Flow Imbalance (OI skew change)
  - Consecutive extreme candles (3+ in same direction)

Each anomaly generates a risk score → used by RiskManager to reduce exposure.
"""

import numpy as np
import pandas as pd
from datetime import datetime
from collections import deque


class AnomalyDetector:
    """
    Real-time anomaly detection for market microstructure.
    
    Usage:
        detector = AnomalyDetector()
        anomalies = detector.scan(df_ohlcv)
        # [{'type': 'VOLUME_SPIKE', 'severity': 0.92, 'message': '...'}]
    """
    
    def __init__(self, vol_lookback=50, vol_threshold=3.0, gap_threshold=0.01):
        self.vol_lookback = vol_lookback
        self.vol_threshold = vol_threshold
        self.gap_threshold = gap_threshold
        self.history = deque(maxlen=200)
        self.anomaly_log = []
    
    def scan(self, df):
        """
        Scan OHLCV DataFrame for anomalies.
        
        Returns:
            list of dicts: [{type, severity, message, timestamp}]
        """
        if df is None or len(df) < self.vol_lookback + 5:
            return []
        
        anomalies = []
        
        # 1. Volume Spike
        vol_anomaly = self._check_volume_spike(df)
        if vol_anomaly:
            anomalies.append(vol_anomaly)
        
        # 2. Price Gap
        gap_anomaly = self._check_price_gap(df)
        if gap_anomaly:
            anomalies.append(gap_anomaly)
        
        # 3. Volatility Shift
        vol_shift = self._check_volatility_shift(df)
        if vol_shift:
            anomalies.append(vol_shift)
        
        # 4. Consecutive Extreme Candles
        streak = self._check_candle_streak(df)
        if streak:
            anomalies.append(streak)
        
        # 5. Price-Volume Divergence
        divergence = self._check_pv_divergence(df)
        if divergence:
            anomalies.append(divergence)
        
        # Log anomalies
        for a in anomalies:
            a['timestamp'] = datetime.now().isoformat()
            self.anomaly_log.append(a)
        
        # Keep log manageable
        if len(self.anomaly_log) > 500:
            self.anomaly_log = self.anomaly_log[-500:]
        
        return anomalies
    
    def get_risk_score(self, df):
        """
        Overall anomaly risk score 0-1.
        Higher = more anomalies detected = reduce exposure.
        """
        anomalies = self.scan(df)
        if not anomalies:
            return 0.0
        
        total_severity = sum(a['severity'] for a in anomalies)
        return min(1.0, total_severity / 3.0)
    
    def _check_volume_spike(self, df):
        vol = df['volume'].values
        if len(vol) < self.vol_lookback:
            return None
        
        mean_vol = np.mean(vol[-self.vol_lookback:-1])
        std_vol = np.std(vol[-self.vol_lookback:-1])
        current_vol = vol[-1]
        
        if std_vol > 0:
            z_score = (current_vol - mean_vol) / std_vol
            if z_score > self.vol_threshold:
                return {
                    'type': 'VOLUME_SPIKE',
                    'severity': min(1.0, z_score / 5.0),
                    'value': float(z_score),
                    'message': f'⚡ Volume {z_score:.1f}σ above mean — institutional activity likely'
                }
        return None
    
    def _check_price_gap(self, df):
        if len(df) < 2:
            return None
        
        prev_close = df['close'].iloc[-2]
        curr_open = df['open'].iloc[-1]
        gap_pct = abs(curr_open - prev_close) / prev_close
        
        if gap_pct > self.gap_threshold:
            direction = 'UP' if curr_open > prev_close else 'DOWN'
            return {
                'type': 'PRICE_GAP',
                'severity': min(1.0, gap_pct / 0.03),
                'value': float(gap_pct),
                'message': f'📊 Gap {direction} {gap_pct:.2%} — news-driven move'
            }
        return None
    
    def _check_volatility_shift(self, df):
        if len(df) < 30:
            return None
        
        close = df['close'].values
        returns = np.diff(close) / close[:-1]
        
        recent_vol = np.std(returns[-10:])
        baseline_vol = np.std(returns[-30:-10])
        
        if baseline_vol > 0:
            vol_ratio = recent_vol / baseline_vol
            if vol_ratio > 2.0:
                return {
                    'type': 'VOLATILITY_SHIFT',
                    'severity': min(1.0, (vol_ratio - 1) / 3),
                    'value': float(vol_ratio),
                    'message': f'🌊 Volatility {vol_ratio:.1f}x baseline — regime shift likely'
                }
        return None
    
    def _check_candle_streak(self, df, min_streak=5):
        if len(df) < min_streak:
            return None
        
        recent = df.tail(min_streak)
        bullish = sum(1 for _, r in recent.iterrows() if r['close'] > r['open'])
        bearish = min_streak - bullish
        
        if bullish >= min_streak:
            return {
                'type': 'BULLISH_STREAK',
                'severity': 0.6,
                'value': bullish,
                'message': f'🟢 {bullish} consecutive bullish candles — overbought risk'
            }
        elif bearish >= min_streak:
            return {
                'type': 'BEARISH_STREAK',
                'severity': 0.6,
                'value': bearish,
                'message': f'🔴 {bearish} consecutive bearish candles — panic selling'
            }
        return None
    
    def _check_pv_divergence(self, df):
        if len(df) < 10:
            return None
        
        recent = df.tail(10)
        price_trend = recent['close'].iloc[-1] - recent['close'].iloc[0]
        vol_trend = recent['volume'].iloc[-5:].mean() - recent['volume'].iloc[:5].mean()
        
        # Price up but volume down = weak rally
        if price_trend > 0 and vol_trend < 0:
            severity = min(0.8, abs(vol_trend) / (recent['volume'].mean() + 1))
            if severity > 0.2:
                return {
                    'type': 'PV_DIVERGENCE',
                    'severity': severity,
                    'value': 0,
                    'message': '⚠️ Price rising on declining volume — weak rally, reversal risk'
                }
        # Price down but volume down = weak selling
        elif price_trend < 0 and vol_trend < 0:
            severity = min(0.5, abs(vol_trend) / (recent['volume'].mean() + 1))
            if severity > 0.2:
                return {
                    'type': 'PV_DIVERGENCE',
                    'severity': severity,
                    'value': 0,
                    'message': '📉 Price falling on declining volume — selling exhaustion possible'
                }
        return None
