"""
🧠 Memory-Efficient V2 Brain Training Script
Trains the TransformerLSTM V2 model chunk-by-chunk to avoid OOM kills.

Instead of loading all 400K+ sequences into RAM:
1. Process 1 chunk (20K rows) → get ~3,900 sequences
2. Train 1 epoch on that chunk
3. Free memory, load next chunk
4. After all chunks, run validation epochs
"""

import os
import gc
import time
import json
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from datetime import datetime

# Project imports
from src.brain import TradingBrain, TransformerLSTM, DEVICE
from src.focal_loss import CombinedTradingLoss
from src.indicators import TechnicalIndicators
from src.data_loader import SequenceBuilder, FEATURE_COLUMNS_V2

# Fix: Some indicators use "RSI" not "RSI_14" — auto-detect
FEATURE_COLUMNS_FLEX = [
    'close', 'SMA_20', 'EMA_50', 'MACD', 'MACD_Signal', 'MACD_Hist',
    'plus_di', 'minus_di', 'ADX',
    'KC_Upper', 'KC_Lower', 'KC_Middle', 'volume_shock',
    '15m_EMA_50', '15m_SMA_20', '15m_MACD', '15m_ADX',
    '1H_EMA_50', '1H_ADX'
]

# RSI columns — will try both naming conventions
RSI_VARIANTS = {
    'RSI_14': ['RSI_14', 'RSI', 'rsi_14', 'rsi'],
    '15m_RSI_14': ['15m_RSI_14', '15m_RSI'],
    '1H_RSI_14': ['1H_RSI_14', '1H_RSI'],
}


def find_available_features(df):
    """Find which features are available in the DataFrame."""
    available = []
    for col in FEATURE_COLUMNS_FLEX:
        if col in df.columns:
            available.append(col)
    
    # Handle RSI naming variants
    for target, variants in RSI_VARIANTS.items():
        for variant in variants:
            if variant in df.columns:
                available.append(variant)
                break
    
    return available


def process_chunk_to_sequences(chunk_df, scaler, seq_builder, fit_scaler=False):
    """Process a single chunk into sequences, memory-efficient."""
    try:
        # Normalize columns
        chunk_df.columns = [c.strip().lower() if '15m' not in c and '1H' not in c 
                           else c.strip() for c in chunk_df.columns]
        
        # Create timestamp index
        if 'datetime' in chunk_df.columns:
            chunk_df['timestamp'] = pd.to_datetime(chunk_df['datetime'])
        elif 'date' in chunk_df.columns and 'time' in chunk_df.columns:
            chunk_df['timestamp'] = pd.to_datetime(
                chunk_df['date'].astype(str) + ' ' + chunk_df['time'].astype(str))
        elif 'date' in chunk_df.columns:
            chunk_df['timestamp'] = pd.to_datetime(chunk_df['date'])
        else:
            return None, None, scaler
        
        chunk_df.set_index('timestamp', inplace=True)
        chunk_df.sort_index(inplace=True)
        
        # Apply multi-timeframe indicators
        df_rich = TechnicalIndicators.apply_multi_timeframe_features(chunk_df)
        if df_rich.empty or len(df_rich) < 70:
            return None, None, scaler
        
        # Find available features
        features = find_available_features(df_rich)
        if len(features) < 10:
            return None, None, scaler
        
        # Build sequences
        X, y, scaler = seq_builder.build_sequences(
            df_rich, features, scaler=scaler, fit_scaler=fit_scaler
        )
        
        return X, y, scaler
        
    except Exception as e:
        print(f"   ❌ Chunk error: {e}")
        return None, None, scaler


def train_v2_memory_efficient():
    """Main training function — processes chunks one at a time."""
    
    print("=" * 60)
    print("🧠 TRADE KARO AI — V2 BRAIN TRAINING (Memory-Efficient)")
    print(f"   Device: {DEVICE}")
    print(f"   Time: {datetime.now().isoformat()}")
    print("=" * 60)
    
    # Data files
    data_files = [
        "data/NIFTY 50_minute.csv",
        "data/NIFTY BANK_minute.csv"
    ]
    available = [f for f in data_files if os.path.exists(f)]
    
    if not available:
        print("❌ No training data found!")
        return
    
    for f in available:
        sz = os.path.getsize(f) / (1024*1024)
        print(f"   📁 {f} ({sz:.1f} MB)")
    
    # Initialize
    seq_builder = SequenceBuilder(lookback=60, future_horizon=5, threshold=0.001)
    scaler = None
    
    # Build a fresh V2 brain
    print("\n[INIT] Building TransformerLSTM V2 Brain...")
    num_features = 19  # Will be auto-adjusted
    brain = TradingBrain(input_features=num_features, use_v2=True)
    model = brain.model
    
    # Loss
    criterion = CombinedTradingLoss(focal_weight=0.7, smooth_weight=0.3, alpha=0.75, gamma=2.0)
    optimizer = optim.AdamW(model.parameters(), lr=0.001, weight_decay=1e-4)
    
    # Training config
    chunk_size = 30000  # Rows per chunk (1-min candles)
    total_chunks_trained = 0
    total_sequences = 0
    total_loss_sum = 0
    val_chunks = []  # Save last few chunks for validation
    
    print(f"\n{'='*60}")
    print("📊 PHASE 1: CHUNK-BY-CHUNK TRAINING")
    print(f"{'='*60}\n")
    
    for file_idx, file_path in enumerate(available):
        print(f"\n📁 [{file_idx+1}/{len(available)}] Processing: {file_path}")
        
        chunk_count = sum(1 for _ in pd.read_csv(file_path, chunksize=chunk_size))
        print(f"   Total chunks: ~{chunk_count}")
        
        for chunk_idx, chunk in enumerate(pd.read_csv(file_path, chunksize=chunk_size)):
            t0 = time.time()
            
            X, y, scaler = process_chunk_to_sequences(
                chunk, scaler, seq_builder, 
                fit_scaler=(total_chunks_trained == 0)
            )
            
            if X is None or len(X) == 0:
                continue
            
            # Auto-rebuild model if feature count changes
            actual_features = X.shape[2]
            current_features = brain._get_input_size()
            
            if actual_features != current_features and total_chunks_trained == 0:
                print(f"   [REBUILD] {current_features} → {actual_features} features")
                model = TransformerLSTM(input_size=actual_features).to(DEVICE)
                brain.model = model
                brain.input_features = actual_features
                optimizer = optim.AdamW(model.parameters(), lr=0.001, weight_decay=1e-4)
                num_features = actual_features
            
            # Save last 5% for validation
            if chunk_idx >= chunk_count * 0.90:
                val_chunks.append((X.copy(), y.copy()))
                continue
            
            # Train on this chunk (2 epochs per chunk)
            model.train()
            chunk_loss = 0
            chunk_correct = 0
            
            # Mini-batch within the chunk
            batch_size = 128
            indices = np.random.permutation(len(X))
            
            for epoch in range(2):
                for start in range(0, len(X), batch_size):
                    end = min(start + batch_size, len(X))
                    batch_idx = indices[start:end]
                    
                    X_batch = torch.tensor(X[batch_idx], dtype=torch.float32).to(DEVICE)
                    y_batch = torch.tensor(y[batch_idx], dtype=torch.float32).unsqueeze(1).to(DEVICE)
                    
                    optimizer.zero_grad()
                    outputs = model(X_batch)
                    loss = criterion(outputs, y_batch)
                    loss.backward()
                    torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
                    optimizer.step()
                    
                    chunk_loss += loss.item() * len(batch_idx)
                    predicted = (outputs > 0.5).float()
                    chunk_correct += (predicted == y_batch).sum().item()
            
            total_sequences += len(X) * 2  # 2 epochs
            total_chunks_trained += 1
            avg_loss = chunk_loss / (len(X) * 2)
            accuracy = chunk_correct / (len(X) * 2)
            total_loss_sum += avg_loss
            elapsed = time.time() - t0
            
            print(f"   Chunk {chunk_idx+1:3d}/{chunk_count} | "
                  f"Seqs: {len(X):5d} | Loss: {avg_loss:.4f} | "
                  f"Acc: {accuracy:.2%} | Time: {elapsed:.1f}s")
            
            # Free memory
            del X, y
            gc.collect()
            
            # Save checkpoint every 10 chunks
            if total_chunks_trained % 10 == 0:
                brain.save_model()
                print(f"   💾 Checkpoint saved (chunk {total_chunks_trained})")
    
    # PHASE 2: Validation
    print(f"\n{'='*60}")
    print("📊 PHASE 2: VALIDATION")
    print(f"{'='*60}\n")
    
    if val_chunks:
        model.eval()
        val_loss_total = 0
        val_correct = 0
        val_total = 0
        
        with torch.no_grad():
            for X_val, y_val in val_chunks:
                X_t = torch.tensor(X_val, dtype=torch.float32).to(DEVICE)
                y_t = torch.tensor(y_val, dtype=torch.float32).unsqueeze(1).to(DEVICE)
                
                out = model(X_t)
                loss = criterion(out, y_t)
                
                val_loss_total += loss.item() * len(X_val)
                predicted = (out > 0.5).float()
                val_correct += (predicted == y_t).sum().item()
                val_total += len(X_val)
                
                del X_t, y_t
                gc.collect()
        
        val_loss = val_loss_total / max(val_total, 1)
        val_acc = val_correct / max(val_total, 1)
        print(f"   Validation Loss: {val_loss:.4f}")
        print(f"   Validation Accuracy: {val_acc:.2%}")
        print(f"   Validation Samples: {val_total}")
    else:
        val_loss = 0
        val_acc = 0
        print("   ⚠️ No validation data (all used for training)")
    
    # PHASE 3: Final Save
    print(f"\n{'='*60}")
    print("💾 SAVING FINAL MODEL")
    print(f"{'='*60}\n")
    
    brain.save_model()
    
    # Save training metadata
    metadata = {
        'training_date': datetime.now().isoformat(),
        'model_version': 'v2',
        'architecture': 'TransformerLSTM',
        'total_chunks': total_chunks_trained,
        'total_sequences_trained': total_sequences,
        'num_features': num_features,
        'avg_train_loss': total_loss_sum / max(total_chunks_trained, 1),
        'val_loss': val_loss,
        'val_accuracy': val_acc,
        'data_files': available,
        'device': str(DEVICE)
    }
    
    with open('models/metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)
    
    # Also save the scaler
    if scaler:
        import joblib
        joblib.dump(scaler, 'models/scaler_v2.pkl')
        # Also update the main scaler
        joblib.dump(scaler, 'models/scaler.pkl')
        print("   ✅ Scaler saved")
    
    print(f"\n{'='*60}")
    print(f"🎉 TRAINING COMPLETE!")
    print(f"   Model: TransformerLSTM V2")
    print(f"   Parameters: {sum(p.numel() for p in model.parameters()):,}")
    print(f"   Chunks Trained: {total_chunks_trained}")
    print(f"   Total Sequences: {total_sequences:,}")
    print(f"   Avg Train Loss: {total_loss_sum / max(total_chunks_trained, 1):.4f}")
    print(f"   Val Accuracy: {val_acc:.2%}")
    print(f"   Saved: models/tradenet_actor.pth")
    print(f"{'='*60}")


if __name__ == "__main__":
    train_v2_memory_efficient()
