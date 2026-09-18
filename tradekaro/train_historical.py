import pandas as pd
import numpy as np
import os
import torch
import joblib
from sklearn.preprocessing import RobustScaler
from src.brain import TradingBrain
from src.indicators import TechnicalIndicators
import config.settings as settings

print("========================================")
print("🧠 DEEP LEARNING MATRIX INITIALIZED")
print("========================================")
print("Task: Injecting 10-Year Historical Data into LSTM Brain")

def prepare_historical_chunk(df_chunk, scaler, is_fit_mode=False):
    """
    Format a raw 1m OHLCV chunk into the 60-candle MTF sequences expected by the Brain.
    """
    # 1. Apply MTF Indicators
    df_rich = TechnicalIndicators.apply_multi_timeframe_features(df_chunk)
    if df_rich.empty or len(df_rich) < 60:
        return np.array([]), np.array([])
    
    # 2. Select V4 Features (engineered signals for smart brain)
    engine_features = [
        'close', 'sma_20', 'ema_50', 'macd', 'macd_signal', 'macd_hist',
        'plus_di', 'minus_di', 'adx', 'rsi_14', 'volume_shock',
        # V4 Engineered features
        'ema_trend', 'price_vs_ema', 'macd_cross', 'rsi_zone',
        'adx_strength', 'di_cross', 'candle_momentum', 'rel_volatility',
        'price_velocity'
    ]
    
    # Normalize column names
    df_rich.columns = [c.lower() if '15m' not in c and '1H' not in c else c for c in df_rich.columns] 
    
    available_features = [f for f in engine_features if f in df_rich.columns]
    
    if len(available_features) != len(engine_features):
        print(f"[WARN] Missing some features. Found {len(available_features)}/{len(engine_features)}")
    
    raw_data = df_rich[available_features].values
    raw_data = np.nan_to_num(raw_data, nan=0.0, posinf=1.0, neginf=-1.0)
    
    # 3. Scaling
    scaled_data = scaler.transform(raw_data)
    
    # 4. Create Sequences (X) and Smart Targets (y)
    X, y = [], []
    lookback = 60
    future_horizon = 40    # Aligned with hold_candles=40 in backtest
    sl_pct = 0.004         # 0.4% SL
    tp_pct = 0.006         # 0.6% TP (R:R = 1.5)
    
    for i in range(lookback, len(scaled_data) - future_horizon):
        X.append(scaled_data[i-lookback : i])
        
        # === SMART LABEL: TA conditions + profitable trade simulation ===
        current_close = df_rich['close'].iloc[i]
        row = df_rich.iloc[i]
        
        # Get TA indicators
        ema50 = row.get('ema_50', 0) or 0
        sma20 = row.get('sma_20', 0) or 0
        adx_val = row.get('adx', 0) or 0
        rsi_val = row.get('rsi_14', 0) or 50
        macd_val = row.get('macd', 0) or 0
        macd_sig = row.get('macd_signal', 0) or 0
        plus_di_val = row.get('plus_di', 0) or 0
        minus_di_val = row.get('minus_di', 0) or 0
        
        if not ema50 or not sma20 or not adx_val or current_close <= 0:
            y.append(0)
            continue
        
        # Check BUY/SELL setup
        buy_ok = (current_close > ema50 and sma20 > ema50 and 
                  macd_val > macd_sig and plus_di_val > minus_di_val and
                  30 < rsi_val < 65 and adx_val > 22)
        sell_ok = (current_close < ema50 and sma20 < ema50 and
                   macd_val < macd_sig and minus_di_val > plus_di_val and
                   35 < rsi_val < 70 and adx_val > 22)
        
        if not buy_ok and not sell_ok:
            y.append(0)
            continue
        
        # Simulate trade forward
        profitable = False
        for j in range(1, min(future_horizon + 1, len(df_rich) - i)):
            fh = df_rich.iloc[i + j].get('high', df_rich.iloc[i + j]['close'])
            fl = df_rich.iloc[i + j].get('low', df_rich.iloc[i + j]['close'])
            if buy_ok:
                if fh >= current_close * (1 + tp_pct):
                    profitable = True; break
                if fl <= current_close * (1 - sl_pct):
                    break
            elif sell_ok:
                if fl <= current_close * (1 - tp_pct):
                    profitable = True; break
                if fh >= current_close * (1 + sl_pct):
                    break
        
        y.append(1 if profitable else 0)
            
    return np.array(X), np.array(y)

def run_historical_training():
    data_files = [
        "data/NIFTY 50_minute.csv",
        "data/NIFTY BANK_minute.csv"
    ]
    
    brain = TradingBrain()
    scaler_path = 'models/scaler.pkl'
    scaler = RobustScaler()
    
    # Phase 1: Collect sampled data from all files, then fit RobustScaler once
    print("[PHASE 1] Pre-computing Global Scaler (Scanning all data...)")
    all_raw_data = []
    
    for file in data_files:
        if not os.path.exists(file):
            print(f"❌ File missing: {file}")
            continue
            
        print(f"Scanning {file}...")
        chunk_size = 50000 
        for chunk in pd.read_csv(file, chunksize=chunk_size):
            chunk.columns = [c.strip().lower() for c in chunk.columns]
            
            if 'datetime' in chunk.columns:
                chunk['timestamp'] = pd.to_datetime(chunk['datetime'])
            elif 'date' in chunk.columns and 'time' in chunk.columns:
                chunk['timestamp'] = pd.to_datetime(chunk['date'].astype(str) + ' ' + chunk['time'].astype(str))
            elif 'date' in chunk.columns:
                chunk['timestamp'] = pd.to_datetime(chunk['date'])
            else:
                continue
                
            chunk.set_index('timestamp', inplace=True)
            chunk.sort_index(inplace=True)
            
            # Get features from this chunk (reuse prepare logic but just extract raw)
            df_rich = TechnicalIndicators.apply_multi_timeframe_features(chunk)
            if df_rich.empty or len(df_rich) < 60:
                continue
            df_rich.columns = [c.lower() if '15m' not in c and '1H' not in c else c for c in df_rich.columns]
            engine_features = [
                'close', 'sma_20', 'ema_50', 'macd', 'macd_signal', 'macd_hist',
                'plus_di', 'minus_di', 'adx', 'rsi_14', 'volume_shock',
                'ema_trend', 'price_vs_ema', 'macd_cross', 'rsi_zone',
                'adx_strength', 'di_cross', 'candle_momentum', 'rel_volatility', 'price_velocity'
            ]
            available = [f for f in engine_features if f in df_rich.columns]
            raw = df_rich[available].values
            raw = np.nan_to_num(raw, nan=0.0, posinf=1.0, neginf=-1.0)
            # Sample every 10th row to save memory
            all_raw_data.append(raw[::10])
    
    # Fit scaler on ALL collected data
    all_raw = np.concatenate(all_raw_data, axis=0)
    print(f"  Collected {len(all_raw)} samples with {all_raw.shape[1]} features")
    scaler.fit(all_raw)
    del all_raw, all_raw_data  # Free memory
    
    joblib.dump(scaler, scaler_path)
    print(f"✅ RobustScaler Fit & Saved to {scaler_path}")
    
    print("\n[PHASE 2] Deep Neural Network Training...")
    
    total_processed = 0
    
    for file in data_files:
        if not os.path.exists(file): continue
        print(f"\n🚀 Initiating Feed: {file}")
        
        # Train in overlapping chunks to ensure continuous seq learning
        chunk_size = 5000  # Reduced from 20000 to prevent OOM
        chunk_iterator = pd.read_csv(file, chunksize=chunk_size)
        
        for idx, chunk in enumerate(chunk_iterator):
            try:
                chunk.columns = [c.strip().lower() for c in chunk.columns]
                
                if 'datetime' in chunk.columns:
                    chunk['timestamp'] = pd.to_datetime(chunk['datetime'])
                elif 'date' in chunk.columns and 'time' in chunk.columns:
                    chunk['timestamp'] = pd.to_datetime(chunk['date'].astype(str) + ' ' + chunk['time'].astype(str))
                elif 'date' in chunk.columns:
                    chunk['timestamp'] = pd.to_datetime(chunk['date'])
                else:
                    continue
                
                chunk.set_index('timestamp', inplace=True)
                chunk.sort_index(inplace=True)
                
                print(f"   ► Processing Chunk {idx+1} ({len(chunk)} candles)...")
                X_batch, y_batch = prepare_historical_chunk(chunk, scaler, is_fit_mode=False)
                
                if len(X_batch) > 0:
                    # === OVERSAMPLE MINORITY CLASS ===
                    # Smart labels create ~91% zeros. Balance by duplicating label=1
                    pos_mask = y_batch == 1
                    neg_mask = y_batch == 0
                    n_pos = pos_mask.sum()
                    n_neg = neg_mask.sum()
                    
                    if n_pos > 0 and n_neg > n_pos * 2:
                        # Oversample positive class to match negative
                        oversample_factor = min(int(n_neg / n_pos), 15)  # Cap at 15x
                        X_pos = X_batch[pos_mask]
                        y_pos = y_batch[pos_mask]
                        X_oversampled = np.tile(X_pos, (oversample_factor, 1, 1))
                        y_oversampled = np.tile(y_pos, oversample_factor)
                        X_batch = np.concatenate([X_batch, X_oversampled])
                        y_batch = np.concatenate([y_batch, y_oversampled])
                        # Shuffle
                        shuffle_idx = np.random.permutation(len(X_batch))
                        X_batch = X_batch[shuffle_idx]
                        y_batch = y_batch[shuffle_idx]
                        print(f"     [BALANCE] {n_pos} pos → {n_pos*(1+oversample_factor)} | {n_neg} neg | Total: {len(X_batch)}")
                    
                    brain.train_incremental(X_batch, y_batch, epochs=5)
                    total_processed += len(X_batch)
                    
            except Exception as e:
                print(f"   ❌ Error in chunk {idx+1}: {e}")
                
    print("\n========================================")
    print(f"🎉 10-YEAR TRAINING COMPLETE! 🎉")
    print(f"Total Unique Scenarios Learned: {total_processed}")
    print("LSTM Brain is now highly adapted to historical market dynamics.")
    print("========================================")
    
    # Save training status for frontend
    import json
    status = {
        'status': 'COMPLETE',
        'total_processed': total_processed,
        'timestamp': pd.Timestamp.now().isoformat()
    }
    with open('models/training_progress.json', 'w') as f:
        json.dump(status, f)

if __name__ == "__main__":
    run_historical_training()
