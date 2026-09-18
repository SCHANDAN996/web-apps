"""
🧠 Experience Replay Buffer — Memory-Based Learning

Stores all trading decisions with full context.
Enables the AI to learn MORE from mistakes and
replay difficult market scenarios during retraining.

Inspired by DeepMind's DQN experience replay (Mnih et al. 2015)
"""

import json
import os
import numpy as np
from datetime import datetime
from collections import deque
import random


class ExperienceReplayBuffer:
    """
    Stores trading experiences for later replay during training.

    Each experience = {
        features: (60, N) array snapshot,
        prediction: float (0-1),
        actual_outcome: 0 or 1,
        pnl: float,
        regime: str,
        difficulty: float (0-1, how hard was this to predict?)
    }

    Priority Replay:
    - Harder experiences (wrong predictions) get replayed more often
    - Extreme market moves get higher priority
    - Regime transitions get highest priority
    """

    BUFFER_FILE = 'models/experience_buffer.json'

    def __init__(self, max_size=10000, priority_alpha=0.6):
        self.max_size = max_size
        self.priority_alpha = priority_alpha
        self.buffer = deque(maxlen=max_size)
        self.priorities = deque(maxlen=max_size)
        self._load()

    def store(self, features, prediction, actual, pnl=0, regime="UNKNOWN"):
        """
        Store a new experience.

        Args:
            features: np.ndarray of shape (lookback, num_features)
            prediction: Model's prediction (0-1 probability)
            actual: Actual outcome (1=profitable, 0=not)
            pnl: Realized P&L
            regime: Market regime at time of trade
        """
        # Calculate difficulty (how wrong was the prediction?)
        error = abs(prediction - actual)
        difficulty = error

        # Boost priority for regime transitions and extreme moves
        if regime == "TRANSITION":
            difficulty *= 1.5
        if abs(pnl) > 500:  # Large move
            difficulty *= 1.3

        experience = {
            'features': features.tolist() if isinstance(features, np.ndarray) else features,
            'prediction': float(prediction),
            'actual': int(actual),
            'pnl': float(pnl),
            'regime': regime,
            'difficulty': float(difficulty),
            'timestamp': datetime.now().isoformat()
        }

        self.buffer.append(experience)
        self.priorities.append(difficulty ** self.priority_alpha)

    def sample(self, batch_size=64):
        """
        Sample a batch of experiences with priority weighting.
        Harder experiences are sampled more frequently.

        Returns:
            X: np.ndarray (batch, lookback, features)
            y: np.ndarray (batch,)
        """
        if len(self.buffer) < batch_size:
            batch_size = len(self.buffer)

        if batch_size == 0:
            return np.array([]), np.array([])

        # Priority-weighted sampling
        probs = np.array(list(self.priorities))
        probs = probs / probs.sum()

        indices = np.random.choice(len(self.buffer), size=batch_size,
                                   replace=False, p=probs)

        X_list = []
        y_list = []

        buffer_list = list(self.buffer)
        for idx in indices:
            exp = buffer_list[idx]
            X_list.append(np.array(exp['features']))
            y_list.append(exp['actual'])

        return np.array(X_list), np.array(y_list)

    def get_stats(self):
        """Get buffer statistics."""
        if not self.buffer:
            return {'size': 0}

        experiences = list(self.buffer)
        return {
            'size': len(self.buffer),
            'max_size': self.max_size,
            'avg_difficulty': round(np.mean([e['difficulty'] for e in experiences]), 3),
            'regime_breakdown': self._regime_counts(),
            'accuracy_in_buffer': round(
                np.mean([e['actual'] == (1 if e['prediction'] > 0.5 else 0)
                         for e in experiences]) * 100, 1
            )
        }

    def _regime_counts(self):
        from collections import Counter
        return dict(Counter(e['regime'] for e in self.buffer).most_common())

    def get_hardest(self, n=10):
        """Get the N hardest experiences (for focused retraining)."""
        sorted_exp = sorted(self.buffer, key=lambda x: x['difficulty'], reverse=True)
        return sorted_exp[:n]

    def _save(self):
        """Save buffer to disk (only metadata, not full features for size)."""
        try:
            os.makedirs(os.path.dirname(self.BUFFER_FILE) or 'models', exist_ok=True)
            # Save last 1000 experiences (with features) + metadata
            save_data = {
                'experiences': list(self.buffer)[-1000:],
                'total_stored': len(self.buffer)
            }
            with open(self.BUFFER_FILE, 'w') as f:
                json.dump(save_data, f)
        except Exception as e:
            print(f"[ExperienceReplay] Save error: {e}")

    def _load(self):
        try:
            if os.path.exists(self.BUFFER_FILE):
                with open(self.BUFFER_FILE, 'r') as f:
                    data = json.load(f)
                for exp in data.get('experiences', []):
                    self.buffer.append(exp)
                    self.priorities.append(
                        exp.get('difficulty', 0.5) ** self.priority_alpha
                    )
        except Exception:
            pass

    def clear(self):
        """Clear the buffer."""
        self.buffer.clear()
        self.priorities.clear()
        if os.path.exists(self.BUFFER_FILE):
            os.remove(self.BUFFER_FILE)
