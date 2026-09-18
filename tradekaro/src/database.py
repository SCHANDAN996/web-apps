import sqlite3
import datetime
import pandas as pd
import json
import time
import pytz

class TradingDB:
    def __init__(self, db_name='trading_data.db'):
        self.db_name = db_name
        self.conn = sqlite3.connect(self.db_name, check_same_thread=False, timeout=30)
        # WAL mode हाई कंकरेंसी (Concurrency) के लिए जरूरी है
        self.conn.execute("PRAGMA journal_mode=WAL;") 
        self.conn.execute("PRAGMA wal_autocheckpoint = 1000;") # Added to fix 56GB bug
        self.conn.execute("PRAGMA busy_timeout = 30000;") # 30s timeout
        self.create_tables()

    def _execute_retry(self, query, params=(), max_retries=5):
        """Execute query with retry logic for locking errors"""
        for i in range(max_retries):
            try:
                self.conn.execute(query, params)
                self.conn.commit()
                return
            except sqlite3.OperationalError as e:
                if 'locked' in str(e):
                    time.sleep(0.1 * (2 ** i)) # Exponential backoff
                else:
                    raise e
        raise Exception(f"Database locked after {max_retries} retries")

    def create_tables(self):
        """सभी आवश्यक टेबल्स बनाना (अगर वे मौजूद नहीं हैं)"""
        
        # 1. Trades Table: किए गए ट्रेड्स का रिकॉर्ड
        self.conn.execute('''CREATE TABLE IF NOT EXISTS trades 
                          (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                           symbol TEXT, 
                           side TEXT, 
                           price REAL, 
                           qty INTEGER, 
                           time TIMESTAMP,
                           order_id TEXT,
                           pnl REAL DEFAULT 0)''')
        
        # 2. Signals Table: AI द्वारा जनरेट किए गए सिग्नल्स का ऑडिट
        self.conn.execute('''CREATE TABLE IF NOT EXISTS signals
                           (id INTEGER PRIMARY KEY AUTOINCREMENT,
                            symbol TEXT,
                            prediction REAL,
                            sentiment TEXT,
                            time TIMESTAMP)''')

        # 3. Market Data Table: OHLCV (कैंडल) डेटा
        self.conn.execute('''CREATE TABLE IF NOT EXISTS market_data
                          (symbol TEXT,
                           timestamp TIMESTAMP,
                           open REAL,
                           high REAL,
                           low REAL,
                           close REAL,
                           volume REAL,
                           interval TEXT,
                           PRIMARY KEY (symbol, timestamp, interval))''')
        
        # 4. News Table: सेंटीमेंट स्कोर के साथ खबरें
        self.conn.execute('''CREATE TABLE IF NOT EXISTS news
                        (id INTEGER PRIMARY KEY AUTOINCREMENT,
                         symbol TEXT,
                         title TEXT,
                         publisher TEXT,
                         link TEXT UNIQUE,
                         publish_time TIMESTAMP,
                         type TEXT,
                         sentiment_score REAL DEFAULT 0)''')
        
        # 5. Delta Options 'Wide' Table (Pro Feature): ऑप्शन चेन का स्ट्राइक-वाइज डेटा
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS delta_options_wide (
                timestamp INTEGER, expiry TEXT, strike REAL, underlying TEXT, 
                underlying_price REAL, ce_ltp REAL, ce_oi INTEGER, ce_iv REAL, 
                pe_ltp REAL, pe_oi INTEGER, pe_iv REAL,
                PRIMARY KEY (underlying, expiry, strike, timestamp)
            )
        ''')

        # 6. Delta Futures Table: क्रिप्टो फ्यूचर्स स्नैपशॉट
        self.conn.execute('''CREATE TABLE IF NOT EXISTS delta_futures
                                 (symbol TEXT,
                                  timestamp TIMESTAMP,
                                  mark_price REAL,
                                  contract_type TEXT,
                                  data_json TEXT,
                                  PRIMARY KEY (symbol, timestamp))''')

        # 7. Derivatives Metrics (New for Brain Upgrade)
        # PCR (Put Call Ratio), Max Pain, IndiaVIX stored here
        self.conn.execute('''CREATE TABLE IF NOT EXISTS derivatives_metrics
                          (symbol TEXT,
                           timestamp TIMESTAMP,
                           pcr REAL,
                           total_ce_oi INTEGER,
                           total_pe_oi INTEGER,
                           max_pain REAL,
                           PRIMARY KEY (symbol, timestamp))''')

        # 8. NSE Option Chain Table (ATM +/- 30)
        self.conn.execute('''CREATE TABLE IF NOT EXISTS nse_option_chain
                          (symbol TEXT,
                           timestamp TIMESTAMP,
                           strike REAL,
                           type TEXT,
                           expiry TEXT,
                           ltp REAL,
                           oi INTEGER,
                           volume INTEGER,
                           underlying TEXT,
                           PRIMARY KEY (symbol, timestamp, strike, type))''')

        # पुराने वर्जन के डेटाबेस में न्यूज़ सेंटीमेंट कॉलम सुनिश्चित करना
        try:
            self.conn.execute("ALTER TABLE news ADD COLUMN sentiment_score REAL DEFAULT 0")
        except sqlite3.OperationalError:
            pass # कॉलम पहले से मौजूद है

        # 9. Agent Registry (The Council Memory)
        self.conn.execute('''CREATE TABLE IF NOT EXISTS agent_registry
                          (agent_name TEXT PRIMARY KEY,
                           status TEXT,
                           confidence REAL,
                           last_update TIMESTAMP,
                           details TEXT)''')

        # 10. Trade Journal (Full Trade Tracking with R:R, SL, TP, etc.)
        self.conn.execute('''CREATE TABLE IF NOT EXISTS trade_journal
                          (id INTEGER PRIMARY KEY AUTOINCREMENT,
                           trade_type TEXT DEFAULT 'PAPER',
                           symbol TEXT,
                           instrument TEXT DEFAULT 'EQ',
                           side TEXT,
                           qty INTEGER DEFAULT 1,
                           entry_price REAL,
                           exit_price REAL,
                           sl_price REAL,
                           tp_price REAL,
                           entry_time TIMESTAMP,
                           exit_time TIMESTAMP,
                           pnl REAL DEFAULT 0,
                           pnl_percent REAL DEFAULT 0,
                           rr_ratio REAL DEFAULT 0,
                           planned_rr REAL DEFAULT 2.0,
                           exit_reason TEXT,
                           confidence REAL DEFAULT 0,
                           council_reason TEXT,
                           status TEXT DEFAULT 'OPEN')''')

        self.conn.commit()

    def update_agent_state(self, agent_name, status, confidence, details=""):
        """Update the state of an AI Agent (Macro, Sentiment, etc.)"""
        try:
            timestamp = datetime.datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%Y-%m-%d %H:%M:%S')
            query = "INSERT OR REPLACE INTO agent_registry VALUES (?, ?, ?, ?, ?)"
            self._execute_retry(query, (agent_name, status, confidence, timestamp, str(details)))
        except Exception as e:
            print(f"❌ DB Error (Update Agent): {e}")

    def get_council_status(self):
        """Retrieve the latest status of The Council"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM agent_registry")
            rows = cursor.fetchall()
            status = {}
            for r in rows:
                status[r[0]] = {
                    "status": r[1],
                    "confidence": r[2],
                    "updated": r[3],
                    "details": r[4]
                }
            return status
        except Exception as e:
            print(f"❌ DB Error (Get Council): {e}")
            return {}

    def store_nse_option_chain(self, data):
        """Store Option Chain Bulk Data"""
        try:
            query = "INSERT OR REPLACE INTO nse_option_chain VALUES (?,?,?,?,?,?,?,?,?)"
            for i in range(5):
                try:
                    self.conn.executemany(query, data)
                    self.conn.commit()
                    break
                except sqlite3.OperationalError as e:
                    if 'locked' in str(e):
                        time.sleep(0.2)
                    else:
                        raise e
        except Exception as e:
            print(f"❌ DB Error (Store Options): {e}")

    def get_nse_option_chain(self, symbol):
        """Get latest option chain for a symbol"""
        try:
            # Get latest timestamp first
            cursor = self.conn.cursor()
            cursor.execute("SELECT MAX(timestamp) FROM nse_option_chain WHERE underlying = ?", (symbol,))
            result = cursor.fetchone()
            if not result or not result[0]: return [] # Handle None result
            latest_ts = result[0]
            
            # Optimize: Fetch only the NEAREST expiry to reduce payload size
            cursor.execute("SELECT DISTINCT expiry FROM nse_option_chain WHERE underlying = ? AND timestamp = ?", (symbol, latest_ts))
            expiries = [row[0] for row in cursor.fetchall()]
            
            if not expiries: return []
            
            # Sort to find nearest (Assuming ISO or Lexical sortable format)
            nearest_expiry = sorted(expiries)[0]

            query = """
                SELECT strike, type, ltp, oi, volume, expiry 
                FROM nse_option_chain 
                WHERE underlying = ? AND timestamp = ? AND expiry = ?
                ORDER BY strike ASC
            """
            cursor.execute(query, (symbol, latest_ts, nearest_expiry))
            return cursor.fetchall()
        except Exception as e:
            print(f"❌ DB Error (Get Options): {e}")
            return []

    def get_option_metrics(self, symbol):
        """
        Calculates Key Option Metrics:
        1. PCR (Put Call Ratio) = Total PE OI / Total CE OI
        2. Max Pain (Strike with max monetary loss for option buyers) - Simplified
        3. Total OI
        """
        try:
            chain = self.get_nse_option_chain(symbol)
            if not chain: return None
            
            total_pe_oi = 0
            total_ce_oi = 0
            max_ce_oi = 0
            max_pe_oi = 0
            ce_resistance_strike = 0
            pe_support_strike = 0
            
            # chain row: (strike, type, ltp, oi, volume, expiry)
            # index: 0=strike, 1=type, 3=oi
            
            for row in chain:
                strike = row[0]
                opt_type = row[1]
                oi = row[3]
                
                if opt_type == 'CE':
                    total_ce_oi += oi
                    if oi > max_ce_oi:
                        max_ce_oi = oi
                        ce_resistance_strike = strike
                else:
                    total_pe_oi += oi
                    if oi > max_pe_oi:
                        max_pe_oi = oi
                        pe_support_strike = strike
            
            pcr = round(total_pe_oi / total_ce_oi, 2) if total_ce_oi > 0 else 0
            
            return {
                "pcr": pcr,
                "total_ce_oi": total_ce_oi,
                "total_pe_oi": total_pe_oi,
                "resistance": ce_resistance_strike,
                "support": pe_support_strike,
                "sentiment": "BULLISH" if pcr > 1 else "BEARISH" # Simple heuristic
            }
        except Exception as e:
            print(f"❌ DB Error (Option Metrics): {e}")
            return None

    def log_derivative_metric(self, symbol, pcr, ce_oi, pe_oi, max_pain=0):
        """Option Chain Analysis Data को रिकॉर्ड करना"""
        try:
            # Round float values for storage efficiency
            pcr = round(float(pcr), 2)
            max_pain = round(float(max_pain), 2)
            query = "INSERT OR REPLACE INTO derivatives_metrics VALUES (?, datetime('now'), ?, ?, ?, ?)"
            self._execute_retry(query, (symbol, pcr, ce_oi, pe_oi, max_pain))
        except Exception as e:
            print(f"❌ DB Error (Derivatives Log): {e}")

    def store_wide_delta_options(self, records):
        """प्रोसेस्ड 'Wide' फॉर्मेट क्रिप्टो ऑप्शन डेटा स्टोर करना"""
        query = "INSERT OR REPLACE INTO delta_options_wide VALUES (?,?,?,?,?,?,?,?,?,?,?)"
        try:
            self.conn.executemany(query, records)
            self.conn.commit()
            # print(f"   [DB] Stored {len(records)} Wide Option records.")
        except Exception as e:
            print(f"❌ DB Error (Store Wide Options): {e}")

    def get_news_sentiment(self, symbol):
        """किसी स्टॉक के लिए न्यूज़ का औसत सेंटीमेंट स्कोर प्राप्त करना"""
        cursor = self.conn.cursor()
        query = "SELECT AVG(sentiment_score) FROM news WHERE symbol = ?"
        cursor.execute(query, (symbol,))
        result = cursor.fetchone()
        return result[0] if result[0] is not None else 0

    def store_bulk_data(self, symbol, interval, df):
        """OHLCV कैंडल डेटा को डेटाबेस में सेव करना"""
        try:
            if isinstance(df.columns, pd.MultiIndex):
                try: df.columns = df.columns.droplevel(1)
                except: pass
            
            # Round numeric columns to 2 decimal places for storage efficiency
            numeric_cols = ['open', 'high', 'low', 'close', 'volume']
            try:
                # Ensure columns exist before rounding
                existing_cols = [col for col in numeric_cols if col in df.columns]
                df[existing_cols] = df[existing_cols].round(2)
            except Exception as e:
                print(f"[WARN] Rounding Failed: {e}")

            data = []
            for index, row in df.iterrows():
                ts = index.isoformat() if hasattr(index, 'isoformat') else str(index)
                data.append((symbol, ts, float(row['Open']), float(row['High']), 
                             float(row['Low']), float(row['Close']), float(row['Volume']), interval))
            
            query = 'INSERT OR REPLACE INTO market_data (symbol, timestamp, open, high, low, close, volume, interval) VALUES (?,?,?,?,?,?,?,?)'
            
            # Manual Retry Logic for executemany
            for i in range(5):
                try:
                    self.conn.executemany(query, data)
                    self.conn.commit()
                    break
                except sqlite3.OperationalError as e:
                    if 'locked' in str(e):
                        time.sleep(0.2)
                    else:
                        raise e
        except Exception as e:
            print(f"❌ DB Error (Store Candles): {e}")

    def get_market_data(self, symbol, interval, limit=100):
        """
        Retrieves market data. 
        OPTIMIZATION: If interval > 1m and not 1d, fetches 1m data and resamples it on-the-fly.
        """
        try:
            # 1. Direct Fetch for Base Intervals
            if interval in ['1m', '1d']:
                query = f'''SELECT timestamp, open, high, low, close, volume 
                            FROM market_data 
                            WHERE symbol = ? AND interval = ? 
                            ORDER BY timestamp DESC LIMIT {limit}'''
                
                df = pd.DataFrame()
                for i in range(5):
                    try:
                        df = pd.read_sql_query(query, self.conn, params=[str(symbol), str(interval)])
                        break
                    except Exception as e:
                        if 'locked' in str(e):
                            time.sleep(0.1 * (2 ** i))
                        else:
                            print(f"❌ DB Error (Read Market Data): {e}")
                            return pd.DataFrame()
                
                if not df.empty:
                    df['timestamp'] = pd.to_datetime(df['timestamp'], format='mixed', utc=True)
                    df.set_index('timestamp', inplace=True)
                    df.sort_index(inplace=True)
                    df.columns = ['open', 'high', 'low', 'close', 'volume']
                    return df
                return pd.DataFrame()

            # 2. Resampling Logic for Derived Intervals (5m, 15m, 30m, 1h)
            else:
                # Fetch more 1m data to ensure we have enough for the resampled limit
                # roughly limit * ratio (e.g. 5m needs 5x 1m data)
                multiplier = 1
                if 'm' in interval:
                    multiplier = int(interval.replace('m', ''))
                elif 'h' in interval:
                    multiplier = int(interval.replace('h', '')) * 60
                
                required_1m_limit = limit * multiplier * 2 # Safety buffer
                
                # Fetch 1m Data
                query = f'''SELECT timestamp, open, high, low, close, volume 
                            FROM market_data 
                            WHERE symbol = ? AND interval = '1m' 
                            ORDER BY timestamp DESC LIMIT {required_1m_limit}'''
                
                df = pd.DataFrame()
                for i in range(5):
                    try:
                        df = pd.read_sql_query(query, self.conn, params=[str(symbol)])
                        break
                    except Exception as e:
                        if 'locked' in str(e):
                            time.sleep(0.1 * (2 ** i))
                        else:
                            print(f"❌ DB Error (Read Market Data Resample): {e}")
                            return pd.DataFrame()

                if not df.empty:
                    df['timestamp'] = pd.to_datetime(df['timestamp'], format='mixed', utc=True)
                    df.set_index('timestamp', inplace=True)
                    df.sort_index(inplace=True)
                    df.columns = ['open', 'high', 'low', 'close', 'volume']

                    # Pandas Resampling
                    # '1m' -> interval
                    # '1m' -> interval
                    freq_map = {
                        '1m': '1min', '5m': '5min', '15m': '15min', '30m': '30min', 
                        '1h': '1h', '1d': '1D',
                        '5min': '5min', '15min': '15min', '30min': '30min'
                    }
                    pd_freq = freq_map.get(interval, interval)
                    
                    # Fallback: if interval ends with 'm' and not in map, replace 'm' with 'min'
                    if pd_freq.endswith('m') and pd_freq not in ['1h', '4h']:
                         pd_freq = pd_freq.replace('m', 'min')

                    print(f"DEBUG REF: Resampling {interval} -> {pd_freq}")
                    
                    try:
                        resampled_df = df.resample(pd_freq).agg({
                            'open': 'first',
                            'high': 'max',
                            'low': 'min',
                            'close': 'last',
                            'volume': 'sum'
                        }).dropna()

                        return resampled_df.tail(limit)
                    
                    except Exception as e:
                        print(f"❌ Resample Error: {e}")
                        return pd.DataFrame()

                return pd.DataFrame()

        except Exception as e:
            print(f"❌ DB Error (Get Market Data): {e}")
            return pd.DataFrame()

    def clean_redundant_data(self):
        """Removes all market data that is NOT 1m or 1d to save space."""
        try:
            query = "DELETE FROM market_data WHERE interval NOT IN ('1m', '1d')"
            cursor = self.conn.cursor()
            cursor.execute(query)
            deleted_rows = cursor.rowcount
            self.conn.commit()
            print(f"🧹 Cleanup: Removed {deleted_rows} redundant rows from database.")
            
            # Optional: Vacuum to reclaim storage space
            self.conn.execute("VACUUM")
            print("🧹 Cleanup: Database optimized (VACUUM completed).")
            return deleted_rows
        except Exception as e:
            print(f"❌ DB Cleanup Error: {e}")
            return 0

    def store_news(self, news_item):
        """Data Engine से मिली खबरों को स्टोर करना"""
        try:
            query = '''INSERT OR IGNORE INTO news 
                       (symbol, title, publisher, link, publish_time, type) 
                       VALUES (?, ?, ?, ?, ?, ?)'''
            
            self.conn.execute(query, (
                news_item.get('symbol'),
                news_item.get('title'),
                news_item.get('publisher'),
                news_item.get('link'),
                news_item.get('providerPublishTime'),
                news_item.get('type', 'STORY')
            ))
            self.conn.commit()
        except Exception as e:
            print(f"❌ DB Error (Store News): {e}")

    def store_delta_futures(self, df):
        """डेल्टा फ्यूचर्स डेटा को स्टोर करना"""
        try:
            data = []
            if 'timestamp' not in df.columns:
                df['timestamp'] = datetime.datetime.now()
            
            for index, row in df.iterrows():
                symbol = row.get('symbol')
                mark_price = row.get('mark_price')
                contract_type = row.get('contract_type')
                
                # ... (rest of store_delta_futures logic if any) ...
                data_json = json.dumps(row.to_dict(), default=str)
                data.append((symbol, df['timestamp'].iloc[index], mark_price, contract_type, data_json))

            self.conn.executemany('INSERT OR REPLACE INTO delta_futures VALUES (?, ?, ?, ?, ?)', data)
            self.conn.commit()
        except Exception as e:
            print(f"❌ DB Error (Store Delta Futures): {e}")

    def store_delta_options(self, options_data):
        """
        Stores processed Delta Exchange Options Data.
        Expected data format: List of dictionaries or tuples matching schema.
        Schema: timestamp, expiry, strike, underlying, underlying_price, 
                ce_ltp, ce_oi, ce_iv, pe_ltp, pe_oi, pe_iv
        """
        try:
            # Upsert Logic
            query = '''INSERT OR REPLACE INTO delta_options_wide 
                       (timestamp, expiry, strike, underlying, underlying_price, 
                        ce_ltp, ce_oi, ce_iv, pe_ltp, pe_oi, pe_iv)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'''
            
            # Convert list of dicts to list of tuples if needed
            rows = []
            for item in options_data:
                rows.append((
                    item.get('timestamp'),
                    item.get('expiry'),
                    item.get('strike'),
                    item.get('underlying'),
                    round(float(item.get('underlying_price', 0)), 2),
                    round(float(item.get('ce_ltp', 0)), 2),
                    int(item.get('ce_oi', 0)),
                    round(float(item.get('ce_iv', 0)), 2),
                    round(float(item.get('pe_ltp', 0)), 2),
                    int(item.get('pe_oi', 0)),
                    round(float(item.get('pe_iv', 0)), 2)
                ))
            
            for i in range(5):
                try:
                    self.conn.executemany(query, rows)
                    self.conn.commit()
                    break
                except sqlite3.OperationalError as e:
                    if 'locked' in str(e):
                        time.sleep(0.2)
                    else:
                        raise e
            print(f"✅ Delta Options: Stored {len(rows)} records.")
        except Exception as e:
            print(f"❌ DB Error (Store Delta Options): {e}")


    def log_trade(self, symbol, side, price, qty, order_id):
        """किए गए ट्रेड को रिकॉर्ड करना (IST Time)"""
        price = round(price, 2)
        ist_now = datetime.datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%Y-%m-%d %H:%M:%S')
        query = "INSERT INTO trades (symbol, side, price, qty, time, order_id) VALUES (?, ?, ?, ?, ?, ?)"
        self._execute_retry(query, (symbol, side, price, qty, ist_now, order_id))

    def log_signal(self, symbol, prediction):
        """AI प्रेडिक्शन सिग्नल को रिकॉर्ड करना (IST Time)"""
        # Round prediction for storage efficiency in TEXT/JSON
        prediction = round(float(prediction), 3)
        ist_now = datetime.datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%Y-%m-%d %H:%M:%S')
        query = "INSERT INTO signals (symbol, prediction, sentiment, time) VALUES (?, ?, ?, ?)"
        sentiment = 'BULLISH' if prediction > 0.5 else 'BEARISH'
        self._execute_retry(query, (symbol, prediction, sentiment, ist_now))

    def log_thought(self, thought_text):
        """AI के 'विचार' (Logs) को DB में सेव करना for Neural Stream History"""
        try:
            # Create table if not exists (Lazy init to avoid migration script dependency)
            self.conn.execute('''CREATE TABLE IF NOT EXISTS ai_thoughts 
                               (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                                thought TEXT, 
                                time TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
            
            query = "INSERT INTO ai_thoughts (thought) VALUES (?)"
            self._execute_retry(query, (thought_text,))
        except Exception as e:
            print(f"❌ DB Log Thought Error: {e}")

    def get_recent_thoughts(self, limit=50):
        """Retrieve recent AI thoughts"""
        try:
            cursor = self.conn.cursor()
            # Ensure table exists before querying
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ai_thoughts'")
            if not cursor.fetchone(): return []
            
            cursor.execute(f"SELECT thought, time FROM ai_thoughts ORDER BY time DESC LIMIT {limit}")
            return [{"text": r[0], "time": r[1]} for r in cursor.fetchall()]
        except Exception as e:
            print(f"❌ DB Get Thoughts Error: {e}")
            return []

    def get_recent_trades(self, limit=10):
        """डैशबोर्ड के लिए हालिया ट्रेड्स प्राप्त करना"""
        cursor = self.conn.cursor()
        cursor.execute(f"SELECT * FROM trades ORDER BY time DESC LIMIT {limit}")
        return cursor.fetchall()

    def get_db_stats(self):
        """Database Stats for Data Inspector"""
        stats = {
            "db_size": "Unknown",
            "total_rows": 0,
            "symbol_count": 0,
            "details": []
        }
        try:
            import os
            if os.path.exists(self.db_name):
                size_mb = os.path.getsize(self.db_name) / (1024 * 1024)
                stats["db_size"] = f"{size_mb:.2f} MB"

            # Count total rows in market_data
            cursor = self.conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM market_data")
            stats["total_rows"] = cursor.fetchone()[0]

            # Detailed Stats by Symbol
            query = """
                SELECT symbol, interval, COUNT(*) as count, MIN(timestamp), MAX(timestamp)
                FROM market_data
                GROUP BY symbol, interval
                ORDER BY count DESC
            """
            cursor.execute(query)
            rows = cursor.fetchall()
            
            unique_symbols = set()
            for row in rows:
                unique_symbols.add(row[0])
                stats["details"].append({
                    "symbol": row[0],
                    "timeframe": row[1],
                    "count": row[2],
                    "min_date": str(row[3]),
                    "max_date": str(row[4])
                })
            
            stats["symbol_count"] = len(unique_symbols)
            
        except Exception as e:
            print(f"❌ DB Stats Error: {e}")
            
        return stats

    def get_latest_news(self, limit=50):
        """Fetch latest news with sentiment"""
        news_items = []
        try:
            cursor = self.conn.cursor()
            query = "SELECT symbol, title, publisher, link, publish_time, type, sentiment_score FROM news ORDER BY publish_time DESC LIMIT ?"
            cursor.execute(query, (limit,))
            rows = cursor.fetchall()
            
            for row in rows:
                news_items.append({
                    "symbol": row[0],
                    "title": row[1],
                    "publisher": row[2],
                    "link": row[3],
                    "time": row[4],
                    "type": row[5],
                    "sentiment": row[6]
                })
        except Exception as e:
            print(f"❌ DB News Error: {e}")
            
        return news_items

    def get_active_pnl_v2(self):
        """Calculate PnL for today's trades based on latest market data"""
        print("DEBUG: EXECUTING V2 LOGIC")
        try:
            # 1. Get Today's Trades (IST)
            ist_date = datetime.datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%Y-%m-%d')
            query = f"SELECT symbol, side, price, qty, time FROM trades WHERE time LIKE '{ist_date}%' ORDER BY time DESC"
            trades = self.conn.execute(query).fetchall()
            
            total_pnl = 0
            positions = []
            
            for symbol, side, entry_price, qty, trade_time in trades:
                # Get One Latest Price
                price_query = "SELECT close FROM market_data WHERE symbol = ? ORDER BY timestamp DESC LIMIT 1"
                current_price_row = self.conn.execute(price_query, (symbol,)).fetchone()
                
                if current_price_row:
                    current_price = current_price_row[0]
                    # Short PnL: (Entry - Current) * Qty
                    # Long PnL: (Current - Entry) * Qty
                    if side == 'S':
                        pnl = (entry_price - current_price) * qty
                    else:
                        pnl = (current_price - entry_price) * qty
                    
                    total_pnl += pnl
                    print(f"DEBUG: {symbol} PnL: {pnl}")
                    pos_dict = {
                        "symbol": symbol,
                        "side": side,
                        "action": side, 
                        "entry": float(entry_price),
                        "price": float(entry_price), 
                        "qty": int(qty),
                        "value": round(float(entry_price) * int(qty), 2),
                        "current": float(current_price),
                        "pnl": round(pnl, 2),
                        "time": trade_time,
                        "status": "OPEN"
                    }
                    # print(f"DEBUG: Pos: {pos_dict}")
                    positions.append(pos_dict)
                else:
                    # If no current price found
                    pos_dict = {
                        "symbol": symbol,
                        "side": side,
                        "action": side,
                        "entry": float(entry_price),
                        "price": float(entry_price),
                        "qty": int(qty),
                        "value": round(float(entry_price) * int(qty), 2),
                        "current": float(entry_price), 
                        "pnl": 0.0,
                        "time": trade_time,
                        "status": "OPEN"
                    }
                    # print(f"DEBUG: Else Pos: {pos_dict}")
                    positions.append(pos_dict)

            return {"total_pnl": round(total_pnl, 2), "positions": positions}
        except Exception as e:
            print(f"Error calculating PnL: {e}")
            return {"total_pnl": 0, "positions": []}

    def prune_old_data(self):
        """Purge old logs to maintain DB size automatically"""
        try:
            print("🧹 Auto-pruning old database records...")
            cursor = self.conn.cursor()
            
            # Keep latest 10,000 ai_thoughts
            cursor.execute("SELECT COUNT(*) FROM ai_thoughts")
            if cursor.fetchone()[0] > 10000:
                self._execute_retry("DELETE FROM ai_thoughts WHERE id NOT IN (SELECT id FROM ai_thoughts ORDER BY time DESC LIMIT 10000)")
            
            # Keep latest 10,000 signals
            cursor.execute("SELECT COUNT(*) FROM signals")
            if cursor.fetchone()[0] > 10000:
                self._execute_retry("DELETE FROM signals WHERE id NOT IN (SELECT id FROM signals ORDER BY time DESC LIMIT 10000)")
            
            # Remove market_data (1m) older than 7 days
            seven_days_ago = (datetime.datetime.now() - datetime.timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S')
            self._execute_retry("DELETE FROM market_data WHERE interval = '1m' AND timestamp < ?", (seven_days_ago,))
            
            # Remove nse_option_chain older than 3 days
            three_days_ago = (datetime.datetime.now() - datetime.timedelta(days=3)).strftime('%Y-%m-%d %H:%M:%S')
            self._execute_retry("DELETE FROM nse_option_chain WHERE timestamp < ?", (three_days_ago,))
            
            # Remove delta_options_wide older than 90 days.
            # The column is declared INTEGER but rows actually store datetime
            # strings, so compare against a formatted cutoff like the tables above.
            ninety_days_ago = (datetime.datetime.now() - datetime.timedelta(days=90)).strftime('%Y-%m-%d %H:%M:%S')
            self._execute_retry("DELETE FROM delta_options_wide WHERE timestamp < ?", (ninety_days_ago,))
                
            # Perform WAL Checkpoint & VACUUM to reclaim disk space
            try:
                self.conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
                # VACUUM rewrites the entire file and holds an exclusive lock for
                # minutes on a multi-GB database, so only pay that cost when there
                # is a meaningful amount of free space to reclaim.
                page_count = self.conn.execute("PRAGMA page_count;").fetchone()[0]
                free_pages = self.conn.execute("PRAGMA freelist_count;").fetchone()[0]
                if page_count and free_pages > page_count * 0.15:
                    self.conn.execute("VACUUM;")
                    print(f"✅ WAL Checkpoint & VACUUM executed ({free_pages} free pages reclaimed).")
                else:
                    print(f"✅ WAL Checkpoint OK. VACUUM skipped ({free_pages}/{page_count} pages free).")
            except Exception as ve:
                print(f"⚠️ VACUUM / Checkpoint skipped: {ve}")

            print("✅ Auto-pruning completed successfully.")
        except Exception as e:
            print(f"❌ DB Auto-pruning Error: {e}")

    def close(self):
        """डेटाबेस कनेक्शन बंद करना"""
        self.conn.close()

    # ═══════════════════════════════════════════
    # TRADE JOURNAL METHODS
    # ═══════════════════════════════════════════

    def log_trade_journal(self, trade_type, symbol, instrument, side, qty,
                          entry_price, sl_price, tp_price, confidence=0,
                          council_reason='', planned_rr=2.0, entry_time=None):
        """Log a new trade entry into the journal. Returns the trade ID."""
        try:
            entry_price = round(float(entry_price), 2) if entry_price is not None else None
            sl_price = round(float(sl_price), 2) if sl_price is not None else None
            tp_price = round(float(tp_price), 2) if tp_price is not None else None

            if entry_time is None:
                ist = pytz.timezone('Asia/Kolkata')
                entry_time = datetime.datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')
            else:
                entry_time = str(entry_time)[:19]  # Trim to YYYY-MM-DD HH:MM:SS
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO trade_journal 
                (trade_type, symbol, instrument, side, qty, entry_price, 
                 sl_price, tp_price, entry_time, confidence, council_reason, 
                 planned_rr, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'OPEN')
            ''', (trade_type, symbol, instrument, side, qty, entry_price,
                  sl_price, tp_price, entry_time, confidence, council_reason, planned_rr))
            self.conn.commit()
            trade_id = cursor.lastrowid
            return trade_id
        except Exception as e:
            print(f"❌ Trade Journal Log Error: {e}")
            return None

    def update_trade_journal_exit(self, trade_id, exit_price, exit_reason='MANUAL', exit_time=None):
        """Update a trade's exit details and calculate P&L and R:R."""
        try:
            exit_price = round(float(exit_price), 2) if exit_price is not None else None

            if exit_time is None:
                ist = pytz.timezone('Asia/Kolkata')
                exit_time = datetime.datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')
            else:
                exit_time = str(exit_time)[:19]
            cursor = self.conn.cursor()
            cursor.execute('SELECT entry_price, sl_price, side, qty FROM trade_journal WHERE id = ?', (trade_id,))
            row = cursor.fetchone()
            if not row:
                print(f"❌ Trade #{trade_id} not found")
                return
            
            entry_price, sl_price, side, qty = row
            
            # Calculate P&L
            if side == 'BUY':
                pnl = (exit_price - entry_price) * qty
            else:
                pnl = (entry_price - exit_price) * qty
            
            pnl_percent = ((exit_price - entry_price) / entry_price * 100) if entry_price else 0
            if side == 'SELL': pnl_percent = -pnl_percent
            
            # Calculate achieved R:R
            risk = abs(entry_price - sl_price) if sl_price else 1
            reward = abs(exit_price - entry_price)
            rr_ratio = round(reward / risk, 2) if risk > 0 else 0
            
            self._execute_retry('''
                UPDATE trade_journal SET 
                    exit_price = ?, exit_time = ?, pnl = ?, pnl_percent = ?,
                    rr_ratio = ?, exit_reason = ?, status = 'CLOSED'
                WHERE id = ?
            ''', (exit_price, exit_time, round(pnl, 2), round(pnl_percent, 2),
                  rr_ratio, exit_reason, trade_id))
            print(f"📊 Trade #{trade_id} CLOSED: P&L ₹{pnl:.2f} | R:R {rr_ratio}")
        except Exception as e:
            print(f"❌ Trade Journal Exit Error: {e}")

    def get_journal_trades(self, trade_type='ALL', limit=200, status='ALL', date_from=None, date_to=None):
        """Fetch trades from the journal with optional type and date filters."""
        try:
            cursor = self.conn.cursor()
            query = 'SELECT * FROM trade_journal'
            params = []
            conditions = []
            
            if trade_type != 'ALL':
                conditions.append('trade_type = ?')
                params.append(trade_type)
            if status != 'ALL':
                conditions.append('status = ?')
                params.append(status)
            if date_from:
                conditions.append('entry_time >= ?')
                params.append(f"{date_from} 00:00:00")
            if date_to:
                conditions.append('entry_time <= ?')
                params.append(f"{date_to} 23:59:59")
            
            if conditions:
                query += ' WHERE ' + ' AND '.join(conditions)
            query += ' ORDER BY entry_time DESC LIMIT ?'
            params.append(limit)
            
            cursor.execute(query, params)
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            print(f"❌ Trade Journal Fetch Error: {e}")
            return []

    def get_journal_summary(self, trade_type='ALL', date_from=None, date_to=None):
        """Get summary statistics for a trade type using SQL aggregation (fast)."""
        try:
            cursor = self.conn.cursor()
            conditions = ["status = 'CLOSED'"]
            params = []
            
            if trade_type != 'ALL':
                conditions.append('trade_type = ?')
                params.append(trade_type)
            if date_from:
                conditions.append('entry_time >= ?')
                params.append(f"{date_from} 00:00:00")
            if date_to:
                conditions.append('entry_time <= ?')
                params.append(f"{date_to} 23:59:59")
            
            where = ' WHERE ' + ' AND '.join(conditions) if conditions else ''
            
            cursor.execute(f'''
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as wins,
                    SUM(CASE WHEN pnl <= 0 THEN 1 ELSE 0 END) as losses,
                    COALESCE(SUM(pnl), 0) as total_pnl,
                    COALESCE(AVG(rr_ratio), 0) as avg_rr,
                    COALESCE(AVG(pnl), 0) as avg_pnl
                FROM trade_journal {where}
            ''', params)
            
            row = cursor.fetchone()
            total, wins, losses, total_pnl, avg_rr, avg_pnl = row
            wins = wins or 0
            losses = losses or 0
            total = total or 0
            win_rate = round(wins / total * 100, 1) if total > 0 else 0
            
            # Max drawdown from cumulative PnL
            cursor.execute(f'''
                SELECT pnl FROM trade_journal {where} ORDER BY entry_time ASC
            ''', params)
            pnl_list = [r[0] for r in cursor.fetchall() if r[0] is not None]
            max_dd = 0
            cumulative = 0
            peak = 0
            for p in pnl_list:
                cumulative += p
                if cumulative > peak:
                    peak = cumulative
                dd = peak - cumulative
                if dd > max_dd:
                    max_dd = dd
            
            return {
                'total': total,
                'wins': wins,
                'losses': losses,
                'winRate': win_rate,
                'pnl': round(total_pnl, 2),
                'avgRR': round(avg_rr, 2),
                'avgPnl': round(avg_pnl, 2),
                'maxDD': round(-max_dd, 2)
            }
        except Exception as e:
            print(f"❌ Trade Journal Summary Error: {e}")
            return {'total': 0, 'wins': 0, 'losses': 0, 'winRate': 0,
                    'pnl': 0, 'avgRR': 0, 'maxDD': 0, 'avgPnl': 0}