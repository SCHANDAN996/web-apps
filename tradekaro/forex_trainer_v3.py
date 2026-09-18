"""
🏋️ Forex Master Trainer V3 — Trains All 4 Council Models
One command to train everything with walk-forward validation.

Usage:
    cd /var/www/tradekaro/Trading_AI_Project
    ./venv/bin/python forex_trainer_v3.py
"""

import os
import sys
import time
import gc
import numpy as np
import pandas as pd
from datetime import datetime
from sklearn.preprocessing import RobustScaler
import joblib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from forex_features import (
    XGB_FEATURES, GRU_FEATURES, REGIME_FEATURES, RISK_FEATURES,
    compute_all_features, get_model_features
)
from forex_data_pipeline import (
    load_and_resample, remove_weekends, filter_sessions,
    generate_labels, generate_regime_labels, build_sequences, split_data
)
from forex_model_regime import RegimeDetector
from forex_model_xgb import EVRegressor
from forex_model_gru import SequencePredictor
from forex_model_risk import RiskEstimator
from forex_council import ForexCouncil

SCALER_PATH = 'models/forex_scaler.pkl'
PIP = 0.0001


def log(msg):
    ts = datetime.now().strftime('%H:%M:%S')
    print(f"[Trainer {ts}] {msg}", flush=True)


def train_all():
    """Master training pipeline for all 4 council models."""
    start_time = time.time()

    log("=" * 60)
    log("🏛️ FOREX COUNCIL — MASTER TRAINING V3")
    log("=" * 60)

    # ═══════════════════════════════════════════════════════════
    # STEP 1: DATA PIPELINE
    # ═══════════════════════════════════════════════════════════
    log("\n📦 STEP 1: Data Pipeline")
    log("-" * 40)

    df = load_and_resample()
    df = remove_weekends(df)
    df = compute_all_features(df)

    log(f"  Features: {len(df.columns)} columns, {len(df):,} rows")

    # Session filter for training (keep dead=False for training)
    df = filter_sessions(df, keep_dead=False)

    # Generate labels
    df = generate_labels(df)
    df = generate_regime_labels(df)

    # Split chronologically
    train_df, val_df, test_df = split_data(df)

    # ── Scale features ──
    log("\n  Fitting RobustScaler...")
    xgb_cols = [c for c in XGB_FEATURES if c in train_df.columns]
    gru_cols = [c for c in GRU_FEATURES if c in train_df.columns]
    regime_cols = [c for c in REGIME_FEATURES if c in train_df.columns]
    risk_cols = [c for c in RISK_FEATURES if c in train_df.columns]

    # Fit scaler on all numeric features from training data
    all_feature_cols = list(set(xgb_cols + gru_cols + regime_cols + risk_cols))
    scaler = RobustScaler()
    scaler.fit(train_df[all_feature_cols].values)
    joblib.dump({'scaler': scaler, 'columns': all_feature_cols}, SCALER_PATH)
    log(f"  Scaler fitted on {len(all_feature_cols)} features")

    # Scale all splits
    def scale_features(split_df, cols):
        """Scale specific columns using fitted scaler."""
        # Map columns to scaler indices
        col_indices = [all_feature_cols.index(c) for c in cols if c in all_feature_cols]
        all_scaled = scaler.transform(split_df[all_feature_cols].values)
        result = np.zeros((len(split_df), len(cols)), dtype=np.float32)
        for i, c in enumerate(cols):
            if c in all_feature_cols:
                result[:, i] = all_scaled[:, all_feature_cols.index(c)]
            else:
                result[:, i] = split_df[c].values if c in split_df.columns else 0
        return np.nan_to_num(result, nan=0.0, posinf=1.0, neginf=-1.0)

    # Prepare data for each model
    X_train_xgb = scale_features(train_df, xgb_cols)
    X_val_xgb = scale_features(val_df, xgb_cols)
    X_test_xgb = scale_features(test_df, xgb_cols)

    X_train_regime = scale_features(train_df, regime_cols)
    X_val_regime = scale_features(val_df, regime_cols)

    X_train_risk = scale_features(train_df, risk_cols)
    X_val_risk = scale_features(val_df, risk_cols)

    y_train = train_df['label'].values
    y_val = val_df['label'].values
    y_test = test_df['label'].values
    
    y_train_pips = train_df['label_pips'].values
    y_val_pips = val_df['label_pips'].values
    y_test_pips = test_df['label_pips'].values

    y_train_regime = train_df['regime_label'].values
    y_val_regime = val_df['regime_label'].values

    # Risk target = actual ATR
    y_train_risk = train_df['atr_14_raw'].values if 'atr_14_raw' in train_df.columns else np.full(len(train_df), 10 * PIP)
    y_val_risk = val_df['atr_14_raw'].values if 'atr_14_raw' in val_df.columns else np.full(len(val_df), 10 * PIP)

    log(f"\n  Data ready (before balancing):")
    log(f"    Train: {len(train_df):,} | Val: {len(val_df):,} | Test: {len(test_df):,}")
    log(f"    XGB features: {len(xgb_cols)} | GRU features: {len(gru_cols)}")
    log(f"    Labels — BUY: {(y_train==1).sum():,} | SELL: {(y_train==2).sum():,} | HOLD: {(y_train==0).sum():,}")

    # ── CLASS BALANCING: Not used for EV Regression ──
    # For Expected Value regression, we must train on the TRUE distribution, 
    # otherwise the model will artificially overestimate expected profits.
    # We will ONLY balance classes for the Sequence Predictor later.
    log(f"    Total train samples (unbalanced): {len(y_train):,}")

    # ═══════════════════════════════════════════════════════════
    # STEP 2: TRAIN MODEL 3 — REGIME DETECTOR
    # ═══════════════════════════════════════════════════════════
    log("\n🌲 STEP 2: Training Regime Detector (Random Forest)")
    log("-" * 40)

    # Subsample regime data for speed (100K is plenty for RF)
    if len(X_train_regime) > 100000:
        ridx = np.random.choice(len(X_train_regime), 100000, replace=False)
        X_train_regime_sub = X_train_regime[ridx]
        y_train_regime_sub = y_train_regime[ridx]
    else:
        X_train_regime_sub = X_train_regime
        y_train_regime_sub = y_train_regime

    regime_model = RegimeDetector()
    regime_model.train(X_train_regime_sub, y_train_regime_sub,
                       X_val_regime, y_val_regime,
                       feature_names=regime_cols)
    regime_model.save()
    gc.collect()

    # ═══════════════════════════════════════════════════════════
    # STEP 2.5: HYBRID OPTION B — TRANSFORMER FEATURES
    # ═══════════════════════════════════════════════════════════
    log("\n🤖 STEP 2.5: Augmenting with Transformer Features (Option B)")
    log("-" * 40)
    
    seq_model = SequencePredictor()
    if seq_model.load():
        log("  Loaded pre-trained Causal Transformer.")
        
        log("  Building 60-bar sequences for feature augmentation...")
        X_train_gru_seq, _ = build_sequences(
            _make_scaled_df(train_df, gru_cols, scaler, all_feature_cols), gru_cols)
        X_val_gru_seq, _ = build_sequences(
            _make_scaled_df(val_df, gru_cols, scaler, all_feature_cols), gru_cols)
            
        log("  Predicting Transformer probabilities...")
        tf_train_probs = seq_model.predict_proba(X_train_gru_seq)
        tf_val_probs = seq_model.predict_proba(X_val_gru_seq)
        
        # Align tabular features (drop first 60 bars)
        X_train_xgb = X_train_xgb[60:]
        y_train_pips = y_train_pips[60:]
        X_val_xgb = X_val_xgb[60:]
        y_val_pips = y_val_pips[60:]
        X_train_risk = X_train_risk[60:]
        y_train_risk = y_train_risk[60:]
        X_val_risk = X_val_risk[60:]
        y_val_risk = y_val_risk[60:]
        
        # Append tf_prob_buy and tf_prob_sell
        X_train_xgb = np.hstack((X_train_xgb, tf_train_probs[:, 1:3]))
        X_val_xgb = np.hstack((X_val_xgb, tf_val_probs[:, 1:3]))
        xgb_cols = xgb_cols + ['tf_prob_buy', 'tf_prob_sell']
        
        log(f"  Added 2 Transformer features. Total XGB features: {len(xgb_cols)}")
    else:
        log("  ⚠️ Failed to load Transformer! Skipping Option B augmentation.")

    # ═══════════════════════════════════════════════════════════
    # STEP 3: TRAIN MODEL 1 — XGBOOST DIRECTION
    # ═══════════════════════════════════════════════════════════
    log("\n🧠 STEP 3: Training XGBoost EV Regressor")
    log("-" * 40)

    xgb_model = EVRegressor()
    xgb_model.train(X_train_xgb, y_train_pips,
                    X_val_xgb, y_val_pips,
                    feature_names=xgb_cols)
    xgb_model.save()
    gc.collect()
    
    log("\n🏁 Stopping early after XGBoost EV Custom Loss training.")
    import sys
    sys.exit(0)

    # ═══════════════════════════════════════════════════════════
    # STEP 4: TRAIN MODEL 2 — GRU SEQUENCE
    # ═══════════════════════════════════════════════════════════
    log("\n🎯 STEP 4: Training GRU Sequence Predictor")
    log("-" * 40)

    # Build GRU sequences
    log("  Building 60-bar sequences for GRU...")

    # Scale GRU features separately for sequence building
    X_train_gru_seq, y_train_gru_seq = build_sequences(
        _make_scaled_df(train_df, gru_cols, scaler, all_feature_cols),
        gru_cols
    )
    X_val_gru_seq, y_val_gru_seq = build_sequences(
        _make_scaled_df(val_df, gru_cols, scaler, all_feature_cols),
        gru_cols
    )

    log(f"  GRU sequences (raw): Train={len(X_train_gru_seq):,} | Val={len(X_val_gru_seq):,}")

    # ── SUBSAMPLE GRU for CPU training speed ──
    # With balanced labels, we have ~380K BUY+SELL. Cap to 150K total for CPU.
    MAX_GRU_SAMPLES = 150000
    if len(X_train_gru_seq) > MAX_GRU_SAMPLES:
        buy_idx = np.where(y_train_gru_seq == 1)[0]
        sell_idx = np.where(y_train_gru_seq == 2)[0]
        hold_idx = np.where(y_train_gru_seq == 0)[0]

        # Equal samples per class (balanced training)
        per_class = MAX_GRU_SAMPLES // 3
        buy_keep = np.random.choice(buy_idx, min(per_class, len(buy_idx)), replace=False)
        sell_keep = np.random.choice(sell_idx, min(per_class, len(sell_idx)), replace=False)
        hold_keep = np.random.choice(hold_idx, min(per_class, len(hold_idx)), replace=False)

        keep_idx = np.concatenate([buy_keep, sell_keep, hold_keep])
        np.random.shuffle(keep_idx)
        X_train_gru_seq = X_train_gru_seq[keep_idx]
        y_train_gru_seq = y_train_gru_seq[keep_idx]
        log(f"  GRU subsampled: {len(X_train_gru_seq):,} (BUY={len(buy_keep):,} SELL={len(sell_keep):,} HOLD={len(hold_keep):,})")

    # Val also subsample for speed
    if len(X_val_gru_seq) > 30000:
        vidx = np.random.choice(len(X_val_gru_seq), 30000, replace=False)
        X_val_gru_seq = X_val_gru_seq[vidx]
        y_val_gru_seq = y_val_gru_seq[vidx]

    if len(X_train_gru_seq) > 0:
        gru_model = SequencePredictor(
            input_size=X_train_gru_seq.shape[2],
            hidden_size=128,
            num_classes=3
        )
        # gru_model.train(X_train_gru_seq, y_train_gru_seq,
        #                 X_val_gru_seq, y_val_gru_seq,
        #                 epochs=30, batch_size=256, patience=10)
        # gru_model.save()
        log("  [GRU skipped for EV testing]")
    else:
        log("  ⚠️ No GRU sequences generated!")
    gc.collect()

    # ═══════════════════════════════════════════════════════════
    # STEP 5: TRAIN MODEL 4 — RISK ESTIMATOR
    # ═══════════════════════════════════════════════════════════
    log("\n📐 STEP 5: Training Risk Estimator (XGBoost)")
    log("-" * 40)

    risk_model = RiskEstimator(sl_mult=1.5, tp_mult=2.5)
    risk_model.train(X_train_risk, y_train_risk,
                     X_val_risk, y_val_risk,
                     feature_names=risk_cols)
    risk_model.save()
    gc.collect()

    # ═══════════════════════════════════════════════════════════
    # STEP 6: COUNCIL VALIDATION ON TEST SET
    # ═══════════════════════════════════════════════════════════
    log("\n⚖️ STEP 6: Council Validation (Test Set)")
    log("-" * 40)

    council = ForexCouncil(min_confidence=0.35)  # 3-class: 0.33 is random
    council.load_all()

    # Run council on test set
    if len(X_test_xgb) > 0:
        _validate_council(council, test_df, xgb_cols, gru_cols,
                          regime_cols, risk_cols, scaler, all_feature_cols)

    # ═══════════════════════════════════════════════════════════
    # DONE
    # ═══════════════════════════════════════════════════════════
    elapsed = time.time() - start_time
    log("\n" + "=" * 60)
    log(f"🎉 TRAINING COMPLETE!")
    log(f"⏱️  Total time: {elapsed:.0f}s ({elapsed/60:.1f} min)")
    log(f"📁 Models saved in models/")
    log("=" * 60)


def _balance_classes(X, y, hold_ratio=3.0):
    """Undersample HOLD class to hold_ratio × minority for balanced training."""
    buy_idx = np.where(y == 1)[0]
    sell_idx = np.where(y == 2)[0]
    hold_idx = np.where(y == 0)[0]

    minority_count = max(len(buy_idx), len(sell_idx))
    n_hold_keep = int(minority_count * hold_ratio)
    n_hold_keep = min(n_hold_keep, len(hold_idx))

    hold_keep = np.random.choice(hold_idx, n_hold_keep, replace=False)
    keep_idx = np.concatenate([buy_idx, sell_idx, hold_keep])
    np.random.shuffle(keep_idx)

    return X[keep_idx], y[keep_idx]


def _make_scaled_df(df, cols, scaler, all_cols):
    """Create a DataFrame with scaled features for sequence building."""
    scaled_all = scaler.transform(df[all_cols].values)
    result = df.copy()
    for i, c in enumerate(all_cols):
        if c in cols:
            result[c] = scaled_all[:, i]
    return result


def _validate_council(council, test_df, xgb_cols, gru_cols,
                      regime_cols, risk_cols, scaler, all_cols):
    """Run council decisions on test set and report metrics."""
    from forex_data_pipeline import build_sequences, LOOKBACK

    # Prepare test data
    X_test_xgb = np.nan_to_num(
        scaler.transform(test_df[all_cols].values),
        nan=0.0, posinf=1.0, neginf=-1.0
    )
    # Map to xgb feature indices
    xgb_idx = [all_cols.index(c) for c in xgb_cols if c in all_cols]
    regime_idx = [all_cols.index(c) for c in regime_cols if c in all_cols]
    risk_idx = [all_cols.index(c) for c in risk_cols if c in all_cols]

    X_xgb = X_test_xgb[:, xgb_idx]
    X_regime = X_test_xgb[:, regime_idx]
    X_risk = X_test_xgb[:, risk_idx]

    # GRU sequences
    scaled_df = _make_scaled_df(test_df, gru_cols, scaler, all_cols)
    X_gru, y_gru = build_sequences(scaled_df, gru_cols, LOOKBACK)

    if len(X_gru) == 0:
        log("  ⚠️ Not enough test data for GRU sequences")
        return

    # Align arrays (GRU starts at index LOOKBACK)
    n = min(len(X_gru), len(X_xgb) - LOOKBACK)
    X_xgb = X_xgb[LOOKBACK:LOOKBACK + n]
    X_regime = X_regime[LOOKBACK:LOOKBACK + n]
    X_risk = X_risk[LOOKBACK:LOOKBACK + n]
    X_gru = X_gru[:n]

    close = test_df['close'].values[LOOKBACK:LOOKBACK + n]
    high = test_df['high'].values[LOOKBACK:LOOKBACK + n]
    low = test_df['low'].values[LOOKBACK:LOOKBACK + n]
    hours = test_df.index.hour[LOOKBACK:LOOKBACK + n] if hasattr(test_df.index, 'hour') else np.full(n, 12)
    labels = test_df['label'].values[LOOKBACK:LOOKBACK + n]

    # Get batch decisions
    decisions = council.decide_batch(X_xgb, X_gru, X_regime, X_risk, hours, close)

    # Simulate trades
    trades = []
    for i, dec in enumerate(decisions):
        if dec['action'] != 'TRADE':
            continue
        if i + 40 >= n:
            continue

        entry = close[i]
        sl_dist = dec['sl_dist']
        tp_dist = dec['tp_dist']
        direction = dec['direction']

        # Simulate forward
        won = False
        lost = False
        for j in range(1, 41):
            idx = i + j
            if idx >= n:
                break
            if direction == 'BUY':
                if high[idx] >= entry + tp_dist:
                    won = True
                    break
                if low[idx] <= entry - sl_dist:
                    lost = True
                    break
            else:  # SELL
                if low[idx] <= entry - tp_dist:
                    won = True
                    break
                if high[idx] >= entry + sl_dist:
                    lost = True
                    break

        trades.append({
            'direction': direction,
            'won': won,
            'pnl_pips': tp_dist / PIP if won else (-sl_dist / PIP if lost else 0),
            'confidence': dec['confidence']
        })

    # Report
    if trades:
        n_trades = len(trades)
        wins = sum(1 for t in trades if t['won'])
        wr = wins / n_trades * 100
        total_pnl = sum(t['pnl_pips'] for t in trades)
        avg_win = np.mean([t['pnl_pips'] for t in trades if t['won']]) if wins else 0
        avg_loss = np.mean([abs(t['pnl_pips']) for t in trades if not t['won'] and t['pnl_pips'] < 0]) if (n_trades - wins) > 0 else 1
        pf = (sum(t['pnl_pips'] for t in trades if t['won']) /
              abs(sum(t['pnl_pips'] for t in trades if t['pnl_pips'] < 0)) if
              sum(t['pnl_pips'] for t in trades if t['pnl_pips'] < 0) != 0 else float('inf'))
        expectancy = (wr / 100 * avg_win) - ((100 - wr) / 100 * avg_loss)

        buys = sum(1 for t in trades if t['direction'] == 'BUY')
        sells = n_trades - buys
        buy_wr = sum(1 for t in trades if t['direction'] == 'BUY' and t['won']) / max(buys, 1) * 100
        sell_wr = sum(1 for t in trades if t['direction'] == 'SELL' and t['won']) / max(sells, 1) * 100

        log(f"\n  📊 COUNCIL VALIDATION RESULTS:")
        log(f"  {'─' * 40}")
        log(f"  Total trades:    {n_trades}")
        log(f"  Win Rate:        {wr:.1f}%")
        log(f"  Profit Factor:   {pf:.2f}")
        log(f"  Expectancy:      {expectancy:.1f} pips/trade")
        log(f"  Total P&L:       {total_pnl:.0f} pips")
        log(f"  Avg Win:         {avg_win:.1f} pips")
        log(f"  Avg Loss:        {avg_loss:.1f} pips")
        log(f"  {'─' * 40}")
        log(f"  BUY trades:      {buys} (WR: {buy_wr:.1f}%)")
        log(f"  SELL trades:     {sells} (WR: {sell_wr:.1f}%)")
        log(f"  Trade rate:      {n_trades/n*100:.2f}% of candles")
        log(f"  Selectivity:     1 trade per {n/max(n_trades,1):.0f} candles")

        # Council stats
        stats = council.get_stats()
        log(f"\n  🚫 Filter breakdown:")
        log(f"    Blocked (session):    {stats.get('blocked_session', 0):,}")
        log(f"    Blocked (regime):     {stats.get('blocked_regime', 0):,}")
        log(f"    Blocked (disagree):   {stats.get('blocked_disagree', 0):,}")
        log(f"    Blocked (confidence): {stats.get('blocked_confidence', 0):,}")
        log(f"    Blocked (cooldown):   {stats.get('blocked_cooldown', 0):,}")
    else:
        log("  ⚠️ No trades generated in test period!")
        log("  Try lowering min_confidence threshold")


if __name__ == '__main__':
    train_all()
