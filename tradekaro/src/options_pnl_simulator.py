"""
📈 Options P&L Simulator — What-If Scenario Analysis

Answer: "If NIFTY moves to 23000 in 3 days, what's my straddle worth?"
  Simulates P&L across price range and time decay
"""

import math
import numpy as np


class OptionsPnLSimulator:
    
    def simulate_pnl(self, positions, spot, price_range_pct=5, days_range=7, steps=20):
        prices = np.linspace(spot * (1 - price_range_pct/100), spot * (1 + price_range_pct/100), steps)
        days = list(range(0, days_range + 1))
        
        results = []
        for day in days:
            row = {'day': day}
            for price in prices:
                total_pnl = 0
                for pos in positions:
                    entry_premium = pos.get('entry_premium', 0)
                    strike = pos['strike']
                    qty = pos.get('qty', 1) * pos.get('lot_size', 25)
                    otype = pos.get('type', 'CE')
                    iv = pos.get('iv', 15) / 100
                    days_left = max(pos.get('expiry_days', 7) - day, 0.01)
                    
                    theo = self._bs_price(price, strike, days_left/365, iv, otype)
                    pnl = (theo - entry_premium) * qty
                    if pos.get('side', 'BUY') == 'SELL':
                        pnl = -pnl
                    total_pnl += pnl
                
                row[f'price_{round(price)}'] = round(total_pnl, 0)
            results.append(row)
        
        # Key levels
        today_pnl = results[0] if results else {}
        max_profit = max(today_pnl.values()) if today_pnl else 0
        max_loss = min(today_pnl.values()) if today_pnl else 0
        
        return {
            'matrix': results,
            'prices': [round(p, 0) for p in prices],
            'max_profit_today': max_profit,
            'max_loss_today': max_loss,
            'breakevens': self._find_breakevens(results[0] if results else {}, prices)
        }
    
    def quick_pnl(self, entry_price, strike, target_spot, iv, expiry_days, 
                  option_type='CE', side='BUY', qty=25):
        theo = self._bs_price(target_spot, strike, expiry_days/365, iv/100, option_type)
        pnl = (theo - entry_price) * qty
        if side == 'SELL':
            pnl = -pnl
        return {'theoretical_price': round(theo, 2), 'pnl': round(pnl, 2), 
                'pnl_pct': round(pnl / (entry_price * qty) * 100, 2)}
    
    def _bs_price(self, S, K, T, sigma, otype):
        T = max(T, 0.001)
        r = 0.065
        d1 = (math.log(S/K) + (r + sigma**2/2)*T) / (sigma*math.sqrt(T))
        d2 = d1 - sigma*math.sqrt(T)
        nd1 = (1 + math.erf(d1/math.sqrt(2)))/2
        nd2 = (1 + math.erf(d2/math.sqrt(2)))/2
        if otype == 'CE':
            return S*nd1 - K*math.exp(-r*T)*nd2
        else:
            return K*math.exp(-r*T)*(1-nd2) - S*(1-nd1)
    
    def _find_breakevens(self, row, prices):
        bes = []
        vals = [v for k, v in row.items() if k.startswith('price_')]
        for i in range(1, len(vals)):
            if (vals[i-1] < 0 and vals[i] >= 0) or (vals[i-1] >= 0 and vals[i] < 0):
                bes.append(round(prices[i], 0))
        return bes
