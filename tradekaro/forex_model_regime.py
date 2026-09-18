"""
🌲 Model 3: Random Forest Regime Detector
Classifies market into: RANGING (0), TRENDING (1), VOLATILE (2)
Acts as GATEKEEPER — blocks trades during volatile regimes.
"""

import numpy as np
import joblib
import os
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score

MODEL_PATH = 'models/forex_regime_rf.pkl'


class RegimeDetector:
    """Random Forest regime classifier."""

    def __init__(self):
        self.model = None
        self.feature_names = []
        self.classes = {0: 'RANGING', 1: 'TRENDING', 2: 'VOLATILE'}

    def build(self):
        self.model = RandomForestClassifier(
            n_estimators=200,
            max_depth=8,
            min_samples_leaf=50,
            min_samples_split=100,
            class_weight='balanced',
            random_state=42,
            n_jobs=-1
        )

    def train(self, X_train, y_train, X_val=None, y_val=None, feature_names=None):
        """Train regime detector."""
        self.feature_names = feature_names or []
        self.build()

        print(f"  [Regime] Training on {len(X_train):,} samples...")
        self.model.fit(X_train, y_train)

        train_acc = accuracy_score(y_train, self.model.predict(X_train))
        print(f"  [Regime] Train accuracy: {train_acc:.1%}")

        if X_val is not None and y_val is not None:
            val_acc = accuracy_score(y_val, self.model.predict(X_val))
            print(f"  [Regime] Val accuracy: {val_acc:.1%}")

            val_pred = self.model.predict(X_val)
            print(classification_report(
                y_val, val_pred,
                target_names=['RANGING', 'TRENDING', 'VOLATILE'],
                zero_division=0
            ))

        # Feature importance
        if self.feature_names:
            importances = self.model.feature_importances_
            sorted_idx = np.argsort(importances)[::-1]
            print("  [Regime] Top features:")
            for i in range(min(5, len(sorted_idx))):
                idx = sorted_idx[i]
                print(f"    {self.feature_names[idx]}: {importances[idx]:.3f}")

        return self

    def predict(self, X):
        """Predict regime: 0=RANGING, 1=TRENDING, 2=VOLATILE."""
        if self.model is None:
            return np.ones(len(X), dtype=int)  # Default: TRENDING
        return self.model.predict(X)

    def predict_proba(self, X):
        """Get regime probabilities."""
        if self.model is None:
            return np.full((len(X), 3), 1 / 3)
        return self.model.predict_proba(X)

    def save(self, path=MODEL_PATH):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        joblib.dump({
            'model': self.model,
            'feature_names': self.feature_names,
            'classes': self.classes
        }, path)
        print(f"  [Regime] Saved to {path}")

    def load(self, path=MODEL_PATH):
        if os.path.exists(path):
            data = joblib.load(path)
            self.model = data['model']
            self.feature_names = data.get('feature_names', [])
            self.classes = data.get('classes', self.classes)
            print(f"  [Regime] Loaded from {path}")
            return True
        return False
