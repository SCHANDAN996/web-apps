import time
import subprocess
import datetime
import os
import sys
from src.database import TradingDB
from src.social_connector import SocialDataConnector
import data_downloader

# Windows process check helper
def is_data_engine_running():
    try:
        wmic_cmd = "wmic process where \"name='python.exe'\" get commandline, processid"
        output = subprocess.check_output(wmic_cmd, shell=True, stderr=subprocess.DEVNULL).decode()
        return 'main.py' in output
    except:
        return False

def log(msg):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp}] [OVERNIGHT-BRAIN] {msg}"
    print(log_msg)
    try:
        if not os.path.exists('logs'): os.makedirs('logs')
        # UTF-8 encoding for file is fine, but print can fail
        with open("logs/overnight_training.log", "a", encoding="utf-8") as f:
            f.write(log_msg + "\n")
    except Exception:
        pass

def fetch_and_store_data():
    """Compiles all data fetching logic"""
    log("[DATA] Starting Data Collection Cycle...")
    db = TradingDB()
    social = SocialDataConnector()
    
    # 1. Social Data (Twitter/Web)
    try:
        log("   > Fetching Social/Web Sentiment...")
        sentiment_data = social.fetch_social_sentiment()
        count = 0
        for item in sentiment_data:
            db.store_news(item)
            count += 1
        log(f"   > Stored {count} new social signals.")
    except Exception as e:
        log(f"   [ERROR] Social Fetch Failed: {e}")
        
    # 2. Market Data (Quick Update)
    try:
        log("   > Updating Market Data (Last 5 Days)...")
        # Run in quick_mode=True to avoid rate limits
        data_downloader.download_historical_data(quick_mode=True) 
        log("   > Market Data Updated.")
    except Exception as e:
        log(f"   [ERROR] Market Data Update Failed: {e}")
            
    db.close()

def run_training_cycle():
    log("[TRAIN] Starting Deep Learning Retraining...")
    start_time = time.time()
    
    try:
        # Run train_model.py
        result = subprocess.run([sys.executable, "train_model.py"], capture_output=True, text=True)
        
        duration = round(time.time() - start_time, 2)
        
        if result.returncode == 0:
            log(f"[SUCCESS] Model Retraining Complete! (Took {duration}s)")
            # Log relevant output lines
            output_lines = result.stdout.split('\n')
            for line in output_lines:
                if "Training on" in line or "Accuracy" in line or "Saved" in line:
                    log(f"   >> {line.strip()}")
        else:
            log(f"[FAIL] Retraining Failed: {result.stderr}")
            
    except Exception as e:
        log(f"[ERROR] Critical Error in Training Cycle: {e}")

def main():
    log("==========================================")
    log("[INIT] OVERNIGHT TRAINING AGENT STARTING")
    log("==========================================")
    log("   - Task: Fetch Data (Twitter/Web/Market) & Retrain AI")
    log("   - Schedule: Every 30 minutes")
    
    cycle_count = 1
    
    while True:
        log(f"\n=== Cycle #{cycle_count} ===")
        
        # 1. Arranging Data (as requested by User)
        fetch_and_store_data()
        
        # 2. Training AI
        run_training_cycle()
        
        log("[SLEEP] Brain entering sleep mode for 30 minutes...")
        cycle_count += 1
        
        # Sleep for 30 minutes (1800 seconds)
        time.sleep(1800)

if __name__ == "__main__":
    main()
