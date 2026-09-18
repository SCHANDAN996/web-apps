"""
📊 ThirstyDataEngine V3 — Yahoo Finance Only
Removed all Shoonya API dependency for data fetching.
Uses yfinance exclusively for NSE stocks, indices, crypto, forex, and macros.
"""

import time
import threading
import logging
import sys
import os
import pandas as pd
import psutil
import requests
import json
from datetime import datetime, timedelta

# Keep project root in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import config.settings as settings
from src.database import TradingDB


class ThirstyDataEngine:
    def __init__(self, api_connector=None):
        self.db = TradingDB()
        self.api = api_connector  # Kept for backward compat but NOT used for data
        self.is_running = False
        self.daily_fetch_tracker = {}  # Track daily data fetches

        # Load Data Config
        self.CONFIG_FILE = 'config/data_config.json'
        self.config = self._load_config()

    def _load_config(self):
        config = {"fetch_mode": "LIVE", "auto_sync": True, "data_source": "YAHOO"}
        try:
            if os.path.exists(self.CONFIG_FILE):
                with open(self.CONFIG_FILE, 'r') as f:
                    loaded = json.load(f)
                    config.update(loaded)
        except:
            pass
        return config

    def update_config(self, new_config):
        self.config = new_config
        with open(self.CONFIG_FILE, 'w') as f:
            json.dump(self.config, f)
        print(f"[DataEngine] Config Updated: {self.config}")

    def start_drinking(self):
        """Starts the Data Ingestion Loop (Yahoo Finance based)."""
        print("[INFO] 🚰 ThirstyDataEngine V3 (Yahoo Finance Only) Activated...")
        self.is_running = True

        # Start Market Data Loop (NSE + Global)
        t1 = threading.Thread(target=self._fetch_market_data_loop)
        t1.daemon = True
        t1.start()

        # Start News Fetcher Loop
        t2 = threading.Thread(target=self._fetch_news_loop)
        t2.daemon = True
        t2.start()

        # Start Crypto Options Loop (Delta Exchange)
        t3 = threading.Thread(target=self._fetch_crypto_options_loop)
        t3.daemon = True
        t3.start()

    def _enforce_cpu_cap(self):
        """Checks CPU usage and throttles execution if > 60%."""
        try:
            usage = psutil.cpu_percent(interval=None)
            if usage > 60:
                time.sleep(5)
            elif usage > 40:
                time.sleep(2)
        except Exception:
            pass

    def _is_market_open(self):
        """Checks if Indian Market (NSE) is open (09:15-15:30 IST, Mon-Fri)."""
        utc_now = datetime.utcnow()
        ist_now = utc_now + timedelta(hours=5, minutes=30)

        # Weekend check
        if ist_now.weekday() >= 5:
            return False

        # Time check
        current_time = ist_now.time()
        start = datetime.strptime("09:15", "%H:%M").time()
        end = datetime.strptime("15:30", "%H:%M").time()

        return start <= current_time <= end

    def _get_yahoo_ticker(self, symbol):
        """Map generic symbol to Yahoo Finance ticker."""
        # Indices
        if symbol == 'NIFTY':
            return '^NSEI'
        if symbol == 'BANKNIFTY':
            return '^NSEBANK'
        if symbol == 'FINNIFTY':
            return 'NIFTY_FIN_SERVICE.NS'

        # Global Assets (already in Yahoo format)
        if '-' in symbol or '=X' in symbol or '^' in symbol:
            return symbol

        # NSE Stocks
        return f"{symbol}.NS"

    def _fetch_yahoo_data_with_retry(self, ticker_obj, period="5d", interval="1m", retries=3):
        """Fetches ticker history with exponential backoff retries."""
        for attempt in range(retries):
            try:
                df = ticker_obj.history(period=period, interval=interval)
                if df is not None and not df.empty:
                    return df
            except Exception as e:
                if attempt < retries - 1:
                    sleep_sec = 2 ** attempt
                    time.sleep(sleep_sec)
                else:
                    raise e
        return pd.DataFrame()

    def _fetch_yahoo_data(self, symbol, db_symbol=None):
        """Fetches 1m and 1d data from Yahoo Finance with retry and stores in DB."""
        try:
            target_db_symbol = db_symbol if db_symbol else symbol
            import yfinance as yf
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                ticker = yf.Ticker(symbol)

                # === 1-Minute Data (Last 5 days) ===
                try:
                    df = self._fetch_yahoo_data_with_retry(ticker, period="5d", interval="1m", retries=3)
                    if not df.empty:
                        df.reset_index(inplace=True)
                        if 'Datetime' not in df.columns and 'Date' in df.columns:
                            df = df.rename(columns={'Date': 'Datetime'})
                        if df['Datetime'].dt.tz is not None:
                            df['Datetime'] = df['Datetime'].dt.tz_localize(None)
                        df.set_index('Datetime', inplace=True)
                        self.db.store_bulk_data(target_db_symbol, '1m', df)
                        # Only log occasionally to reduce noise
                        if len(df) > 100:
                            print(f"[DATA] ✅ {target_db_symbol}: {len(df)} candles (1m)")
                except Exception as e:
                    print(f"[DATA] ⚠️ 1m fetch failed for {target_db_symbol} after retries: {e}")

                # === Daily Data (Last 1 year) — Only fetch once per 4 hours ===
                last_fetch = self.daily_fetch_tracker.get(f"{target_db_symbol}_daily")
                if not last_fetch or (datetime.now() - last_fetch).total_seconds() > 14400:
                    try:
                        df_d = self._fetch_yahoo_data_with_retry(ticker, period="1y", interval="1d", retries=3)
                        if not df_d.empty:
                            df_d.reset_index(inplace=True)
                            if 'Datetime' not in df_d.columns and 'Date' in df_d.columns:
                                df_d = df_d.rename(columns={'Date': 'Datetime'})
                            if df_d['Datetime'].dt.tz is not None:
                                df_d['Datetime'] = df_d['Datetime'].dt.tz_localize(None)
                            df_d.set_index('Datetime', inplace=True)
                            self.db.store_bulk_data(target_db_symbol, '1d', df_d)
                            self.daily_fetch_tracker[f"{target_db_symbol}_daily"] = datetime.now()
                    except Exception as e:
                        print(f"[DATA] ⚠️ 1d fetch failed for {target_db_symbol} after retries: {e}")

        except Exception as e:
            print(f"[WARN] Yahoo Fetch Failed for {symbol}: {e}")

    def get_market_data_safe(self, symbol, interval='5m', limit=100):
        """
        Safe market data retrieval with staleness check and fallback.
        """
        df = self.db.get_market_data(symbol, interval, limit)
        if not df.empty and isinstance(df.index, pd.DatetimeIndex):
            last_time = df.index[-1]
            import pytz
            now_ist = datetime.now(pytz.timezone('Asia/Kolkata'))
            if hasattr(last_time, 'to_pydatetime'):
                last_dt = last_time.to_pydatetime()
                if last_dt.tzinfo is None:
                    last_dt = pytz.timezone('Asia/Kolkata').localize(last_dt)
                diff_mins = (now_ist - last_dt).total_seconds() / 60.0
                if diff_mins > 10 and interval != '1d':
                    print(f"⚠️ [DATA STALE] Data for {symbol} is {diff_mins:.1f} mins old. Using daily fallback.")
                    df_daily = self.db.get_market_data(symbol, '1d', limit=10)
                    if not df_daily.empty:
                        return df_daily.resample('5min').ffill().tail(limit)
        return df

    def _fetch_market_data_loop(self):
        """Main loop: Fetches data for ALL symbols using Yahoo Finance."""
        while self.is_running:
            self._enforce_cpu_cap()

            # Reload config from file (allows UI to change settings)
            self.config = self._load_config()

            # EOD mode check
            if self.config.get('fetch_mode') == 'EOD':
                self._check_eod_triggers()
                time.sleep(5)
                continue

            # Market hours check for NSE stocks
            market_open = self._is_market_open()

            try:
                # === PHASE 1: NSE Stocks + Indices ===
                if market_open:
                    # Get subscription filter
                    subs = self.config.get('subscriptions', {})
                    stock_subs = subs.get('STOCKS', {})
                    index_subs = subs.get('INDICES', {})

                    for symbol in settings.TRADING_SYMBOLS:
                        self._enforce_cpu_cap()

                        # Check subscription filter
                        category = 'INDICES' if symbol in settings.INDICES else 'STOCKS'
                        current_subs = index_subs if category == 'INDICES' else stock_subs
                        if subs and not current_subs.get(symbol, True):
                            continue

                        # Fetch from Yahoo
                        yahoo_ticker = self._get_yahoo_ticker(symbol)
                        self._fetch_yahoo_data(yahoo_ticker, db_symbol=symbol)
                        time.sleep(1.0)  # Rate limiting between symbols (CPU optimized)

                # === PHASE 2: Global Assets (24/7) ===
                for symbol in settings.GLOBAL_SYMBOLS:
                    self._enforce_cpu_cap()

                    # Check subscription filter
                    subs = self.config.get('subscriptions', {})
                    if '-' in symbol or symbol.startswith('BTC') or symbol.startswith('ETH'):
                        cat_subs = subs.get('CRYPTO', {})
                    elif '=X' in symbol:
                        cat_subs = subs.get('FOREX', {})
                    else:
                        cat_subs = subs.get('MACROS', {})

                    if subs and not cat_subs.get(symbol, True):
                        continue

                    self._fetch_yahoo_data(symbol, db_symbol=symbol)
                    time.sleep(1.0)  # Rate limiting (CPU optimized)

                # Sleep between full cycles
                if market_open:
                    time.sleep(120)  # 2 minutes during market hours (CPU optimized)
                else:
                    time.sleep(600)  # 10 minutes when market closed (CPU optimized)

            except Exception as e:
                print(f"[WARN] [DataEngine] Loop Error: {e}")
                time.sleep(60)

    def _check_eod_triggers(self):
        """Checks time for Auto-Sync Triggers (Configurable Times)"""
        now = datetime.now()
        schedule = self.config.get('eod_schedule', {})
        nse_time_str = schedule.get('NSE', '15:35')

        try:
            nh, nm = map(int, nse_time_str.split(':'))
        except (ValueError, AttributeError):
            nh, nm = 15, 35

        if now.hour == nh and now.minute == nm:
            if not getattr(self, 'nse_eod_done', False):
                print(f"[EOD] Triggering NSE End-of-Day Sync at {nse_time_str}...")
                self.nse_eod_done = True
        else:
            self.nse_eod_done = False

    def force_sync(self, target_type=None):
        """Manually triggers a full data update."""
        print(f"[SYNC] Starting Force Sync (Target: {target_type or 'ALL'})...")

        if target_type in [None, 'NSE']:
            for symbol in settings.TRADING_SYMBOLS:
                yahoo_ticker = self._get_yahoo_ticker(symbol)
                self._fetch_yahoo_data(yahoo_ticker, db_symbol=symbol)
                time.sleep(0.3)

        if target_type in [None, 'GLOBAL']:
            for symbol in settings.GLOBAL_SYMBOLS:
                self._fetch_yahoo_data(symbol, db_symbol=symbol)
                time.sleep(0.3)

        print(f"[SYNC] Completed Force Sync for {target_type or 'ALL'}")

    def _fetch_news_loop(self):
        """Fetches Market News via RSS feeds."""
        import feedparser
        rss_feeds = [
            "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
            "https://www.moneycontrol.com/rss/MCtopnews.xml",
            "https://finance.yahoo.com/news/rssindex"
        ]

        while self.is_running:
            self._enforce_cpu_cap()
            try:
                for url in rss_feeds:
                    try:
                        feed = feedparser.parse(url)
                        for entry in feed.entries[:10]:
                            try:
                                title = entry.title
                                sentiment = 0
                                if any(w in title.lower() for w in ['surge', 'jump', 'high', 'profit', 'bull']):
                                    sentiment = 0.5
                                elif any(w in title.lower() for w in ['drop', 'fall', 'loss', 'bear', 'crash']):
                                    sentiment = -0.5

                                self.db.store_news({
                                    "symbol": "MARKET",
                                    "title": entry.title,
                                    "publisher": entry.get('source', {}).get('title', 'Unknown'),
                                    "link": entry.link,
                                    "providerPublishTime": datetime.now(),
                                    "type": "RSS",
                                    "sentiment": sentiment
                                })
                            except:
                                pass
                    except:
                        pass

                time.sleep(600)  # Every 10 minutes
            except Exception as e:
                time.sleep(60)

    # --- CRYPTO DELTA EXCHANGE INTEGRATION ---
    def _sync_delta_products(self):
        """Fetches Product Metadata from Delta Exchange (Strikes, Expiry, Type)"""
        try:
            res = requests.get("https://api.delta.exchange/v2/products")
            if res.status_code == 200:
                data = res.json().get('result', [])
                self.delta_products_cache = {}
                for p in data:
                    if p['contract_type'] in ['call_options', 'put_options'] and \
                       p['underlying_asset']['symbol'] in ['BTC', 'ETH']:
                        self.delta_products_cache[p['id']] = {
                            'symbol': p['symbol'],
                            'underlying': p['underlying_asset']['symbol'],
                            'strike': float(p['strike_price']),
                            'type': 'CE' if p['contract_type'] == 'call_options' else 'PE',
                            'expiry': p['settlement_time']
                        }
                logging.info(f"[Crypto] Cached {len(self.delta_products_cache)} Delta Options Contracts.")
        except Exception as e:
            print(f"[Crypto] Product Sync Error: {e}")

    def _fetch_crypto_options_loop(self):
        """Fetches Live Crypto Options Tickers"""
        logging.info("[DataEngine] Starting Delta Exchange Options Loop...")
        self._sync_delta_products()

        last_sync = datetime.now()

        while self.is_running:
            self._enforce_cpu_cap()

            # Reload config
            self.config = self._load_config()

            if self.config.get('fetch_mode') == 'EOD':
                time.sleep(10)
                continue

            try:
                # Resync products every hour
                if (datetime.now() - last_sync).seconds > 3600:
                    self._sync_delta_products()
                    last_sync = datetime.now()

                res = requests.get("https://api.delta.exchange/v2/tickers")
                if res.status_code == 200:
                    tickers = res.json().get('result', [])

                    # Re-organizing for Wide Table
                    chain_map = {}

                    for t in tickers:
                        pid = t['product_id']
                        if pid in self.delta_products_cache:
                            meta = self.delta_products_cache[pid]
                            key = (meta['underlying'], meta['expiry'], meta['strike'])

                            if key not in chain_map:
                                chain_map[key] = {
                                    'timestamp': datetime.now(),
                                    'expiry': meta['expiry'],
                                    'strike': meta['strike'],
                                    'underlying': meta['underlying'],
                                    'underlying_price': float(t.get('spot_price') or 0),
                                    'ce_ltp': 0, 'ce_oi': 0, 'ce_iv': 0,
                                    'pe_ltp': 0, 'pe_oi': 0, 'pe_iv': 0
                                }

                            row = chain_map[key]
                            if meta['type'] == 'CE':
                                row['ce_ltp'] = float(t.get('mark_price') or 0)
                                row['ce_oi'] = int(float(t.get('oi') or 0))
                            else:
                                row['pe_ltp'] = float(t.get('mark_price') or 0)
                                row['pe_oi'] = int(float(t.get('oi') or 0))

                    if chain_map:
                        flat_data = list(chain_map.values())
                        self.db.store_delta_options(flat_data)

                time.sleep(30)  # Live Updates (CPU optimized from 3s)

            except Exception as e:
                print(f"[Crypto] Loop Error: {e}")
                time.sleep(10)