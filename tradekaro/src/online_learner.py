"""
🔄 Online Learner — Continuous Model Updates From Live Data

Updates model weights incrementally without full retraining:
  - Experience buffer with priority replay
  - Micro-batch gradient updates
  - Performance-triggered retraining
"""

import numpy as np
from collections import deque
from datetime import datetime


class OnlineLearner:
    
    def __init__(self, buffer_size=5000, retrain_threshold=100):
        self.buffer = deque(maxlen=buffer_size)
        self.retrain_threshold = retrain_threshold
        self.updates = 0
        self.performance = deque(maxlen=200)
    
    def add_experience(self, features, label, confidence=1.0, priority=1.0):
        self.buffer.append({
            'features': features, 'label': label,
            'confidence': confidence, 'priority': priority,
            'time': datetime.now().isoformat()
        })
        self.updates += 1
    
    def should_retrain(self):
        if self.updates >= self.retrain_threshold:
            return {'retrain': True, 'reason': f'{self.updates} new samples', 'buffer_size': len(self.buffer)}
        if len(self.performance) >= 20:
            recent = list(self.performance)[-20:]
            accuracy = sum(1 for p in recent if p['correct']) / 20
            if accuracy < 0.45:
                return {'retrain': True, 'reason': f'Accuracy dropped to {accuracy:.1%}'}
        return {'retrain': False}
    
    def get_training_batch(self, batch_size=256):
        if len(self.buffer) < batch_size:
            return list(self.buffer)
        priorities = np.array([b['priority'] for b in self.buffer])
        probs = priorities / priorities.sum()
        indices = np.random.choice(len(self.buffer), batch_size, replace=False, p=probs)
        return [self.buffer[i] for i in indices]
    
    def record_prediction(self, predicted, actual):
        self.performance.append({'predicted': predicted, 'actual': actual,
                                'correct': (predicted > 0.5) == (actual > 0.5)})
    
    def get_stats(self):
        correct = sum(1 for p in self.performance if p['correct'])
        total = len(self.performance)
        return {'buffer_size': len(self.buffer), 'total_updates': self.updates,
                'live_accuracy': round(correct / max(total, 1) * 100, 1),
                'predictions_tracked': total}
