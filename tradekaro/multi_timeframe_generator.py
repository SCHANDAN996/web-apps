import pandas as pd
import argparse
import os

def process_historical_data(input_file, symbol="NIFTY"):
    print(f"Reading historical file: {input_file}...")
    
    try:
        # Load the CSV
        df = pd.read_csv(input_file)
        
        # Clean column names based on the user's screenshot ('date', 'open', 'high', 'low', 'close', 'volume')
        df.columns = [c.strip().lower() for c in df.columns]
        
        # Rename 'date' to 'timestamp' if necessary
        if 'date' in df.columns:
            df.rename(columns={'date': 'timestamp'}, inplace=True)
            
        # Ensure 'volume' exists, if not fill with 0
        if 'volume' not in df.columns:
            df['volume'] = 0
            
        # Check required columns
        required_cols = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        for col in required_cols:
            if col not in df.columns:
                print(f"❌ Error: Missing required column '{col}'. Available columns: {df.columns}")
                return
                
        # Parse datetime
        print("Parsing timestamps... (this might take a few seconds for large files)")
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Add the 'symbol' column
        df['symbol'] = symbol
        
        # Reorder to standard format
        df = df[['symbol', 'timestamp', 'open', 'high', 'low', 'close', 'volume']]
        
        # Sort by oldest to newest
        df = df.sort_values(by='timestamp')
        df.set_index('timestamp', inplace=True)
        
        # Define output directory
        out_dir = "colab/export_data"
        os.makedirs(out_dir, exist_ok=True)
        
        # 1. Save standard 1-minute base file
        out_1m = os.path.join(out_dir, "market_data_1m.csv")
        df.reset_index().to_csv(out_1m, index=False)
        print(f"✅ Saved 1-Minute Data: {out_1m} ({len(df)} rows)")
        
        # 2. Resampling Rules (How to convert 1m to other timeframes)
        ohlc_dict = {
            'symbol': 'first',
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }
        
        timeframes = {
            '5m': '5min',
            '15m': '15min',
            '30m': '30min',
            '1h': 'h',
            '1d': 'd'
        }
        
        print("\n⏳ Auto-generating higher timeframes...")
        
        # Resample and save each timeframe
        for name, tf in timeframes.items():
            try:
                # Resample
                resampled_df = df.resample(tf).agg(ohlc_dict)
                # Drop empty rows (weekends/nights when market is closed)
                resampled_df.dropna(inplace=True) 
                
                # Save to CSV
                out_path = os.path.join(out_dir, f"market_data_{name}.csv")
                resampled_df.reset_index().to_csv(out_path, index=False)
                print(f"✅ Generated {name} Data: {out_path} ({len(resampled_df)} rows)")
            except Exception as e:
                print(f"⚠️ Failed to generate {name} timeframe: {e}")
                
        print("\n🎉 ALL DONE!")
        print("Next Steps for you:")
        print("1. Upload 'market_data_1m.csv' to Colab.")
        print("2. Run the PPO Transformer on the 1m data first.")
        print("3. When done, you can repeat by modifying the Colab script to read the 5m, 15m, etc. files for timeframe-specific training.")

    except Exception as e:
        print(f"❌ Critical Error processing file: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert 1m base CSV into all timeframes (5m, 15m, 30m, 1h, 1d)")
    parser.add_argument("input_csv", help="Path to your downloaded NIFTY 1m Excel/CSV file")
    parser.add_argument("--symbol", default="NIFTY", help="Symbol name (e.g., NIFTY, RELIANCE)")
    
    args = parser.parse_args()
    if os.path.exists(args.input_csv):
        process_historical_data(args.input_csv, args.symbol)
    else:
        print(f"❌ File not found: {args.input_csv}")
