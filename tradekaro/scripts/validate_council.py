"""Quick validation-only script — skips training, uses saved models."""
import os, sys, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

import joblib
from forex_features import XGB_FEATURES, GRU_FEATURES, REGIME_FEATURES, RISK_FEATURES
from forex_data_pipeline import (
    load_and_resample, remove_weekends, filter_sessions,
    generate_labels, generate_regime_labels, split_data,
    build_sequences, LOOKBACK, compute_all_features
)
from forex_council import ForexCouncil

PIP = 0.0001

print("📦 Loading data...")
df = load_and_resample()
df = remove_weekends(df)
df = compute_all_features(df)
df = filter_sessions(df, keep_dead=False)
df = generate_labels(df)
df = generate_regime_labels(df)
_, _, test_df = split_data(df)

# Load scaler
scaler_data = joblib.load('models/forex_scaler.pkl')
scaler = scaler_data['scaler']
all_cols = scaler_data['columns']

xgb_cols = [c for c in XGB_FEATURES if c in test_df.columns]
gru_cols = [c for c in GRU_FEATURES if c in test_df.columns]
regime_cols = [c for c in REGIME_FEATURES if c in test_df.columns]
risk_cols = [c for c in RISK_FEATURES if c in test_df.columns]

# Scale test data
X_test_all = np.nan_to_num(scaler.transform(test_df[all_cols].values), nan=0, posinf=1, neginf=-1)
xgb_idx = [all_cols.index(c) for c in xgb_cols if c in all_cols]
regime_idx = [all_cols.index(c) for c in regime_cols if c in all_cols]
risk_idx = [all_cols.index(c) for c in risk_cols if c in all_cols]

X_xgb = X_test_all[:, xgb_idx]
X_regime = X_test_all[:, regime_idx]
X_risk = X_test_all[:, risk_idx]

# GRU sequences
def make_scaled_df(df, cols, scaler, all_cols):
    scaled_all = scaler.transform(df[all_cols].values)
    result = df.copy()
    for i, c in enumerate(all_cols):
        if c in cols:
            result[c] = scaled_all[:, i]
    return result

scaled_df = make_scaled_df(test_df, gru_cols, scaler, all_cols)
X_gru, y_gru = build_sequences(scaled_df, gru_cols, LOOKBACK)

n = min(len(X_gru), len(X_xgb) - LOOKBACK)
X_xgb = X_xgb[LOOKBACK:LOOKBACK + n]
X_regime = X_regime[LOOKBACK:LOOKBACK + n]
X_risk = X_risk[LOOKBACK:LOOKBACK + n]
X_gru = X_gru[:n]

close = test_df['close'].values[LOOKBACK:LOOKBACK + n]
high = test_df['high'].values[LOOKBACK:LOOKBACK + n]
low = test_df['low'].values[LOOKBACK:LOOKBACK + n]
hours = test_df.index.hour[LOOKBACK:LOOKBACK + n]

# Load council
print("\n⚖️ Loading council...")
council = ForexCouncil(min_ev_pips=2.5)
council.load_all()

print(f"\n🎯 Running council on {n:,} test candles...")
decisions = council.decide_batch(X_xgb, X_gru, X_regime, X_risk, hours, close)

# Simulate trades
trades = []
atr_array = test_df['atr_norm'].values[LOOKBACK:LOOKBACK + n] * close

for i, dec in enumerate(decisions):
    if dec['action'] != 'TRADE':
        continue
    if i + 40 >= n:
        continue
        
    direction = dec['direction']
    entry = close[i]
    sl_dist = dec['sl_dist']
    tp_dist = dec['tp_dist']

    spread_val = 2.0 * PIP
    won = False
    lost = False
    pnl = 0.0
    atr = atr_array[i]
    
    if direction == 'BUY':
        effective_entry = entry + spread_val
        highest_high = effective_entry
        current_sl = effective_entry - sl_dist
        
        for j in range(1, 61):
            idx = i + j
            if idx >= n:
                break
                
            highest_high = max(highest_high, high[idx])
            trailing_stop = highest_high - (2.5 * atr)
            current_sl = max(current_sl, trailing_stop)
            
            if high[idx] >= effective_entry + tp_dist:
                won = True
                pnl = tp_dist
                break
            if low[idx] <= current_sl:
                lost = True
                pnl = current_sl - effective_entry
                break
    else:
        effective_entry = entry - spread_val
        lowest_low = effective_entry
        current_sl = effective_entry + sl_dist
        
        for j in range(1, 61):
            idx = i + j
            if idx >= n:
                break
                
            lowest_low = min(lowest_low, low[idx])
            trailing_stop = lowest_low + (2.5 * atr)
            current_sl = min(current_sl, trailing_stop)
            
            if low[idx] <= effective_entry - tp_dist:
                won = True
                pnl = tp_dist
                break
            if high[idx] >= current_sl:
                lost = True
                pnl = effective_entry - current_sl
                break

    # Adaptive Position Sizing
    base_risk = 1.0
    ev_abs = dec['confidence']
    if ev_abs > 3.0:
        risk = base_risk * 1.2
    elif ev_abs < 1.5:
        risk = base_risk * 0.5
    else:
        risk = base_risk

    pnl_pips = (pnl / PIP) * risk
    raw_pnl_pips = pnl / PIP  # For correct win/loss avg calculations

    trades.append({
        'direction': direction, 'won': won, 'lost': lost,
        'pnl_pips': pnl_pips,
        'raw_pnl_pips': raw_pnl_pips,
        'confidence': dec['confidence']
    })

# Report
if trades:
    n_trades = len(trades)
    wins = sum(1 for t in trades if t['raw_pnl_pips'] > 0)
    wr = wins / n_trades * 100
    total_pnl = sum(t['pnl_pips'] for t in trades)
    avg_win = np.mean([t['raw_pnl_pips'] for t in trades if t['raw_pnl_pips'] > 0]) if wins else 0
    losses = [abs(t['raw_pnl_pips']) for t in trades if t['raw_pnl_pips'] < 0]
    avg_loss = np.mean(losses) if losses else 1
    gross_win = sum(t['pnl_pips'] for t in trades if t['won'])
    gross_loss = abs(sum(t['pnl_pips'] for t in trades if t['pnl_pips'] < 0))
    pf = gross_win / gross_loss if gross_loss > 0 else float('inf')
    expectancy = (wr/100 * avg_win) - ((100-wr)/100 * avg_loss)

    buys = sum(1 for t in trades if t['direction'] == 'BUY')
    sells = n_trades - buys
    buy_wr = sum(1 for t in trades if t['direction']=='BUY' and t['raw_pnl_pips'] > 0) / max(buys,1) * 100
    sell_wr = sum(1 for t in trades if t['direction']=='SELL' and t['raw_pnl_pips'] > 0) / max(sells,1) * 100

    print(f"\n{'='*50}")
    print(f"📊 COUNCIL VALIDATION RESULTS")
    print(f"{'='*50}")
    print(f"  Total trades:    {n_trades:,}")
    print(f"  Win Rate:        {wr:.1f}%")
    print(f"  Profit Factor:   {pf:.2f}")
    print(f"  Expectancy:      {expectancy:.1f} pips/trade")
    print(f"  Total P&L:       {total_pnl:,.0f} pips")
    print(f"  Avg Win:         {avg_win:.1f} pips")
    print(f"  Avg Loss:        {avg_loss:.1f} pips")
    print(f"  {'─'*40}")
    print(f"  BUY trades:      {buys} (WR: {buy_wr:.1f}%)")
    print(f"  SELL trades:     {sells} (WR: {sell_wr:.1f}%)")
    print(f"  Selectivity:     1 trade per {n/max(n_trades,1):.0f} candles")

    # Already baked 2 pips spread into entry prices
    print(f"\n  📎 Realized Results (Spread-Baked):")
    print(f"  Net P&L:         {total_pnl:,.0f} pips")
    print(f"  Net Expectancy:  {expectancy:.1f} pips/trade")

    stats = council.get_stats()
    print(f"\n  🚫 Filter breakdown:")
    for k, v in stats.items():
        if k.startswith('blocked'):
            print(f"    {k}: {v:,}")
else:
    print("⚠️ No trades generated!")
    stats = council.get_stats()
    print(f"Stats: {stats}")
