import yfinance as yf
from src.database import TradingDB
import datetime

def download_historical_data(quick_mode=False):
    """
    Downloads historical data for key indices/stocks.
    quick_mode=True: Only fetch last 5 days (for fast updates).
    """
    print(f"[DOWNLOADER] Starting download cycle... (Quick Mode: {quick_mode})")
    
    symbols = ["^NSEI", "^NSEBANK", "BTC-USD", "ETH-USD"]
    period = "5d" if quick_mode else "1mo"
    interval = "15m" if quick_mode else "1h"
    
    db = TradingDB()
    
    for symbol in symbols:
        try:
            print(f"   > Fetching {symbol}...")
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period, interval=interval)
            
            if df.empty:
                print(f"   [WARN] No data for {symbol}")
                continue
                
            count = 0
            for timestamp, row in df.iterrows():
                # Convert timestamp to string if needed
                ts_str = str(timestamp)
                
                db.conn.execute("""
                    INSERT OR REPLACE INTO market_data 
                    (symbol, timestamp, open, high, low, close, volume, interval)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (symbol, ts_str, row['Open'], row['High'], row['Low'], row['Close'], row['Volume'], interval))
                count += 1
            
            db.conn.commit()
            print(f"   > Saved {count} candles for {symbol}")
            
        except Exception as e:
            print(f"   [ERROR] Failed {symbol}: {e}")
            
    print("[DOWNLOADER] Cycle Complete.")
    db.close()

if __name__ == "__main__":
    download_historical_data()
