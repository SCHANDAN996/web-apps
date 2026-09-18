"""
📊 Economic Indicators — GDP, CPI, PMI, IIP Tracking

Macro data for context-aware trading:
  If GDP growing + low inflation + rising PMI → BULLISH environment
"""

from datetime import datetime
from collections import deque


class EconomicIndicators:
    
    INDICATORS = {
        'GDP': {'weight': 0.3, 'bullish_above': 5.0},
        'CPI': {'weight': 0.2, 'bullish_below': 5.0},
        'PMI': {'weight': 0.2, 'bullish_above': 50.0},
        'IIP': {'weight': 0.15, 'bullish_above': 3.0},
        'REPO_RATE': {'weight': 0.15, 'bullish_below': 7.0},
    }
    
    def __init__(self):
        self.data = {}
        self.history = deque(maxlen=100)
    
    def update(self, indicator, value, period=''):
        self.data[indicator] = {
            'value': value, 'period': period,
            'updated': datetime.now().isoformat()
        }
        self.history.append({'indicator': indicator, 'value': value, 'time': datetime.now().isoformat()})
    
    def macro_score(self):
        if not self.data: return {'score': 50, 'environment': 'UNKNOWN'}
        score = 50
        for ind, config in self.INDICATORS.items():
            if ind in self.data:
                val = self.data[ind]['value']
                weight = config['weight'] * 100
                if 'bullish_above' in config:
                    score += weight if val > config['bullish_above'] else -weight
                elif 'bullish_below' in config:
                    score += weight if val < config['bullish_below'] else -weight
        
        score = max(0, min(100, score))
        env = 'FAVORABLE' if score > 60 else 'UNFAVORABLE' if score < 40 else 'NEUTRAL'
        return {
            'score': round(score, 1), 'environment': env,
            'data': {k: v['value'] for k, v in self.data.items()},
            'impact': 'INCREASE RISK' if env == 'FAVORABLE' else 'REDUCE RISK' if env == 'UNFAVORABLE' else 'NORMAL'
        }
