"""
🌍 FOREX Brain Trainer — EURUSD Dedicated Model
Separate from Indian market (NIFTY/BN) model.
Features: CPU capping, chunked training, progress logging to DB for UI.
"""

import os
import sys
import time
import psutil
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from datetime import datetime

sys.path.append(os.path.dirname(__file__))
from src.brain import SimpleBrainV3, DEVICE
from src.database import TradingDB

# ============================================================
# CONFIG
# ============================================================
DATA_FILE = 'data/EURUSD_minute.csv'
MODEL_PATH = 'models/forex_brain_eurusd.pth'
LOOKBACK = 60
CHUNK_SIZE = 50000
BATCH_SIZE = 512
EPOCHS_PER_CHUNK = 2
CPU_LIMIT = 95
FEATURES = ['open', 'high', 'low', 'close',
            'rsi', 'ema_fast', 'ema_slow', 'atr',
            'macd', 'macd_signal', 'bb_upper', 'bb_lower',
            'returns', 'volatility']

db = TradingDB()


def log(msg):
    ts = datetime.now().strftime('%H:%M:%S')
    print(f"[FOREX {ts}] {msg}", flush=True)
    try:
        db.log_thought(f"🌍 {msg}")
    except:
        pass


def cpu_gate():
    """Check CPU once — sleep 2s if over limit."""
    if psutil.cpu_percent(interval=0) > CPU_LIMIT:
        time.sleep(2)


def add_indicators(df):
    c = df['close']
    delta = c.diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    df['rsi'] = 100 - (100 / (1 + gain / (loss + 1e-10)))
    df['ema_fast'] = c.ewm(span=9).mean()
    df['ema_slow'] = c.ewm(span=21).mean()
    hl = df['high'] - df['low']
    hc = (df['high'] - c.shift()).abs()
    lc = (df['low'] - c.shift()).abs()
    df['atr'] = pd.concat([hl, hc, lc], axis=1).max(axis=1).rolling(14).mean()
    e12 = c.ewm(span=12).mean()
    e26 = c.ewm(span=26).mean()
    df['macd'] = e12 - e26
    df['macd_signal'] = df['macd'].ewm(span=9).mean()
    sma = c.rolling(20).mean()
    std = c.rolling(20).std()
    df['bb_upper'] = sma + 2 * std
    df['bb_lower'] = sma - 2 * std
    df['returns'] = c.pct_change()
    df['volatility'] = df['returns'].rolling(20).std()
    for col in ['open', 'high', 'low', 'bb_upper', 'bb_lower', 'ema_fast', 'ema_slow']:
        df[col] = (df[col] - c) / (c + 1e-10)
    df['close'] = c.pct_change()
    df.dropna(inplace=True)
    df.replace([np.inf, -np.inf], 0, inplace=True)
    return df


def create_sequences(df, lookback=60):
    data = df[FEATURES].values.astype(np.float32)
    closes = df['close'].values
    n = len(data)
    num_seq = n - lookback - 5
    if num_seq <= 0:
        return np.array([]), np.array([])
    idx = np.arange(lookback)[None, :] + np.arange(num_seq)[:, None]
    X = data[idx]
    future_idx = np.arange(lookback, lookback + num_seq)
    y = (closes[future_idx + 5] > closes[future_idx]).astype(np.float32)
    return X, y


def load_or_build_model(input_size):
    if os.path.exists(MODEL_PATH):
        try:
            ckpt = torch.load(MODEL_PATH, map_location=DEVICE, weights_only=False)
            model = SimpleBrainV3(input_size=ckpt.get('input_size', input_size)).to(DEVICE)
            model.load_state_dict(ckpt['model_state'])
            log(f"✅ Loaded existing FOREX model")
            return model, ckpt.get('input_size', input_size)
        except Exception as e:
            log(f"⚠️ Load failed: {e}")
    log(f"🔨 Building NEW FOREX model ({input_size} features)")
    return SimpleBrainV3(input_size=input_size).to(DEVICE), input_size


def save_model(model, input_size, info=""):
    os.makedirs('models', exist_ok=True)
    torch.save({
        'input_size': input_size,
        'model_state': model.state_dict(),
        'model_version': 'v3',
        'model_type': 'FOREX_EURUSD',
        'timestamp': datetime.now().isoformat(),
        'info': info
    }, MODEL_PATH)


def train():
    log("=" * 40)
    log("🚀 FOREX Training Starting (EURUSD)")
    log(f"   CPU Limit: {CPU_LIMIT}% | Chunk: {CHUNK_SIZE}")
    log("=" * 40)

    if not os.path.exists(DATA_FILE):
        log(f"❌ File not found: {DATA_FILE}")
        return

    total_rows = sum(1 for _ in open(DATA_FILE)) - 1
    total_chunks = (total_rows // CHUNK_SIZE) + 1
    log(f"📊 {total_rows:,} rows | {total_chunks} chunks")

    model, input_size = load_or_build_model(len(FEATURES))
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    criterion = nn.BCELoss()

    chunk_num = 0
    total_trained = 0
    last_loss = 0

    for chunk_df in pd.read_csv(DATA_FILE, chunksize=CHUNK_SIZE):
        chunk_num += 1
        cpu_gate()

        chunk_df.columns = [c.strip().lower() for c in chunk_df.columns]

        try:
            chunk_df = add_indicators(chunk_df)
        except:
            continue

        if len(chunk_df) < LOOKBACK + 10:
            continue

        X, y = create_sequences(chunk_df, LOOKBACK)
        if len(X) == 0:
            continue

        if X.shape[2] != input_size:
            input_size = X.shape[2]
            model = SimpleBrainV3(input_size=input_size).to(DEVICE)
            optimizer = optim.Adam(model.parameters(), lr=0.001)

        # Train
        model.train()
        n = len(X)
        for epoch in range(EPOCHS_PER_CHUNK):
            indices = np.random.permutation(n)
            for start in range(0, n, BATCH_SIZE):
                end = min(start + BATCH_SIZE, n)
                bi = indices[start:end]
                xb = torch.tensor(X[bi], dtype=torch.float32).to(DEVICE)
                yb = torch.tensor(y[bi], dtype=torch.float32).unsqueeze(1).to(DEVICE)
                xb = torch.nan_to_num(xb, nan=0.0, posinf=1.0, neginf=-1.0)

                optimizer.zero_grad()
                out = model(xb)
                loss = criterion(out, yb)
                loss.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                optimizer.step()
                last_loss = loss.item()

                del xb, yb, out

            # CPU gate once per epoch
            cpu_gate()

        total_trained += n
        pct = round((chunk_num / total_chunks) * 100, 1)
        log(f"✅ Chunk {chunk_num}/{total_chunks} | Loss: {last_loss:.4f} | Samples: {n:,} | {pct}%")

        # Save every 5 chunks
        if chunk_num % 5 == 0:
            save_model(model, input_size, f"chunk_{chunk_num}")

        del X, y, chunk_df

    model.eval()
    save_model(model, input_size, "complete")
    log(f"🎉 DONE! Total: {total_trained:,} samples | Loss: {last_loss:.4f}")


if __name__ == '__main__':
    train()
