"""
🛡️ Hedge Calculator — Optimal Hedge Ratio for Any Position

Calculates how many puts/futures needed to hedge a stock portfolio:
  Delta hedge, Beta hedge, Minimum variance hedge
"""

import numpy as np


class HedgeCalculator:
    
    def delta_hedge(self, stock_qty, stock_price, option_delta, lot_size=25):
        position_value = stock_qty * stock_price
        delta_exposure = stock_qty  # Each share = 1 delta
        options_needed = abs(delta_exposure) / (abs(option_delta) * lot_size)
        return {
            'hedge_lots': round(options_needed), 'hedge_side': 'BUY_PE' if stock_qty > 0 else 'BUY_CE',
            'delta_before': delta_exposure, 'delta_after': round(delta_exposure - options_needed * option_delta * lot_size, 1),
            'cost_estimate': 'Depends on option premium'
        }
    
    def beta_hedge(self, portfolio_value, portfolio_beta, nifty_price, nifty_lot_size=25):
        hedge_value = portfolio_value * portfolio_beta
        nifty_lots = hedge_value / (nifty_price * nifty_lot_size)
        return {
            'nifty_lots': round(nifty_lots), 'hedge_value': round(hedge_value, 0),
            'portfolio_beta': portfolio_beta,
            'action': f'SELL {round(nifty_lots)} NIFTY futures to neutralize beta'
        }
    
    def collar_hedge(self, stock_price, stock_qty, put_strike, call_strike, put_premium, call_premium):
        net_cost = (put_premium - call_premium) * stock_qty
        max_loss = (stock_price - put_strike) * stock_qty + net_cost
        max_gain = (call_strike - stock_price) * stock_qty - net_cost
        return {
            'net_cost': round(net_cost, 2), 'max_loss': round(max_loss, 2), 'max_gain': round(max_gain, 2),
            'protection_below': put_strike, 'capped_above': call_strike,
            'breakeven': round(stock_price + net_cost / stock_qty, 2)
        }
    
    def minimum_variance_hedge(self, stock_returns, hedge_returns):
        if len(stock_returns) != len(hedge_returns) or len(stock_returns) < 20:
            return {'ratio': 1.0}
        cov = np.cov(stock_returns, hedge_returns)[0][1]
        var = np.var(hedge_returns)
        ratio = cov / max(var, 1e-8)
        return {'ratio': round(ratio, 3), 'interpretation': f'Hedge {abs(ratio):.1%} of position'}
