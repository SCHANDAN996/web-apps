"""
📈 Performance Tracker — Live Trade Monitoring

Tracks every AI prediction vs actual outcome to:
- Measure real accuracy over time
- Detect model degradation early
- Calculate live Sharpe/drawdown
- Alert when performance drops below threshold
"""

import json
import os
import numpy as np
from datetime import datetime
from collections import deque


class PerformanceTracker:
    """
    Monitors AI trading performance in real-time.
    
    Tracks:
    - Prediction accuracy (predicted vs actual direction)
    - Win rate, P&L, expectancy
    - Rolling Sharpe ratio
    - Drawdown
    - Model degradation detection
    """

    DATA_FILE = 'logs/performance_history.json'
    ALERT_THRESHOLD_ACCURACY = 0.45  # Alert if accuracy drops below 45%
    ALERT_THRESHOLD_DRAWDOWN = 0.15  # Alert if drawdown exceeds 15%

    def __init__(self, window=200):
        self.window = window
        self.predictions = deque(maxlen=window)  # (confidence, predicted, actual, pnl)
        self.equity = deque(maxlen=5000)
        self.peak_equity = 0
        self.alerts = []
        self._load()

    def record_prediction(self, confidence, predicted_action, actual_outcome, pnl=0):
        """
        Record a single prediction.

        Args:
            confidence: Brain's confidence (0-1)
            predicted_action: 'BUY' or 'SELL'
            actual_outcome: 'PROFIT' or 'LOSS'
            pnl: Actual P&L of the trade
        """
        correct = 1 if actual_outcome == 'PROFIT' else 0
        self.predictions.append({
            'timestamp': datetime.now().isoformat(),
            'confidence': confidence,
            'predicted': predicted_action,
            'correct': correct,
            'pnl': pnl
        })

        # Update equity
        current = self.equity[-1] if self.equity else 100000
        current += pnl
        self.equity.append(current)
        self.peak_equity = max(self.peak_equity, current)

        # Check for alerts
        self._check_alerts()
        self._save()

    def get_metrics(self):
        """Get current performance metrics."""
        if not self.predictions:
            return {'status': 'No data'}

        preds = list(self.predictions)
        correct = sum(p['correct'] for p in preds)
        pnls = [p['pnl'] for p in preds]

        accuracy = correct / len(preds)
        wins = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p <= 0]

        # Drawdown
        drawdown = 0
        if self.equity and self.peak_equity > 0:
            drawdown = (self.peak_equity - self.equity[-1]) / self.peak_equity

        # Rolling Sharpe
        if len(pnls) > 10:
            returns = np.array(pnls) / (self.equity[-1] + 1e-9)
            sharpe = np.mean(returns) / (np.std(returns) + 1e-9) * np.sqrt(252)
        else:
            sharpe = 0

        # Confidence calibration
        high_conf = [p for p in preds if p['confidence'] > 0.7]
        high_conf_acc = sum(p['correct'] for p in high_conf) / len(high_conf) if high_conf else 0

        return {
            'total_predictions': len(preds),
            'accuracy': round(accuracy * 100, 1),
            'win_rate': round(len(wins) / len(pnls) * 100, 1) if pnls else 0,
            'total_pnl': round(sum(pnls), 2),
            'avg_win': round(np.mean(wins), 2) if wins else 0,
            'avg_loss': round(abs(np.mean(losses)), 2) if losses else 0,
            'profit_factor': round(sum(wins) / (abs(sum(losses)) + 1e-9), 2),
            'max_drawdown': round(drawdown * 100, 2),
            'sharpe_ratio': round(sharpe, 3),
            'high_conf_accuracy': round(high_conf_acc * 100, 1),
            'current_equity': round(self.equity[-1], 2) if self.equity else 100000
        }

    def is_degraded(self):
        """Check if model performance has degraded significantly."""
        if len(self.predictions) < 30:
            return False, "Too few predictions"

        recent = list(self.predictions)[-30:]
        accuracy = sum(p['correct'] for p in recent) / len(recent)

        if accuracy < self.ALERT_THRESHOLD_ACCURACY:
            return True, f"Accuracy dropped to {accuracy:.1%} (threshold: {self.ALERT_THRESHOLD_ACCURACY:.0%})"

        drawdown = 0
        if self.equity and self.peak_equity > 0:
            drawdown = (self.peak_equity - self.equity[-1]) / self.peak_equity
        if drawdown > self.ALERT_THRESHOLD_DRAWDOWN:
            return True, f"Drawdown at {drawdown:.1%} (threshold: {self.ALERT_THRESHOLD_DRAWDOWN:.0%})"

        return False, "Performance OK"

    def _check_alerts(self):
        degraded, reason = self.is_degraded()
        if degraded:
            alert = {'timestamp': datetime.now().isoformat(), 'reason': reason}
            self.alerts.append(alert)
            print(f"[ALERT] 🚨 Performance Degradation: {reason}")

    def _save(self):
        try:
            os.makedirs(os.path.dirname(self.DATA_FILE) or 'logs', exist_ok=True)
            data = {
                'predictions': list(self.predictions),
                'equity': list(self.equity)[-500:],
                'peak_equity': self.peak_equity,
                'alerts': self.alerts[-20:]
            }
            with open(self.DATA_FILE, 'w') as f:
                json.dump(data, f)
        except Exception:
            pass

    def _load(self):
        try:
            if os.path.exists(self.DATA_FILE):
                with open(self.DATA_FILE, 'r') as f:
                    data = json.load(f)
                for p in data.get('predictions', [])[-self.window:]:
                    self.predictions.append(p)
                for e in data.get('equity', []):
                    self.equity.append(e)
                self.peak_equity = data.get('peak_equity', 0)
                self.alerts = data.get('alerts', [])
        except Exception:
            pass
