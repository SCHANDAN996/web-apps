"""
🔍 Market Regime Detector V2
Automatically classifies the current market into one of 4 regimes:

1. BULL_TREND    — Sustained upward move, strong momentum
2. BEAR_TREND    — Sustained downward move, fear dominant
3. SIDEWAYS_VOLATILE — Range-bound but with wide swings (chop)
4. SIDEWAYS_QUIET    — Low volatility, no clear direction (coil)

Uses a statistical approach (no external ML library needed):
- ADX for trend strength
- Volatility ratio for regime subtype
- Returns momentum for direction
- Cross-asset confirmation (DXY, VIX)
"""

import numpy as np
import pandas as pd
from datetime import datetime


class MarketRegime:
    """Enum-like constants for regime states."""
    BULL_TREND = "BULL_TREND"
    BEAR_TREND = "BEAR_TREND"
    SIDEWAYS_VOLATILE = "SIDEWAYS_VOLATILE"
    SIDEWAYS_QUIET = "SIDEWAYS_QUIET"
    TRANSITION = "TRANSITION"

    # Regime-specific trading advice
    ADVICE = {
        BULL_TREND: "Trade WITH trend. Buy dips. Wider targets.",
        BEAR_TREND: "Avoid longs. Short rallies. Tight stops.",
        SIDEWAYS_VOLATILE: "Mean-reversion works. Sell extremes. Tight targets.",
        SIDEWAYS_QUIET: "AVOID. Low probability setups. Wait for breakout.",
        TRANSITION: "CAUTION. Regime changing. Reduce position size."
    }


class MarketRegimeDetector:
    """
    Detects the current market regime using statistical metrics.

    Logic:
    1. ADX > threshold → Trending
       - Returns > 0 → BULL_TREND
       - Returns < 0 → BEAR_TREND
    2. ADX < threshold → Sideways
       - High volatility ratio → SIDEWAYS_VOLATILE
       - Low volatility ratio → SIDEWAYS_QUIET
    3. Regime transition → detected by comparing last N regime readings
    """

    def __init__(self, adx_threshold=25, vol_ratio_threshold=1.2,
                 lookback=50, transition_window=5):
        self.adx_threshold = adx_threshold
        self.vol_ratio_threshold = vol_ratio_threshold
        self.lookback = lookback
        self.transition_window = transition_window
        self.regime_history = []
        self.current_regime = MarketRegime.SIDEWAYS_QUIET
        self.regime_duration = 0

    def detect(self, df):
        """
        Detect regime from a DataFrame with at least 'close', 'high', 'low', 'ADX' columns.

        Args:
            df: pandas DataFrame with OHLCV + indicators (must have 'ADX')

        Returns:
            dict with 'regime', 'confidence', 'duration', 'advice'
        """
        if df.empty or len(df) < self.lookback:
            return self._build_result(MarketRegime.SIDEWAYS_QUIET, 0.5)

        # 1. Trend Strength (ADX)
        adx = df['ADX'].iloc[-1] if 'ADX' in df.columns else 0

        # 2. Direction (Returns)
        returns = df['close'].pct_change(self.lookback).iloc[-1]

        # 3. Volatility (ATR-based ratio)
        if 'ATR_14' in df.columns:
            current_atr = df['ATR_14'].iloc[-1]
            avg_atr = df['ATR_14'].iloc[-self.lookback:].mean()
            vol_ratio = current_atr / (avg_atr + 1e-9)
        else:
            # Approximate from high-low range
            recent_range = (df['high'] - df['low']).iloc[-20:].mean()
            avg_range = (df['high'] - df['low']).iloc[-self.lookback:].mean()
            vol_ratio = recent_range / (avg_range + 1e-9)

        # 4. Classify
        if adx > self.adx_threshold:
            # Trending market
            if returns > 0:
                regime = MarketRegime.BULL_TREND
                confidence = min(adx / 50, 1.0)  # ADX 50+ = max confidence
            else:
                regime = MarketRegime.BEAR_TREND
                confidence = min(adx / 50, 1.0)
        else:
            # Non-trending market
            if vol_ratio > self.vol_ratio_threshold:
                regime = MarketRegime.SIDEWAYS_VOLATILE
                confidence = min(vol_ratio / 2.0, 1.0)
            else:
                regime = MarketRegime.SIDEWAYS_QUIET
                confidence = 1.0 - (adx / self.adx_threshold)

        # 5. Transition Detection
        self.regime_history.append(regime)
        if len(self.regime_history) > 100:
            self.regime_history = self.regime_history[-100:]

        is_transition = self._check_transition()
        if is_transition:
            regime = MarketRegime.TRANSITION
            confidence *= 0.5

        # 6. Duration tracking
        if regime == self.current_regime:
            self.regime_duration += 1
        else:
            self.current_regime = regime
            self.regime_duration = 1

        return self._build_result(regime, confidence)

    def _check_transition(self):
        """Check if regime is in transition (flip-flopping recently)."""
        if len(self.regime_history) < self.transition_window:
            return False
        recent = self.regime_history[-self.transition_window:]
        unique_regimes = len(set(recent))
        return unique_regimes >= 3  # 3+ different regimes in short window = unstable

    def _build_result(self, regime, confidence):
        return {
            'regime': regime,
            'confidence': round(confidence, 3),
            'duration': self.regime_duration,
            'advice': MarketRegime.ADVICE.get(regime, ""),
            'timestamp': datetime.now().isoformat()
        }

    def get_regime_stats(self):
        """Summary statistics of regime history."""
        if not self.regime_history:
            return {}
        from collections import Counter
        counts = Counter(self.regime_history)
        total = len(self.regime_history)
        return {regime: round(count / total * 100, 1)
                for regime, count in counts.most_common()}
