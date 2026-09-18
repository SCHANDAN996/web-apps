import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import argparse
import os

def fetch_historical_data(symbol, interval, output_file):
    print(f"Fetching {interval} data for {symbol}...")
    
    # YFinance limitations:
    # 1m data is only available for the last 7 days line by line, or via continuous fetch.
    # 5m data is available for 60 days.
    # 1h data is available for 730 days.
    
    try:
        # Ticker map for Indian market
        ticker = symbol
        if symbol == "NIFTY":
            ticker = "^NSEI"
        elif symbol == "BANKNIFTY":
            ticker = "^NSEBANK"
            
        print(f"Using Yahoo Finance ticker: {ticker}")
        
        # Calculate max period based on interval
        period = "max"
        if interval == '1m':
            period = "7d"
            print("Note: Yahoo Finance restricts 1-minute data to the last 7 days.")
        elif interval == '5m':
            period = "60d"
            print("Note: Yahoo Finance restricts 5-minute data to the last 60 days.")
            
        # Download data
        df = yf.download(tickers=ticker, period=period, interval=interval, progress=True)
        
        if df.empty:
            print(f"❌ No data found for {ticker}. Try a different symbol or interval.")
            return
            
        # Clean up column names (flatten MultiIndex if present)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)
            
        df.reset_index(inplace=True)
        
        # Standardize columns for our AI format
        df.columns = [c.lower().replace(' ', '_') for c in df.columns]
        
        # We need specific columns: symbol, timestamp, open, high, low, close, volume
        # Rename 'datetime' or 'date' to 'timestamp'
        time_col = 'datetime' if 'datetime' in df.columns else 'date'
        
        final_df = pd.DataFrame()
        final_df['symbol'] = [symbol] * len(df)
        final_df['timestamp'] = df[time_col]
        final_df['open'] = df['open']
        final_df['high'] = df['high']
        final_df['low'] = df['low']
        final_df['close'] = df['close']
        final_df['volume'] = df['volume']
        
        # Sort and save
        final_df = final_df.sort_values(by='timestamp')
        final_df.to_csv(output_file, index=False)
        
        print(f"\n✅ Success! Saved {len(final_df)} rows to {output_file}")
        print("Note: If you need 5+ years of 1-minute data, you must purchase it from a vendor (like TrueData or Zerodha API). Free public APIs restrict minute-level granularity.")
        
    except Exception as e:
        print(f"❌ Error fetching data: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch Historic NIFTY/BANKNIFTY Data directly from YFinance")
    parser.add_argument("--symbol", default="NIFTY", help="NIFTY or BANKNIFTY")
    parser.add_argument("--interval", default="1m", choices=['1m', '5m', '15m', '1h', '1d'], help="Timeframe (e.g., 1m, 5m)")
    
    args = parser.parse_args()
    
    if args.interval == '1m':
        output = "colab/export_data/market_data_1m_history.csv" 
    else:
        output = f"colab/export_data/market_data_{args.interval}_history.csv"
    
    # Ensure export dir exists
    dest_dir = os.path.dirname(output)
    if dest_dir:
        os.makedirs(dest_dir, exist_ok=True)
    
    fetch_historical_data(args.symbol, args.interval, output)
