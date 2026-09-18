import sys
import os
import time

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))

from src.database import TradingDB
from src.brain import TradingBrain
from src.learner import ContinuousLearner
import config.settings as settings
import pandas as pd

def train_initial_model():
    print("🚀 Starting Initial LSTM Training...")
    
    db = TradingDB()
    brain = TradingBrain()
    learner = ContinuousLearner(db, brain)
    
    # Train only on Indices for quick upgrade (Learner will do stocks later)
    symbols = settings.INDICES
    total_samples = 0
    
    # We want to train on as much history as possible
    # Note: DB might only have what DataEngine fetched (5 days of 1m)
    # But 1m resampled to 5m is what we need.
    
    for symbol in symbols:
        try:
            print(f"👉 Processing {symbol}...")
            
            # Fetch MAX available data (limit=10000)
            # Database.get_market_data automatically resamples 1m -> 5m
            df = db.get_market_data(symbol, '5m', limit=10000)
            
            if df.empty or len(df) < 100:
                print(f"   ⚠️ Not enough data for {symbol} (Len: {len(df)})")
                continue
                
            # Prepare X, y using Learner's logic (which uses TechnicalIndicators)
            # This handles scaling and feature extraction
            X, y = learner.prepare_training_data(df)
            
            if len(X) > 0:
                print(f"   🧠 Training on {len(X)} sequences...")
                # Train with fewer epochs for speed (incremental learning continues later)
                brain.train_incremental(X, y, epochs=2)
                total_samples += len(X)
            else:
                print("   ⚠️ No training sequences generated.")
                
        except Exception as e:
            print(f"   ❌ Error training {symbol}: {e}")
            
    print(f"\n✅ Training Complete. Total Samples: {total_samples}")
    print(f"💾 Model Saved to: {brain.model_path}")

if __name__ == "__main__":
    train_initial_model()
