import os
from dotenv import load_dotenv

load_dotenv('config/credentials.env')

# --- DATA UNIVERSE CONFIGURATION ---

# 1. INDICES (Market Direction)
INDICES = ["NIFTY", "BANKNIFTY", "FINNIFTY"]

# 2. TOP LIQUID FNO STOCKS (High Volume)
FNO_STOCKS = [
    "RELIANCE", "HDFCBANK", "ICICIBANK", "INFY", "TCS", "SBIN", "AXISBANK", "KOTAKBANK",
    "LT", "ITC", "BAJFINANCE", "BHARTIARTL", "HCLTECH", "M&M", "MARUTI",
    "SUNPHARMA", "TITAN", "ULTRACEMCO", "ADANIENT", "ADANIPORTS", "WIPRO", "HINDUNILVR",
    "ONGC", "NTPC", "POWERGRID", "JSWSTEEL", "TATASTEEL", "COALINDIA", "BRITANNIA"
]

# 3. FOREX (Global Currency Pairs) -> Yahoo Tickers format
FOREX_PAIRS = [
    "EURUSD=X", "GBPUSD=X", "USDJPY=X", "AUDUSD=X", "USDINR=X" 
]

# 4. CRYPTO (Top Assets) -> Yahoo Tickers format
CRYPTO_PAIRS = [
    "BTC-USD", "ETH-USD", "SOL-USD", "BNB-USD", "XRP-USD", "DOGE-USD"
]

# 5. GLOBAL MACROS (The World's Pulse)
GLOBAL_MACROS = [
    "DX-Y.NYB",  # Dollar Index (Safe Haven)
    "CL=F",      # Crude Oil (Impacts Paints/Tyres/Inflation)
    "GC=F",      # Gold (Fear Gauge)
    "SI=F",      # Silver
    "^VIX"       # Volatility Index
]

# COMBINED LIST FOR MAIN LOOP
TRADING_SYMBOLS = INDICES + FNO_STOCKS # For Indian Market Logic
GLOBAL_SYMBOLS = FOREX_PAIRS + CRYPTO_PAIRS + GLOBAL_MACROS # For Global Monitoring

# Trading Configuration
TIMEFRAME = "5m" 

# Risk Management
TOTAL_CAPITAL = 50000     # ₹50,000 Starting Capital
RISK_PER_TRADE_PERCENT = 2.0 # 2% Max Risk per trade
MAX_TRADES_PER_DAY = int(os.getenv('MAX_TRADES_PER_DAY', 2))
RISK_REWARD_RATIO = 1.5   # TP = 1.5x SL (each win covers 1.5 losses)
STOP_LOSS_PERCENT = 0.40  # Balanced SL ₹100 on NIFTY 25000

# AI Model Settings
LOOKBACK_PERIOD = 60
RSI_PERIOD = 25 # Optimized by Genetic Algo (was 14)
ADX_THRESHOLD = 23 # Optimized by Genetic Algo      

# Options Trading Configuration
ENABLE_OPTIONS_TRADING = os.getenv('ENABLE_OPTIONS_TRADING', 'False').lower() in ('true', '1', 't') # Default False (Options trading disabled)

# Environment
ENVIRONMENT = os.getenv('ENVIRONMENT', 'PAPER_TRADING')

# ═══════════════════════════════════════════════════════════
# EURUSD Council of Models — Professional Forex Config
# ═══════════════════════════════════════════════════════════
EURUSD_SL_ATR_MULT = 1.5       # SL = 1.5 × ATR (dynamic)
EURUSD_TP_ATR_MULT = 3.0       # TP = 3.0 × ATR (1:2 R:R)
EURUSD_MIN_CONFIDENCE = 0.60   # Council combined confidence threshold
EURUSD_MAX_TRADES_DAY = 3      # Max trades per day (selectivity)
EURUSD_XGB_WEIGHT = 0.55       # XGBoost weight in council vote
EURUSD_GRU_WEIGHT = 0.45       # GRU weight in council vote
EURUSD_MIN_ADX = 20            # Minimum ADX for trend trading
EURUSD_SKIP_NEWS_CANDLES = 5   # Skip candles after major news
EURUSD_ACTIVE_SESSIONS = ['london_open', 'ny_overlap', 'ny_active']
EURUSD_LOOKBACK = 60           # 60 × 5min = 5 hours of history
