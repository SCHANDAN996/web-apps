"""
📐 Model 4: XGBoost Risk Estimator
Predicts expected volatility for dynamic SL/TP calculation.
Output: predicted ATR → SL = ATR × 1.5, TP = ATR × 3.0
"""

import numpy as np
import joblib
import os
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error, r2_score

MODEL_PATH = 'models/forex_risk_xgb.pkl'
PIP = 0.0001


class RiskEstimator:
    """XGBoost regression model for volatility/risk estimation."""

    def __init__(self, sl_mult=1.5, tp_mult=3.0):
        self.model = None
        self.feature_names = []
        self.sl_mult = sl_mult
        self.tp_mult = tp_mult

    def build(self):
        self.model = XGBRegressor(
            n_estimators=200,
            max_depth=5,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            reg_lambda=1.0,
            tree_method='hist',
            random_state=42,
            n_jobs=-1,
            verbosity=0
        )

    def train(self, X_train, y_train, X_val=None, y_val=None, feature_names=None):
        """
        Train risk estimator.
        y_train should be the actual ATR values (in price units).
        """
        self.feature_names = feature_names or []
        self.build()

        print(f"  [Risk] Training on {len(X_train):,} samples...")
        print(f"  [Risk] Target ATR range: {y_train.min()/PIP:.1f} - "
              f"{y_train.max()/PIP:.1f} pips")

        self.model.fit(X_train, y_train)

        train_pred = self.model.predict(X_train)
        train_mae = mean_absolute_error(y_train, train_pred)
        print(f"  [Risk] Train MAE: {train_mae/PIP:.2f} pips")

        if X_val is not None and y_val is not None:
            val_pred = self.model.predict(X_val)
            val_mae = mean_absolute_error(y_val, val_pred)
            val_r2 = r2_score(y_val, val_pred)
            print(f"  [Risk] Val MAE: {val_mae/PIP:.2f} pips | R²: {val_r2:.3f}")

        return self

    def predict_atr(self, X):
        """Predict ATR values."""
        if self.model is None:
            return np.full(len(X), 10 * PIP)
        pred = self.model.predict(X)
        return np.clip(pred, 3 * PIP, 30 * PIP)  # Clamp to reasonable range

    def calculate_sl_tp(self, X):
        """
        Calculate dynamic SL/TP for each sample.
        Returns dict with sl_price_dist, tp_price_dist in price units.
        """
        atr = self.predict_atr(X)
        return {
            'atr': atr,
            'sl_dist': atr * self.sl_mult,
            'tp_dist': atr * self.tp_mult,
            'sl_pips': (atr * self.sl_mult) / PIP,
            'tp_pips': (atr * self.tp_mult) / PIP,
            'rr_ratio': self.tp_mult / self.sl_mult
        }

    def save(self, path=MODEL_PATH):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        joblib.dump({
            'model': self.model,
            'feature_names': self.feature_names,
            'sl_mult': self.sl_mult,
            'tp_mult': self.tp_mult
        }, path)
        print(f"  [Risk] Saved to {path}")

    def load(self, path=MODEL_PATH):
        if os.path.exists(path):
            data = joblib.load(path)
            self.model = data['model']
            self.feature_names = data.get('feature_names', [])
            self.sl_mult = data.get('sl_mult', 1.5)
            self.tp_mult = data.get('tp_mult', 3.0)
            print(f"  [Risk] Loaded from {path}")
            return True
        return False
