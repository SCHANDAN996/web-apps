"""
📦 Forex Data Pipeline — Session-Aware Data Preparation
Handles: Loading, resampling, session filtering, label generation.

Labels are 3-class: 0=HOLD, 1=BUY, 2=SELL
Uses SL/TP simulation with dynamic ATR-based levels.
"""

import os
import sys
import numpy as np
import pandas as pd
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from forex_features import (
    compute_all_features, classify_session, is_active_session,
    XGB_FEATURES, GRU_FEATURES, REGIME_FEATURES
)

# ═══════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════
DATA_FILE = 'data/EURUSD_minute.csv'
RESAMPLE_TF = '5min'
LOOKBACK = 60
FUTURE_HORIZON = 60   # 60 × 5min = 5 hours max hold (more time for TP)
SL_ATR_MULT = 1.5     # SL = 1.5 × ATR
TP_ATR_MULT = 2.5     # TP = 2.5 × ATR → 1:1.67 R:R (matched in labels)
MIN_ATR_PIPS = 3      # Skip if ATR too small (illiquid)
MAX_ATR_PIPS = 30     # Skip if ATR too large (news spike)

# EURUSD pip = 0.0001
PIP = 0.0001


def log(msg):
    ts = datetime.now().strftime('%H:%M:%S')
    print(f"[Pipeline {ts}] {msg}", flush=True)


# ═══════════════════════════════════════════════════════════
# STEP 1: LOAD & RESAMPLE
# ═══════════════════════════════════════════════════════════

def load_and_resample(filepath=DATA_FILE, resample=RESAMPLE_TF):
    """Load 1min CSV and resample to 5min."""
    log(f"Loading {filepath}...")

    df = pd.read_csv(filepath)
    df.columns = [c.strip().lower() for c in df.columns]

    # Parse datetime
    if 'datetime' in df.columns:
        df['timestamp'] = pd.to_datetime(df['datetime'], format='%Y%m%d %H%M%S')
    elif 'date' in df.columns:
        df['timestamp'] = pd.to_datetime(df['date'])
    else:
        raise ValueError("No datetime/date column found")

    df.set_index('timestamp', inplace=True)
    df.sort_index(inplace=True)
    log(f"  Raw: {len(df):,} rows, {df.index[0]} → {df.index[-1]}")

    # Resample to 5min
    df5 = df.resample(resample).agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
    }).dropna()

    if 'volume' in df.columns:
        vol = df['volume'].resample(resample).sum()
        df5['volume'] = vol
    else:
        df5['volume'] = 0

    log(f"  Resampled to {resample}: {len(df5):,} rows")
    return df5


# ═══════════════════════════════════════════════════════════
# STEP 2: SESSION FILTER
# ═══════════════════════════════════════════════════════════

def filter_sessions(df, keep_dead=False):
    """Remove dead sessions (Asian, NY close) unless keep_dead=True."""
    if not isinstance(df.index, pd.DatetimeIndex):
        log("  ⚠️ No DatetimeIndex, skipping session filter")
        return df

    before = len(df)
    hours = df.index.hour
    mask = pd.Series([is_active_session(h) for h in hours], index=df.index)

    if keep_dead:
        df_filtered = df.copy()
    else:
        df_filtered = df[mask].copy()

    after = len(df_filtered)
    removed_pct = (1 - after / before) * 100
    log(f"  Session filter: {before:,} → {after:,} ({removed_pct:.0f}% removed)")
    return df_filtered


# ═══════════════════════════════════════════════════════════
# STEP 3: REMOVE WEEKEND GAPS
# ═══════════════════════════════════════════════════════════

def remove_weekends(df):
    """Remove Friday after 21:00 UTC and all of Saturday/Sunday."""
    if not isinstance(df.index, pd.DatetimeIndex):
        return df

    before = len(df)
    # Day of week: Mon=0 ... Sun=6
    dow = df.index.dayofweek
    hour = df.index.hour

    # Keep: Mon-Thu all day + Fri before 21:00
    mask = (dow < 4) | ((dow == 4) & (hour < 21))
    df_clean = df[mask].copy()

    log(f"  Weekend filter: {before:,} → {len(df_clean):,}")
    return df_clean


# ═══════════════════════════════════════════════════════════
# STEP 4: GENERATE 3-CLASS LABELS (BUY / SELL / HOLD)
# ═══════════════════════════════════════════════════════════

def generate_labels(df, future_horizon=FUTURE_HORIZON,
                    sl_mult=SL_ATR_MULT, tp_mult=TP_ATR_MULT):
    """
    Generate 3-class trading labels using SL/TP simulation.

    Labels use the SAME R:R as actual trading (1:1.67) so the model
    learns to predict setups that are ACTUALLY profitable at our R:R.

    For each candle:
    1. Calculate SL = ATR × sl_mult, TP = ATR × tp_mult
    2. Simulate forward: does price hit TP or SL first?
    3. BUY if long TP hit first, SELL if short TP hit first, HOLD otherwise
    
    NO hand-coded trend/ADX filters — let the model learn raw patterns.
    """
    log(f"Generating 3-class labels AND EV continuous labels (label_pips)...")

    labels = np.zeros(len(df), dtype=np.int32)
    label_pips = np.zeros(len(df), dtype=np.float32)
    close = df['close'].values
    high = df['high'].values
    low = df['low'].values
    n = len(df)

    # Get ATR for dynamic SL/TP
    atr = df['atr_14_raw'].values if 'atr_14_raw' in df.columns else np.full(n, 10 * PIP)

    n_buy = 0
    n_sell = 0
    n_hold = 0

    for i in range(n - future_horizon):
        entry = close[i]
        current_atr = atr[i]

        # Skip if ATR is unreasonable
        atr_pips = current_atr / PIP
        if atr_pips < MIN_ATR_PIPS or atr_pips > MAX_ATR_PIPS:
            labels[i] = 0
            n_hold += 1
            continue

        # Asymmetric SL/TP matching actual trading
        sl_dist = current_atr * sl_mult
        tp_dist = current_atr * tp_mult
        
        # 🛑 CRITICAL FIX: Spread-Baked Labels
        # Add a 2-pip spread directly to the entry price so the model learns
        # to only pick setups that can cover the transaction cost.
        SPREAD_VAL = 2.0 * PIP

        # --- Try LONG: TP above, SL below ---
        effective_entry_long = entry + SPREAD_VAL
        tp_long = effective_entry_long + tp_dist
        sl_long = effective_entry_long - sl_dist
        long_won = False
        long_lost = False

        for j in range(1, future_horizon + 1):
            idx = i + j
            if idx >= n:
                break
            if high[idx] >= tp_long:
                long_won = True
                break
            if low[idx] <= sl_long:
                long_lost = True
                break

        # --- Try SHORT: TP below, SL above ---
        effective_entry_short = entry - SPREAD_VAL
        tp_short = effective_entry_short - tp_dist
        sl_short = effective_entry_short + sl_dist
        short_won = False
        short_lost = False

        for j in range(1, future_horizon + 1):
            idx = i + j
            if idx >= n:
                break
            if low[idx] <= tp_short:
                short_won = True
                break
            if high[idx] >= sl_short:
                short_lost = True
                break

        # Assign label — only when ONE direction clearly won
        if long_won and not short_won:
            labels[i] = 1  # BUY — long TP hit, short didn't
            label_pips[i] = tp_dist / PIP
            n_buy += 1
        elif short_won and not long_won:
            labels[i] = 2  # SELL — short TP hit, long didn't
            label_pips[i] = -tp_dist / PIP
            n_sell += 1
        else:
            labels[i] = 0  # HOLD — ambiguous (both hit, neither hit, or timeout)
            n_hold += 1
            
            # For EV Regression, even if it's a HOLD, we can assign the realized loss
            if long_lost and not short_lost:
                label_pips[i] = -sl_dist / PIP
            elif short_lost and not long_lost:
                label_pips[i] = sl_dist / PIP
            else:
                label_pips[i] = 0.0

    # Trim last `future_horizon` candles (no label possible)
    labels[-future_horizon:] = 0
    label_pips[-future_horizon:] = 0.0

    total = n_buy + n_sell + n_hold
    log(f"  Labels: BUY={n_buy:,} ({n_buy/total*100:.1f}%) | "
        f"SELL={n_sell:,} ({n_sell/total*100:.1f}%) | "
        f"HOLD={n_hold:,} ({n_hold/total*100:.1f}%)")

    df['label'] = labels
    df['label_pips'] = label_pips
    return df


# ═══════════════════════════════════════════════════════════
# STEP 5: GENERATE REGIME LABELS (for Model 3 training)
# ═══════════════════════════════════════════════════════════

def generate_regime_labels(df):
    """
    Generate regime labels for training Model 3.
    Uses forward-looking data to create 'true' regime labels.

    0 = RANGING (low future movement)
    1 = TRENDING (strong directional move)
    2 = VOLATILE (large ATR spike, mean-reverting)
    """
    close = df['close'].values
    atr = df['atr_14_raw'].values if 'atr_14_raw' in df.columns else np.full(len(df), 10 * PIP)
    n = len(df)

    regime_labels = np.zeros(n, dtype=np.int32)
    window = 20

    for i in range(window, n - window):
        future_close = close[i:i + window]
        future_range = future_close.max() - future_close.min()
        current_atr = atr[i]

        # Normalize future range by ATR
        range_ratio = future_range / (current_atr * window + 1e-10)

        if atr[i] > np.mean(atr[max(0, i - 50):i]) * 2.0:
            regime_labels[i] = 2  # VOLATILE
        elif range_ratio > 0.15:
            regime_labels[i] = 1  # TRENDING
        else:
            regime_labels[i] = 0  # RANGING

    df['regime_label'] = regime_labels
    return df


# ═══════════════════════════════════════════════════════════
# STEP 6: BUILD SEQUENCES (for GRU Model 2)
# ═══════════════════════════════════════════════════════════

def build_sequences(df, features, lookback=LOOKBACK):
    """Build (X, y) sequences for GRU training."""
    available = [f for f in features if f in df.columns]
    if len(available) < len(features):
        missing = set(features) - set(available)
        log(f"  ⚠️ Missing GRU features: {missing}")

    data = df[available].values.astype(np.float32)
    labels = df['label'].values

    n = len(data)
    num_seq = n - lookback
    if num_seq <= 0:
        return np.array([]), np.array([])

    idx = np.arange(lookback)[None, :] + np.arange(num_seq)[:, None]
    X = data[idx]
    y = labels[lookback:]

    return X, y


# ═══════════════════════════════════════════════════════════
# MASTER PIPELINE
# ═══════════════════════════════════════════════════════════

def run_pipeline(filepath=DATA_FILE, resample=RESAMPLE_TF):
    """
    Complete data pipeline: Load → Resample → Filter → Features → Labels.
    Returns prepared DataFrame with all features and labels.
    """
    log("=" * 50)
    log("🚀 FOREX DATA PIPELINE STARTING")
    log("=" * 50)

    # Step 1: Load & Resample
    df = load_and_resample(filepath, resample)

    # Step 2: Remove weekends
    df = remove_weekends(df)

    # Step 3: Compute features (before session filter, so ATR etc. are accurate)
    df = compute_all_features(df)
    log(f"  Features computed: {len(df.columns)} columns, {len(df):,} rows")

    # Step 4: Session filter (remove dead hours)
    df = filter_sessions(df, keep_dead=False)

    # Step 5: Generate labels
    df = generate_labels(df)

    # Step 6: Generate regime labels
    df = generate_regime_labels(df)

    log(f"\n✅ Pipeline complete: {len(df):,} rows, {len(df.columns)} columns")
    log(f"   Date range: {df.index[0]} → {df.index[-1]}")

    return df


def split_data(df, train_ratio=0.70, val_ratio=0.15):
    """Chronological train/val/test split (NO shuffling)."""
    n = len(df)
    train_end = int(n * train_ratio)
    val_end = int(n * (train_ratio + val_ratio))

    train = df.iloc[:train_end]
    val = df.iloc[train_end:val_end]
    test = df.iloc[val_end:]

    log(f"  Split: Train={len(train):,} | Val={len(val):,} | Test={len(test):,}")
    return train, val, test


if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    df = run_pipeline()
    train, val, test = split_data(df)
    print(f"\nSample features:\n{df[XGB_FEATURES[:5]].tail()}")
    print(f"\nLabel distribution:\n{df['label'].value_counts()}")
