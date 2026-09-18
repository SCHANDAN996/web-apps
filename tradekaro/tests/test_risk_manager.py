"""
Unit tests for RiskManager (Position sizing, confidence veto, SL/TP calculation)
"""
import sys
import os

sys.path.insert(0, os.path.abspath('.'))

from src.risk_manager import RiskManager

class DummyAPI:
    def get_positions(self):
        return []

def test_risk_manager_confidence_threshold():
    rm = RiskManager(DummyAPI())
    
    # High confidence (0.75) -> Should return non-zero qty
    qty_high = rm.calculate_position_size('RELIANCE', 2500, 0.75)
    assert qty_high > 0, "High confidence trade should be approved with >0 qty"

    # Low confidence (0.40 < 0.60 threshold) -> Should return 0 qty (rejected)
    qty_low = rm.calculate_position_size('RELIANCE', 2500, 0.40)
    assert qty_low == 0, "Low confidence trade (<0.60) must be rejected with 0 qty"


def test_stop_loss_calculation():
    rm = RiskManager(DummyAPI())
    entry_price = 1000.0
    
    # BUY Side
    sl_b, tp_b = rm.calculate_stop_loss(entry_price, 'B')
    assert sl_b < entry_price
    assert tp_b > entry_price
    
    # SELL Side
    sl_s, tp_s = rm.calculate_stop_loss(entry_price, 'S')
    assert sl_s > entry_price
    assert tp_s < entry_price

if __name__ == '__main__':
    test_risk_manager_confidence_threshold()
    test_stop_loss_calculation()
    print("✅ RiskManager Unit Tests Passed!")
