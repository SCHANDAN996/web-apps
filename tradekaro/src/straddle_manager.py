"""
📊 Straddle Manager — Auto-Manage Straddle/Strangle Positions

Manages non-directional option strategies:
  Entry: When IV is low and big move expected
  Adjustment: Roll losing leg, add hedge
  Exit: Target profit or time-based exit
"""

from datetime import datetime
from collections import deque


class StraddleManager:
    
    def __init__(self):
        self.active = {}
        self.history = deque(maxlen=100)
    
    def enter_straddle(self, symbol, strike, ce_price, pe_price, qty=1, expiry_days=7):
        cost = (ce_price + pe_price) * qty
        breakeven_up = strike + ce_price + pe_price
        breakeven_down = strike - ce_price - pe_price
        
        self.active[symbol] = {
            'strike': strike, 'ce_entry': ce_price, 'pe_entry': pe_price,
            'qty': qty, 'total_cost': cost,
            'breakeven_up': round(breakeven_up, 2),
            'breakeven_down': round(breakeven_down, 2),
            'entry_time': datetime.now().isoformat(),
            'expiry_days': expiry_days
        }
        return self.active[symbol]
    
    def update_prices(self, symbol, ce_price, pe_price, spot_price):
        if symbol not in self.active:
            return None
        pos = self.active[symbol]
        current_value = (ce_price + pe_price) * pos['qty']
        pnl = current_value - pos['total_cost']
        pnl_pct = pnl / pos['total_cost'] * 100
        
        pos.update({
            'ce_current': ce_price, 'pe_current': pe_price,
            'current_value': round(current_value, 2),
            'pnl': round(pnl, 2), 'pnl_pct': round(pnl_pct, 2),
            'spot': spot_price
        })
        
        # Generate adjustment signals
        adjustment = None
        if pnl_pct > 50:
            adjustment = 'BOOK_PROFIT — 50%+ gain, close position'
        elif pnl_pct < -30:
            adjustment = 'ROLL_LOSING_LEG — adjust to reduce cost'
        elif ce_price > pe_price * 3:
            adjustment = 'SELL_EXTRA_CE — CE overpriced, hedge by selling OTM CE'
        elif pe_price > ce_price * 3:
            adjustment = 'SELL_EXTRA_PE — PE overpriced, hedge by selling OTM PE'
        
        pos['adjustment'] = adjustment
        return pos
    
    def exit_position(self, symbol, ce_price, pe_price):
        if symbol not in self.active:
            return None
        pos = self.active.pop(symbol)
        exit_value = (ce_price + pe_price) * pos['qty']
        pnl = exit_value - pos['total_cost']
        
        result = {**pos, 'exit_value': round(exit_value, 2),
                  'final_pnl': round(pnl, 2), 'result': 'WIN' if pnl > 0 else 'LOSS',
                  'exit_time': datetime.now().isoformat()}
        self.history.append(result)
        return result
    
    def should_enter(self, iv_percentile, expected_move_pct):
        if iv_percentile < 30 and expected_move_pct > 2:
            return {'enter': True, 'reason': 'Low IV + big move expected = cheap straddle'}
        if iv_percentile > 70:
            return {'enter': False, 'reason': 'IV too high — straddle expensive'}
        return {'enter': False, 'reason': 'Conditions not ideal'}
