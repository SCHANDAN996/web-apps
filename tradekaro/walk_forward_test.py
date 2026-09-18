"""
🔬 Walk-Forward Validation for Brain V4
Tests the brain on UNSEEN 2024-2025 data to check for overfitting.
Training was done on 2014-2024 data, so 2024-2025 last portion is the test set.
"""

import torch
import numpy as np
import joblib
import sqlite3
import os

os.chdir('/var/www/tradekaro/Trading_AI_Project')

print("=" * 60)
print("🔬 WALK-FORWARD VALIDATION — Overfitting Check")
print("=" * 60)

# Load model
checkpoint = torch.load('models/tradenet_actor.pth', map_location='cpu', weights_only=False)
print(f"Model: {checkpoint.get('model_version')} | Val Acc: {checkpoint.get('val_acc', 0)*100:.1f}%")

# Load scaler
scaler = joblib.load('models/scaler.pkl')
print(f"Scaler: {type(scaler).__name__} ({scaler.n_features_in_} features)")

# Load model class
from src.brain import TradingBrain
brain = TradingBrain()

# Load historical data from DB
conn = sqlite3.connect('trading_data.db')

V4_FEATURES = [
    'close', 'sma_20', 'ema_50', 'macd', 'macd_signal', 'macd_hist',
    'plus_di', 'minus_di', 'adx', 'volume_shock',
    'ema_trend', 'price_vs_ema', 'macd_cross', 'adx_strength',
    'di_cross', 'candle_momentum', 'rel_volatility', 'price_velocity'
]

for symbol_query in ['%NIFTY 50%', '%NIFTY BANK%']:
    # Get data
    df_raw = None
    for tbl in ['market_data_1m', 'market_data']:
        try:
            import pandas as pd
            df_raw = pd.read_sql(f"SELECT * FROM {tbl} WHERE symbol LIKE ? ORDER BY timestamp", 
                               conn, params=[symbol_query])
            if len(df_raw) > 1000:
                break
        except:
            continue
    
    if df_raw is None or df_raw.empty:
        # Try yfinance data tables
        for tbl_name in ['nifty_5m_data', 'banknifty_5m_data']:
            try:
                df_raw = pd.read_sql(f"SELECT * FROM {tbl_name} ORDER BY timestamp", conn)
                if len(df_raw) > 1000:
                    break
            except:
                continue
    
    if df_raw is None or len(df_raw) < 100:
        print(f"\n⚠️ {symbol_query}: Not enough data in DB. Skipping.")
        continue
    
    sym_name = 'NIFTY' if '50' in symbol_query else 'BANK NIFTY'
    print(f"\n{'='*50}")
    print(f"📊 {sym_name}: {len(df_raw)} candles found")
    
    # Check columns
    df_raw.columns = [c.lower() for c in df_raw.columns]
    avail = [c for c in V4_FEATURES if c in df_raw.columns]
    print(f"   Features available: {len(avail)}/{len(V4_FEATURES)}")
    
    if len(avail) < 10:
        # Need to compute features from OHLCV
        print(f"   ⚠️ Need to compute features from raw OHLCV...")
        
        if 'close' not in df_raw.columns:
            print(f"   ❌ No 'close' column. Available: {list(df_raw.columns[:10])}")
            continue

conn.close()

# Alternative: Test on backtest journal — split trades by date
print("\n" + "=" * 60)
print("📊 ALTERNATIVE: Testing on Recent vs Old Trades")
print("=" * 60)

conn = sqlite3.connect('trading_data.db')
c = conn.cursor()

# Get date range
c.execute("SELECT MIN(entry_time), MAX(entry_time) FROM trade_journal WHERE status='CLOSED'")
min_date, max_date = c.fetchone()
print(f"Data range: {min_date} → {max_date}")

# Split: first 70% = "training period", last 30% = "test period"
c.execute("SELECT COUNT(*) FROM trade_journal WHERE status='CLOSED'")
total = c.fetchone()[0]
split_offset = int(total * 0.7)

c.execute(f"""SELECT entry_time FROM trade_journal WHERE status='CLOSED' 
ORDER BY entry_time LIMIT 1 OFFSET {split_offset}""")
split_date = c.fetchone()[0][:10]

print(f"Total trades: {total}")
print(f"Split at: {split_date} (70/30)")

for period_name, condition in [("TRAIN Period (First 70%)", f"entry_time < '{split_date}'"),
                                ("TEST Period (Last 30%)", f"entry_time >= '{split_date}'")]:
    c.execute(f'''SELECT 
        COUNT(*),
        SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END),
        ROUND(SUM(pnl), 0),
        ROUND(AVG(pnl), 2),
        ROUND(SUM(CASE WHEN pnl>0 THEN pnl ELSE 0 END) / 
          NULLIF(ABS(SUM(CASE WHEN pnl<0 THEN pnl ELSE 0 END)),0), 2)
    FROM trade_journal WHERE status='CLOSED' AND {condition}''')
    
    row = c.fetchone()
    total_t, wins, pnl, avg_pnl, pf = row
    wr = round(wins/total_t*100, 1) if total_t else 0
    
    print(f"\n📊 {period_name}:")
    print(f"   Trades: {total_t} | Wins: {wins}")
    print(f"   Win Rate: {wr}%")
    print(f"   Total P&L: ₹{pnl:,.0f}")
    print(f"   Avg P&L: ₹{avg_pnl}")
    print(f"   Profit Factor: {pf}")

# Per symbol in test period
print(f"\n📈 TEST Period by Symbol:")
c.execute(f'''SELECT symbol, COUNT(*),
    ROUND(SUM(CASE WHEN pnl>0 THEN 1.0 ELSE 0 END)/COUNT(*)*100, 1),
    ROUND(SUM(pnl), 0),
    ROUND(SUM(CASE WHEN pnl>0 THEN pnl ELSE 0 END) / 
      NULLIF(ABS(SUM(CASE WHEN pnl<0 THEN pnl ELSE 0 END)),0), 2)
FROM trade_journal WHERE status='CLOSED' AND entry_time >= '{split_date}'
GROUP BY symbol''')

for row in c.fetchall():
    sym, cnt, wr, pnl, pf = row
    emoji = "✅" if wr >= 60 else "⚠️" if wr >= 50 else "❌"
    print(f"   {emoji} {sym}: {cnt} trades, WR: {wr}%, P&L: ₹{pnl:,.0f}, PF: {pf}")

conn.close()

print("\n" + "=" * 60)
print("🎯 VERDICT:")
print("If TEST Win Rate is within 5% of TRAIN Win Rate → ✅ No overfitting")
print("If TEST >> TRAIN or TEST << TRAIN → ⚠️ Overfitting detected")
print("=" * 60)
