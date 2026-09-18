"""
🧠 Model 1: XGBoost Direction Classifier
Predicts trade direction: HOLD (0), BUY (1), SELL (2)
Uses ALL 25 features as tabular snapshot input.
"""

import numpy as np
import joblib
import os
from xgboost import DMatrix, train as xgb_train, Booster
from sklearn.metrics import root_mean_squared_error, mean_absolute_error

MODEL_PATH = 'models/forex_direction_xgb.pkl'


class EVRegressor:
    """XGBoost Expected Value (EV) predictor (pips)."""

    def __init__(self):
        self.model = None
        self.feature_names = []
        self.classes = {0: 'HOLD', 1: 'BUY', 2: 'SELL'}
        self.beta = 3.0   # Directional penalty coefficient
        self.gamma = 0.2  # Overconfidence penalty coefficient

    def directional_ev_loss(self, predt, dtrain):
        """Custom Loss: MSE + Directional Penalty + Overconfidence Penalty."""
        y = dtrain.get_label()
        grad = 2.0 * (predt - y)
        hess = 2.0 * np.ones_like(predt)
        
        # Identify wrong direction
        wrong_sign = (y * predt) < 0
        
        # 1. Directional Penalty
        grad += self.beta * wrong_sign.astype(float) * (-y)
        
        # 2. Overconfidence Penalty (scales with absolute magnitude of prediction)
        grad += self.gamma * wrong_sign.astype(float) * (-y) * np.abs(predt)
        
        return grad, hess

    def train(self, X_train, y_train, X_val=None, y_val=None, feature_names=None):
        """Train EV regressor using native xgb API with custom loss."""
        self.feature_names = feature_names or [f"f{i}" for i in range(X_train.shape[1])]
        
        print(f"  [XGB-EV] Training on {len(X_train):,} samples, {X_train.shape[1]} features...")
        print(f"  [XGB-EV] Target Mean: {np.mean(y_train):.2f} pips | Std: {np.std(y_train):.2f} pips")

        dtrain = DMatrix(X_train, label=y_train, feature_names=self.feature_names)
        evals = [(dtrain, 'train')]
        
        if X_val is not None:
            dval = DMatrix(X_val, label=y_val, feature_names=self.feature_names)
            evals.append((dval, 'val'))

        params = {
            'max_depth': 5,
            'learning_rate': 0.05,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'tree_method': 'hist',
            'seed': 42,
            'disable_default_eval_metric': 1,
            'n_jobs': -1
        }
        
        # Define evaluation metric for custom objective
        def eval_rmse(predt, dtrain):
            y = dtrain.get_label()
            rmse = float(root_mean_squared_error(y, predt))
            return 'rmse', rmse

        self.model = xgb_train(
            params,
            dtrain,
            num_boost_round=500,
            evals=evals,
            obj=self.directional_ev_loss,
            custom_metric=eval_rmse,
            early_stopping_rounds=30,
            verbose_eval=False
        )

        # Training metrics
        train_pred = self.model.predict(dtrain)
        train_rmse = root_mean_squared_error(y_train, train_pred)
        print(f"  [XGB-EV] Train RMSE: {train_rmse:.2f} pips")

        # Validation metrics
        if X_val is not None and y_val is not None:
            val_pred = self.model.predict(dval)
            val_rmse = root_mean_squared_error(y_val, val_pred)
            val_mae = mean_absolute_error(y_val, val_pred)
            print(f"  [XGB-EV] Val RMSE: {val_rmse:.2f} pips | MAE: {val_mae:.2f} pips")

        # Feature importance
        scores = self.model.get_score(importance_type='weight')
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        print("  [XGB] Top 10 features:")
        for k, v in sorted_scores[:10]:
            print(f"    {k}: {v}")

        return self

    def predict(self, X):
        """Predict expected pips."""
        if self.model is None:
            return np.zeros(len(X), dtype=float)
        dmatrix = DMatrix(X, feature_names=self.feature_names)
        return self.model.predict(dmatrix)

    def predict_with_confidence(self, X):
        """Returns (predicted_pips, confidence). Confidence is magnitude of prediction."""
        pred = self.predict(X)
        confidence = np.abs(pred)  # Larger absolute pip value = higher conviction
        return pred, confidence

    def save(self, path=MODEL_PATH):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        joblib.dump({
            'model': self.model,
            'feature_names': self.feature_names,
            'classes': self.classes
        }, path)
        size_mb = os.path.getsize(path) / (1024 * 1024)
        print(f"  [XGB] Saved to {path} ({size_mb:.1f} MB)")

    def load(self, path=MODEL_PATH):
        if os.path.exists(path):
            data = joblib.load(path)
            self.model = data['model']
            self.feature_names = data.get('feature_names', [])
            self.classes = data.get('classes', self.classes)
            print(f"  [XGB] Loaded from {path}")
            return True
        return False
