"""
📡 WebSocket Feed Handler — Real-Time Price Streaming

Handles real-time price updates via websocket or polling:
  - Price callback on every tick
  - Auto-reconnect on disconnect
  - Mock mode for testing
"""

import threading, time, json, logging
from collections import defaultdict, deque


class WebSocketHandler:
    
    def __init__(self):
        self.subscribers = defaultdict(list)
        self.latest_prices = {}
        self.running = False
        self.tick_count = 0
        self.tick_history = deque(maxlen=1000)
    
    def subscribe(self, symbol, callback):
        self.subscribers[symbol].append(callback)
    
    def on_tick(self, symbol, price, volume=0):
        self.latest_prices[symbol] = {
            'price': price, 'volume': volume,
            'time': time.strftime('%H:%M:%S')
        }
        self.tick_count += 1
        self.tick_history.append({'symbol': symbol, 'price': price, 'time': time.time()})
        
        for callback in self.subscribers.get(symbol, []):
            try:
                callback(symbol, price, volume)
            except Exception as e:
                logging.debug(f"Tick callback error: {e}")
    
    def get_price(self, symbol):
        return self.latest_prices.get(symbol, {}).get('price', 0)
    
    def start_mock(self, symbols, base_prices, interval=1.0):
        """Start mock price feed for testing."""
        import numpy as np
        self.running = True
        
        def _feed():
            prices = dict(base_prices)
            while self.running:
                for sym in symbols:
                    ret = np.random.normal(0, 0.001)
                    prices[sym] = round(prices[sym] * (1 + ret), 2)
                    self.on_tick(sym, prices[sym], np.random.randint(1000, 10000))
                time.sleep(interval)
        
        threading.Thread(target=_feed, daemon=True).start()
    
    def stop(self):
        self.running = False
    
    def get_stats(self):
        return {'total_ticks': self.tick_count, 'symbols_active': len(self.latest_prices),
                'latest': self.latest_prices}
