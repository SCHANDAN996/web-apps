"""
📊 Confidence Calibrator — Make AI Predictions Reliable

Problem: Model says 0.7 but actual win rate is 55%
Solution: Platt scaling to calibrate raw scores to actual probabilities
"""

import numpy as np
import math


class ConfidenceCalibrator:
    
    def __init__(self):
        self.predictions = []
        self.actuals = []
        self.a = 1.0  # Platt parameters
        self.b = 0.0
        self.calibrated = False
    
    def add_sample(self, predicted, actual):
        self.predictions.append(predicted)
        self.actuals.append(1 if actual else 0)
    
    def calibrate(self):
        if len(self.predictions) < 50:
            return {'status': 'NEED_MORE_DATA', 'samples': len(self.predictions)}
        
        preds = np.array(self.predictions)
        acts = np.array(self.actuals)
        
        # Simple Platt scaling via logistic regression
        best_a, best_b, best_loss = 1.0, 0.0, float('inf')
        for a in np.linspace(0.5, 3.0, 20):
            for b in np.linspace(-1.0, 1.0, 20):
                calibrated = 1 / (1 + np.exp(-(a * preds + b)))
                loss = -np.mean(acts * np.log(calibrated + 1e-8) + (1-acts) * np.log(1-calibrated + 1e-8))
                if loss < best_loss:
                    best_loss = loss
                    best_a, best_b = a, b
        
        self.a, self.b = best_a, best_b
        self.calibrated = True
        
        return {'a': round(best_a, 3), 'b': round(best_b, 3), 'status': 'CALIBRATED'}
    
    def transform(self, raw_score):
        if not self.calibrated:
            return raw_score
        return round(1 / (1 + math.exp(-(self.a * raw_score + self.b))), 4)
    
    def reliability_diagram(self, bins=10):
        if len(self.predictions) < bins * 5:
            return {}
        preds = np.array(self.predictions)
        acts = np.array(self.actuals)
        bin_edges = np.linspace(0, 1, bins + 1)
        diagram = {}
        for i in range(bins):
            mask = (preds >= bin_edges[i]) & (preds < bin_edges[i+1])
            if mask.sum() > 0:
                label = f'{bin_edges[i]:.1f}-{bin_edges[i+1]:.1f}'
                diagram[label] = {
                    'predicted': round(float(preds[mask].mean()), 3),
                    'actual': round(float(acts[mask].mean()), 3),
                    'count': int(mask.sum())
                }
        return diagram
