"""
💰 Paper Trade Simulator — Full Simulation Without Real Money

Complete paper trading engine:
  - Simulates order placement with realistic fills
  - Tracks positions, P&L, margin
  - Calculates brokerage + STT + GST
  - Drawdown monitoring
  - Performance analytics identical to live trading
"""

import time
from datetime import datetime
from collections import defaultdict


class PaperTradeSimulator:
    """
    Full paper trading engine with realistic execution.
    
    Usage:
        sim = PaperTradeSimulator(capital=500000)
        sim.buy('RELIANCE', qty=10, price=2500)
        sim.sell('RELIANCE', qty=10, price=2550)
        print(sim.get_portfolio())
    """
    
    # NSE charges (approximate)
    BROKERAGE_PCT = 0.03     # 0.03% per side
    STT_PCT = 0.025          # 0.025% delivery
    GST_PCT = 18             # 18% on brokerage
    STAMP_DUTY = 0.003       # 0.003%
    SEBI_FEE = 0.0001        # 0.0001%
    
    def __init__(self, capital=500000, slippage_pct=0.05):
        self.initial_capital = capital
        self.cash = capital
        self.slippage_pct = slippage_pct
        self.positions = {}    # {symbol: {qty, avg_price, side}}
        self.trades = []
        self.order_id = 0
        self.peak_equity = capital
    
    def buy(self, symbol, qty, price, order_type='MARKET'):
        """Place a buy order."""
        fill_price = price * (1 + self.slippage_pct / 100)
        cost = fill_price * qty
        charges = self._calculate_charges(cost)
        total_cost = cost + charges['total']
        
        if total_cost > self.cash:
            return {'status': 'REJECTED', 'reason': f'Insufficient cash (need ₹{total_cost:.0f}, have ₹{self.cash:.0f})'}
        
        self.cash -= total_cost
        self.order_id += 1
        
        if symbol in self.positions:
            pos = self.positions[symbol]
            total_qty = pos['qty'] + qty
            pos['avg_price'] = (pos['avg_price'] * pos['qty'] + fill_price * qty) / total_qty
            pos['qty'] = total_qty
        else:
            self.positions[symbol] = {'qty': qty, 'avg_price': fill_price, 'side': 'LONG'}
        
        trade = {
            'id': self.order_id, 'symbol': symbol, 'side': 'BUY',
            'qty': qty, 'price': round(fill_price, 2), 'cost': round(total_cost, 2),
            'charges': charges, 'time': datetime.now().isoformat()
        }
        self.trades.append(trade)
        return {'status': 'FILLED', **trade}
    
    def sell(self, symbol, qty, price, order_type='MARKET'):
        """Place a sell order."""
        if symbol not in self.positions or self.positions[symbol]['qty'] < qty:
            return {'status': 'REJECTED', 'reason': 'Insufficient position'}
        
        fill_price = price * (1 - self.slippage_pct / 100)
        revenue = fill_price * qty
        charges = self._calculate_charges(revenue)
        net_revenue = revenue - charges['total']
        
        self.cash += net_revenue
        pos = self.positions[symbol]
        pnl = (fill_price - pos['avg_price']) * qty
        
        pos['qty'] -= qty
        if pos['qty'] == 0:
            del self.positions[symbol]
        
        self.order_id += 1
        trade = {
            'id': self.order_id, 'symbol': symbol, 'side': 'SELL',
            'qty': qty, 'price': round(fill_price, 2), 'pnl': round(pnl, 2),
            'charges': charges, 'time': datetime.now().isoformat()
        }
        self.trades.append(trade)
        
        # Update peak
        equity = self.get_equity()
        if equity > self.peak_equity:
            self.peak_equity = equity
        
        return {'status': 'FILLED', **trade}
    
    def get_equity(self):
        """Total equity = cash + position value."""
        position_value = sum(
            p['qty'] * p['avg_price'] for p in self.positions.values()
        )
        return round(self.cash + position_value, 2)
    
    def get_portfolio(self):
        """Full portfolio status."""
        equity = self.get_equity()
        drawdown = (self.peak_equity - equity) / max(self.peak_equity, 1) * 100
        
        wins = [t for t in self.trades if t.get('pnl', 0) > 0]
        losses = [t for t in self.trades if t.get('pnl', 0) < 0]
        total_sells = [t for t in self.trades if t['side'] == 'SELL']
        
        return {
            'equity': equity,
            'cash': round(self.cash, 2),
            'positions': {s: {'qty': p['qty'], 'avg': round(p['avg_price'], 2)} 
                         for s, p in self.positions.items()},
            'total_pnl': round(equity - self.initial_capital, 2),
            'return_pct': round((equity / self.initial_capital - 1) * 100, 2),
            'drawdown_pct': round(drawdown, 2),
            'total_trades': len(self.trades),
            'win_rate': round(len(wins) / max(len(total_sells), 1) * 100, 1),
            'total_charges': round(sum(t.get('charges', {}).get('total', 0) for t in self.trades), 2)
        }
    
    def _calculate_charges(self, turnover):
        """Calculate realistic trading charges."""
        brokerage = turnover * self.BROKERAGE_PCT / 100
        stt = turnover * self.STT_PCT / 100
        gst = brokerage * self.GST_PCT / 100
        stamp = turnover * self.STAMP_DUTY / 100
        sebi = turnover * self.SEBI_FEE / 100
        
        total = brokerage + stt + gst + stamp + sebi
        return {
            'brokerage': round(brokerage, 2), 'stt': round(stt, 2),
            'gst': round(gst, 2), 'stamp': round(stamp, 2),
            'sebi': round(sebi, 2), 'total': round(total, 2)
        }
