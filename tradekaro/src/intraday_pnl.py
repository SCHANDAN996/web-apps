"""
💹 Intraday P&L Tracker — Real-Time Mark-to-Market

Tracks live P&L with:
  - Real-time MTM (mark-to-market) on every tick
  - Realized + Unrealized P&L breakdown
  - Per-position and portfolio-level P&L
  - Intraday high/low watermark
  - Running brokerage cost tracking
  - Time-weighted P&L (when did you make/lose money?)
"""

from datetime import datetime, time as dt_time
from collections import defaultdict, deque


class IntradayPnLTracker:
    """
    Real-time P&L tracking for intraday positions.
    
    Usage:
        tracker = IntradayPnLTracker()
        tracker.add_position('NIFTY', 'BUY', qty=25, entry_price=22500)
        tracker.update_price('NIFTY', 22550)
        print(tracker.get_pnl())
        # {'total_unrealized': 1250, 'total_realized': 0}
    """
    
    def __init__(self):
        self.positions = {}
        self.realized_pnl = 0
        self.trade_log = []
        self.pnl_snapshots = deque(maxlen=1000)
        self.high_watermark = 0
        self.low_watermark = 0
        self.total_charges = 0
    
    def add_position(self, symbol, side, qty, entry_price, charges=0):
        """Add or update a position."""
        key = symbol
        self.total_charges += charges
        
        if key in self.positions:
            pos = self.positions[key]
            if pos['side'] == side:
                # Average up/down
                total_qty = pos['qty'] + qty
                pos['avg_price'] = (pos['avg_price'] * pos['qty'] + entry_price * qty) / total_qty
                pos['qty'] = total_qty
            else:
                # Partial/full close
                close_qty = min(pos['qty'], qty)
                if side == 'BUY':
                    pnl = (pos['avg_price'] - entry_price) * close_qty
                else:
                    pnl = (entry_price - pos['avg_price']) * close_qty
                
                self.realized_pnl += pnl
                pos['qty'] -= close_qty
                
                if pos['qty'] <= 0:
                    del self.positions[key]
                
                self.trade_log.append({
                    'symbol': symbol, 'pnl': round(pnl, 2),
                    'qty': close_qty, 'time': datetime.now().isoformat()
                })
        else:
            self.positions[key] = {
                'symbol': symbol, 'side': side, 'qty': qty,
                'avg_price': entry_price, 'current_price': entry_price,
                'unrealized': 0
            }
    
    def update_price(self, symbol, current_price):
        """Update LTP for MTM calculation."""
        if symbol in self.positions:
            pos = self.positions[symbol]
            pos['current_price'] = current_price
            
            if pos['side'] == 'BUY':
                pos['unrealized'] = (current_price - pos['avg_price']) * pos['qty']
            else:
                pos['unrealized'] = (pos['avg_price'] - current_price) * pos['qty']
        
        # Snapshot
        total = self._total_unrealized() + self.realized_pnl
        self.high_watermark = max(self.high_watermark, total)
        self.low_watermark = min(self.low_watermark, total)
        
        self.pnl_snapshots.append({
            'time': datetime.now().strftime('%H:%M:%S'),
            'total_pnl': round(total, 2)
        })
    
    def close_position(self, symbol, exit_price, qty=None, charges=0):
        """Close a position (full or partial)."""
        if symbol not in self.positions:
            return {'error': 'No position found'}
        
        pos = self.positions[symbol]
        close_qty = qty or pos['qty']
        close_qty = min(close_qty, pos['qty'])
        
        self.total_charges += charges
        
        if pos['side'] == 'BUY':
            pnl = (exit_price - pos['avg_price']) * close_qty
        else:
            pnl = (pos['avg_price'] - exit_price) * close_qty
        
        self.realized_pnl += pnl
        pos['qty'] -= close_qty
        
        result = {
            'symbol': symbol, 'pnl': round(pnl, 2),
            'entry': pos['avg_price'], 'exit': exit_price,
            'qty': close_qty, 'result': 'WIN' if pnl > 0 else 'LOSS'
        }
        
        self.trade_log.append({**result, 'time': datetime.now().isoformat()})
        
        if pos['qty'] <= 0:
            del self.positions[symbol]
        
        return result
    
    def get_pnl(self):
        """Get complete P&L breakdown."""
        unrealized = self._total_unrealized()
        total = unrealized + self.realized_pnl
        net = total - self.total_charges
        
        return {
            'total_unrealized': round(unrealized, 2),
            'total_realized': round(self.realized_pnl, 2),
            'gross_pnl': round(total, 2),
            'total_charges': round(self.total_charges, 2),
            'net_pnl': round(net, 2),
            'high_watermark': round(self.high_watermark, 2),
            'low_watermark': round(self.low_watermark, 2),
            'open_positions': len(self.positions),
            'closed_trades': len(self.trade_log),
            'positions': {
                s: {'side': p['side'], 'qty': p['qty'],
                    'avg': round(p['avg_price'], 2),
                    'ltp': round(p['current_price'], 2),
                    'pnl': round(p['unrealized'], 2)}
                for s, p in self.positions.items()
            }
        }
    
    def get_time_pnl(self):
        """Get P&L curve over time (for charting)."""
        return list(self.pnl_snapshots)
    
    def reset_day(self):
        """Reset for new trading day."""
        self.positions.clear()
        self.realized_pnl = 0
        self.trade_log.clear()
        self.pnl_snapshots.clear()
        self.high_watermark = 0
        self.low_watermark = 0
        self.total_charges = 0
    
    def _total_unrealized(self):
        return sum(p['unrealized'] for p in self.positions.values())
