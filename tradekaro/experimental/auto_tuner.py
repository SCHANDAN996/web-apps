"""
⚙️ Auto-Hyperparameter Tuner — Self-Optimizing Model Configuration

Instead of manually tuning learning_rate, batch_size, dropout, etc.,
this engine automatically finds the best combination.

Uses Random Search (lightweight, no Optuna needed):
1. Define search space
2. Sample N random configs
3. Train mini model for each (few epochs)
4. Pick best → use for full training

Also adapts live trading parameters:
  - Confidence threshold (when to trade)
  - Stop-loss percentage
  - Position size multiplier
"""

import json
import os
import random
import time
import numpy as np
from datetime import datetime


class AutoHyperTuner:
    """
    Auto-tunes model and trading hyperparameters.
    
    Usage:
        tuner = AutoHyperTuner()
        
        # Model hyperparameters
        best = tuner.tune_model(X_train, y_train, X_val, y_val, n_trials=20)
        # {'lr': 0.001, 'batch_size': 128, 'dropout': 0.2, ...}
        
        # Trading parameters (adapts based on performance)
        params = tuner.tune_trading_params(win_rate=0.55, avg_win=1500, avg_loss=800)
    """
    
    RESULTS_FILE = 'models/tuning_results.json'
    
    # Model hyperparameter search space
    MODEL_SEARCH_SPACE = {
        'learning_rate': [0.0001, 0.0003, 0.0005, 0.001, 0.003, 0.005],
        'batch_size': [32, 64, 128, 256],
        'dropout': [0.1, 0.15, 0.2, 0.3, 0.4],
        'hidden_dim': [64, 128, 256],
        'num_heads': [2, 4, 8],
        'lstm_layers': [1, 2, 3],
        'weight_decay': [1e-5, 1e-4, 1e-3],
        'focal_gamma': [1.0, 1.5, 2.0, 3.0],
        'focal_alpha': [0.5, 0.6, 0.7, 0.75, 0.8],
    }
    
    def __init__(self):
        self.results = self._load_results()
    
    def tune_model(self, X_train, y_train, X_val, y_val, n_trials=20, 
                   epochs_per_trial=3):
        """
        Random search over model hyperparameters.
        Quick: trains only `epochs_per_trial` epochs per config.
        """
        import torch
        import torch.nn as nn
        import torch.optim as optim
        from src.brain import TransformerLSTM, DEVICE
        from src.focal_loss import CombinedTradingLoss
        
        print(f"⚙️ Auto-Tuning: {n_trials} trials, {epochs_per_trial} epochs each")
        
        best_score = 0
        best_config = None
        trial_results = []
        
        for trial in range(n_trials):
            config = self._sample_config()
            
            try:
                # Build model
                model = TransformerLSTM(
                    input_size=X_train.shape[2],
                    hidden_dim=config['hidden_dim'],
                    num_heads=config['num_heads'],
                    num_layers=config['lstm_layers'],
                    dropout=config['dropout']
                ).to(DEVICE)
                
                criterion = CombinedTradingLoss(
                    focal_weight=0.7, smooth_weight=0.3,
                    alpha=config['focal_alpha'], gamma=config['focal_gamma']
                )
                
                optimizer = optim.AdamW(
                    model.parameters(),
                    lr=config['learning_rate'],
                    weight_decay=config['weight_decay']
                )
                
                # Quick train
                batch_size = config['batch_size']
                model.train()
                
                for epoch in range(epochs_per_trial):
                    indices = np.random.permutation(len(X_train))
                    for start in range(0, len(X_train), batch_size):
                        end = min(start + batch_size, len(X_train))
                        idx = indices[start:end]
                        
                        X_b = torch.tensor(X_train[idx], dtype=torch.float32).to(DEVICE)
                        y_b = torch.tensor(y_train[idx], dtype=torch.float32).unsqueeze(1).to(DEVICE)
                        
                        optimizer.zero_grad()
                        out = model(X_b)
                        loss = criterion(out, y_b)
                        loss.backward()
                        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                        optimizer.step()
                
                # Validate
                model.eval()
                with torch.no_grad():
                    X_v = torch.tensor(X_val, dtype=torch.float32).to(DEVICE)
                    y_v = torch.tensor(y_val, dtype=torch.float32).to(DEVICE)
                    out = model(X_v)
                    preds = (out.squeeze() > 0.5).float()
                    acc = (preds == y_v).float().mean().item()
                
                trial_results.append({
                    'trial': trial + 1, 'config': config,
                    'val_accuracy': round(acc, 4)
                })
                
                if acc > best_score:
                    best_score = acc
                    best_config = config
                
                print(f"  Trial {trial+1}/{n_trials}: acc={acc:.4f} "
                      f"(lr={config['learning_rate']}, bs={config['batch_size']}, "
                      f"d={config['dropout']})")
                
                del model, optimizer
                torch.cuda.empty_cache() if torch.cuda.is_available() else None
                
            except Exception as e:
                print(f"  Trial {trial+1} FAILED: {e}")
                continue
        
        # Save results
        self.results['model_tuning'] = {
            'best_config': best_config,
            'best_accuracy': best_score,
            'trials': trial_results,
            'timestamp': datetime.now().isoformat()
        }
        self._save_results()
        
        print(f"\n🏆 Best Config (acc={best_score:.4f}): {best_config}")
        return best_config
    
    def tune_trading_params(self, win_rate, avg_win, avg_loss, 
                           current_drawdown=0):
        """
        Adapt trading parameters based on recent performance.
        
        Returns optimized: confidence_threshold, sl_pct, position_multiplier
        """
        # Edge = (win_rate * avg_win - (1-win_rate) * avg_loss) / avg_loss
        edge = (win_rate * avg_win - (1 - win_rate) * avg_loss) / max(avg_loss, 1)
        
        # Confidence threshold: higher edge → more aggressive
        if edge > 0.3:
            conf_threshold = 0.55  # More trades
        elif edge > 0.1:
            conf_threshold = 0.60  # Standard
        elif edge > 0:
            conf_threshold = 0.65  # Conservative
        else:
            conf_threshold = 0.70  # Very conservative
        
        # SL adjustment based on win rate
        if win_rate > 0.60:
            sl_pct = 1.5  # Tighter stops (winning enough)
        elif win_rate > 0.50:
            sl_pct = 2.0  # Standard
        else:
            sl_pct = 2.5  # Wider stops (need wins to run)
        
        # Position size multiplier based on drawdown
        if current_drawdown > 5:
            pos_multiplier = 0.5  # Half size
        elif current_drawdown > 3:
            pos_multiplier = 0.75
        elif edge > 0.3:
            pos_multiplier = 1.25  # Increase when winning
        else:
            pos_multiplier = 1.0
        
        params = {
            'confidence_threshold': conf_threshold,
            'stop_loss_pct': sl_pct,
            'position_multiplier': pos_multiplier,
            'edge': round(edge, 4),
            'updated': datetime.now().isoformat()
        }
        
        self.results['trading_params'] = params
        self._save_results()
        
        return params
    
    def _sample_config(self):
        """Sample random config from search space."""
        return {
            key: random.choice(values)
            for key, values in self.MODEL_SEARCH_SPACE.items()
        }
    
    def _load_results(self):
        if os.path.exists(self.RESULTS_FILE):
            try:
                with open(self.RESULTS_FILE, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def _save_results(self):
        os.makedirs(os.path.dirname(self.RESULTS_FILE) or 'models', exist_ok=True)
        with open(self.RESULTS_FILE, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
