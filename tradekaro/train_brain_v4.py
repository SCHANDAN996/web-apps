# train_brain_v4.py
"""
Brain V4 — Time-Series Split + Class Weights
Overfitting Fix: Chronological split, no oversampling, weighted BCE loss.
"""
import sys, os
sys.path.insert(0, '/var/www/tradekaro/Trading_AI_Project')
os.chdir('/var/www/tradekaro/Trading_AI_Project')

import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import joblib
from sklearn.preprocessing import RobustScaler
from sklearn.utils.class_weight import compute_class_weight
from src.brain import SimpleBrainV3, DEVICE
from src.indicators import TechnicalIndicators
from src.data_loader import DataSplitter
from config.feature_config import V4_FEATURES, FEATURE_VERSION

print("=" * 50)
print("🧠 BRAIN V4 — TIME-SERIES TRAINING (Overfitting Fix)")
print("=" * 50)

# ── Step 1: Load ALL data ──
data_files = ["data/NIFTY 50_minute.csv", "data/NIFTY BANK_minute.csv"]
all_dfs = []

for file in data_files:
    if not os.path.exists(file):
        print(f"❌ Missing: {file}")
        continue
    print(f"📂 Loading {file}...")
    df = pd.read_csv(file)
    df.columns = [c.strip().lower() for c in df.columns]
    if 'date' in df.columns:
        df['timestamp'] = pd.to_datetime(df['date'])
    elif 'datetime' in df.columns:
        df['timestamp'] = pd.to_datetime(df['datetime'])
    df.set_index('timestamp', inplace=True)
    df.sort_index(inplace=True)
    
    # Resample to 5min
    df5 = df.resample('5min').agg({
        'open': 'first', 'high': 'max', 'low': 'min',
        'close': 'last', 'volume': 'sum'
    }).dropna()
    
    # Apply indicators
    df5 = TechnicalIndicators.apply_all(df5)
    df5.columns = [c.lower() for c in df5.columns]
    all_dfs.append(df5)
    print(f"   → {len(df5)} candles after indicators")

# ── Step 2: Select features + Scale ──
features = V4_FEATURES

# Collect all raw feature data
all_raw = []
all_close = []
all_high = []
all_low = []
for df5 in all_dfs:
    available = [f for f in features if f in df5.columns]
    raw = np.nan_to_num(df5[available].values, nan=0.0, posinf=1.0, neginf=-1.0)
    all_raw.append(raw)
    all_close.append(df5['close'].values)
    all_high.append(df5['high'].values if 'high' in df5.columns else df5['close'].values)
    all_low.append(df5['low'].values if 'low' in df5.columns else df5['close'].values)

n_features = all_raw[0].shape[1]
print(f"\n📊 Features ({len(features)} total, version {FEATURE_VERSION}): {n_features} → {available}")

# Fit RobustScaler on ALL data
combined_raw = np.concatenate(all_raw, axis=0)
scaler = RobustScaler()
scaler.fit(combined_raw)
joblib.dump(scaler, 'models/scaler.pkl')
print(f"✅ RobustScaler fit on {len(combined_raw)} samples")

# Scale each dataset
all_scaled = [scaler.transform(r) for r in all_raw]

# ── Step 3: Build sequences + Smart Labels ──
lookback = 60
future_horizon = 40
sl_pct = 0.004  # 0.4%
tp_pct = 0.006  # 0.6% (R:R = 1.5)

X_all, Y_all = [], []

for idx, (scaled, close, high, low) in enumerate(zip(all_scaled, all_close, all_high, all_low)):
    print(f"\n🔨 Building sequences from dataset {idx+1}...")
    n_seqs = 0
    n_pos = 0
    
    for i in range(lookback, len(scaled) - future_horizon):
        X_all.append(scaled[i - lookback: i])
        
        # Simple profitable trade label
        entry = close[i]
        if entry <= 0:
            Y_all.append(0)
            continue
        
        profitable = False
        for j in range(1, future_horizon + 1):
            if i + j >= len(high):
                break
            if high[i + j] >= entry * (1 + tp_pct):
                profitable = True
                break
            if low[i + j] <= entry * (1 - sl_pct):
                break
        
        Y_all.append(1 if profitable else 0)
        n_seqs += 1
        if profitable:
            n_pos += 1
    
    print(f"   → {n_seqs} sequences, {n_pos} positive ({n_pos/max(n_seqs,1)*100:.1f}%)")

X = np.array(X_all, dtype=np.float32)
Y = np.array(Y_all, dtype=np.float32)
del X_all, Y_all, all_scaled, combined_raw  # Free memory

print(f"\n📊 Total: {len(X)} sequences, {(Y==1).sum()} positive ({(Y==1).mean()*100:.1f}%)")

# ── Step 4: Time-Series Split (Chronological) ──
print("\n🔄 Splitting data chronologically (No Shuffle)...")
(X_train, y_train), (X_val, y_val), (X_test, y_test) = DataSplitter.split(X, Y, train_ratio=0.70, val_ratio=0.15)

print(f"📊 Train: {len(X_train)} | Val: {len(X_val)} | Test: {len(X_test)}")
print(f"   Train Pos: {(y_train==1).sum()} | Val Pos: {(y_val==1).sum()} | Test Pos: {(y_test==1).sum()}")

# ── Step 5: Class Weights (Oversampling removed) ──
print("\n⚖️ Computing Class Weights for Loss Function...")
class_weights = compute_class_weight('balanced', classes=np.array([0, 1]), y=y_train)
class_weight_tensor = torch.tensor(class_weights, dtype=torch.float).to(DEVICE)
print(f"   Class 0 (HOLD) weight: {class_weights[0]:.4f}")
print(f"   Class 1 (PROFIT) weight: {class_weights[1]:.4f}")

# ── Step 6: Build model + Train ──
model = SimpleBrainV3(input_size=n_features, hidden_size=64).to(DEVICE)
optimizer = optim.Adam(model.parameters(), lr=0.001)
scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=5, factor=0.5)

best_val_loss = float('inf')
patience_counter = 0
EPOCHS = 50
BATCH_SIZE = 256

print(f"\n🚀 Starting training: {EPOCHS} epochs, batch={BATCH_SIZE}")
print("-" * 60)

def weighted_bce_loss(outputs, targets, weights):
    """Manually apply class weights to BCE Loss."""
    outputs = outputs.squeeze()
    targets = targets.squeeze()
    sample_weights = torch.where(targets == 1, weights[1], weights[0])
    loss = nn.functional.binary_cross_entropy(outputs, targets, weight=sample_weights)
    return loss

for epoch in range(EPOCHS):
    # TRAIN
    model.train()
    train_loss = 0
    n_batches = 0
    indices = np.random.permutation(len(X_train))
    
    for start in range(0, len(X_train), BATCH_SIZE):
        end = min(start + BATCH_SIZE, len(X_train))
        bi = indices[start:end]
        
        xb = torch.tensor(X_train[bi], dtype=torch.float32).to(DEVICE)
        yb = torch.tensor(y_train[bi], dtype=torch.float32).unsqueeze(1).to(DEVICE)
        
        optimizer.zero_grad()
        out = model(xb)
        loss = weighted_bce_loss(out, yb, class_weight_tensor)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        
        train_loss += loss.item()
        n_batches += 1
        del xb, yb, out
    
    train_loss /= n_batches
    
    # VALIDATE
    model.eval()
    with torch.no_grad():
        val_preds = []
        for vs in range(0, len(X_val), 512):
            ve = min(vs + 512, len(X_val))
            xv = torch.tensor(X_val[vs:ve], dtype=torch.float32).to(DEVICE)
            val_preds.append(model(xv).cpu().numpy())
            del xv
        val_preds = np.concatenate(val_preds).flatten()
        val_loss = -np.mean(y_val * np.log(np.clip(val_preds, 1e-7, 1)) + 
                           (1 - y_val) * np.log(np.clip(1 - val_preds, 1e-7, 1)))
        val_acc = ((val_preds > 0.5) == y_val).mean()
        
        pred_std = val_preds.std()
        pred_above = (val_preds > 0.5).sum()
    
    scheduler.step(val_loss)
    
    print(f"  Ep{epoch+1:02d}: TrLoss={train_loss:.4f} VlLoss={val_loss:.4f} "
          f"VlAcc={val_acc:.1%} PredStd={pred_std:.4f} >0.5:{pred_above}")
    
    # Early stopping + save best
    if val_loss < best_val_loss:
        best_val_loss = val_loss
        patience_counter = 0
        checkpoint = {
            'model_state': model.state_dict(),
            'input_size': n_features,
            'model_version': 'v4',
            'feature_version': FEATURE_VERSION,
            'timestamp': pd.Timestamp.now().isoformat(),
            'val_loss': val_loss,
            'val_acc': float(val_acc),
            'pred_std': float(pred_std),
            'class_weights': class_weights.tolist()
        }
        torch.save(checkpoint, 'models/tradenet_actor.pth')
        print(f"    ✅ Saved best model (val_loss={val_loss:.4f}, acc={val_acc:.1%})")
    else:
        patience_counter += 1
        if patience_counter >= 12:
            print(f"\n⏹ Early stopping at epoch {epoch+1}")
            break

# ── Final Report ──
print("\n" + "=" * 50)
print("🎉 TRAINING COMPLETE!")
print(f"Best Val Loss: {best_val_loss:.4f}")

# Load best model and test on TEST set
checkpoint = torch.load('models/tradenet_actor.pth', map_location=DEVICE)
model.load_state_dict(checkpoint['model_state'])
model.eval()

with torch.no_grad():
    test_preds = []
    for vs in range(0, len(X_test), 512):
        ve = min(vs + 512, len(X_test))
        xv = torch.tensor(X_test[vs:ve], dtype=torch.float32).to(DEVICE)
        test_preds.append(model(xv).cpu().numpy())
    test_preds = np.concatenate(test_preds).flatten()

test_acc = ((test_preds > 0.5) == y_test).mean()
print(f"\n📊 TEST SET PERFORMANCE (Unseen Data):")
print(f"   Accuracy: {test_acc:.1%}")
print(f"   Pred Spread: min={test_preds.min():.4f} max={test_preds.max():.4f} std={test_preds.std():.4f}")
print(f"   >0.7: {(test_preds>0.7).sum()} | 0.5-0.7: {((test_preds>=0.5)&(test_preds<0.7)).sum()} | <0.3: {(test_preds<0.3).sum()}")

print("=" * 50)
