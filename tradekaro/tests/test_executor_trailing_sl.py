"""
A trailing stop-loss may only ever move in the trade's favour. If it can widen
when the price moves against you, the stop stops protecting anything — so these
assertions are about direction, not exact prices.
"""
import os
import sys

sys.path.insert(0, os.path.abspath('.'))

from src.executor import OrderExecutor


class DummyAPI:
    def get_positions(self):
        return []


def _executor():
    return OrderExecutor(DummyAPI())


def test_buy_stop_tightens_when_price_rises():
    ex = _executor()
    current_sl = 996.0
    new_sl = ex.update_trailing_sl(
        current_price=1010.0, entry_price=1000.0, side='B', current_sl=current_sl)
    assert new_sl > current_sl, "a rising price should pull a BUY stop up"


def test_buy_stop_never_widens_when_price_falls():
    ex = _executor()
    current_sl = 996.0
    new_sl = ex.update_trailing_sl(
        current_price=990.0, entry_price=1000.0, side='B', current_sl=current_sl)
    assert new_sl == current_sl, "a falling price must never loosen a BUY stop"


def test_sell_stop_tightens_when_price_falls():
    ex = _executor()
    current_sl = 1004.0
    new_sl = ex.update_trailing_sl(
        current_price=990.0, entry_price=1000.0, side='S', current_sl=current_sl)
    assert new_sl < current_sl, "a falling price should pull a SELL stop down"


def test_sell_stop_never_widens_when_price_rises():
    ex = _executor()
    current_sl = 1004.0
    new_sl = ex.update_trailing_sl(
        current_price=1010.0, entry_price=1000.0, side='S', current_sl=current_sl)
    assert new_sl == current_sl, "a rising price must never loosen a SELL stop"


if __name__ == '__main__':
    test_buy_stop_tightens_when_price_rises()
    test_buy_stop_never_widens_when_price_falls()
    test_sell_stop_tightens_when_price_falls()
    test_sell_stop_never_widens_when_price_rises()
    print("✅ Trailing stop-loss tests passed!")
