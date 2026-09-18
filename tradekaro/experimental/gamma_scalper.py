"""
⚡ Gamma Scalping Engine — Delta-Neutral Options Hedging

When holding options (straddle/strangle), gamma scalping:
  1. Buy underlying when price drops (delta becomes negative)
  2. Sell underlying when price rises (delta becomes positive)
  3. Net effect: lock in gamma profits from volatility

Makes money when market MOVES (regardless of direction).
"""

import numpy as np
from datetime import datetime
from collections import deque


class GammaScalpingEngine:
    """
    Auto-hedges options positions by scalping gamma.
    
    Usage:
        engine = GammaScalpingEngine(lot_size=25)
        action = engine.check_hedge(
            spot_price=22500, strike=22500, 
            option_delta=0.45, position_qty=2
        )
        # {'action': 'BUY_FUTURES', 'qty': 3, 'reason': 'Delta hedge needed'}
    """
    
    def __init__(self, lot_size=25, hedge_threshold=0.15, max_hedge_lots=10):
        self.lot_size = lot_size
        self.hedge_threshold = hedge_threshold
        self.max_hedge_lots = max_hedge_lots
        self.current_hedge = 0  # Current futures hedge position
        self.scalp_history = deque(maxlen=200)
        self.total_scalp_pnl = 0
    
    def check_hedge(self, spot_price, option_delta, position_qty,
                    option_type='CE', current_futures=0):
        """
        Check if delta hedge adjustment needed.
        
        Args:
            spot_price: Current underlying price
            option_delta: Current option delta (0 to 1 for CE, -1 to 0 for PE)
            position_qty: Number of option lots
            current_futures: Current futures hedge (positive = long)
        """
        # Total position delta
        if option_type == 'CE':
            position_delta = option_delta * position_qty * self.lot_size
        else:
            position_delta = option_delta * position_qty * self.lot_size  # Already negative for PE
        
        # Net delta including hedge
        net_delta = position_delta + (current_futures * self.lot_size)
        
        # Delta in terms of lots
        delta_lots = net_delta / self.lot_size
        
        # Check if hedge needed
        if abs(delta_lots) > self.hedge_threshold:
            hedge_qty = -round(delta_lots)  # Opposite direction
            hedge_qty = max(-self.max_hedge_lots, min(self.max_hedge_lots, hedge_qty))
            
            action = 'BUY_FUTURES' if hedge_qty > 0 else 'SELL_FUTURES'
            
            return {
                'action': action,
                'qty': abs(hedge_qty),
                'net_delta_before': round(delta_lots, 2),
                'net_delta_after': round(delta_lots + hedge_qty, 2),
                'reason': f'Delta imbalance: {delta_lots:.2f} lots, hedge {hedge_qty:+d}',
                'spot_price': spot_price,
                'timestamp': datetime.now().isoformat()
            }
        
        return {
            'action': 'HOLD',
            'net_delta': round(delta_lots, 2),
            'reason': f'Delta within threshold ({delta_lots:.2f} < {self.hedge_threshold})'
        }
    
    def record_scalp(self, buy_price, sell_price, qty):
        """Record a completed gamma scalp trade."""
        pnl = (sell_price - buy_price) * qty * self.lot_size
        self.total_scalp_pnl += pnl
        self.scalp_history.append({
            'buy': buy_price, 'sell': sell_price, 'qty': qty,
            'pnl': round(pnl, 0), 'time': datetime.now().isoformat()
        })
        return pnl
    
    def estimate_gamma_profit(self, spot_price, gamma, expected_move_pct):
        """
        Estimate potential gamma profit from a move.
        Gamma P&L ≈ 0.5 * Gamma * (ΔS)² * lot_size
        """
        move = spot_price * expected_move_pct / 100
        gamma_pnl = 0.5 * gamma * move ** 2 * self.lot_size
        return {
            'expected_move': round(move, 2),
            'gamma_pnl_per_lot': round(gamma_pnl, 0),
            'breakeven_move_pct': round(expected_move_pct, 3)
        }
    
    def get_stats(self):
        return {
            'total_scalps': len(self.scalp_history),
            'total_pnl': round(self.total_scalp_pnl, 0),
            'avg_pnl': round(self.total_scalp_pnl / max(len(self.scalp_history), 1), 0)
        }
