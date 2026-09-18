"""
🧠 TradeKaro AI — Live Training (Memory-Optimized)
Trains TransformerLSTM Brain on market data with mini-batches to prevent OOM.

Usage:
    python live_train.py              # Full training
    python live_train.py --continuous # 4-hour loop
"""

import sys
import os
import gc
import time
import numpy as np
import pandas as pd
import torch
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.brain import TradingBrain, DEVICE
from src.indicators import TechnicalIndicators
from src.data_loader import SequenceBuilder
from src.feature_store import FEATURES_V2
import config.settings as settings

# Memory-safe settings
CHUNK_SIZE = 5000      # Process 5K candles at a time
BATCH_SIZE = 32        # Mini-batch size for gradient updates
MAX_ROWS = 50000       # Max rows to load per file
EPOCHS_PER_CHUNK = 3   # Epochs per chunk


def load_csv(filepath, max_rows=MAX_ROWS):
    """Load and standardize CSV data."""
    print(f"  📂 Loading: {os.path.basename(filepath)} (max {max_rows} rows)")
    df = pd.read_csv(filepath, nrows=max_rows)
    df.columns = [c.strip().lower() for c in df.columns]

    rename = {}
    for c in df.columns:
        if 'open' in c: rename[c] = 'open'
        elif 'high' in c: rename[c] = 'high'
        elif 'low' in c and 'close' not in c: rename[c] = 'low'
        elif 'close' in c and 'adj' not in c: rename[c] = 'close'
        elif 'volume' in c or 'vol' in c: rename[c] = 'volume'
    df = df.rename(columns=rename)

    for col in ['open', 'high', 'low', 'close']:
        if col not in df.columns:
            print(f"    ❌ Missing '{col}', skipping")
            return None
    if 'volume' not in df.columns:
        df['volume'] = 0

    df = df.dropna(subset=['open', 'high', 'low', 'close'])
    print(f"    ✅ {len(df)} candles loaded")
    return df


def train_mini_batch(brain, X_all, y_all, epochs=3, batch_size=32):
    """Mini-batch training to prevent OOM."""
    brain.model.train()

    for epoch in range(epochs):
        indices = np.random.permutation(len(X_all))
        total_loss = 0
        n_batches = 0

        for start in range(0, len(indices), batch_size):
            batch_idx = indices[start:start + batch_size]
            X_batch = torch.tensor(X_all[batch_idx], dtype=torch.float32).to(DEVICE)
            y_batch = torch.tensor(y_all[batch_idx], dtype=torch.float32).unsqueeze(1).to(DEVICE)

            brain.optimizer.zero_grad()
            outputs = brain.model(X_batch)
            loss = brain.criterion(outputs, y_batch)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(brain.model.parameters(), max_norm=1.0)
            brain.optimizer.step()

            total_loss += loss.item()
            n_batches += 1

            # Free GPU/CPU memory
            del X_batch, y_batch, outputs, loss
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

        avg_loss = total_loss / max(n_batches, 1)
        if epoch == epochs - 1:
            print(f"      Loss: {avg_loss:.4f} ({n_batches} batches)")

    # Explicit cleanup
    gc.collect()


def run_training():
    """Train on all available CSV files."""
    print(f"\n{'=' * 50}")
    print(f"🧠 TRADEKARO AI — LIVE TRAINING")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"💻 Device: {DEVICE} | Chunk: {CHUNK_SIZE} | Batch: {BATCH_SIZE}")
    print(f"{'=' * 50}\n")

    brain = TradingBrain(input_features=len(FEATURES_V2), seq_length=settings.LOOKBACK_PERIOD)
    seq_builder = SequenceBuilder(lookback=settings.LOOKBACK_PERIOD, future_horizon=5, threshold=0.001)

    data_files = [os.path.join('data', f) for f in os.listdir('data') if f.endswith('.csv')]
    if not data_files:
        print("❌ No CSV files found!"); return 0

    print(f"📂 {len(data_files)} files found\n")
    total_samples = 0
    start = time.time()

    for i, fpath in enumerate(data_files, 1):
        symbol = os.path.basename(fpath).replace('_minute.csv', '').replace('.csv', '')
        print(f"[{i}/{len(data_files)}] 🏋️ Training: {symbol}")

        df = load_csv(fpath)
        if df is None:
            continue

        file_samples = 0

        # Process in small chunks
        for chunk_start in range(0, len(df), CHUNK_SIZE):
            chunk = df.iloc[chunk_start:chunk_start + CHUNK_SIZE].copy()
            if len(chunk) < 200:
                continue

            try:
                df_rich = TechnicalIndicators.apply_multi_timeframe_features(chunk)
                if df_rich.empty or len(df_rich) < 80:
                    continue

                X, y, _ = seq_builder.build_sequences(df_rich, FEATURES_V2)
                if len(X) == 0:
                    continue

                # Check feature dimension
                current_dim = brain._get_input_size()
                new_dim = X.shape[2]
                if current_dim != new_dim:
                    print(f"    ⚙️ Feature rebuild: {current_dim} → {new_dim}")
                    if brain.use_v2:
                        from src.brain import TransformerLSTM
                        brain.model = TransformerLSTM(input_size=new_dim).to(DEVICE)
                    else:
                        from src.brain import LSTMModel
                        brain.model = LSTMModel(input_size=new_dim).to(DEVICE)
                    brain.optimizer = torch.optim.AdamW(brain.model.parameters(), lr=0.001, weight_decay=1e-4)
                    brain.input_features = new_dim

                # Mini-batch training
                train_mini_batch(brain, X, y, epochs=EPOCHS_PER_CHUNK, batch_size=BATCH_SIZE)
                file_samples += len(X)

                # Memory cleanup after each chunk
                del X, y, df_rich, chunk
                gc.collect()

            except Exception as e:
                print(f"    ⚠️ Chunk error: {str(e)[:60]}")
                gc.collect()
                continue

        total_samples += file_samples
        print(f"  ✅ {symbol}: {file_samples} samples\n")

        # Save checkpoint after each file
        brain.save_model()
        gc.collect()

    elapsed = time.time() - start

    print(f"{'=' * 50}")
    print(f"🏁 TRAINING COMPLETE!")
    print(f"⏱️ {elapsed:.0f}s ({elapsed/60:.1f} min)")
    print(f"📊 {total_samples:,} total samples")
    print(f"💾 Model: models/tradenet_actor.pth ({os.path.getsize('models/tradenet_actor.pth')/(1024*1024):.1f} MB)")
    print(f"{'=' * 50}\n")
    return total_samples


def main():
    if '--continuous' in sys.argv:
        print("🔄 CONTINUOUS MODE — every 4 hours")
        cycle = 0
        while True:
            cycle += 1
            print(f"\n### CYCLE {cycle} ###")
            try:
                run_training()
            except Exception as e:
                print(f"❌ Cycle {cycle} error: {e}")
            print(f"💤 Sleeping 4 hours...\n")
            time.sleep(4 * 3600)
    else:
        run_training()


if __name__ == '__main__':
    main()
