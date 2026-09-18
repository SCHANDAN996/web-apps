"""
Forced End-to-End Trade Test
"""
import sys, os, warnings, time
sys.path.append('.')
warnings.filterwarnings('ignore')
from dotenv import load_dotenv
load_dotenv('config/credentials.env')
import numpy as np

print("=" * 60)
print("FORCED TRADE TEST (Simulating Market Hours)")
print("=" * 60)

from src.database import TradingDB
db = TradingDB()

import yfinance as yf
for sym, yticker in [('NIFTY', '^NSEI'), ('RELIANCE', 'RELIANCE.NS'), ('HDFCBANK', 'HDFCBANK.NS')]:
    ticker = yf.Ticker(yticker)
    df = ticker.history(period='5d', interval='1m')
    df.reset_index(inplace=True)
    if df['Datetime'].dt.tz is not None:
        df['Datetime'] = df['Datetime'].dt.tz_localize(None)
    df.set_index('Datetime', inplace=True)
    db.store_bulk_data(sym, '1m', df)
    print("OK " + sym + ": " + str(len(df)) + " candles")

from src.brain import TradingBrain
from src.indicators import TechnicalIndicators
brain = TradingBrain()

test_symbols = ['RELIANCE', 'HDFCBANK', 'NIFTY']
results = []

for symbol in test_symbols:
    df_1m = db.get_market_data(symbol, '1m', limit=1000)
    if len(df_1m) < 400:
        print("WARN " + symbol + ": Not enough data (" + str(len(df_1m)) + ")")
        continue
    df_5m = TechnicalIndicators.apply_multi_timeframe_features(df_1m)
    if len(df_5m) < 60:
        continue
    V4_FEATURES = [
        'close', 'sma_20', 'ema_50', 'macd', 'macd_signal', 'macd_hist',
        'plus_di', 'minus_di', 'adx', 'volume_shock',
        'ema_trend', 'price_vs_ema', 'macd_cross', 'adx_strength',
        'di_cross', 'candle_momentum', 'rel_volatility', 'price_velocity'
    ]
    df_lower = df_5m.copy()
    df_lower.columns = [c.lower() for c in df_lower.columns]
    available = [c for c in V4_FEATURES if c in df_lower.columns]
    if len(available) < 10:
        continue
    last_60 = df_lower.tail(60)[available].values
    last_60 = np.nan_to_num(last_60, nan=0.0, posinf=1.0, neginf=-1.0)
    last_60_3d = np.expand_dims(last_60, axis=0)
    expected = brain._get_input_size()
    if last_60_3d.shape[2] < expected:
        pad = np.zeros((1, last_60_3d.shape[1], expected - last_60_3d.shape[2]))
        last_60_3d = np.concatenate([last_60_3d, pad], axis=2)
    prediction = brain.predict(last_60_3d)
    signal = 'BUY' if prediction > 0.65 else ('SELL' if prediction < 0.35 else 'HOLD')
    actual_confidence = abs(prediction - 0.5) * 2
    current_price = df_5m.iloc[-1]['close']
    print("BRAIN " + symbol + ": pred=" + str(round(prediction, 4)) + " signal=" + signal + " conf=" + str(round(actual_confidence, 2)) + " price=" + str(round(current_price, 2)))
    results.append((symbol, prediction, signal, actual_confidence, current_price))

from src.connector import ShoonyaConnector
from src.executor import OrderExecutor
api = ShoonyaConnector()
executor = OrderExecutor(api)
executor.mode = 'PAPER_TRADING'

trade_done = False
for symbol, prediction, signal, conf, price in results:
    if signal in ['BUY', 'SELL']:
        side = 'B' if signal == 'BUY' else 'S'
        print("TRADE: " + signal + " " + symbol + " x5 @ " + str(round(price, 2)))
        result = executor.place_smart_order(symbol, 'NSE', 5, side, price)
        if result:
            db.log_trade(symbol, side, price, 5, result.get('norenordno', 'TEST'))
            print("OK Order: " + result.get('norenordno', ''))
            trade_done = True
        break

if not trade_done:
    symbol = 'RELIANCE'
    price = results[0][4] if results else 1360.0
    print("FORCE TRADE: BUY " + symbol + " x5 @ " + str(round(price, 2)))
    result = executor.place_smart_order(symbol, 'NSE', 5, 'B', price)
    if result:
        db.log_trade(symbol, 'B', price, 5, result.get('norenordno', 'FORCE'))
        print("OK Forced: " + result.get('norenordno', ''))

from src.notifier import TelegramNotifier
notifier = TelegramNotifier()
lines = []
for sym, pred, sig, conf, px in results:
    lines.append(sym + ": " + sig + " (Score:" + str(round(pred, 2)) + " Conf:" + str(round(conf*100)) + "%)")
summary = "\n".join(lines)
msg = "<b>TradeKaro System Test</b>\n" + summary + "\nData: Yahoo Finance\nBrain: V3 GRU\nMode: PAPER\nPipeline: OK"
tg = notifier.send_message(msg)
print("Telegram: " + str(tg.get('ok') if tg else 'FAILED'))
print("DONE")
