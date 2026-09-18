"""
🗳️ Ensemble Brain — Multi-Model Voting System

3 Models, 1 Decision:
  1. TransformerLSTM — Deep learning: sequential patterns + cross-time attention
  2. XGBoost         — Gradient boosting: feature importance, handles noise
  3. RandomForest    — Bagging: robust to outliers, good in sideways markets

Final Prediction = Weighted average based on rolling accuracy per model.
"""

import numpy as np
import os
import json
import joblib
import logging
from datetime import datetime
from collections import deque

from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier

import torch
from src.brain import TradingBrain, TransformerLSTM, DEVICE


class EnsembleBrain:
    """
    Multi-Model Voting System.
    
    Each model predicts independently → weighted average = final confidence.
    Weights are dynamic: updated every N predictions based on rolling accuracy.
    
    Usage:
        ensemble = EnsembleBrain(input_features=19)
        confidence = ensemble.predict(last_60_candles_3d)  # (1, 60, 19)
        
    Training:
        ensemble.train_ml_models(X_flat, y)  # X_flat = (N, features) for XGB/RF
    """
    
    WEIGHTS_FILE = 'models/ensemble_weights.json'
    XGB_MODEL_FILE = 'models/ensemble_xgb.pkl'
    RF_MODEL_FILE = 'models/ensemble_rf.pkl'
    
    def __init__(self, input_features=19, use_transformer=True):
        self.input_features = input_features
        
        # Model 1: TransformerLSTM (deep learning)
        self.transformer_brain = TradingBrain(
            input_features=input_features, use_v2=use_transformer
        )
        
        # Model 2: XGBoost (gradient boosting)
        self.xgb_model = self._load_or_build_xgb()
        
        # Model 3: RandomForest (bagging)
        self.rf_model = self._load_or_build_rf()
        
        # Dynamic weights (start equal)
        self.weights = self._load_weights()
        
        # Per-model rolling accuracy tracker
        self.accuracy_tracker = {
            'transformer': deque(maxlen=100),
            'xgboost': deque(maxlen=100),
            'random_forest': deque(maxlen=100)
        }
        
        self._ml_trained = os.path.exists(self.XGB_MODEL_FILE)
        
        print(f"[Ensemble] ✅ Initialized with weights: "
              f"T={self.weights['transformer']:.2f} "
              f"X={self.weights['xgboost']:.2f} "
              f"R={self.weights['random_forest']:.2f}")
    
    def predict(self, last_60_candles):
        """
        Ensemble prediction — 3 models vote.
        
        Args:
            last_60_candles: np.ndarray shape (1, 60, features) or (60, features)
            
        Returns:
            float: confidence 0.0 to 1.0 (weighted average)
        """
        votes = {}
        
        # Ensure 3D input
        if last_60_candles.ndim == 2:
            last_60_candles = last_60_candles[np.newaxis, :]
        
        # Vote 1: TransformerLSTM
        try:
            t_score = self.transformer_brain.predict(last_60_candles)
            votes['transformer'] = t_score
        except Exception as e:
            logging.warning(f"[Ensemble] Transformer failed: {e}")
            votes['transformer'] = 0.5
        
        # Vote 2 & 3: XGBoost + RandomForest (need flat features)
        if self._ml_trained:
            try:
                # Flatten: take last candle's features + rolling stats
                flat_features = self._prepare_flat_features(last_60_candles)
                
                xgb_proba = self.xgb_model.predict_proba(flat_features)[:, 1][0]
                votes['xgboost'] = float(xgb_proba)
                
                rf_proba = self.rf_model.predict_proba(flat_features)[:, 1][0]
                votes['random_forest'] = float(rf_proba)
                
            except Exception as e:
                logging.warning(f"[Ensemble] ML models failed: {e}")
                votes['xgboost'] = 0.5
                votes['random_forest'] = 0.5
        else:
            # ML models not trained yet — use transformer only
            votes['xgboost'] = 0.5
            votes['random_forest'] = 0.5
        
        # Weighted average
        total_weight = sum(self.weights[k] for k in votes)
        final_score = sum(
            votes[k] * self.weights[k] for k in votes
        ) / max(total_weight, 0.01)
        
        return round(final_score, 4)
    
    def train_ml_models(self, X_sequences, y_labels):
        """
        Train XGBoost + RandomForest on flattened sequence data.
        
        Args:
            X_sequences: np.ndarray (N, 60, features) — time series sequences
            y_labels: np.ndarray (N,) — binary labels
        """
        print("[Ensemble] 🏋️ Training XGBoost + RandomForest...")
        
        # Flatten sequences to feature vectors
        X_flat = self._flatten_sequences(X_sequences)
        
        print(f"   Flat features shape: {X_flat.shape}")
        print(f"   Labels: {len(y_labels)} ({sum(y_labels)} positive)")
        
        # Train XGBoost
        print("   📈 Training XGBoost...")
        self.xgb_model = XGBClassifier(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            min_child_weight=3,
            reg_alpha=0.1,
            reg_lambda=1.0,
            eval_metric='logloss',
            random_state=42,
            n_jobs=-1
        )
        self.xgb_model.fit(X_flat, y_labels)
        joblib.dump(self.xgb_model, self.XGB_MODEL_FILE)
        print(f"   ✅ XGBoost trained. Saved.")
        
        # Train RandomForest
        print("   🌲 Training RandomForest...")
        self.rf_model = RandomForestClassifier(
            n_estimators=200,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            max_features='sqrt',
            class_weight='balanced',
            random_state=42,
            n_jobs=-1
        )
        self.rf_model.fit(X_flat, y_labels)
        joblib.dump(self.rf_model, self.RF_MODEL_FILE)
        print(f"   ✅ RandomForest trained. Saved.")
        
        self._ml_trained = True
        
        # Quick accuracy check on training data
        xgb_acc = self.xgb_model.score(X_flat, y_labels)
        rf_acc = self.rf_model.score(X_flat, y_labels)
        print(f"   📊 Training Accuracy — XGB: {xgb_acc:.2%} | RF: {rf_acc:.2%}")
    
    def record_outcome(self, model_name, predicted, actual):
        """Record prediction outcome for weight adjustment."""
        correct = 1 if (predicted > 0.5) == (actual > 0.5) else 0
        if model_name in self.accuracy_tracker:
            self.accuracy_tracker[model_name].append(correct)
    
    def update_weights(self):
        """Recalculate weights based on rolling accuracy."""
        new_weights = {}
        for name in ['transformer', 'xgboost', 'random_forest']:
            history = list(self.accuracy_tracker[name])
            if len(history) >= 20:
                acc = sum(history) / len(history)
                # Accuracy-based weight: 0.3 to 2.0 range
                new_weights[name] = max(0.3, min(2.0, acc * 2))
            else:
                new_weights[name] = self.weights.get(name, 1.0)
        
        self.weights = new_weights
        self._save_weights()
        print(f"[Ensemble] 🔄 Weights updated: "
              f"T={self.weights['transformer']:.2f} "
              f"X={self.weights['xgboost']:.2f} "
              f"R={self.weights['random_forest']:.2f}")
    
    def get_individual_votes(self, last_60_candles):
        """Returns each model's individual prediction for debugging."""
        if last_60_candles.ndim == 2:
            last_60_candles = last_60_candles[np.newaxis, :]
        
        votes = {}
        
        try:
            votes['transformer'] = self.transformer_brain.predict(last_60_candles)
        except Exception:
            votes['transformer'] = 0.5
        
        if self._ml_trained:
            try:
                flat = self._prepare_flat_features(last_60_candles)
                votes['xgboost'] = float(self.xgb_model.predict_proba(flat)[:, 1][0])
                votes['random_forest'] = float(self.rf_model.predict_proba(flat)[:, 1][0])
            except Exception:
                votes['xgboost'] = 0.5
                votes['random_forest'] = 0.5
        else:
            votes['xgboost'] = 0.5
            votes['random_forest'] = 0.5
        
        return votes
    
    def _flatten_sequences(self, X_seq):
        """
        Convert (N, 60, features) → (N, flat_features).
        
        Extracts:
        - Last candle features (current state)
        - Rolling mean of last 10 candles
        - Rolling std of last 10 candles
        - Min/Max of sequence
        - Momentum (last - first)
        """
        N, T, F = X_seq.shape
        
        last = X_seq[:, -1, :]          # (N, F) — current candle
        mean_10 = X_seq[:, -10:, :].mean(axis=1)  # (N, F) — recent avg
        std_10 = X_seq[:, -10:, :].std(axis=1)    # (N, F) — recent vol
        seq_min = X_seq.min(axis=1)     # (N, F)
        seq_max = X_seq.max(axis=1)     # (N, F)
        momentum = X_seq[:, -1, :] - X_seq[:, 0, :]  # (N, F) — change
        
        flat = np.concatenate([last, mean_10, std_10, seq_min, seq_max, momentum], axis=1)
        return flat
    
    def _prepare_flat_features(self, X_3d):
        """Prepare flat features for a single prediction."""
        return self._flatten_sequences(X_3d)
    
    def _load_or_build_xgb(self):
        if os.path.exists(self.XGB_MODEL_FILE):
            return joblib.load(self.XGB_MODEL_FILE)
        return XGBClassifier(n_estimators=200, max_depth=6, random_state=42)
    
    def _load_or_build_rf(self):
        if os.path.exists(self.RF_MODEL_FILE):
            return joblib.load(self.RF_MODEL_FILE)
        return RandomForestClassifier(n_estimators=200, max_depth=10, random_state=42)
    
    def _load_weights(self):
        if os.path.exists(self.WEIGHTS_FILE):
            with open(self.WEIGHTS_FILE, 'r') as f:
                return json.load(f)
        return {'transformer': 1.0, 'xgboost': 1.0, 'random_forest': 1.0}
    
    def _save_weights(self):
        os.makedirs(os.path.dirname(self.WEIGHTS_FILE) or 'models', exist_ok=True)
        with open(self.WEIGHTS_FILE, 'w') as f:
            json.dump(self.weights, f, indent=2)
