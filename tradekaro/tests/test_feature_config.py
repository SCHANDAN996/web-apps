"""
The feature contract, checked against what the indicators actually emit.

The previous version of this file asserted the list had 18 entries and
contained 'macd' and 'adx'. Both passed for months while the system was
broken, because they compared the list to itself. The indicators emit 'MACD'
and 'ADX'; 'macd' and 'adx' matched nothing, six of the eighteen names were
dropped in silence on every call, and the model -- one column short -- refused
to predict and returned a neutral 0.5 instead. The bot placed no trades from
22 July to 6 August.

So the assertion that matters is not how long the list is. It is that every
name on it exists in a real indicator frame.
"""
import os
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.feature_config import (FEATURE_VERSION, FEATURES,
                                   REQUIRED_FEATURE_COUNT, describe_coverage,
                                   select_features)
from src.indicators import TechnicalIndicators


def synthetic_candles(n=3000):
    """A believable random walk -- enough bars to clear indicator warmup."""
    rng = np.random.default_rng(20260806)
    close = 100 + np.cumsum(rng.normal(0, 0.35, n))
    spread = rng.uniform(0.05, 0.4, n)
    return pd.DataFrame({
        'open': close + rng.normal(0, 0.1, n),
        'high': close + spread,
        'low': close - spread,
        'close': close,
        'volume': rng.integers(1_000, 50_000, n),
    }, index=pd.date_range('2026-01-01 09:15', periods=n, freq='1min'))


@pytest.fixture(scope='module')
def indicator_frame():
    return TechnicalIndicators.apply_multi_timeframe_features(synthetic_candles())


def test_every_feature_exists_in_the_indicator_output(indicator_frame):
    """The check that was missing. A typo or case slip fails here, loudly."""
    coverage = describe_coverage(indicator_frame)

    assert coverage['complete'], (
        f"{len(coverage['missing'])} feature(s) named in FEATURES are not "
        f"produced by TechnicalIndicators: {coverage['missing']}")


def test_select_features_returns_every_column_in_order(indicator_frame):
    selected = select_features(indicator_frame)

    assert list(selected.columns) == FEATURES
    assert selected.shape[1] == REQUIRED_FEATURE_COUNT


def test_select_features_raises_instead_of_returning_a_short_frame(indicator_frame):
    """Silently returning the intersection is the bug this guards."""
    crippled = indicator_frame.drop(columns=['MACD', 'ADX'])

    with pytest.raises(KeyError) as excinfo:
        select_features(crippled)

    assert 'MACD' in str(excinfo.value)
    assert 'ADX' in str(excinfo.value)


def test_the_features_survive_resampling_to_every_traded_timeframe():
    """MultiTimeframeBrain resamples to 5m/15m/1H and needs all of them there.

    1H is excluded: an hour bar needs 60 times the history, and how much the
    live engine actually holds is tracked separately.
    """
    candles = synthetic_candles(6000)

    for periods, freq in ((1, None), (5, '5min'), (15, '15min')):
        if freq is None:
            frame = candles
        else:
            frame = candles.resample(freq).agg({
                'open': 'first', 'high': 'max', 'low': 'min',
                'close': 'last', 'volume': 'sum'}).dropna()

        coverage = describe_coverage(
            TechnicalIndicators.apply_multi_timeframe_features(frame))

        assert coverage['complete'], (
            f"{periods}m timeframe is missing {coverage['missing']}")


def test_selected_features_are_finite(indicator_frame):
    """NaN or inf reaching the model is a silent corruption of its input."""
    selected = select_features(indicator_frame)

    assert np.isfinite(selected.to_numpy(dtype=float)).all(), (
        "non-finite values in: "
        f"{selected.columns[~np.isfinite(selected.to_numpy(dtype=float)).all(axis=0)].tolist()}")


def test_feature_names_are_unique():
    assert len(FEATURES) == len(set(FEATURES))


def test_required_count_tracks_the_list():
    assert REQUIRED_FEATURE_COUNT == len(FEATURES)


def test_version_is_recorded():
    """Whatever the value, it has to exist -- checkpoints are stamped with it."""
    assert FEATURE_VERSION
