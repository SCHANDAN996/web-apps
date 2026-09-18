"""
Tests for the limits that stop RiskManager from losing money: the daily loss
halt, the per-day trade cap, and the capital ceiling on position size.

Note: can_place_trade() also refuses everything after 15:15 IST, so these
tests only assert the *blocking* cases — those hold at any time of day.
"""
import os
import sys

sys.path.insert(0, os.path.abspath('.'))

from src.risk_manager import RiskManager


class DummyAPI:
    def get_positions(self):
        return []


def test_daily_loss_limit_halts_trading():
    rm = RiskManager(DummyAPI())
    limit = rm.max_daily_loss

    assert rm.check_emergency_exit(-(limit / 2)) is False, "half the limit must not halt trading"
    assert rm.stop_trading is False

    assert rm.check_emergency_exit(-(limit + 1)) is True, "past the daily loss limit trading must halt"
    assert rm.stop_trading is True
    # Once halted, nothing else may get through.
    assert rm.can_place_trade() is False


def test_daily_trade_cap_blocks_further_trades():
    rm = RiskManager(DummyAPI())
    rm.trade_count = rm.max_trades
    assert rm.can_place_trade() is False, f"more than {rm.max_trades} trades/day must be blocked"


def test_position_size_never_exceeds_capital():
    rm = RiskManager(DummyAPI())
    capital = rm.total_capital

    for price in (50.0, 2500.0, 25000.0):
        qty = rm.calculate_position_size('RELIANCE', price, confidence=0.9)
        assert qty * price <= capital, \
            f"sizing {qty} @ {price} would need more than the {capital} capital"


def test_low_confidence_is_rejected():
    rm = RiskManager(DummyAPI())
    assert rm.calculate_position_size('RELIANCE', 2500, confidence=0.40) == 0


def test_risk_per_trade_comes_from_config_not_a_hardcoded_default():
    """A value set in ai_config.json must actually reach RiskManager.

    The lookup used to ask for 'trading.risk_per_trade_percent' while the
    config file defines 'trading.risk_per_trade_pct', so every edit to that
    setting was silently ignored in favour of the hardcoded 2.0.
    """
    rm = RiskManager(DummyAPI())
    configured = rm.config.get('trading.risk_per_trade_pct', None)

    assert configured is not None, "ai_config.json should define trading.risk_per_trade_pct"
    assert rm.risk_per_trade_pct == configured, \
        f"config says {configured} but RiskManager is using {rm.risk_per_trade_pct}"


if __name__ == '__main__':
    test_daily_loss_limit_halts_trading()
    test_daily_trade_cap_blocks_further_trades()
    test_position_size_never_exceeds_capital()
    test_low_confidence_is_rejected()
    test_risk_per_trade_comes_from_config_not_a_hardcoded_default()
    print("✅ Risk limit tests passed!")
