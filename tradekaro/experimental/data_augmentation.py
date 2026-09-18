"""
🔧 Data Augmentation — Generate Synthetic Market Data

Creates realistic synthetic scenarios for training:
  - Flash crash simulation
  - V-shaped recovery
  - Sideways chop with noise
  - Trend day with controlled momentum
"""

import numpy as np
import pandas as pd


class DataAugmentor:
    
    def generate_crash(self, base_price=22000, length=100, crash_pct=5):
        prices = [base_price]
        for i in range(length):
            if 30 < i < 50:
                ret = np.random.normal(-crash_pct/20, 0.005)
            else:
                ret = np.random.normal(0.0001, 0.002)
            prices.append(prices[-1] * (1 + ret))
        return self._to_ohlcv(prices)
    
    def generate_recovery(self, base_price=22000, length=100, drop_pct=3, recovery_pct=5):
        prices = [base_price]
        for i in range(length):
            if 20 < i < 40:
                ret = np.random.normal(-drop_pct/20, 0.003)
            elif 40 <= i < 70:
                ret = np.random.normal(recovery_pct/30, 0.004)
            else:
                ret = np.random.normal(0, 0.002)
            prices.append(prices[-1] * (1 + ret))
        return self._to_ohlcv(prices)
    
    def generate_trend(self, base_price=22000, length=200, daily_ret=0.002, noise=0.003):
        prices = [base_price]
        for _ in range(length):
            ret = np.random.normal(daily_ret, noise)
            prices.append(prices[-1] * (1 + ret))
        return self._to_ohlcv(prices)
    
    def generate_sideways(self, base_price=22000, length=200, range_pct=2):
        prices = [base_price]
        for _ in range(length):
            ret = np.random.normal(0, range_pct/100/3)
            prices.append(np.clip(prices[-1] * (1+ret), 
                         base_price*(1-range_pct/100), base_price*(1+range_pct/100)))
        return self._to_ohlcv(prices)
    
    def augment_dataset(self, n_each=5):
        all_data = []
        for _ in range(n_each):
            all_data.append(('crash', self.generate_crash()))
            all_data.append(('recovery', self.generate_recovery()))
            all_data.append(('trend_up', self.generate_trend(daily_ret=0.002)))
            all_data.append(('trend_down', self.generate_trend(daily_ret=-0.002)))
            all_data.append(('sideways', self.generate_sideways()))
        return all_data
    
    def _to_ohlcv(self, closes):
        df = pd.DataFrame()
        c = np.array(closes[1:])
        noise = np.random.uniform(0.001, 0.005, len(c))
        df['open'] = c * (1 + np.random.uniform(-0.002, 0.002, len(c)))
        df['high'] = np.maximum(c, df['open']) * (1 + noise)
        df['low'] = np.minimum(c, df['open']) * (1 - noise)
        df['close'] = c
        df['volume'] = np.random.randint(50000, 500000, len(c))
        return df
