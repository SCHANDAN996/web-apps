"""
🕵️ Insider Detector — Bulk/Block Deal Tracking

Tracks institutional activity:
  Bulk deals (>0.5% market cap)
  Block deals (min ₹10 crore, off-market)
  Promoter buying/selling
"""

from collections import deque
from datetime import datetime


class InsiderDetector:
    
    def __init__(self):
        self.deals = deque(maxlen=500)
    
    def add_deal(self, symbol, deal_type, buyer_seller, qty, price, value_cr):
        self.deals.append({
            'symbol': symbol, 'type': deal_type,
            'party': buyer_seller, 'qty': qty, 'price': price,
            'value_cr': value_cr, 'date': datetime.now().strftime('%Y-%m-%d'),
            'signal': 'BULLISH' if 'BUY' in deal_type.upper() or 'PROMOTER' in buyer_seller.upper() else 'WATCH'
        })
    
    def get_recent(self, symbol=None, days=7):
        result = list(self.deals)
        if symbol:
            result = [d for d in result if d['symbol'] == symbol]
        return result[-20:]
    
    def detect_accumulation(self, symbol):
        deals = [d for d in self.deals if d['symbol'] == symbol]
        if len(deals) < 2: return {'detected': False}
        buys = sum(d['value_cr'] for d in deals if 'BUY' in d.get('type','').upper())
        sells = sum(d['value_cr'] for d in deals if 'SELL' in d.get('type','').upper())
        if buys > sells * 2:
            return {'detected': True, 'signal': 'INSTITUTIONAL_ACCUMULATION',
                    'buy_value': buys, 'sell_value': sells}
        return {'detected': False}
