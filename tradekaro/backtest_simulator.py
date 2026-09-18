"""
Backtest Simulator — Runs AI Brain predictions on historical data
and generates simulated trades with full P&L, R:R, SL/TP tracking.
Results are saved to trade_journal table as 'BACKTEST' trades.
"""
import pandas as pd
import numpy as np
import os
import sys
import joblib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.brain import TradingBrain
from src.database import TradingDB
from src.indicators import TechnicalIndicators
import config.settings as settings


def run_backtest(symbol='NIFTY', data_file=None, confidence_threshold=0.55,
                 hold_candles=40, rr_target=2.0):
    """
    Run backtest on historical data.
    
    Args:
        symbol: Trading symbol name
        data_file: Path to CSV file
        confidence_threshold: Minimum prediction score for trade entry (0-1)
        hold_candles: Max candles to hold a position before forced exit
        rr_target: Target Risk:Reward ratio
    """
    print("=" * 50)
    print(f"🏦 BACKTEST ENGINE — {symbol}")
    print("=" * 50)

    # Initialize components
    db = TradingDB()
    brain = TradingBrain()

    # Load scaler
    scaler = None
    scaler_path = 'models/scaler.pkl'
    if os.path.exists(scaler_path):
        scaler = joblib.load(scaler_path)
        print(f"[INFO] Loaded scaler: {scaler_path}")

    # Load data
    if data_file is None:
        data_file = f'data/{symbol}_minute.csv'
        if not os.path.exists(data_file):
            data_file = f'data/{symbol} 50_minute.csv'  # NIFTY 50_minute.csv format
    
    if not os.path.exists(data_file):
        print(f"❌ Data file not found: {data_file}")
        return

    print(f"[INFO] Loading data: {data_file}")
    df_raw = pd.read_csv(data_file)
    df_raw.columns = [c.strip().lower() for c in df_raw.columns]
    print(f"[INFO] Total rows: {len(df_raw):,}")

    # Parse timestamp
    if 'date' in df_raw.columns:
        df_raw['timestamp'] = pd.to_datetime(df_raw['date'])
    elif 'datetime' in df_raw.columns:
        df_raw['timestamp'] = pd.to_datetime(df_raw['datetime'])
    else:
        print("❌ No date/datetime column found!")
        return

    df_raw.set_index('timestamp', inplace=True)
    df_raw.sort_index(inplace=True)

    # V4 Feature columns for brain (must match training)
    V4_FEATURES = [
        'close', 'sma_20', 'ema_50', 'macd', 'macd_signal', 'macd_hist',
        'plus_di', 'minus_di', 'adx', 'volume_shock',
        'ema_trend', 'price_vs_ema', 'macd_cross', 'adx_strength',
        'di_cross', 'candle_momentum', 'rel_volatility', 'price_velocity'
    ]

    # Process in chunks (simulate real-world streaming)
    chunk_size = 5000
    total_chunks = len(df_raw) // chunk_size
    
    sl_percent = settings.STOP_LOSS_PERCENT  # e.g., 0.98 → 0.98% SL
    tp_percent = sl_percent * rr_target  # TP = SL * R:R

    trade_count = 0
    cooldown = 0  # Candles to skip after a trade

    print(f"[CONFIG] SL: {sl_percent}% | TP: {tp_percent}% | R:R Target: {rr_target}")
    print(f"[CONFIG] Confidence Threshold: {confidence_threshold} | Hold: {hold_candles} candles")
    print(f"[INFO] Processing {total_chunks} chunks of {chunk_size} candles each...")
    print()

    for chunk_idx in range(total_chunks):
        start = chunk_idx * chunk_size
        end = start + chunk_size + 500  # overlap for indicators
        chunk = df_raw.iloc[start:min(end, len(df_raw))].copy()

        if len(chunk) < 400:
            continue

        # Apply indicators
        try:
            df_5m = TechnicalIndicators.apply_multi_timeframe_features(chunk)
        except Exception as e:
            print(f"   ⚠️ Indicator error in chunk {chunk_idx}: {e}")
            continue

        if df_5m.empty or len(df_5m) < 70:
            continue

        # Find available features
        # Find available features (lowercase to match V4 training)
        df_5m_lower = df_5m.copy()
        df_5m_lower.columns = [c.lower() for c in df_5m_lower.columns]
        available = [c for c in V4_FEATURES if c in df_5m_lower.columns]
        
        if len(available) < 10:
            continue

        # Scan through the chunk for trade signals
        for i in range(60, len(df_5m) - hold_candles - 1):
            if cooldown > 0:
                cooldown -= 1
                continue

            # === BRAIN V4 AS PRIMARY SIGNAL ===
            try:
                window = df_5m_lower.iloc[i-60:i]
                features = window[available].values
                features = np.nan_to_num(features, nan=0.0, posinf=1.0, neginf=-1.0)
                
                if scaler and features.shape[1] == scaler.n_features_in_:
                    try:
                        features = scaler.transform(features)
                    except:
                        pass
                
                features_3d = np.expand_dims(features, axis=0)
                expected = brain._get_input_size()
                if features_3d.shape[2] < expected:
                    pad = np.zeros((1, features_3d.shape[1], expected - features_3d.shape[2]))
                    features_3d = np.concatenate([features_3d, pad], axis=2)
                
                prediction = brain.predict(features_3d)
                
                # Brain decides entry
                side = None
                if prediction > confidence_threshold:
                    side = 'BUY'
                elif prediction < (1 - confidence_threshold):
                    side = 'SELL'
                else:
                    continue
                    
            except Exception:
                continue

            # Entry point
            entry_price = df_5m.iloc[i]['close']
            entry_time = df_5m.index[i] if hasattr(df_5m.index[i], 'strftime') else str(df_5m.index[i])

            # Calculate SL and TP
            if side == 'BUY':
                sl_price = round(entry_price * (1 - sl_percent / 100), 2)
                tp_price = round(entry_price * (1 + tp_percent / 100), 2)
            else:
                sl_price = round(entry_price * (1 + sl_percent / 100), 2)
                tp_price = round(entry_price * (1 - tp_percent / 100), 2)

            # Simulate forward — check if SL or TP hits first
            exit_price = None
            exit_reason = None
            exit_j = hold_candles
            best_price = entry_price  # For trailing SL
            trailing_sl = sl_price
            
            for j in range(1, hold_candles + 1):
                if i + j >= len(df_5m):
                    break
                
                candle = df_5m.iloc[i + j]
                high = candle['high'] if 'high' in df_5m.columns else candle['close']
                low = candle['low'] if 'low' in df_5m.columns else candle['close']

                if side == 'BUY':
                    # Trail SL when price moves 40%+ towards TP
                    if high > best_price:
                        best_price = high
                    tp_dist = tp_price - entry_price
                    if tp_dist > 0:
                        move_ratio = (best_price - entry_price) / tp_dist
                        if move_ratio >= 0.5:
                            trailing_sl = max(trailing_sl, entry_price + (best_price - entry_price) * 0.2)
                    
                    if low <= trailing_sl:
                        exit_price = trailing_sl
                        exit_reason = 'SL_HIT'
                        exit_j = j
                        break
                    elif high >= tp_price:
                        exit_price = tp_price
                        exit_reason = 'TP_HIT'
                        exit_j = j
                        break
                else:  # SELL
                    if low < best_price:
                        best_price = low
                    tp_dist = entry_price - tp_price
                    if tp_dist > 0:
                        move_ratio = (entry_price - best_price) / tp_dist
                        if move_ratio >= 0.5:
                            trailing_sl = min(trailing_sl, entry_price - (entry_price - best_price) * 0.2)
                    
                    if high >= trailing_sl:
                        exit_price = trailing_sl
                        exit_reason = 'SL_HIT'
                        exit_j = j
                        break
                    elif low <= tp_price:
                        exit_price = tp_price
                        exit_reason = 'TP_HIT'
                        exit_j = j
                        break

            # If neither SL nor TP hit, exit at last candle's close
            exit_candle_idx = min(i + hold_candles, len(df_5m) - 1)
            if exit_price is None:
                exit_price = df_5m.iloc[exit_candle_idx]['close']
                exit_reason = 'TIME_EXIT'
                exit_j = hold_candles
            
            # Get the exit time from the candle that triggered the exit
            exit_candle_actual = min(i + exit_j, len(df_5m) - 1)
            exit_time = df_5m.index[exit_candle_actual]
            if hasattr(exit_time, 'strftime'):
                exit_time = exit_time.strftime('%Y-%m-%d %H:%M:%S')
            else:
                exit_time = str(exit_time)

            # Calculate lot size (NIFTY=25, BANKNIFTY=15)
            if 'BANK' in symbol.upper():
                qty = 15
            elif 'NIFTY' in symbol.upper():
                qty = 25
            else:
                qty = 1

            # Log to trade_journal with HISTORICAL timestamps
            trade_id = db.log_trade_journal(
                trade_type='BACKTEST',
                symbol=symbol,
                instrument='EQ',
                side=side,
                qty=qty,
                entry_price=round(entry_price, 2),
                sl_price=sl_price,
                tp_price=tp_price,
                confidence=round(prediction, 4),
                council_reason=f'Pred:{prediction:.4f}',
                planned_rr=rr_target,
                entry_time=entry_time
            )

            if trade_id:
                db.update_trade_journal_exit(trade_id, round(exit_price, 2), exit_reason, exit_time=exit_time)
                trade_count += 1

            # Cooldown — skip next 'hold_candles' to avoid overlapping trades
            cooldown = hold_candles

        print(f"   ✅ Chunk {chunk_idx + 1}/{total_chunks} done. Trades so far: {trade_count}")

    # Print Summary
    summary = db.get_journal_summary('BACKTEST')
    print()
    print("=" * 50)
    print(f"🎯 BACKTEST COMPLETE — {symbol}")
    print("=" * 50)
    print(f"Total Trades: {summary['total']}")
    print(f"Wins: {summary['wins']} | Losses: {summary['losses']}")
    print(f"Win Rate: {summary['winRate']}%")
    print(f"Total P&L: ₹{summary['pnl']:,.2f}")
    print(f"Avg R:R: {summary['avgRR']}")
    print(f"Avg P&L/Trade: ₹{summary['avgPnl']:,.2f}")
    print(f"Max Drawdown: ₹{summary['maxDD']:,.2f}")
    print("=" * 50)

    db.close()
    return summary


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='TradeKaro Backtest Simulator')
    parser.add_argument('--symbol', default='NIFTY', help='Symbol to backtest')
    parser.add_argument('--confidence', type=float, default=0.6, help='Confidence threshold')
    parser.add_argument('--hold', type=int, default=10, help='Max hold candles')
    parser.add_argument('--rr', type=float, default=2.0, help='Target R:R ratio')
    args = parser.parse_args()

    # Auto-detect data file
    data_file = None
    for fname in [f'data/{args.symbol}_minute.csv', f'data/{args.symbol} 50_minute.csv',
                  f'data/NIFTY 50_minute.csv', f'data/NIFTY BANK_minute.csv']:
        if os.path.exists(fname):
            data_file = fname
            break

    run_backtest(
        symbol=args.symbol,
        data_file=data_file,
        confidence_threshold=args.confidence,
        hold_candles=args.hold,
        rr_target=args.rr
    )
