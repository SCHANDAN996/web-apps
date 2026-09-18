"""
⚖️ Risk Parity Engine — Equal Risk Contribution Portfolio

Traditional: Equal capital allocation (25% each)
Risk Parity: Each position contributes EQUAL RISK to portfolio

Example:
  NIFTY (low vol) gets MORE capital (because same ₹ = less risk)
  BANKNIFTY (high vol) gets LESS capital (same ₹ = more risk)

Result: Portfolio with same return but LOWER drawdown.
"""

import numpy as np


class RiskParityEngine:
    """
    Risk parity portfolio construction.
    
    Usage:
        engine = RiskParityEngine(capital=500000)
        alloc = engine.allocate({
            'NIFTY': {'returns': nifty_returns},
            'BANKNIFTY': {'returns': banknifty_returns},
            'RELIANCE': {'returns': reliance_returns}
        })
        # {'NIFTY': 250000, 'BANKNIFTY': 120000, 'RELIANCE': 130000}
    """
    
    def __init__(self, capital=500000, max_position_pct=40, leverage=1.0):
        self.capital = capital
        self.max_position_pct = max_position_pct
        self.leverage = leverage
    
    def allocate(self, assets):
        """
        Allocate capital so each asset contributes equal risk.
        
        Args:
            assets: dict {symbol: {'returns': np.array}}
        """
        if not assets:
            return {}
        
        # Calculate volatility for each asset
        vols = {}
        for sym, data in assets.items():
            returns = data.get('returns', np.array([0]))
            if len(returns) < 5:
                vols[sym] = 0.02  # Default 2%
            else:
                vols[sym] = np.std(returns) * np.sqrt(252)  # Annualized
        
        # Inverse volatility weights (higher vol → lower weight)
        inv_vols = {sym: 1.0 / max(v, 0.001) for sym, v in vols.items()}
        total_inv = sum(inv_vols.values())
        
        weights = {sym: iv / total_inv for sym, iv in inv_vols.items()}
        
        # Apply constraints
        effective_capital = self.capital * self.leverage
        allocations = {}
        max_alloc = effective_capital * self.max_position_pct / 100
        
        for sym, weight in weights.items():
            alloc = min(weight * effective_capital, max_alloc)
            allocations[sym] = round(alloc, 0)
        
        return allocations
    
    def get_risk_contributions(self, assets, allocations):
        """Calculate actual risk contribution of each position."""
        contributions = {}
        total_risk = 0
        
        for sym, data in assets.items():
            returns = data.get('returns', np.array([0]))
            vol = np.std(returns) * np.sqrt(252) if len(returns) > 5 else 0.02
            alloc = allocations.get(sym, 0)
            risk = alloc * vol
            contributions[sym] = risk
            total_risk += risk
        
        # As percentage of total risk
        pct = {sym: round(r / max(total_risk, 1) * 100, 1) 
               for sym, r in contributions.items()}
        
        return {
            'contributions_pct': pct,
            'contributions_abs': {k: round(v, 0) for k, v in contributions.items()},
            'total_portfolio_risk': round(total_risk, 0),
            'is_parity': max(pct.values()) - min(pct.values()) < 10 if pct else False
        }
    
    def rebalance_signal(self, current_alloc, target_alloc, threshold_pct=5):
        """Check if rebalancing is needed (drift > threshold)."""
        trades = []
        for sym in set(list(current_alloc.keys()) + list(target_alloc.keys())):
            curr = current_alloc.get(sym, 0)
            target = target_alloc.get(sym, 0)
            diff = target - curr
            diff_pct = abs(diff) / max(target, 1) * 100
            
            if diff_pct > threshold_pct:
                trades.append({
                    'symbol': sym,
                    'action': 'BUY' if diff > 0 else 'SELL',
                    'amount': abs(round(diff, 0)),
                    'drift_pct': round(diff_pct, 1)
                })
        
        return {
            'needs_rebalance': len(trades) > 0,
            'trades': trades
        }
