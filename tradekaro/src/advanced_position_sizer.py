"""
📊 Advanced Position Sizer — Optimal-f, Anti-Martingale, Kelly Variants

Goes beyond basic Kelly:
  Full Kelly, Half Kelly, Quarter Kelly
  Optimal-f (maximize geometric growth)
  Anti-martingale (increase after wins)
  Fixed fractional
"""

import numpy as np


class AdvancedPositionSizer:
    
    def fixed_fractional(self, capital, risk_pct=2.0, stop_loss_pct=1.5):
        risk_amount = capital * risk_pct / 100
        position_value = risk_amount / (stop_loss_pct / 100)
        return {'position_value': round(position_value, 0), 'risk_amount': round(risk_amount, 0),
                'pct_of_capital': round(position_value / capital * 100, 1)}
    
    def kelly(self, win_rate, avg_win, avg_loss, fraction=0.5):
        if avg_loss <= 0: return {'kelly_pct': 0}
        b = avg_win / avg_loss
        p = win_rate / 100
        full_kelly = p - (1 - p) / b
        adjusted = max(0, full_kelly * fraction)
        return {'full_kelly': round(full_kelly * 100, 2), 'adjusted_kelly': round(adjusted * 100, 2),
                'fraction': fraction, 'max_risk_pct': round(min(adjusted * 100, 25), 2)}
    
    def optimal_f(self, trade_results, steps=100):
        if not trade_results: return {'optimal_f': 0}
        best_f, best_growth = 0, 0
        max_loss = abs(min(trade_results))
        
        for f in np.linspace(0.01, 0.5, steps):
            growth = 1.0
            for r in trade_results:
                growth *= (1 + f * r / max_loss)
                if growth <= 0: break
            if growth > best_growth:
                best_growth = growth
                best_f = f
        
        return {'optimal_f': round(best_f, 4), 'geometric_growth': round(best_growth, 4),
                'risk_pct': round(best_f * 100, 2)}
    
    def anti_martingale(self, capital, base_risk_pct, consecutive_wins):
        multiplier = 1 + consecutive_wins * 0.25
        multiplier = min(multiplier, 3.0)
        risk = capital * base_risk_pct / 100 * multiplier
        return {'risk_amount': round(risk, 0), 'multiplier': multiplier,
                'effective_risk_pct': round(base_risk_pct * multiplier, 2)}
    
    def recommend(self, capital, win_rate, avg_win, avg_loss, recent_streak=0):
        kelly = self.kelly(win_rate, avg_win, avg_loss)
        ff = self.fixed_fractional(capital)
        am = self.anti_martingale(capital, 2.0, max(0, recent_streak))
        
        if win_rate > 55:
            method = 'HALF_KELLY'
            size = capital * kelly['adjusted_kelly'] / 100
        elif recent_streak > 3:
            method = 'ANTI_MARTINGALE'
            size = am['risk_amount']
        else:
            method = 'FIXED_FRACTIONAL'
            size = ff['risk_amount']
        
        return {'method': method, 'position_size': round(size, 0), 'kelly': kelly,
                'fixed_frac': ff, 'anti_mart': am}
