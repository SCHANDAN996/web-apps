"""
👥 Multi-Account Manager — Manage Multiple Trading Accounts

Tracks P&L, positions, and config across accounts:
  Main account, paper account, aggressive account, conservative account
"""

from datetime import datetime
from collections import defaultdict


class MultiAccountManager:
    
    def __init__(self):
        self.accounts = {}
    
    def add_account(self, name, capital, risk_profile='MODERATE', active=True):
        self.accounts[name] = {
            'capital': capital, 'current_value': capital,
            'risk_profile': risk_profile, 'active': active,
            'positions': {}, 'trades': [], 'created': datetime.now().isoformat()
        }
    
    def get_account(self, name):
        return self.accounts.get(name)
    
    def record_trade(self, account_name, trade):
        if account_name not in self.accounts: return
        acc = self.accounts[account_name]
        acc['trades'].append({**trade, 'time': datetime.now().isoformat()})
        acc['current_value'] += trade.get('pnl', 0)
    
    def portfolio_summary(self):
        summary = {}
        total_capital = 0
        total_pnl = 0
        for name, acc in self.accounts.items():
            pnl = acc['current_value'] - acc['capital']
            total_capital += acc['capital']
            total_pnl += pnl
            summary[name] = {
                'capital': acc['capital'], 'current': round(acc['current_value'], 0),
                'pnl': round(pnl, 0), 'return_pct': round(pnl / acc['capital'] * 100, 2),
                'trades': len(acc['trades']), 'active': acc['active']
            }
        summary['_total'] = {'capital': total_capital, 'pnl': round(total_pnl, 0),
                            'return_pct': round(total_pnl / max(total_capital, 1) * 100, 2)}
        return summary
    
    def get_risk_allocation(self):
        profiles = defaultdict(float)
        for acc in self.accounts.values():
            profiles[acc['risk_profile']] += acc['current_value']
        return dict(profiles)
