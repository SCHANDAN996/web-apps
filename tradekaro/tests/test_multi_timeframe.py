"""
Unit tests for MultiTimeframeBrain.vote on synthetic candles.
"""
import sys
import os
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.abspath('.'))

from src.brain import TradingBrain
from src.multi_timeframe_brain import MultiTimeframeBrain


def candles(n=1000):
    # 1000 1m candles -> 200 5-minute bars, enough for a 60-bar lookback on
    # each of the four views.
    dates = pd.date_range("2026-01-01 09:15", periods=n, freq="1min")
    rng = np.random.default_rng(7)
    close = 100 + np.cumsum(rng.normal(0, 0.2, n))
    return pd.DataFrame({
        'open': close + rng.normal(0, 0.05, n),
        'high': close + 0.3,
        'low': close - 0.3,
        'close': close,
        'volume': rng.integers(100, 1000, n),
    }, index=dates)


class ConstantBrain:
    """A saturated model: the same answer whatever it is shown."""
    def predict(self, X):
        return 0.5549


class ReadingBrain:
    """A model that responds to its input, strongly bullish."""
    def predict(self, X):
        # Varies with the latest bar, always well above the BUY line.
        return 0.80 + (abs(float(X[0, -1, :].sum())) % 1.0) * 0.05


def test_mtf_brain_voting():
    mtf_brain = MultiTimeframeBrain(TradingBrain())

    result = mtf_brain.vote(candles())
    assert 'direction' in result
    assert 'confidence' in result
    assert 'agreement' in result
    assert 'votes' in result
    print(f"✅ MultiTimeframeBrain Test Passed! Result: {result['direction']} (Agreement {result['agreement']}/4)")


def test_a_model_that_ignores_its_input_does_not_trade():
    """The 2026-09-15 finding: 0.5549 on every bar came out as a unanimous BUY."""
    result = MultiTimeframeBrain(ConstantBrain(), scaler=None).vote(candles())

    assert result['direction'] == 'HOLD'
    assert result['agreement'] == 0
    assert result['failed_views'], "a stuck model must be named, not look like a quiet market"
    assert 'stuck' in result['failed_views'][0]


def test_a_model_that_reads_its_input_still_votes():
    result = MultiTimeframeBrain(ReadingBrain(), scaler=None).vote(candles())

    assert result['direction'] == 'BUY'
    assert result['agreement'] == 4
    assert not result['failed_views']


if __name__ == '__main__':
    test_mtf_brain_voting()
