import pandas as pd
import argparse
import os

def convert_kaggle_to_ai_format(input_file, symbol_name="NIFTY"):
    print(f"Reading {input_file}...")
    try:
        # Most Kaggle historical datasets use these common column names
        # Assuming format like: Date, Time, Open, High, Low, Close, Volume
        df = pd.read_csv(input_file)
        
        # Clean up columns (make lowercase and strip spaces)
        df.columns = [c.strip().lower() for c in df.columns]
        
        # Determine Datetime format
        if 'datetime' in df.columns:
            df['timestamp'] = pd.to_datetime(df['datetime'])
        elif 'date' in df.columns and 'time' in df.columns:
            df['timestamp'] = pd.to_datetime(df['date'] + ' ' + df['time'])
        else:
            print("❌ Cannot find 'date/time' or 'datetime' columns. Available:", df.columns)
            return
            
        # Ensure we have OHLCV
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        for col in required_cols:
            if col not in df.columns:
                print(f"❌ Missing required column: {col}")
                return
                
        # Build Final DataFrame
        final_df = pd.DataFrame()
        final_df['symbol'] = [symbol_name] * len(df)
        final_df['timestamp'] = df['timestamp']
        final_df['open'] = df['open']
        final_df['high'] = df['high']
        final_df['low'] = df['low']
        final_df['close'] = df['close']
        final_df['volume'] = df['volume']
        
        # Sort by oldest to newest
        final_df = final_df.sort_values(by='timestamp')
        
        # Save Output
        output_name = "market_data_1m_historical.csv"
        final_df.to_csv(output_name, index=False)
        print(f"✅ Successfully formatted {len(final_df)} rows!")
        print(f"File saved as: {output_name}")
        print("Upload this file to Colab, rename it to 'market_data_1m.csv', and run the notebook.")
        
    except Exception as e:
        print(f"Error processing file: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert Kaggle Historical CSV to TradeKaro AI Format")
    parser.add_argument("input_csv", help="Path to the downloaded Kaggle CSV file")
    parser.add_argument("--symbol", default="NIFTY", help="Symbol name (e.g., NIFTY, BANKNIFTY)")
    
    args = parser.parse_args()
    if os.path.exists(args.input_csv):
        convert_kaggle_to_ai_format(args.input_csv, args.symbol)
    else:
        print("File not found.")
