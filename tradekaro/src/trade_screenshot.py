"""
📸 Trade Screenshot — Capture System State at Trade Time

Auto-saves complete system state when a trade fires:
  Market data, indicators, signals, AI confidence — all frozen in time
"""

import json, os
from datetime import datetime


class TradeScreenshot:
    
    def __init__(self, dir='data/screenshots'):
        self.dir = dir
        os.makedirs(dir, exist_ok=True)
    
    def capture(self, trade, market_state=None, signals=None, ai_confidence=None):
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        symbol = trade.get('symbol', 'UNKNOWN')
        
        screenshot = {
            'timestamp': datetime.now().isoformat(),
            'trade': trade,
            'market_state': market_state or {},
            'signals': signals or {},
            'ai_confidence': ai_confidence,
        }
        
        filepath = os.path.join(self.dir, f'{symbol}_{ts}.json')
        with open(filepath, 'w') as f:
            json.dump(screenshot, f, indent=2, default=str)
        
        return filepath
    
    def get_screenshots(self, symbol=None, limit=20):
        files = sorted(os.listdir(self.dir), reverse=True)
        if symbol:
            files = [f for f in files if f.startswith(symbol)]
        result = []
        for f in files[:limit]:
            try:
                with open(os.path.join(self.dir, f)) as fd:
                    result.append(json.load(fd))
            except: pass
        return result
    
    def review_trade(self, filepath):
        with open(filepath) as f:
            return json.load(f)
