"""
📈 Options Strategy Engine — Auto-Select Optimal Options Strategy

Selects strategy based on:
  - Market Regime (Bull/Bear/Sideways)
  - Implied Volatility (High/Low)
  - Gamma Exposure (GEX)
  - Event Calendar (RBI/Budget days)

Strategy Matrix:
  BULL + Low IV      → Bull Call Spread
  BEAR + Low IV      → Bear Put Spread
  SIDEWAYS + High IV → Iron Condor / Short Straddle
  TRANSITION + High  → Long Straddle (bet on big move)
  Event Day          → Long Strangle (bet on direction unknown)
"""

import json
import os
import logging
from datetime import datetime


class OptionsStrategy:
    """Represents a single options strategy with entry/exit rules."""
    
    def __init__(self, name, legs, max_loss, max_profit, 
                 profit_target_pct=50, stop_loss_pct=100):
        self.name = name
        self.legs = legs  # List of dicts: {type: CE/PE, action: BUY/SELL, strike, qty}
        self.max_loss = max_loss
        self.max_profit = max_profit
        self.profit_target_pct = profit_target_pct
        self.stop_loss_pct = stop_loss_pct
        self.created = datetime.now().isoformat()
    
    def to_dict(self):
        return {
            'name': self.name,
            'legs': self.legs,
            'max_loss': self.max_loss,
            'max_profit': self.max_profit,
            'profit_target_pct': self.profit_target_pct,
            'stop_loss_pct': self.stop_loss_pct,
            'created': self.created
        }


class OptionsStrategyEngine:
    """
    Auto-selects and constructs optimal options strategy.
    
    Usage:
        engine = OptionsStrategyEngine()
        strategy = engine.select_strategy(
            regime='BULL_TREND',
            iv_percentile=30,
            spot_price=22500,
            atm_strike=22500,
            expiry='2026-03-13'
        )
        # Returns OptionsStrategy object with legs, P&L limits, etc.
    """
    
    # Strategy selection matrix
    STRATEGY_MATRIX = {
        ('BULL_TREND', 'LOW_IV'):       'BULL_CALL_SPREAD',
        ('BULL_TREND', 'HIGH_IV'):      'BULL_PUT_SPREAD',  # Sell high IV
        ('BEAR_TREND', 'LOW_IV'):       'BEAR_PUT_SPREAD',
        ('BEAR_TREND', 'HIGH_IV'):      'BEAR_CALL_SPREAD',
        ('SIDEWAYS_QUIET', 'HIGH_IV'):  'IRON_CONDOR',
        ('SIDEWAYS_QUIET', 'LOW_IV'):   'IRON_BUTTERFLY',
        ('SIDEWAYS_VOLATILE', 'HIGH_IV'): 'SHORT_STRADDLE',
        ('SIDEWAYS_VOLATILE', 'LOW_IV'): 'LONG_STRADDLE',
        ('TRANSITION', 'HIGH_IV'):      'LONG_STRADDLE',
        ('TRANSITION', 'LOW_IV'):       'LONG_STRANGLE',
    }
    
    # Strike spacing per index
    STRIKE_GAP = {
        'NIFTY': 50,
        'BANKNIFTY': 100,
        'FINNIFTY': 50,
        'DEFAULT': 50
    }
    
    def __init__(self):
        self.active_strategies = []
        self.history = []
    
    def select_strategy(self, regime, iv_percentile, spot_price, 
                       atm_strike=None, symbol='NIFTY', expiry=None,
                       lot_size=25, is_event_day=False):
        """
        Select and construct the optimal options strategy.
        
        Args:
            regime: str — Market regime (BULL_TREND, BEAR_TREND, etc.)
            iv_percentile: float — Current IV percentile (0-100)
            spot_price: float — Current spot/underlying price
            atm_strike: float — ATM strike (auto-calculated if None)
            symbol: str — NIFTY, BANKNIFTY, etc.
            expiry: str — Expiry date
            lot_size: int — Lot size for the symbol
            is_event_day: bool — RBI/Budget day flag
        
        Returns:
            OptionsStrategy object
        """
        # Determine IV level
        iv_level = 'HIGH_IV' if iv_percentile > 50 else 'LOW_IV'
        
        # Event day override
        if is_event_day:
            strategy_name = 'LONG_STRANGLE'
        else:
            key = (regime, iv_level)
            strategy_name = self.STRATEGY_MATRIX.get(key, 'IRON_CONDOR')
        
        # Calculate ATM strike
        gap = self.STRIKE_GAP.get(symbol, 50)
        if atm_strike is None:
            atm_strike = round(spot_price / gap) * gap
        
        # Build strategy legs
        strategy = self._build_strategy(
            strategy_name, atm_strike, gap, lot_size, expiry, spot_price
        )
        
        logging.info(f"[Options] Selected: {strategy_name} | "
                    f"Regime: {regime} | IV: {iv_percentile}% | "
                    f"ATM: {atm_strike}")
        
        return strategy
    
    def _build_strategy(self, name, atm, gap, lot_size, expiry, spot):
        """Construct strategy legs based on name."""
        
        builders = {
            'BULL_CALL_SPREAD': self._bull_call_spread,
            'BULL_PUT_SPREAD': self._bull_put_spread,
            'BEAR_PUT_SPREAD': self._bear_put_spread,
            'BEAR_CALL_SPREAD': self._bear_call_spread,
            'IRON_CONDOR': self._iron_condor,
            'IRON_BUTTERFLY': self._iron_butterfly,
            'SHORT_STRADDLE': self._short_straddle,
            'LONG_STRADDLE': self._long_straddle,
            'LONG_STRANGLE': self._long_strangle,
        }
        
        builder = builders.get(name, self._iron_condor)
        return builder(atm, gap, lot_size, expiry)
    
    def _bull_call_spread(self, atm, gap, qty, expiry):
        legs = [
            {'type': 'CE', 'action': 'BUY',  'strike': atm,       'qty': qty},
            {'type': 'CE', 'action': 'SELL', 'strike': atm + gap*2, 'qty': qty},
        ]
        max_loss = gap * 2 * qty  # Approximate debit
        max_profit = gap * 2 * qty
        return OptionsStrategy('Bull Call Spread', legs, max_loss, max_profit,
                              profit_target_pct=60, stop_loss_pct=80)
    
    def _bull_put_spread(self, atm, gap, qty, expiry):
        legs = [
            {'type': 'PE', 'action': 'SELL', 'strike': atm,        'qty': qty},
            {'type': 'PE', 'action': 'BUY',  'strike': atm - gap*2, 'qty': qty},
        ]
        max_loss = gap * 2 * qty
        max_profit = gap * qty  # Credit received
        return OptionsStrategy('Bull Put Spread', legs, max_loss, max_profit,
                              profit_target_pct=50, stop_loss_pct=100)
    
    def _bear_put_spread(self, atm, gap, qty, expiry):
        legs = [
            {'type': 'PE', 'action': 'BUY',  'strike': atm,        'qty': qty},
            {'type': 'PE', 'action': 'SELL', 'strike': atm - gap*2, 'qty': qty},
        ]
        max_loss = gap * 2 * qty
        max_profit = gap * 2 * qty
        return OptionsStrategy('Bear Put Spread', legs, max_loss, max_profit,
                              profit_target_pct=60, stop_loss_pct=80)
    
    def _bear_call_spread(self, atm, gap, qty, expiry):
        legs = [
            {'type': 'CE', 'action': 'SELL', 'strike': atm,        'qty': qty},
            {'type': 'CE', 'action': 'BUY',  'strike': atm + gap*2, 'qty': qty},
        ]
        max_loss = gap * 2 * qty
        max_profit = gap * qty  # Credit received
        return OptionsStrategy('Bear Call Spread', legs, max_loss, max_profit,
                              profit_target_pct=50, stop_loss_pct=100)
    
    def _iron_condor(self, atm, gap, qty, expiry):
        legs = [
            {'type': 'PE', 'action': 'SELL', 'strike': atm - gap*2, 'qty': qty},
            {'type': 'PE', 'action': 'BUY',  'strike': atm - gap*4, 'qty': qty},
            {'type': 'CE', 'action': 'SELL', 'strike': atm + gap*2, 'qty': qty},
            {'type': 'CE', 'action': 'BUY',  'strike': atm + gap*4, 'qty': qty},
        ]
        max_loss = gap * 2 * qty  # Difference between strikes
        max_profit = gap * qty  # Total credit
        return OptionsStrategy('Iron Condor', legs, max_loss, max_profit,
                              profit_target_pct=40, stop_loss_pct=100)
    
    def _iron_butterfly(self, atm, gap, qty, expiry):
        legs = [
            {'type': 'CE', 'action': 'SELL', 'strike': atm, 'qty': qty},
            {'type': 'PE', 'action': 'SELL', 'strike': atm, 'qty': qty},
            {'type': 'CE', 'action': 'BUY',  'strike': atm + gap*3, 'qty': qty},
            {'type': 'PE', 'action': 'BUY',  'strike': atm - gap*3, 'qty': qty},
        ]
        max_loss = gap * 3 * qty
        max_profit = gap * 2 * qty
        return OptionsStrategy('Iron Butterfly', legs, max_loss, max_profit,
                              profit_target_pct=50, stop_loss_pct=80)
    
    def _short_straddle(self, atm, gap, qty, expiry):
        legs = [
            {'type': 'CE', 'action': 'SELL', 'strike': atm, 'qty': qty},
            {'type': 'PE', 'action': 'SELL', 'strike': atm, 'qty': qty},
        ]
        max_loss = float('inf')  # Unlimited risk!
        max_profit = gap * 3 * qty  # Approximate credit
        return OptionsStrategy('Short Straddle', legs, max_loss, max_profit,
                              profit_target_pct=30, stop_loss_pct=50)
    
    def _long_straddle(self, atm, gap, qty, expiry):
        legs = [
            {'type': 'CE', 'action': 'BUY', 'strike': atm, 'qty': qty},
            {'type': 'PE', 'action': 'BUY', 'strike': atm, 'qty': qty},
        ]
        max_loss = gap * 4 * qty  # Premium paid
        max_profit = float('inf')  # Unlimited
        return OptionsStrategy('Long Straddle', legs, max_loss, max_profit,
                              profit_target_pct=80, stop_loss_pct=60)
    
    def _long_strangle(self, atm, gap, qty, expiry):
        legs = [
            {'type': 'CE', 'action': 'BUY', 'strike': atm + gap*2, 'qty': qty},
            {'type': 'PE', 'action': 'BUY', 'strike': atm - gap*2, 'qty': qty},
        ]
        max_loss = gap * 2 * qty
        max_profit = float('inf')
        return OptionsStrategy('Long Strangle', legs, max_loss, max_profit,
                              profit_target_pct=100, stop_loss_pct=70)
    
    def get_strategy_for_regime(self, regime, iv_pct):
        """Quick helper — get strategy name without building legs."""
        iv_level = 'HIGH_IV' if iv_pct > 50 else 'LOW_IV'
        return self.STRATEGY_MATRIX.get((regime, iv_level), 'IRON_CONDOR')
