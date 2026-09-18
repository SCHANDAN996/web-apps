"""
🧬 Meta-Learner Signal Aggregator — Unified Signal From ALL Modules

The BRAIN of the AI system. Takes signals from ALL 50+ modules:
  - Brain V2 prediction
  - Ensemble voting
  - Candle patterns
  - Order flow
  - Regime detection
  - Sentiment
  - Fibonacci levels
  - Market breadth
  ...and weights them into ONE final signal.

Uses confidence-weighted aggregation with dynamic weight adjustment.
"""

from datetime import datetime
from collections import defaultdict


class MetaLearnerAggregator:
    """
    Combines all AI module signals into one unified trading signal.
    
    Usage:
        meta = MetaLearnerAggregator()
        signal = meta.aggregate({
            'brain_v2': {'direction': 'BUY', 'confidence': 0.78},
            'ensemble': {'direction': 'BUY', 'confidence': 0.72},
            'candle_pattern': {'direction': 'BUY', 'confidence': 0.65},
            'order_flow': {'direction': 'SELL', 'confidence': 0.55},
            'regime': {'direction': 'BUY', 'confidence': 0.80},
        })
        # {'final_signal': 'BUY', 'confidence': 0.74, 'agreement': 0.80}
    """
    
    # Module weights (higher = more trusted)
    DEFAULT_WEIGHTS = {
        'brain_v2':         1.0,    # Core brain
        'ensemble':         0.9,    # Multi-model voting
        'regime':           0.85,   # Market regime
        'order_flow':       0.80,   # Buy/sell pressure
        'multi_timeframe':  0.75,   # Multi-TF voting
        'candle_pattern':   0.70,   # Candlestick patterns
        'fibonacci':        0.65,   # S/R levels
        'sentiment':        0.60,   # News sentiment
        'social':           0.50,   # Social media buzz
        'market_breadth':   0.55,   # Internal breadth
        'anomaly':          0.70,   # Anomaly alerts
        'correlation':      0.50,   # Cross-asset
        'microstructure':   0.60,   # Tick patterns
        'session':          0.45,   # Intraday session
        'watchlist':        0.40,   # Scanner score
    }
    
    def __init__(self):
        self.weights = self.DEFAULT_WEIGHTS.copy()
        self.history = []
        self.accuracy_tracker = defaultdict(lambda: {'correct': 0, 'total': 0})
    
    def aggregate(self, signals, min_confidence=0.55):
        """
        Aggregate all module signals into one.
        
        Args:
            signals: dict {module_name: {direction, confidence}}
            min_confidence: minimum to act
        """
        if not signals:
            return {'final_signal': 'HOLD', 'confidence': 0.5, 'agreement': 0}
        
        # Weighted voting
        buy_score = 0
        sell_score = 0
        total_weight = 0
        module_votes = {}
        
        for module, sig in signals.items():
            direction = sig.get('direction', 'HOLD')
            conf = sig.get('confidence', 0.5)
            weight = self.weights.get(module, 0.5)
            
            weighted_conf = conf * weight
            
            if direction in ['BUY', 'BULLISH', 'LONG']:
                buy_score += weighted_conf
                module_votes[module] = 'BUY'
            elif direction in ['SELL', 'BEARISH', 'SHORT']:
                sell_score += weighted_conf
                module_votes[module] = 'SELL'
            else:
                module_votes[module] = 'HOLD'
            
            total_weight += weight
        
        # Normalize
        if total_weight > 0:
            buy_score /= total_weight
            sell_score /= total_weight
        
        # Final signal
        net_score = buy_score - sell_score
        
        if net_score > 0.1 and buy_score > min_confidence:
            final = 'BUY'
            confidence = buy_score
        elif net_score < -0.1 and sell_score > min_confidence:
            final = 'SELL'
            confidence = sell_score
        else:
            final = 'HOLD'
            confidence = 0.5
        
        # Agreement ratio
        most_common = max(set(module_votes.values()), key=list(module_votes.values()).count)
        agreement = sum(1 for v in module_votes.values() if v == most_common) / len(module_votes)
        
        result = {
            'final_signal': final,
            'confidence': round(confidence, 4),
            'agreement': round(agreement, 2),
            'buy_score': round(buy_score, 4),
            'sell_score': round(sell_score, 4),
            'modules_agree': sum(1 for v in module_votes.values() if v == final),
            'total_modules': len(signals),
            'votes': module_votes,
            'timestamp': datetime.now().isoformat()
        }
        
        self.history.append(result)
        return result
    
    def update_module_weight(self, module, was_correct):
        """Dynamically adjust module weight based on accuracy."""
        self.accuracy_tracker[module]['total'] += 1
        if was_correct:
            self.accuracy_tracker[module]['correct'] += 1
        
        stats = self.accuracy_tracker[module]
        if stats['total'] >= 10:
            accuracy = stats['correct'] / stats['total']
            # Adjust weight: better accuracy → higher weight
            self.weights[module] = max(0.1, min(1.0, accuracy * 1.2))
    
    def get_module_rankings(self):
        """Rank modules by accuracy."""
        rankings = []
        for module, stats in self.accuracy_tracker.items():
            if stats['total'] > 0:
                acc = stats['correct'] / stats['total'] * 100
                rankings.append({
                    'module': module, 'accuracy': round(acc, 1),
                    'trades': stats['total'], 'weight': self.weights.get(module, 0.5)
                })
        return sorted(rankings, key=lambda x: x['accuracy'], reverse=True)
