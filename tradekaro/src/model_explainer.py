"""
🔍 AI Model Explainability — Feature Importance & Decision Transparency

Without SHAP library (too heavy), uses:
  1. Permutation Importance — shuffle one feature, measure accuracy drop
  2. Gradient-based Saliency — which inputs cause biggest output change
  3. Attention Weights — from TransformerLSTM (built-in)
  4. Feature Contribution Breakdown — per-prediction explanation

Makes the AI's decisions transparent and auditable.
"""

import numpy as np
import torch
from datetime import datetime


class ModelExplainer:
    """
    Explains AI model predictions without external libraries.
    
    Usage:
        explainer = ModelExplainer(brain)
        
        # Global feature importance
        importance = explainer.permutation_importance(X_test, y_test)
        
        # Single prediction explanation
        reasons = explainer.explain_prediction(single_input)
    """
    
    FEATURE_NAMES = [
        'close', 'SMA_20', 'EMA_50', 'MACD', 'MACD_Signal', 'MACD_Hist',
        'plus_di', 'minus_di', 'ADX', 'KC_Upper', 'KC_Lower', 'KC_Middle',
        'volume_shock', '15m_EMA_50', '15m_SMA_20', '15m_MACD', '15m_ADX',
        '1H_EMA_50', '1H_ADX', 'RSI_14', '15m_RSI_14', '1H_RSI_14'
    ]
    
    def __init__(self, brain):
        self.brain = brain
    
    def permutation_importance(self, X, y, n_repeats=5):
        """
        Permutation importance: shuffle each feature, measure accuracy drop.
        Bigger drop = more important feature.
        """
        baseline_acc = self._calculate_accuracy(X, y)
        importances = {}
        
        n_features = X.shape[2]
        
        for f in range(n_features):
            drops = []
            for _ in range(n_repeats):
                X_permuted = X.copy()
                np.random.shuffle(X_permuted[:, :, f])
                perm_acc = self._calculate_accuracy(X_permuted, y)
                drops.append(baseline_acc - perm_acc)
            
            fname = self.FEATURE_NAMES[f] if f < len(self.FEATURE_NAMES) else f'feature_{f}'
            importances[fname] = {
                'importance': round(np.mean(drops), 4),
                'std': round(np.std(drops), 4),
                'rank': 0  # Filled later
            }
        
        # Rank
        sorted_imp = sorted(importances.items(), key=lambda x: x[1]['importance'], reverse=True)
        for rank, (name, data) in enumerate(sorted_imp, 1):
            data['rank'] = rank
        
        return dict(sorted_imp)
    
    def explain_prediction(self, X_single):
        """
        Explain a single prediction by measuring each feature's contribution.
        Uses leave-one-out: zero each feature and measure score change.
        """
        if X_single.ndim == 2:
            X_single = X_single[np.newaxis, :, :]
        
        base_score = self.brain.predict(X_single)
        contributions = {}
        
        n_features = X_single.shape[2]
        
        for f in range(n_features):
            X_zeroed = X_single.copy()
            X_zeroed[:, :, f] = 0
            zeroed_score = self.brain.predict(X_zeroed)
            
            impact = base_score - zeroed_score
            fname = self.FEATURE_NAMES[f] if f < len(self.FEATURE_NAMES) else f'feature_{f}'
            contributions[fname] = round(impact, 4)
        
        # Sort by absolute impact
        sorted_contrib = sorted(contributions.items(), 
                               key=lambda x: abs(x[1]), reverse=True)
        
        # Top drivers
        top_bullish = [(n, v) for n, v in sorted_contrib if v > 0][:5]
        top_bearish = [(n, v) for n, v in sorted_contrib if v < 0][:5]
        
        return {
            'base_score': round(base_score, 4),
            'direction': 'BULLISH' if base_score > 0.55 else 'BEARISH' if base_score < 0.45 else 'NEUTRAL',
            'top_bullish_drivers': top_bullish,
            'top_bearish_drivers': top_bearish,
            'all_contributions': dict(sorted_contrib)
        }
    
    def attention_analysis(self, X_single):
        """
        Get attention weights from TransformerLSTM.
        Shows which timesteps the model focuses on.
        """
        attention = self.brain.get_attention_map(X_single)
        if attention is None:
            return None
        
        # Average across heads
        avg_attention = attention.mean(axis=0) if attention.ndim > 1 else attention
        
        # Find most important timesteps
        top_timesteps = np.argsort(avg_attention.flatten())[-5:][::-1]
        
        return {
            'attention_weights': avg_attention.tolist() if hasattr(avg_attention, 'tolist') else [],
            'most_important_timesteps': top_timesteps.tolist(),
            'focus_on_recent': float(avg_attention[-10:].sum() / max(avg_attention.sum(), 1e-6)),
            'description': f"Model focuses {avg_attention[-10:].sum()/max(avg_attention.sum(),1e-6):.0%} on last 10 candles"
        }
    
    def generate_report(self, X_single, feature_values=None):
        """Generate full explainability report for one prediction."""
        explanation = self.explain_prediction(X_single)
        attention = self.attention_analysis(X_single)
        
        lines = [
            f"🔍 *AI Decision Report*",
            f"Score: {explanation['base_score']:.4f} ({explanation['direction']})",
            "",
            "📊 *Top Bullish Drivers:*"
        ]
        
        for name, impact in explanation['top_bullish_drivers'][:3]:
            lines.append(f"  🟢 {name}: +{impact:.4f}")
        
        lines.append("\n📉 *Top Bearish Drivers:*")
        for name, impact in explanation['top_bearish_drivers'][:3]:
            lines.append(f"  🔴 {name}: {impact:.4f}")
        
        if attention:
            lines.append(f"\n⏰ *Attention:* {attention['description']}")
        
        return '\n'.join(lines)
    
    def _calculate_accuracy(self, X, y):
        """Calculate model accuracy on given data."""
        correct = 0
        total = len(X)
        
        for i in range(min(total, 200)):  # Cap for speed
            score = self.brain.predict(X[i:i+1])
            pred = 1 if score > 0.5 else 0
            if pred == y[i]:
                correct += 1
        
        return correct / min(total, 200)
