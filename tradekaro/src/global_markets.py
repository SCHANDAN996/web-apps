"""
🌍 Global Markets Tracker — US/Asia/Europe Correlation

Track global markets for overnight impact on Indian markets:
  SGX NIFTY, DOW, NASDAQ, US VIX, Dollar Index
"""

from collections import deque
from datetime import datetime


class GlobalMarketsTracker:
    
    INDICES = {
        'SGX_NIFTY': {'weight': 0.9, 'description': 'Best NIFTY predictor'},
        'DOW': {'weight': 0.6, 'description': 'US blue chips'},
        'NASDAQ': {'weight': 0.5, 'description': 'US tech'},
        'US_VIX': {'weight': 0.7, 'description': 'Fear gauge (inverse)'},
        'DXY': {'weight': 0.4, 'description': 'Dollar strength (inverse)'},
        'NIKKEI': {'weight': 0.3, 'description': 'Japan'},
        'HANG_SENG': {'weight': 0.4, 'description': 'Hong Kong/China'},
    }
    
    def __init__(self):
        self.data = {}
        self.history = deque(maxlen=100)
    
    def update(self, index, value, change_pct):
        self.data[index] = {
            'value': value, 'change_pct': change_pct,
            'last_updated': datetime.now().isoformat()
        }
    
    def predict_nifty_opening(self):
        if not self.data: return {'prediction': 'NO_DATA'}
        
        weighted_sum = 0
        total_weight = 0
        
        for idx, config in self.INDICES.items():
            if idx in self.data:
                change = self.data[idx]['change_pct']
                weight = config['weight']
                if idx in ['US_VIX', 'DXY']:
                    change = -change  # Inverse correlation
                weighted_sum += change * weight
                total_weight += weight
        
        predicted_gap = weighted_sum / max(total_weight, 0.01)
        
        return {
            'predicted_gap_pct': round(predicted_gap, 3),
            'direction': 'GAP_UP' if predicted_gap > 0.2 else 'GAP_DOWN' if predicted_gap < -0.2 else 'FLAT',
            'confidence': 'HIGH' if abs(predicted_gap) > 0.5 else 'MEDIUM',
            'contributors': {k: round(v['change_pct'], 2) for k, v in self.data.items()}
        }
    
    def get_risk_sentiment(self):
        vix = self.data.get('US_VIX', {}).get('change_pct', 0)
        if vix > 10: return 'EXTREME_FEAR'
        if vix > 5: return 'FEAR'
        if vix < -5: return 'GREED'
        return 'NEUTRAL'
