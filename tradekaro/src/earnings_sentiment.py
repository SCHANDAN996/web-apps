"""
📜 Earnings Sentiment — Transcript Sentiment Analysis

Analyze earnings call transcripts and results announcements:
  Positive words: beat, growth, record, strong, exceeded
  Negative words: missed, decline, challenge, weak, lower
"""

import re
from collections import Counter


class EarningsSentiment:
    
    POSITIVE = ['beat', 'growth', 'record', 'strong', 'exceeded', 'robust', 'profit',
                'improvement', 'healthy', 'outperform', 'guidance raised', 'margin expansion',
                'revenue growth', 'order book', 'momentum', 'upbeat', 'encouraged']
    NEGATIVE = ['missed', 'decline', 'challenge', 'weak', 'lower', 'pressure', 'loss',
                'downgrade', 'slowdown', 'margin compression', 'cautious', 'headwind',
                'uncertainty', 'deterioration', 'disappointing']
    
    def analyze_text(self, text):
        text_lower = text.lower()
        words = re.findall(r'\w+', text_lower)
        
        pos_count = sum(1 for kw in self.POSITIVE if kw in text_lower)
        neg_count = sum(1 for kw in self.NEGATIVE if kw in text_lower)
        
        total = pos_count + neg_count
        if total == 0: return {'sentiment': 'NEUTRAL', 'score': 0, 'confidence': 'LOW'}
        
        score = (pos_count - neg_count) / total
        
        return {
            'sentiment': 'POSITIVE' if score > 0.2 else 'NEGATIVE' if score < -0.2 else 'NEUTRAL',
            'score': round(score, 3),
            'positive_hits': pos_count, 'negative_hits': neg_count,
            'key_positives': [kw for kw in self.POSITIVE if kw in text_lower],
            'key_negatives': [kw for kw in self.NEGATIVE if kw in text_lower],
            'trading_signal': 'BUY' if score > 0.3 else 'SELL' if score < -0.3 else 'HOLD'
        }
    
    def compare_quarters(self, text_q1, text_q2):
        s1 = self.analyze_text(text_q1)
        s2 = self.analyze_text(text_q2)
        change = s2['score'] - s1['score']
        return {
            'q1': s1['score'], 'q2': s2['score'],
            'change': round(change, 3),
            'trend': 'IMPROVING' if change > 0.1 else 'WORSENING' if change < -0.1 else 'STABLE'
        }
