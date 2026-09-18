"""
📱 Push Notifications — Mobile Alerts via ntfy.sh (Free)

Send mobile push notifications for trade alerts:
  Free, no app store submission needed
  Install ntfy app → subscribe to your topic → get alerts!
"""

import threading
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


class PushNotifications:
    
    BASE_URL = 'https://ntfy.sh'
    
    def __init__(self, topic='tradekaro_ai'):
        self.topic = topic
        self.enabled = HAS_REQUESTS
        self.sent_count = 0
    
    def send(self, message, title='TradeKaro AI', priority='default', tags='chart'):
        if not self.enabled: return
        try:
            threading.Thread(target=lambda: requests.post(
                f'{self.BASE_URL}/{self.topic}',
                data=message.encode('utf-8'),
                headers={'Title': title, 'Priority': priority, 'Tags': tags},
                timeout=5
            ), daemon=True).start()
            self.sent_count += 1
        except: pass
    
    def trade_alert(self, symbol, side, price, confidence):
        emoji = '🟢' if side == 'BUY' else '🔴'
        self.send(
            f'{emoji} {side} {symbol} @ ₹{price}\nConfidence: {confidence:.0%}',
            title=f'{side} Signal — {symbol}', priority='high', tags='moneybag'
        )
    
    def pnl_alert(self, pnl, trade_count):
        emoji = '💰' if pnl > 0 else '📉'
        self.send(f'{emoji} Day P&L: ₹{pnl:,.0f}\nTrades: {trade_count}',
                 title='Daily P&L Update', tags='chart_with_upwards_trend')
    
    def risk_alert(self, message):
        self.send(f'⚠️ {message}', title='Risk Alert', priority='urgent', tags='warning')
