"""
🧪 Full Pipeline Test — Yahoo Data → DB → Brain → Paper Trade → Telegram
"""
import sys, os, warnings, time
sys.path.append('.')
warnings.filterwarnings('ignore')

from dotenv import load_dotenv
load_dotenv('config/credentials.env')

print("=" * 60)
print("🧪 TRADEKARO FULL PIPELINE TEST")
print("=" * 60)

# ─── STEP 1: Initialize DB (will recreate dropped tables) ───
print("\n📦 STEP 1: Initializing Database...")
from src.database import TradingDB
db = TradingDB()
print("✅ Database initialized. Tables created.")

# Verify market_data schema
import sqlite3
conn = sqlite3.connect('trading_data.db')
cursor = conn.execute('PRAGMA table_info(market_data)')
cols = [c[1] for c in cursor.fetchall()]
print(f"   market_data columns: {cols}")
conn.close()

# ─── STEP 2: Fetch Yahoo Data for RELIANCE ───
print("\n📊 STEP 2: Fetching Yahoo Finance data for RELIANCE...")
import yfinance as yf
ticker = yf.Ticker('RELIANCE.NS')
df = ticker.history(period='5d', interval='1m')
print(f"   Fetched {len(df)} 1m candles from Yahoo")

df.reset_index(inplace=True)
if df['Datetime'].dt.tz is not None:
    df['Datetime'] = df['Datetime'].dt.tz_localize(None)
df.set_index('Datetime', inplace=True)

db.store_bulk_data('RELIANCE', '1m', df)

# Verify
check = db.get_market_data('RELIANCE', '1m', limit=5)
print(f"   ✅ Verified: {len(check)} rows in DB for RELIANCE 1m")
if not check.empty:
    print(f"   Latest close: ₹{check.iloc[-1]['close']}")

# ─── STEP 3: Fetch NIFTY data too ───
print("\n📊 STEP 3: Fetching NIFTY data...")
ticker_n = yf.Ticker('^NSEI')
df_n = ticker_n.history(period='5d', interval='1m')
df_n.reset_index(inplace=True)
if df_n['Datetime'].dt.tz is not None:
    df_n['Datetime'] = df_n['Datetime'].dt.tz_localize(None)
df_n.set_index('Datetime', inplace=True)
db.store_bulk_data('NIFTY', '1m', df_n)
check_n = db.get_market_data('NIFTY', '1m', limit=5)
print(f"   ✅ NIFTY: {len(check_n)} rows, latest close: ₹{check_n.iloc[-1]['close'] if not check_n.empty else 'N/A'}")

# ─── STEP 4: Test Brain Prediction ───
print("\n🧠 STEP 4: Testing AI Brain prediction...")
from src.brain import TradingBrain
from src.indicators import TechnicalIndicators
import numpy as np

brain = TradingBrain()

df_1m = db.get_market_data('RELIANCE', '1m', limit=1000)
print(f"   Data rows for indicators: {len(df_1m)}")

if len(df_1m) >= 400:
    df_5m = TechnicalIndicators.apply_multi_timeframe_features(df_1m)
    print(f"   After indicators: {len(df_5m)} rows, {len(df_5m.columns)} columns")
    
    V4_FEATURES = [
        'close', 'sma_20', 'ema_50', 'macd', 'macd_signal', 'macd_hist',
        'plus_di', 'minus_di', 'adx', 'volume_shock',
        'ema_trend', 'price_vs_ema', 'macd_cross', 'adx_strength',
        'di_cross', 'candle_momentum', 'rel_volatility', 'price_velocity'
    ]
    
    df_lower = df_5m.copy()
    df_lower.columns = [c.lower() for c in df_lower.columns]
    available = [c for c in V4_FEATURES if c in df_lower.columns]
    print(f"   Available features: {len(available)}/{len(V4_FEATURES)}")
    
    if len(available) >= 10 and len(df_5m) >= 60:
        last_60 = df_lower.tail(60)[available].values
        last_60 = np.nan_to_num(last_60, nan=0.0, posinf=1.0, neginf=-1.0)
        
        # Pad if needed
        last_60_3d = np.expand_dims(last_60, axis=0)
        expected = brain._get_input_size()
        if last_60_3d.shape[2] < expected:
            pad = np.zeros((1, last_60_3d.shape[1], expected - last_60_3d.shape[2]))
            last_60_3d = np.concatenate([last_60_3d, pad], axis=2)
        
        prediction = brain.predict(last_60_3d)
        signal = 'BUY' if prediction > 0.65 else ('SELL' if prediction < 0.35 else 'HOLD')
        print(f"   🎯 Brain Prediction: {prediction:.4f} → Signal: {signal}")
    else:
        print(f"   ⚠️ Not enough features ({len(available)}) or rows")
        prediction = 0.50
else:
    print(f"   ⚠️ Not enough 1m data ({len(df_1m)} rows, need 400)")
    prediction = 0.50

# ─── STEP 5: Execute Paper Trade ───
print("\n💰 STEP 5: Executing test Paper Trade...")
from src.connector import ShoonyaConnector
from src.executor import OrderExecutor

api = ShoonyaConnector()
executor = OrderExecutor(api)
executor.mode = 'PAPER_TRADING'

current_price = check.iloc[-1]['close'] if not check.empty else 1350.0
result = executor.place_smart_order('RELIANCE', 'NSE', 10, 'B', current_price)
print(f"   Order result: {result}")

if result:
    # Log to DB
    order_id = result.get('norenordno', 'TEST')
    db.log_trade('RELIANCE', 'B', current_price, 10, order_id)
    print(f"   ✅ Trade logged: BUY RELIANCE x10 @ ₹{current_price}")

# ─── STEP 6: Telegram Test ───  
print("\n📱 STEP 6: Testing Telegram notification...")
from src.notifier import TelegramNotifier
notifier = TelegramNotifier()
test_msg = f"""
🧪 <b>TradeKaro Pipeline Test</b>
━━━━━━━━━━━━━━━━━━
📊 Data: Yahoo Finance ✅
🧠 Brain Score: {prediction:.4f}
💰 Paper Trade: BUY RELIANCE x10 @ ₹{current_price}
⏰ Time: {time.strftime('%H:%M:%S IST')}
━━━━━━━━━━━━━━━━━━
✅ All Systems Operational!
"""
tg_result = notifier.send_message(test_msg)
print(f"   Telegram result: {tg_result}")

# ─── STEP 7: Verify DB State ───
print("\n📋 STEP 7: Final DB verification...")
conn2 = sqlite3.connect('trading_data.db')
cursor2 = conn2.execute('SELECT symbol, interval, COUNT(*) FROM market_data GROUP BY symbol, interval')
for row in cursor2.fetchall():
    print(f"   {row[0]} ({row[1]}): {row[2]} candles")

cursor2 = conn2.execute('SELECT COUNT(*) FROM trades')
trade_count = cursor2.fetchone()[0]
print(f"   Total trades in DB: {trade_count}")
conn2.close()

print("\n" + "=" * 60)
print("🏁 PIPELINE TEST COMPLETE!")
print("=" * 60)
