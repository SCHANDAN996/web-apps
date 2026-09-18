"""
🤖 RL Position Sizer — Reinforcement Learning for Dynamic Sizing

Q-Learning agent that learns optimal position sizes:
  State: (win_streak, drawdown_level, volatility_level, confidence_bucket)
  Action: (0.25x, 0.5x, 1x, 1.5x, 2x)
  Reward: risk-adjusted P&L
"""

import numpy as np
import json, os
from collections import defaultdict


class RLPositionSizer:
    
    ACTIONS = [0.25, 0.5, 1.0, 1.5, 2.0]  # Position size multipliers
    Q_FILE = 'models/rl_position_sizer_q.json'
    
    def __init__(self, alpha=0.1, gamma=0.95, epsilon=0.1):
        self.alpha = alpha    # Learning rate
        self.gamma = gamma    # Discount factor
        self.epsilon = epsilon # Exploration rate
        self.q_table = defaultdict(lambda: [0.0] * len(self.ACTIONS))
        self._load()
    
    def get_state(self, win_streak, drawdown_pct, volatility, confidence):
        ws = min(win_streak, 5)
        dd = 0 if drawdown_pct < 2 else 1 if drawdown_pct < 5 else 2
        vol = 0 if volatility < 15 else 1 if volatility < 25 else 2
        conf = 0 if confidence < 0.55 else 1 if confidence < 0.7 else 2
        return f"{ws}_{dd}_{vol}_{conf}"
    
    def select_action(self, state):
        if np.random.random() < self.epsilon:
            return np.random.choice(len(self.ACTIONS))
        return int(np.argmax(self.q_table[state]))
    
    def get_multiplier(self, win_streak=0, drawdown_pct=0, volatility=15, confidence=0.6):
        state = self.get_state(win_streak, drawdown_pct, volatility, confidence)
        action_idx = self.select_action(state)
        return {
            'multiplier': self.ACTIONS[action_idx],
            'state': state, 'action': action_idx,
            'method': 'RL_Q_LEARNING'
        }
    
    def update(self, state, action_idx, reward, next_state):
        old_q = self.q_table[state][action_idx]
        max_next = max(self.q_table[next_state])
        new_q = old_q + self.alpha * (reward + self.gamma * max_next - old_q)
        self.q_table[state][action_idx] = new_q
    
    def train_from_trades(self, trades):
        for i in range(len(trades) - 1):
            t = trades[i]
            nt = trades[i + 1]
            state = self.get_state(t.get('streak', 0), t.get('drawdown', 0),
                                  t.get('vol', 15), t.get('confidence', 0.6))
            next_state = self.get_state(nt.get('streak', 0), nt.get('drawdown', 0),
                                       nt.get('vol', 15), nt.get('confidence', 0.6))
            reward = t.get('pnl', 0) / max(abs(t.get('pnl', 1)), 1)
            action = min(range(len(self.ACTIONS)), key=lambda a: abs(self.ACTIONS[a] - t.get('multiplier', 1)))
            self.update(state, action, reward, next_state)
        self._save()
    
    def _load(self):
        if os.path.exists(self.Q_FILE):
            try:
                with open(self.Q_FILE) as f:
                    data = json.load(f)
                    for k, v in data.items(): self.q_table[k] = v
            except: pass
    
    def _save(self):
        os.makedirs(os.path.dirname(self.Q_FILE) or 'models', exist_ok=True)
        with open(self.Q_FILE, 'w') as f: json.dump(dict(self.q_table), f, indent=2)
