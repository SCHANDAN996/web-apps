"""
🛡️ Adversarial Stress Tester — Model Robustness Validation

Tests whether the AI model can survive extreme market conditions:
  1. Synthetic Crashes (COVID-style -15% drops)
  2. Flash Crashes (instant 5% moves in 1 candle)
  3. Noise Injection (how much noise before model breaks?)
  4. Feature Dropout (what if RSI/MACD disappears?)
  5. Confidence Calibration (is 0.80 really 80% accurate?)
"""

import numpy as np
import torch
from datetime import datetime


class StressTester:
    """
    Adversarial robustness testing for trading AI models.
    
    Usage:
        tester = StressTester(brain)
        report = tester.run_full_test(sample_data)
        print(report['summary'])
    """
    
    def __init__(self, brain):
        self.brain = brain
        self.results = {}
    
    def run_full_test(self, X_data, y_labels=None):
        """
        Run complete stress test suite.
        
        Args:
            X_data: np.ndarray (N, 60, features) — test sequences
            y_labels: np.ndarray (N,) — true labels (optional)
        """
        print("🛡️ Running Adversarial Stress Tests...")
        
        # 1. Baseline
        baseline = self._test_baseline(X_data, y_labels)
        
        # 2. Crash scenarios
        crash = self._test_crash_scenarios(X_data)
        
        # 3. Noise robustness
        noise = self._test_noise_robustness(X_data)
        
        # 4. Feature dropout
        dropout = self._test_feature_dropout(X_data)
        
        # 5. Confidence calibration
        calibration = self._test_calibration(X_data, y_labels) if y_labels is not None else None
        
        self.results = {
            'baseline': baseline,
            'crash_resistance': crash,
            'noise_robustness': noise,
            'feature_dropout': dropout,
            'calibration': calibration,
            'timestamp': datetime.now().isoformat(),
            'summary': self._generate_summary(baseline, crash, noise, dropout, calibration)
        }
        
        print(self.results['summary'])
        return self.results
    
    def _test_baseline(self, X, y=None):
        """Test baseline performance."""
        print("  📊 Test 1: Baseline Performance...")
        predictions = []
        for i in range(len(X)):
            score = self.brain.predict(X[i:i+1])
            predictions.append(score)
        
        preds = np.array(predictions)
        
        result = {
            'mean_score': float(np.mean(preds)),
            'std_score': float(np.std(preds)),
            'min_score': float(np.min(preds)),
            'max_score': float(np.max(preds)),
            'buy_signals': int(np.sum(preds > 0.6)),
            'sell_signals': int(np.sum(preds < 0.4)),
            'hold_signals': int(np.sum((preds >= 0.4) & (preds <= 0.6)))
        }
        
        if y is not None:
            binary_pred = (preds > 0.5).astype(int)
            result['accuracy'] = float(np.mean(binary_pred == y))
        
        print(f"    Mean: {result['mean_score']:.4f}, Std: {result['std_score']:.4f}")
        return result
    
    def _test_crash_scenarios(self, X):
        """Test model behavior during extreme market events."""
        print("  💥 Test 2: Crash Scenarios...")
        
        results = {}
        
        # Scenario 1: COVID-style crash (-15% over 5 candles)
        X_crash = X.copy()
        for i in range(min(5, X_crash.shape[1])):
            X_crash[:, -(i+1), 0] *= (1 - 0.03 * (i+1))  # Close price drops
        
        crash_preds = [self.brain.predict(X_crash[i:i+1]) for i in range(len(X_crash))]
        crash_preds = np.array(crash_preds)
        results['covid_crash'] = {
            'mean_score': float(np.mean(crash_preds)),
            'sell_triggered': int(np.sum(crash_preds < 0.4)),
            'buy_triggered': int(np.sum(crash_preds > 0.6))
        }
        
        # Scenario 2: Flash crash (-5% in 1 candle)
        X_flash = X.copy()
        X_flash[:, -1, 0] *= 0.95
        
        flash_preds = [self.brain.predict(X_flash[i:i+1]) for i in range(len(X_flash))]
        flash_preds = np.array(flash_preds)
        results['flash_crash'] = {
            'mean_score': float(np.mean(flash_preds)),
            'sell_triggered': int(np.sum(flash_preds < 0.4))
        }
        
        # Scenario 3: V-shaped recovery (+10% after crash)
        X_recovery = X_crash.copy()
        X_recovery[:, -1, 0] *= 1.10
        
        recovery_preds = [self.brain.predict(X_recovery[i:i+1]) for i in range(len(X_recovery))]
        recovery_preds = np.array(recovery_preds)
        results['v_recovery'] = {
            'mean_score': float(np.mean(recovery_preds)),
            'buy_triggered': int(np.sum(recovery_preds > 0.6))
        }
        
        print(f"    COVID crash avg: {results['covid_crash']['mean_score']:.4f}")
        return results
    
    def _test_noise_robustness(self, X):
        """Test how much noise the model can handle before predictions break."""
        print("  🔊 Test 3: Noise Robustness...")
        
        noise_levels = [0.01, 0.05, 0.10, 0.20, 0.50]
        results = {}
        
        base_preds = np.array([self.brain.predict(X[i:i+1]) for i in range(min(50, len(X)))])
        
        for noise in noise_levels:
            X_noisy = X[:50].copy()
            X_noisy += np.random.normal(0, noise, X_noisy.shape)
            
            noisy_preds = np.array([self.brain.predict(X_noisy[i:i+1]) for i in range(len(X_noisy))])
            
            # How much did predictions change?
            mean_shift = float(np.mean(np.abs(noisy_preds - base_preds)))
            correlation = float(np.corrcoef(base_preds, noisy_preds)[0, 1]) if np.std(base_preds) > 0 else 0
            
            results[f'noise_{noise}'] = {
                'noise_level': noise,
                'mean_shift': round(mean_shift, 4),
                'correlation_with_clean': round(correlation, 4)
            }
        
        # Find breaking point
        for k, v in results.items():
            if v['correlation_with_clean'] < 0.5:
                results['breaking_point'] = v['noise_level']
                break
        else:
            results['breaking_point'] = '>0.50 (robust!)'
        
        print(f"    Breaking point: {results['breaking_point']}")
        return results
    
    def _test_feature_dropout(self, X):
        """Test model resilience when features are zeroed out."""
        print("  🔌 Test 4: Feature Dropout...")
        
        results = {}
        n_features = X.shape[2]
        base_preds = np.array([self.brain.predict(X[i:i+1]) for i in range(min(30, len(X)))])
        
        # Drop each feature and measure impact
        feature_importance = {}
        for f in range(n_features):
            X_dropped = X[:30].copy()
            X_dropped[:, :, f] = 0
            
            dropped_preds = np.array([self.brain.predict(X_dropped[i:i+1]) for i in range(len(X_dropped))])
            impact = float(np.mean(np.abs(dropped_preds - base_preds)))
            feature_importance[f"feature_{f}"] = round(impact, 4)
        
        # Top 5 most important features
        sorted_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)
        results['top_5_important'] = sorted_features[:5]
        results['least_important'] = sorted_features[-3:]
        
        print(f"    Most important: {sorted_features[0]}")
        return results
    
    def _test_calibration(self, X, y):
        """Test if model's confidence matches actual accuracy."""
        print("  🎯 Test 5: Confidence Calibration...")
        
        predictions = np.array([self.brain.predict(X[i:i+1]) for i in range(len(X))])
        
        # Bin predictions
        bins = [(0.0, 0.2), (0.2, 0.4), (0.4, 0.6), (0.6, 0.8), (0.8, 1.0)]
        calibration = {}
        
        for low, high in bins:
            mask = (predictions >= low) & (predictions < high)
            if mask.sum() > 0:
                actual_acc = float(np.mean(y[mask]))
                calibration[f'{low:.1f}-{high:.1f}'] = {
                    'predicted_conf': round((low + high) / 2, 2),
                    'actual_accuracy': round(actual_acc, 4),
                    'count': int(mask.sum()),
                    'calibrated': abs(actual_acc - (low + high) / 2) < 0.15
                }
        
        return calibration
    
    def _generate_summary(self, baseline, crash, noise, dropout, calibration):
        """Generate human-readable summary."""
        lines = ["", "=" * 50, "🛡️ STRESS TEST REPORT", "=" * 50]
        
        lines.append(f"\n📊 Baseline: Mean={baseline['mean_score']:.4f}, "
                     f"Std={baseline['std_score']:.4f}")
        if 'accuracy' in baseline:
            lines.append(f"   Accuracy: {baseline['accuracy']:.2%}")
        
        if crash:
            lines.append(f"\n💥 Crash Tests:")
            for name, data in crash.items():
                if isinstance(data, dict):
                    lines.append(f"   {name}: Score={data.get('mean_score', 'N/A')}")
        
        if noise:
            lines.append(f"\n🔊 Noise Breaking Point: {noise.get('breaking_point', 'N/A')}")
        
        if dropout:
            top = dropout.get('top_5_important', [])
            if top:
                lines.append(f"\n🔌 Most Important Feature: {top[0][0]} (impact: {top[0][1]})")
        
        # Overall grade
        grade = self._calc_grade(baseline, crash, noise)
        lines.append(f"\n{'=' * 50}")
        lines.append(f"📋 OVERALL GRADE: {grade}")
        lines.append(f"{'=' * 50}\n")
        
        return '\n'.join(lines)
    
    def _calc_grade(self, baseline, crash, noise):
        """Calculate overall robustness grade."""
        score = 0
        
        # Baseline score diversity
        if baseline['std_score'] > 0.05:
            score += 2
        
        # Accuracy
        if baseline.get('accuracy', 0) > 0.60:
            score += 3
        
        # Crash response
        if crash and crash.get('covid_crash', {}).get('sell_triggered', 0) > 0:
            score += 2
        
        # Noise robustness
        if noise and noise.get('breaking_point', 0) != '>0.50 (robust!)':
            bp = noise.get('breaking_point', 0)
            if isinstance(bp, (int, float)) and bp >= 0.10:
                score += 2
        else:
            score += 3
        
        grades = {10: 'A+ (Exceptional)', 8: 'A (Strong)', 6: 'B (Good)',
                  4: 'C (Needs Work)', 2: 'D (Fragile)', 0: 'F (Critical)'}
        
        for threshold in sorted(grades.keys(), reverse=True):
            if score >= threshold:
                return grades[threshold]
        return 'F (Critical)'
