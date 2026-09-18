"""
🏭 Professional Training Pipeline for Trade Karo AI
3-Stage Training System: Pre-Train → Fine-Tune → Continuous Learning

Features:
- AdamW optimizer (weight decay regularization)
- OneCycleLR scheduler (warm-up + cosine annealing)
- Focal Loss (class imbalance handling)
- Gradient Clipping (max_norm=1.0)
- Mixed Precision Training (FP16 for speed on GPU)
- EarlyStopping with patience
- Model checkpointing on best validation loss
- Training metrics logging
"""

import os
import time
import json
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from torch.cuda.amp import GradScaler, autocast
from datetime import datetime

from src.brain import TradingBrain, LSTMModel, TransformerLSTM, DEVICE
from src.focal_loss import CombinedTradingLoss
from src.data_loader import (
    SequenceBuilder, DataSplitter, create_data_loaders, FEATURE_COLUMNS_V2
)
from src.indicators import TechnicalIndicators


class EarlyStopping:
    """
    Stops training when validation loss stops improving.
    Saves best model checkpoint automatically.
    """
    
    def __init__(self, patience=10, min_delta=0.0001, checkpoint_path='models/best_brain.pth'):
        self.patience = patience
        self.min_delta = min_delta
        self.checkpoint_path = checkpoint_path
        self.counter = 0
        self.best_loss = float('inf')
        self.should_stop = False
    
    def __call__(self, val_loss, model):
        if val_loss < self.best_loss - self.min_delta:
            self.best_loss = val_loss
            self.counter = 0
            self._save_checkpoint(model, val_loss)
            return False
        else:
            self.counter += 1
            if self.counter >= self.patience:
                print(f"[EarlyStopping] No improvement for {self.patience} epochs. Stopping.")
                self.should_stop = True
                return True
        return False
    
    def _save_checkpoint(self, model, loss):
        os.makedirs(os.path.dirname(self.checkpoint_path), exist_ok=True)
        # Get input_size for both V1 (LSTMModel) and V2 (TransformerLSTM)
        if isinstance(model, TransformerLSTM):
            input_sz = model.input_size
            version = 'v2'
        else:
            input_sz = model.lstm.input_size
            version = 'v1'
        checkpoint = {
            'model_state': model.state_dict(),
            'input_size': input_sz,
            'model_version': version,
            'val_loss': loss,
            'timestamp': datetime.now().isoformat()
        }
        torch.save(checkpoint, self.checkpoint_path)


class TrainingMetrics:
    """Tracks and logs training metrics across epochs."""
    
    def __init__(self, log_dir='logs/training'):
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        self.history = {
            'train_loss': [],
            'val_loss': [],
            'train_acc': [],
            'val_acc': [],
            'learning_rate': [],
            'epoch_time': []
        }
    
    def log_epoch(self, epoch, train_loss, val_loss, train_acc, val_acc, lr, duration):
        self.history['train_loss'].append(train_loss)
        self.history['val_loss'].append(val_loss)
        self.history['train_acc'].append(train_acc)
        self.history['val_acc'].append(val_acc)
        self.history['learning_rate'].append(lr)
        self.history['epoch_time'].append(duration)
        
        print(f"   Epoch {epoch:3d} | "
              f"Train Loss: {train_loss:.4f} | Val Loss: {val_loss:.4f} | "
              f"Train Acc: {train_acc:.2%} | Val Acc: {val_acc:.2%} | "
              f"LR: {lr:.6f} | Time: {duration:.1f}s")
    
    def save(self, filename='training_history.json'):
        path = os.path.join(self.log_dir, filename)
        with open(path, 'w') as f:
            json.dump(self.history, f, indent=2)
        print(f"[Metrics] Saved to {path}")
    
    def get_best_epoch(self):
        if not self.history['val_loss']:
            return 0
        return int(np.argmin(self.history['val_loss'])) + 1


class TrainingPipeline:
    """
    Professional 3-Stage Training Pipeline.
    
    Stage 1: Pre-Training (historical data)
        - Full dataset, proper epochs
        - Learn general market patterns
        
    Stage 2: Fine-Tuning (recent data)
        - Lower learning rate (1/10th)
        - Adapt to recent market regime
        
    Stage 3: Incremental Learning (live data)
        - Micro-batches
        - Experience replay
    """
    
    def __init__(self, input_features=None, learning_rate=0.001,
                 batch_size=256, max_epochs=50):
        self.learning_rate = learning_rate
        self.batch_size = batch_size
        self.max_epochs = max_epochs
        self.input_features = input_features or len(FEATURE_COLUMNS_V2)
        
        # Model
        self.brain = TradingBrain(input_features=self.input_features)
        self.model = self.brain.model
        
        # Loss Function (Focal + Label Smoothing)
        self.criterion = CombinedTradingLoss(
            focal_weight=0.7,
            smooth_weight=0.3,
            alpha=0.75,
            gamma=2.0
        )
        
        # Optimizer (AdamW = Adam + Weight Decay)
        self.optimizer = optim.AdamW(
            self.model.parameters(),
            lr=learning_rate,
            weight_decay=1e-4,
            betas=(0.9, 0.999)
        )
        
        # Mixed Precision (only on GPU)
        self.use_amp = torch.cuda.is_available()
        self.scaler = GradScaler() if self.use_amp else None
        
        # Metrics
        self.metrics = TrainingMetrics()
        
        # Sequence Builder
        self.seq_builder = SequenceBuilder()
    
    def train_stage1_historical(self, data_files, epochs=30, patience=10):
        """
        Stage 1: Pre-Training on historical CSV data.
        
        Args:
            data_files: List of CSV file paths
            epochs: Maximum training epochs
            patience: Early stopping patience
        """
        print("=" * 60)
        print("🧠 STAGE 1: HISTORICAL PRE-TRAINING")
        print("=" * 60)
        
        # Phase A: Collect & Build all sequences
        print("\n[Phase A] Building sequences from historical data...")
        all_X, all_y = [], []
        scaler = None
        
        for file_path in data_files:
            if not os.path.exists(file_path):
                print(f"   ❌ File not found: {file_path}")
                continue
            
            print(f"\n   📁 Processing: {file_path}")
            X_file, y_file, scaler = self._process_csv_file(file_path, scaler)
            
            if len(X_file) > 0:
                all_X.append(X_file)
                all_y.append(y_file)
                print(f"   ✅ Got {len(X_file)} sequences")
        
        if not all_X:
            print("❌ No data processed. Aborting.")
            return
        
        X = np.concatenate(all_X)
        y = np.concatenate(all_y)
        print(f"\n📊 Total Dataset: {len(X)} sequences, {X.shape[2]} features")
        
        # Phase B: Split data (chronological)
        (X_train, y_train), (X_val, y_val), (X_test, y_test) = DataSplitter.split(X, y)
        
        # Phase C: Create DataLoaders
        train_loader, val_loader = create_data_loaders(
            X_train, y_train, X_val, y_val,
            batch_size=self.batch_size,
            augment_train=True,
            balance_classes=True
        )
        
        # Phase D: Rebuild model if feature count changed
        actual_features = X.shape[2]
        current_input = self.brain._get_input_size()
        if actual_features != current_input:
            print(f"[Pipeline] Rebuilding V2 model: {current_input} → {actual_features} features")
            self.model = TransformerLSTM(input_size=actual_features).to(DEVICE)
            self.brain.model = self.model
            self.brain.input_features = actual_features
            self.optimizer = optim.AdamW(
                self.model.parameters(), lr=self.learning_rate, weight_decay=1e-4
            )
        
        # Phase E: Learning Rate Scheduler
        scheduler = optim.lr_scheduler.OneCycleLR(
            self.optimizer,
            max_lr=self.learning_rate * 10,
            epochs=epochs,
            steps_per_epoch=len(train_loader),
            pct_start=0.3,  # 30% warm-up
            anneal_strategy='cos'
        )
        
        # Phase F: Train!
        early_stopping = EarlyStopping(patience=patience)
        
        print(f"\n🚀 Training for up to {epochs} epochs...")
        print(f"   Device: {DEVICE}")
        print(f"   Batch Size: {self.batch_size}")
        print(f"   Learning Rate: {self.learning_rate} → {self.learning_rate * 10} (OneCycleLR)")
        print("-" * 60)
        
        for epoch in range(1, epochs + 1):
            epoch_start = time.time()
            
            # Train
            train_loss, train_acc = self._train_epoch(train_loader, scheduler)
            
            # Validate
            val_loss, val_acc = self._validate_epoch(val_loader)
            
            # Log
            current_lr = self.optimizer.param_groups[0]['lr']
            duration = time.time() - epoch_start
            self.metrics.log_epoch(epoch, train_loss, val_loss, train_acc, val_acc, current_lr, duration)
            
            # Early Stopping
            if early_stopping(val_loss, self.model):
                break
        
        # Phase G: Save final model
        self._save_final_model()
        self.metrics.save()
        
        # Phase H: Evaluate on test set
        test_loader, _ = create_data_loaders(
            X_test, y_test, X_test[:1], y_test[:1],  # Dummy val
            batch_size=self.batch_size * 2,
            augment_train=False,
            balance_classes=False
        )
        test_loss, test_acc = self._validate_epoch(test_loader)
        
        print("=" * 60)
        print(f"🎉 TRAINING COMPLETE!")
        print(f"   Best Epoch: {self.metrics.get_best_epoch()}")
        print(f"   Test Loss: {test_loss:.4f} | Test Accuracy: {test_acc:.2%}")
        print("=" * 60)
    
    def train_stage2_finetune(self, recent_data_df, epochs=10):
        """
        Stage 2: Fine-tuning on recent data (lower LR).
        
        Args:
            recent_data_df: DataFrame of recent 1m candles
            epochs: Fine-tuning epochs
        """
        print("\n" + "=" * 60)
        print("🔧 STAGE 2: FINE-TUNING ON RECENT DATA")
        print("=" * 60)
        
        # Reduce learning rate
        finetune_lr = self.learning_rate / 10
        for param_group in self.optimizer.param_groups:
            param_group['lr'] = finetune_lr
        
        # Build sequences from recent data
        df_rich = TechnicalIndicators.apply_multi_timeframe_features(recent_data_df)
        if df_rich.empty:
            print("❌ Not enough recent data for fine-tuning.")
            return
        
        X, y, _ = self.seq_builder.build_sequences(df_rich, FEATURE_COLUMNS_V2)
        if len(X) == 0:
            print("❌ No sequences generated.")
            return
        
        # 80/20 split for fine-tune
        split_idx = int(len(X) * 0.8)
        X_train, y_train = X[:split_idx], y[:split_idx]
        X_val, y_val = X[split_idx:], y[split_idx:]
        
        train_loader, val_loader = create_data_loaders(
            X_train, y_train, X_val, y_val,
            batch_size=min(self.batch_size, len(X_train)),
            augment_train=False,
            balance_classes=True
        )
        
        print(f"   Fine-tuning LR: {finetune_lr}")
        print(f"   Samples: {len(X_train)} train / {len(X_val)} val")
        print("-" * 60)
        
        for epoch in range(1, epochs + 1):
            epoch_start = time.time()
            train_loss, train_acc = self._train_epoch(train_loader)
            val_loss, val_acc = self._validate_epoch(val_loader)
            duration = time.time() - epoch_start
            self.metrics.log_epoch(epoch, train_loss, val_loss, train_acc, val_acc, finetune_lr, duration)
        
        self._save_final_model()
        print("✅ Fine-tuning complete.")
    
    def train_stage3_incremental(self, X_batch, y_batch, epochs=3):
        """
        Stage 3: Quick incremental training on live micro-batches.
        Used by ContinuousLearner every 4 hours.
        
        Args:
            X_batch: np.ndarray (N, lookback, features)
            y_batch: np.ndarray (N,)
            epochs: Quick epochs
        """
        if len(X_batch) == 0:
            return
        
        self.model.train()
        
        X_tensor = torch.tensor(X_batch, dtype=torch.float32).to(DEVICE)
        y_tensor = torch.tensor(y_batch, dtype=torch.float32).unsqueeze(1).to(DEVICE)
        
        # Check dimension match
        expected_dim = self.brain._get_input_size()
        if X_batch.shape[2] != expected_dim:
            print(f"[Stage3] ⚠️ Feature mismatch ({X_batch.shape[2]} vs {expected_dim}). Skipping.")
            return
        
        # Use lower LR for micro-updates
        micro_lr = self.learning_rate / 50
        for param_group in self.optimizer.param_groups:
            param_group['lr'] = micro_lr
        
        for epoch in range(epochs):
            self.optimizer.zero_grad()
            outputs = self.model(X_tensor)
            loss = self.criterion(outputs, y_tensor)
            loss.backward()
            
            # Gradient clipping
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
            
            self.optimizer.step()
        
        self._save_final_model()
        print(f"[Stage3] Incremental update — Loss: {loss.item():.4f} on {len(X_batch)} samples")
    
    def _train_epoch(self, train_loader, scheduler=None):
        """Train for one epoch."""
        self.model.train()
        total_loss = 0
        correct = 0
        total = 0
        
        for X_batch, y_batch in train_loader:
            X_batch = X_batch.to(DEVICE)
            y_batch = y_batch.unsqueeze(1).to(DEVICE)
            
            self.optimizer.zero_grad()
            
            if self.use_amp:
                with autocast():
                    outputs = self.model(X_batch)
                    loss = self.criterion(outputs, y_batch)
                self.scaler.scale(loss).backward()
                
                # Gradient clipping before step
                self.scaler.unscale_(self.optimizer)
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
                
                self.scaler.step(self.optimizer)
                self.scaler.update()
            else:
                outputs = self.model(X_batch)
                loss = self.criterion(outputs, y_batch)
                loss.backward()
                
                # Gradient clipping
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
                
                self.optimizer.step()
            
            if scheduler:
                scheduler.step()
            
            total_loss += loss.item() * X_batch.size(0)
            predicted = (outputs > 0.5).float()
            correct += (predicted == y_batch).sum().item()
            total += y_batch.size(0)
        
        avg_loss = total_loss / max(total, 1)
        accuracy = correct / max(total, 1)
        return avg_loss, accuracy
    
    def _validate_epoch(self, val_loader):
        """Validate for one epoch (no gradients)."""
        self.model.eval()
        total_loss = 0
        correct = 0
        total = 0
        
        with torch.no_grad():
            for X_batch, y_batch in val_loader:
                X_batch = X_batch.to(DEVICE)
                y_batch = y_batch.unsqueeze(1).to(DEVICE)
                
                outputs = self.model(X_batch)
                loss = self.criterion(outputs, y_batch)
                
                total_loss += loss.item() * X_batch.size(0)
                predicted = (outputs > 0.5).float()
                correct += (predicted == y_batch).sum().item()
                total += y_batch.size(0)
        
        avg_loss = total_loss / max(total, 1)
        accuracy = correct / max(total, 1)
        return avg_loss, accuracy
    
    def _process_csv_file(self, file_path, scaler=None):
        """Process a single CSV file into sequences."""
        all_X, all_y = [], []
        chunk_size = 20000
        is_first_chunk = True
        
        for chunk_idx, chunk in enumerate(pd.read_csv(file_path, chunksize=chunk_size)):
            try:
                # Normalize column names
                chunk.columns = [c.strip().lower() for c in chunk.columns]
                
                # Create timestamp
                if 'datetime' in chunk.columns:
                    chunk['timestamp'] = pd.to_datetime(chunk['datetime'])
                elif 'date' in chunk.columns and 'time' in chunk.columns:
                    chunk['timestamp'] = pd.to_datetime(
                        chunk['date'].astype(str) + ' ' + chunk['time'].astype(str)
                    )
                elif 'date' in chunk.columns:
                    chunk['timestamp'] = pd.to_datetime(chunk['date'])
                else:
                    continue
                
                chunk.set_index('timestamp', inplace=True)
                chunk.sort_index(inplace=True)
                
                # Apply MTF indicators
                df_rich = TechnicalIndicators.apply_multi_timeframe_features(chunk)
                if df_rich.empty:
                    continue
                
                # Build sequences
                X, y, scaler = self.seq_builder.build_sequences(
                    df_rich,
                    FEATURE_COLUMNS_V2,
                    scaler=scaler,
                    fit_scaler=(is_first_chunk and scaler is None)
                )
                
                is_first_chunk = False
                
                if len(X) > 0:
                    all_X.append(X)
                    all_y.append(y)
                    
                if (chunk_idx + 1) % 10 == 0:
                    total = sum(len(x) for x in all_X)
                    print(f"      Chunk {chunk_idx + 1}: {total} sequences so far...")
                    
            except Exception as e:
                print(f"      ❌ Error in chunk {chunk_idx + 1}: {e}")
        
        if all_X:
            return np.concatenate(all_X), np.concatenate(all_y), scaler
        return np.array([]), np.array([]), scaler
    
    def _save_final_model(self):
        """Save the trained model using TradingBrain's save method."""
        self.brain.model = self.model
        self.brain.save_model()


# --- CLI Entry Point ---
if __name__ == "__main__":
    print("=" * 60)
    print("🏭 TRADE KARO AI — PROFESSIONAL TRAINING PIPELINE")
    print("=" * 60)
    
    # Data files
    data_files = [
        "data/NIFTY 50_minute.csv",
        "data/NIFTY BANK_minute.csv"
    ]
    
    # Check which files exist
    available_files = [f for f in data_files if os.path.exists(f)]
    
    if not available_files:
        print("❌ No training data files found!")
        print("   Expected files:")
        for f in data_files:
            print(f"   - {f}")
        exit(1)
    
    print(f"\n📁 Found {len(available_files)} data files:")
    for f in available_files:
        size_mb = os.path.getsize(f) / (1024 * 1024)
        print(f"   - {f} ({size_mb:.1f} MB)")
    
    # Initialize Pipeline
    pipeline = TrainingPipeline(
        learning_rate=0.001,
        batch_size=256,
        max_epochs=30
    )
    
    # Stage 1: Pre-Training
    pipeline.train_stage1_historical(
        available_files,
        epochs=30,
        patience=10
    )
    
    print("\n✅ Pipeline Complete! Model saved to models/tradenet_actor.pth")
