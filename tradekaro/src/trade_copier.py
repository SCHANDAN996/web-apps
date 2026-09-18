"""
🔁 Trade Copier — Mirror Trades Across Accounts/Strategies

Use cases:
  - Copy live trades to paper account for comparison
  - Mirror main account to backup account
  - Relay AI signals to multiple subscribers
  - Scale trades (2x for aggressive account, 0.5x for conservative)
"""

import json
import threading
from datetime import datetime
from collections import deque


class TradeCopier:
    """
    Mirrors trades from source to one or more target accounts.
    
    Usage:
        copier = TradeCopier()
        copier.add_target('paper', paper_executor, scale=1.0)
        copier.add_target('aggressive', live_executor, scale=2.0)
        copier.copy_trade({'symbol': 'NIFTY', 'side': 'BUY', 'qty': 25, 'price': 22500})
    """
    
    def __init__(self):
        self.targets = {}
        self.copy_log = deque(maxlen=500)
        self.stats = {'copied': 0, 'failed': 0, 'skipped': 0}
    
    def add_target(self, name, executor=None, scale=1.0, 
                   enabled=True, filters=None):
        """
        Register a copy target.
        
        Args:
            name: Target identifier
            executor: Object with place_order(symbol, side, qty) method
            scale: Quantity multiplier (2.0 = double size)
            filters: dict of {symbol_whitelist, symbol_blacklist, min_confidence}
        """
        self.targets[name] = {
            'executor': executor,
            'scale': scale,
            'enabled': enabled,
            'filters': filters or {},
            'stats': {'copied': 0, 'failed': 0}
        }
    
    def copy_trade(self, trade):
        """
        Copy a trade to all enabled targets.
        
        Args:
            trade: {symbol, side, qty, price, confidence, ...}
        """
        results = {}
        
        for name, target in self.targets.items():
            if not target['enabled']:
                self.stats['skipped'] += 1
                continue
            
            # Apply filters
            if not self._passes_filter(trade, target['filters']):
                self.stats['skipped'] += 1
                continue
            
            # Scale quantity
            scaled_qty = max(1, int(trade.get('qty', 1) * target['scale']))
            
            try:
                if target['executor']:
                    result = target['executor'].place_order(
                        trade['symbol'], trade['side'], scaled_qty
                    )
                else:
                    result = {'status': 'SIMULATED', 'qty': scaled_qty}
                
                target['stats']['copied'] += 1
                self.stats['copied'] += 1
                results[name] = {'status': 'OK', 'qty': scaled_qty}
                
            except Exception as e:
                target['stats']['failed'] += 1
                self.stats['failed'] += 1
                results[name] = {'status': 'FAILED', 'error': str(e)}
        
        self.copy_log.append({
            'trade': trade, 'results': results,
            'time': datetime.now().isoformat()
        })
        
        return results
    
    def enable_target(self, name):
        if name in self.targets:
            self.targets[name]['enabled'] = True
    
    def disable_target(self, name):
        if name in self.targets:
            self.targets[name]['enabled'] = False
    
    def get_stats(self):
        return {
            'global': self.stats,
            'targets': {n: t['stats'] for n, t in self.targets.items()},
            'recent_copies': len(self.copy_log)
        }
    
    def _passes_filter(self, trade, filters):
        if not filters:
            return True
        
        symbol = trade.get('symbol', '')
        
        whitelist = filters.get('symbol_whitelist')
        if whitelist and symbol not in whitelist:
            return False
        
        blacklist = filters.get('symbol_blacklist', [])
        if symbol in blacklist:
            return False
        
        min_conf = filters.get('min_confidence', 0)
        if trade.get('confidence', 1.0) < min_conf:
            return False
        
        return True
