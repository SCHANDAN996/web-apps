"""
📉 Dynamic VaR Risk Engine — Value at Risk + CVaR Based Position Sizing

Instead of fixed 2% stop-loss:
  VaR: "With 95% confidence, max loss in next day won't exceed ₹X"
  CVaR: "If VaR is breached, average loss will be ₹Y"

Dynamically adjusts:
  - Position size based on VaR budget
  - Stop-loss levels based on tail risk
  - Portfolio-level risk limits
"""

import numpy as np
from datetime import datetime


class VaRRiskEngine:
    """
    Value at Risk and Conditional VaR for dynamic risk management.
    
    Usage:
        engine = VaRRiskEngine(capital=500000, max_var_pct=2.0)
        var = engine.calculate_var(returns_array, confidence=0.95)
        position = engine.optimal_position_size('NIFTY', returns, lot_value=22500*25)
    """
    
    def __init__(self, capital=500000, max_var_pct=2.0, max_cvar_pct=3.0):
        self.capital = capital
        self.max_var_pct = max_var_pct  # Max daily VaR as % of capital
        self.max_cvar_pct = max_cvar_pct
        self.var_budget = capital * max_var_pct / 100  # ₹ amount
    
    def calculate_var(self, returns, confidence=0.95, method='historical'):
        """
        Calculate Value at Risk.
        
        Args:
            returns: np.array of daily returns (e.g., [-0.02, 0.01, -0.005, ...])
            confidence: 95% or 99%
            method: 'historical' or 'parametric'
            
        Returns:
            float: VaR as positive percentage
        """
        if len(returns) < 20:
            return 0.02  # Default 2%
        
        if method == 'historical':
            var = np.percentile(returns, (1 - confidence) * 100)
        else:
            # Parametric (assumes normal distribution)
            mu = np.mean(returns)
            sigma = np.std(returns)
            z = {0.95: 1.645, 0.99: 2.326, 0.90: 1.282}.get(confidence, 1.645)
            var = mu - z * sigma
        
        return abs(var)
    
    def calculate_cvar(self, returns, confidence=0.95):
        """
        Conditional VaR (Expected Shortfall).
        Average loss BEYOND the VaR threshold.
        """
        if len(returns) < 20:
            return 0.03
        
        var = self.calculate_var(returns, confidence)
        tail_losses = returns[returns <= -var]
        
        if len(tail_losses) == 0:
            return var * 1.5
        
        return abs(np.mean(tail_losses))
    
    def optimal_position_size(self, symbol, returns, lot_value,
                             confidence=0.95):
        """
        Calculate optimal position size based on VaR budget.
        
        "How many lots can I trade such that 95% VaR stays within budget?"
        """
        var_pct = self.calculate_var(returns, confidence)
        cvar_pct = self.calculate_cvar(returns, confidence)
        
        # Max position such that VaR doesn't exceed budget
        if var_pct > 0:
            max_position_by_var = self.var_budget / (lot_value * var_pct)
        else:
            max_position_by_var = 1
        
        # Also check CVaR constraint (stricter)
        cvar_budget = self.capital * self.max_cvar_pct / 100
        if cvar_pct > 0:
            max_position_by_cvar = cvar_budget / (lot_value * cvar_pct)
        else:
            max_position_by_cvar = 1
        
        optimal_lots = min(max_position_by_var, max_position_by_cvar)
        optimal_lots = max(1, int(optimal_lots))
        
        return {
            'symbol': symbol,
            'optimal_lots': optimal_lots,
            'var_95': round(var_pct * 100, 2),
            'cvar_95': round(cvar_pct * 100, 2),
            'max_daily_loss': round(optimal_lots * lot_value * var_pct, 0),
            'var_budget': self.var_budget,
            'confidence': confidence
        }
    
    def portfolio_var(self, positions, correlation_matrix=None):
        """
        Calculate portfolio-level VaR considering correlations.
        
        Args:
            positions: list of {symbol, returns, value}
            correlation_matrix: np.array NxN
        """
        n = len(positions)
        if n == 0:
            return 0
        
        individual_vars = []
        values = []
        
        for pos in positions:
            var = self.calculate_var(pos['returns']) * pos['value']
            individual_vars.append(var)
            values.append(pos['value'])
        
        vars_arr = np.array(individual_vars)
        
        if correlation_matrix is not None and correlation_matrix.shape == (n, n):
            # Correlated VaR: sqrt(V' * C * V)
            portfolio_var = np.sqrt(vars_arr @ correlation_matrix @ vars_arr)
        else:
            # Uncorrelated: sqrt(sum of squared VaRs)
            portfolio_var = np.sqrt(np.sum(vars_arr ** 2))
        
        total_value = sum(values)
        
        return {
            'portfolio_var': round(portfolio_var, 0),
            'portfolio_var_pct': round(portfolio_var / max(total_value, 1) * 100, 2),
            'within_budget': portfolio_var <= self.var_budget,
            'individual_vars': {p['symbol']: round(v, 0) 
                               for p, v in zip(positions, individual_vars)}
        }
    
    def dynamic_stop_loss(self, returns, base_sl_pct=1.5):
        """
        Calculate dynamic stop-loss based on recent volatility.
        Tight in calm markets, wider in volatile.
        """
        if len(returns) < 10:
            return base_sl_pct
        
        recent_vol = np.std(returns[-10:]) * 100  # As percentage
        
        # SL = max(base, 2 * recent daily volatility)
        dynamic_sl = max(base_sl_pct, recent_vol * 2)
        
        # Cap at 5%
        return round(min(5.0, dynamic_sl), 2)
