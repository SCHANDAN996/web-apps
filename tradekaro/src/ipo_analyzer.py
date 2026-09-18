"""
📊 IPO Analyzer — New Listing Analysis

Track IPO listings, grey market premium, and listing day performance
"""

from datetime import datetime
from collections import deque


class IPOAnalyzer:
    
    def __init__(self):
        self.ipos = deque(maxlen=200)
    
    def add_ipo(self, name, issue_price, listing_price=None, gmp=None, sector=''):
        entry = {
            'name': name, 'issue_price': issue_price,
            'listing_price': listing_price, 'gmp': gmp,
            'sector': sector, 'date': datetime.now().strftime('%Y-%m-%d')
        }
        if listing_price and issue_price:
            entry['listing_return'] = round((listing_price - issue_price) / issue_price * 100, 2)
            entry['result'] = 'PROFIT' if listing_price > issue_price else 'LOSS'
        self.ipos.append(entry)
        return entry
    
    def listing_prediction(self, gmp, issue_price):
        expected_listing = issue_price + gmp
        expected_return = gmp / issue_price * 100
        confidence = 'HIGH' if abs(expected_return) > 20 else 'MEDIUM' if abs(expected_return) > 5 else 'LOW'
        return {
            'expected_listing': round(expected_listing, 2),
            'expected_return': round(expected_return, 2),
            'confidence': confidence,
            'action': 'APPLY' if expected_return > 10 else 'AVOID' if expected_return < 0 else 'RISKY'
        }
    
    def historical_stats(self):
        if not self.ipos: return {}
        listed = [i for i in self.ipos if i.get('listing_return') is not None]
        if not listed: return {'total_tracked': len(self.ipos)}
        profits = [i for i in listed if i.get('result') == 'PROFIT']
        return {
            'total_tracked': len(self.ipos), 'listed': len(listed),
            'profit_pct': round(len(profits) / len(listed) * 100, 1),
            'avg_listing_return': round(sum(i['listing_return'] for i in listed) / len(listed), 2)
        }
