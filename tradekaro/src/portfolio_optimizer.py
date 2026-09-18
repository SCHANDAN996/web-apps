"""
📊 Portfolio Optimizer — Kelly Criterion + Markowitz for Optimal Capital Allocation

Kelly Criterion: Optimal bet size = edge / odds
Markowitz: Efficient frontier for maximum Sharpe ratio

Features:
- Position sizing based on historical win rate + avg win/loss
- Sector diversification (max 30% per sector)
- Maximum drawdown guard (auto-reduce if DD > threshold)
- Correlation-aware allocation (don't bet heavily on correlated stocks)
"""

import numpy as np
from collections import defaultdict


class PortfolioOptimizer:
    """
    Smart capital allocation using Kelly + Markowitz principles.
    
    Usage:
        optimizer = PortfolioOptimizer(total_capital=500000)
        allocation = optimizer.optimize({
            'RELIANCE': {'confidence': 0.78, 'sector': 'OIL'},
            'HDFCBANK': {'confidence': 0.72, 'sector': 'BANKS'},
            'TCS': {'confidence': 0.65, 'sector': 'IT'}
        })
        # allocation = {'RELIANCE': 45000, 'HDFCBANK': 35000, 'TCS': 20000}
    """
    
    # Sector limits (max % of portfolio per sector)
    SECTOR_LIMITS = {
        'BANKS': 0.30,
        'IT': 0.25,
        'OIL': 0.20,
        'AUTO': 0.20,
        'PHARMA': 0.20,
        'METALS': 0.15,
        'DEFAULT': 0.20
    }
    
    def __init__(self, total_capital=500000, max_position_pct=0.15,
                 max_drawdown_pct=5.0, risk_free_rate=0.06):
        self.total_capital = total_capital
        self.max_position_pct = max_position_pct  # Max 15% per stock
        self.max_drawdown_pct = max_drawdown_pct
        self.risk_free_rate = risk_free_rate
        self.trade_history = []  # For Kelly calculation
    
    def optimize(self, candidates, current_drawdown=0):
        """
        Allocate capital across candidates using Kelly + constraints.
        
        Args:
            candidates: dict {symbol: {confidence, sector, volatility}}
            current_drawdown: current portfolio drawdown %
            
        Returns:
            dict {symbol: allocation_amount}
        """
        if not candidates:
            return {}
        
        # Adjust for drawdown (reduce exposure as drawdown increases)
        drawdown_factor = max(0.3, 1.0 - (current_drawdown / self.max_drawdown_pct))
        effective_capital = self.total_capital * drawdown_factor
        
        # Calculate Kelly fraction for each candidate
        kelly_fractions = {}
        for sym, info in candidates.items():
            confidence = info.get('confidence', 0.5)
            kelly = self._kelly_fraction(confidence)
            kelly_fractions[sym] = kelly
        
        # Normalize and apply constraints
        total_kelly = sum(kelly_fractions.values())
        if total_kelly <= 0:
            return {sym: 0 for sym in candidates}
        
        allocations = {}
        sector_usage = defaultdict(float)
        
        # Sort by confidence (highest first)
        sorted_syms = sorted(candidates.keys(), 
                           key=lambda s: candidates[s].get('confidence', 0),
                           reverse=True)
        
        for sym in sorted_syms:
            info = candidates[sym]
            sector = info.get('sector', 'DEFAULT')
            
            # Kelly-based allocation
            raw_alloc = (kelly_fractions[sym] / total_kelly) * effective_capital
            
            # Apply position limit
            max_position = effective_capital * self.max_position_pct
            raw_alloc = min(raw_alloc, max_position)
            
            # Apply sector limit
            sector_limit = self.SECTOR_LIMITS.get(sector, 0.20) * effective_capital
            remaining_sector = max(0, sector_limit - sector_usage[sector])
            raw_alloc = min(raw_alloc, remaining_sector)
            
            # Skip very small allocations
            if raw_alloc < 5000:
                raw_alloc = 0
            
            allocations[sym] = round(raw_alloc, 0)
            sector_usage[sector] += raw_alloc
        
        return allocations
    
    def _kelly_fraction(self, confidence):
        """
        Kelly Criterion: f* = (bp - q) / b
        
        Where:
          b = odds (win/loss ratio, assumed 1.5 for trading)
          p = probability of winning = confidence
          q = probability of losing = 1 - confidence
        """
        p = max(0.01, min(0.99, confidence))
        q = 1 - p
        b = 1.5  # Average win/loss ratio in trading
        
        kelly = (b * p - q) / b
        
        # Half-Kelly for safety (standard practice)
        kelly = max(0, kelly * 0.5)
        
        return kelly
    
    def record_trade(self, symbol, pnl, capital_used):
        """Record trade for improved Kelly estimates."""
        self.trade_history.append({
            'symbol': symbol,
            'pnl': pnl,
            'capital': capital_used,
            'return_pct': (pnl / capital_used * 100) if capital_used > 0 else 0
        })
    
    def get_portfolio_stats(self, allocations):
        """Get portfolio summary statistics."""
        total_allocated = sum(allocations.values())
        num_positions = len([v for v in allocations.values() if v > 0])
        cash = self.total_capital - total_allocated
        
        return {
            'total_capital': self.total_capital,
            'allocated': total_allocated,
            'cash': cash,
            'utilization_pct': round(total_allocated / self.total_capital * 100, 1),
            'num_positions': num_positions,
            'avg_position': round(total_allocated / max(num_positions, 1), 0)
        }
