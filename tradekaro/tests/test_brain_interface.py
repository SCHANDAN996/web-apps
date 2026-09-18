"""
Regression tests for the brain wrapper contract.

main.py hands callers a MultiTimeframeBrain, not a TradingBrain, and the rest
of the code calls it as if it were the real thing. For months the wrapper was
missing train_incremental, so every incremental training call raised
AttributeError and the model silently never learned from live data. These
tests pin the contract so that gap cannot quietly reopen.
"""
import os
import sys

sys.path.insert(0, os.path.abspath('.'))

from src.brain import TradingBrain
from src.multi_timeframe_brain import MultiTimeframeBrain

# Everything callers invoke on whatever object main.py calls "the brain":
#   predict           -> multi_timeframe_brain internals, backtest paths
#   vote              -> main.py trading loop
#   train_incremental -> learner.py:91, train_historical.py, backtest_engine.py
#   _get_input_size   -> multi_timeframe_brain internals
BRAIN_INTERFACE = ['predict', 'vote', 'train_incremental', '_get_input_size']


class FakeBrain:
    """Stand-in for TradingBrain, so these tests stay fast and model-free."""

    def __init__(self):
        self.calls = []

    def predict(self, X):
        self.calls.append(('predict', X))
        return 0.42

    def train_incremental(self, x_train, y_train, epochs=5, batch_size=256):
        self.calls.append(('train_incremental', x_train, y_train, epochs, batch_size))
        return 'trained'

    def _get_input_size(self):
        return 22


def test_wrapper_exposes_full_brain_interface():
    wrapper = MultiTimeframeBrain(FakeBrain())
    missing = [name for name in BRAIN_INTERFACE if not hasattr(wrapper, name)]
    assert not missing, (
        f"MultiTimeframeBrain is missing {missing}; callers treat it as a TradingBrain"
    )


def test_real_brain_provides_the_delegate_targets():
    # The wrapper forwards to these, so they must exist on the real class too.
    for name in ['predict', 'train_incremental', '_get_input_size']:
        assert hasattr(TradingBrain, name), f"TradingBrain has no {name}"


def test_train_incremental_reaches_the_underlying_brain():
    fake = FakeBrain()
    wrapper = MultiTimeframeBrain(fake)

    result = wrapper.train_incremental('X', 'y', epochs=3)

    assert result == 'trained', "wrapper must return the underlying brain's result"
    assert fake.calls == [('train_incremental', 'X', 'y', 3, 256)], \
        f"arguments were not forwarded intact: {fake.calls}"


def test_predict_reaches_the_underlying_brain():
    fake = FakeBrain()
    wrapper = MultiTimeframeBrain(fake)

    assert wrapper.predict('candles') == 0.42
    assert fake.calls == [('predict', 'candles')]


if __name__ == '__main__':
    test_wrapper_exposes_full_brain_interface()
    test_real_brain_provides_the_delegate_targets()
    test_train_incremental_reaches_the_underlying_brain()
    test_predict_reaches_the_underlying_brain()
    print("✅ Brain interface tests passed!")
