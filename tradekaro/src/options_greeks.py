"""
📐 Options Greeks Calculator — Black-Scholes Based Greeks

Calculates:
  Delta (δ): How much option moves per ₹1 underlying move
  Gamma (γ): Rate of delta change
  Theta (θ): Daily time decay
  Vega (ν): Sensitivity to IV change
  Rho (ρ): Sensitivity to interest rate

Also: Implied Volatility solver via Newton-Raphson.
"""

import math
import numpy as np


class OptionsGreeks:
    """
    Black-Scholes Greeks calculator.
    
    Usage:
        greeks = OptionsGreeks()
        result = greeks.calculate(
            spot=22500, strike=22500, expiry_days=7,
            iv=15, option_type='CE', risk_free=6.5
        )
        # {'delta': 0.52, 'gamma': 0.0003, 'theta': -35.2, 'vega': 12.5}
    """
    
    def calculate(self, spot, strike, expiry_days, iv, 
                  option_type='CE', risk_free=6.5):
        """
        Calculate all Greeks.
        
        Args:
            spot: Current price
            strike: Option strike
            expiry_days: Days to expiry
            iv: Implied volatility (as %, e.g., 15)
            option_type: 'CE' or 'PE'
            risk_free: Risk-free rate (as %, e.g., 6.5)
        """
        S = spot
        K = strike
        T = max(expiry_days / 365, 0.001)
        sigma = iv / 100
        r = risk_free / 100
        
        d1 = (math.log(S / K) + (r + sigma**2 / 2) * T) / (sigma * math.sqrt(T))
        d2 = d1 - sigma * math.sqrt(T)
        
        nd1 = self._norm_cdf(d1)
        nd2 = self._norm_cdf(d2)
        npd1 = self._norm_pdf(d1)
        
        if option_type == 'CE':
            delta = nd1
            price = S * nd1 - K * math.exp(-r * T) * nd2
        else:
            delta = nd1 - 1
            price = K * math.exp(-r * T) * self._norm_cdf(-d2) - S * self._norm_cdf(-d1)
        
        gamma = npd1 / (S * sigma * math.sqrt(T))
        vega = S * npd1 * math.sqrt(T) / 100  # Per 1% IV change
        
        if option_type == 'CE':
            theta = (-(S * npd1 * sigma) / (2 * math.sqrt(T)) 
                    - r * K * math.exp(-r * T) * nd2) / 365
        else:
            theta = (-(S * npd1 * sigma) / (2 * math.sqrt(T)) 
                    + r * K * math.exp(-r * T) * self._norm_cdf(-d2)) / 365
        
        rho = K * T * math.exp(-r * T) * (nd2 if option_type == 'CE' else -self._norm_cdf(-d2)) / 100
        
        # Intrinsic value
        if option_type == 'CE':
            intrinsic = max(0, S - K)
        else:
            intrinsic = max(0, K - S)
        
        return {
            'price': round(price, 2),
            'delta': round(delta, 4),
            'gamma': round(gamma, 6),
            'theta': round(theta, 2),
            'vega': round(vega, 2),
            'rho': round(rho, 4),
            'intrinsic': round(intrinsic, 2),
            'time_value': round(price - intrinsic, 2),
            'moneyness': 'ITM' if intrinsic > 0 else 'ATM' if abs(S - K) / S < 0.005 else 'OTM',
            'd1': round(d1, 4),
            'd2': round(d2, 4)
        }
    
    def implied_volatility(self, market_price, spot, strike, expiry_days,
                           option_type='CE', risk_free=6.5, precision=0.001):
        """
        Solve for IV given market price (Newton-Raphson).
        """
        sigma = 0.20  # Initial guess: 20%
        
        for _ in range(100):
            S, K, T, r = spot, strike, max(expiry_days / 365, 0.001), risk_free / 100
            d1 = (math.log(S / K) + (r + sigma**2 / 2) * T) / (sigma * math.sqrt(T))
            d2 = d1 - sigma * math.sqrt(T)
            
            if option_type == 'CE':
                theo_price = S * self._norm_cdf(d1) - K * math.exp(-r * T) * self._norm_cdf(d2)
            else:
                theo_price = K * math.exp(-r * T) * self._norm_cdf(-d2) - S * self._norm_cdf(-d1)
            
            vega = S * self._norm_pdf(d1) * math.sqrt(T)
            
            if abs(vega) < 1e-10:
                break
            
            diff = market_price - theo_price
            if abs(diff) < precision:
                break
            
            sigma += diff / vega
            sigma = max(0.01, min(5.0, sigma))
        
        return round(sigma * 100, 2)
    
    def position_greeks(self, positions):
        """
        Aggregate Greeks across multiple positions.
        
        Args:
            positions: list of {spot, strike, expiry_days, iv, type, qty, lot_size}
        """
        total = {'delta': 0, 'gamma': 0, 'theta': 0, 'vega': 0}
        
        for pos in positions:
            g = self.calculate(
                pos['spot'], pos['strike'], pos['expiry_days'],
                pos['iv'], pos.get('type', 'CE')
            )
            multiplier = pos.get('qty', 1) * pos.get('lot_size', 1)
            
            for key in total:
                total[key] += g[key] * multiplier
        
        return {k: round(v, 2) for k, v in total.items()}
    
    def _norm_cdf(self, x):
        return (1 + math.erf(x / math.sqrt(2))) / 2
    
    def _norm_pdf(self, x):
        return math.exp(-x**2 / 2) / math.sqrt(2 * math.pi)
