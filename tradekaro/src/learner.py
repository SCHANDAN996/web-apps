"""
🧠 Continuous Learner V2
Background thread that periodically retrains the Brain using recent market data.

V2 Improvements:
- Uses the new TrainingPipeline Stage 3 (incremental)
- Uses SequenceBuilder + FEATURE_COLUMNS_V2 for consistency
- Uses RobustScaler (loaded from models/scaler_v2.pkl)
- Better error handling and logging
"""

import time
import os
import threading
import numpy as np
import pandas as pd
from datetime import datetime
from src.database import TradingDB
from src.brain import TradingBrain
from src.indicators import TechnicalIndicators
from src.data_loader import SequenceBuilder
from src.feature_store import FEATURES_V2
import config.settings as settings


class ContinuousLearner:
    def __init__(self, db: TradingDB, brain: TradingBrain):
        self.db = db
        self.brain = brain
        self.interval_seconds = 4 * 60 * 60  # Every 4 hours
        self.lookback = settings.LOOKBACK_PERIOD  # 60 candles
        self.running = False
        self.seq_builder = SequenceBuilder(
            lookback=self.lookback,
            future_horizon=20,   # Was 5 — now matches hold_candles=20 in backtest
            threshold=0.005      # Was 0.001 — now matches SL 0.5% (aligned with settings)
        )

    def start(self):
        """Start the learning thread"""
        self.running = True
        self.thread = threading.Thread(target=self._learning_loop, daemon=True)
        self.thread.start()
        print("[LEARNER V2] Continuous AI Learning Thread Started.")

    def stop(self):
        """Stop the learning thread"""
        self.running = False
        print("[LEARNER V2] Stopping...")

    def _learning_loop(self):
        """Background loop to fetch fresh data and retrain"""
        while self.running:
            try:
                time.sleep(60)  # Initial wait
                print(f"[LEARNER V2] Waking up to learn... ({datetime.now()})")
                self.learn()
                print(f"[LEARNER V2] Sleeping for {self.interval_seconds/3600} hours.")
                time.sleep(self.interval_seconds)
            except Exception as e:
                print(f"[ERROR] Learner Loop Crashed: {e}")
                time.sleep(60)

    def learn(self):
        """Core learning logic using V2 pipeline."""
        try:
            symbols = settings.TRADING_SYMBOLS + settings.GLOBAL_SYMBOLS
            total_samples = 0

            for symbol in symbols:
                try:
                    # Fetch enough 1m data for MTF resampling
                    limit = 2000
                    df_1m = self.db.get_market_data(symbol, '1m', limit=limit)

                    if len(df_1m) < self.lookback * 5 + 10:
                        continue

                    # Apply MTF indicators (V2 with new features)
                    df_rich = TechnicalIndicators.apply_multi_timeframe_features(df_1m)
                    if df_rich.empty:
                        continue

                    # Build sequences using V2 features
                    X, y, _ = self.seq_builder.build_sequences(
                        df_rich, FEATURES_V2
                    )

                    if len(X) > 0:
                        # Incremental training
                        self.brain.train_incremental(X, y, epochs=3)
                        total_samples += len(X)

                except Exception as e:
                    print(f"[LEARNER V2] Error processing {symbol}: {e}")
                    continue

            if total_samples > 0:
                self.db.log_thought(
                    f"🧠 Brain V2 self-improved on {total_samples} recent market scenarios."
                )
                print(f"[LEARNER V2] ✅ Trained on {total_samples} total samples.")

        except Exception as e:
            print(f"[ERROR] Learning Failed: {e}")
