"""
📦 Professional Trading Data Loader
PyTorch Dataset & DataLoader for the Trading AI Brain.

Features:
- Proper torch.utils.data.Dataset implementation
- Configurable lookback window & future horizon
- Train/Validation/Test splitting (time-series aware — no shuffle leak)
- Data augmentation (Gaussian noise, scale jitter)
- Weighted sampling for class imbalance
- Memory-efficient chunked loading for large datasets
"""

import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset, DataLoader, WeightedRandomSampler
from sklearn.preprocessing import RobustScaler
import joblib
import os


class TradingDataset(Dataset):
    """
    PyTorch Dataset for time-series trading data.
    Each sample = (sequence of `lookback` candles, binary label).
    """

    def __init__(self, X, y, augment=False, noise_std=0.01):
        """
        Args:
            X: np.ndarray of shape (N, lookback, features)
            y: np.ndarray of shape (N,)
            augment: Whether to apply data augmentation
            noise_std: Standard deviation of Gaussian noise for augmentation
        """
        self.X = torch.tensor(X, dtype=torch.float32)
        self.y = torch.tensor(y, dtype=torch.float32)
        self.augment = augment
        self.noise_std = noise_std

    def __len__(self):
        return len(self.X)

    def __getitem__(self, idx):
        x = self.X[idx].clone()
        y = self.y[idx]

        if self.augment and self.training_mode:
            # Gaussian noise augmentation
            noise = torch.randn_like(x) * self.noise_std
            x = x + noise

            # Scale jitter (±5%)
            scale = 1.0 + (torch.rand(1).item() - 0.5) * 0.1
            x = x * scale

        return x, y

    @property
    def training_mode(self):
        """Random augmentation only 50% of the time."""
        return torch.rand(1).item() > 0.5


class SequenceBuilder:
    """
    Converts raw OHLCV + indicator DataFrames into model-ready sequences.
    Handles scaling, windowing, and label generation.
    """

    # Three labels on the 0-1 line the rest of the system already speaks:
    # bearish at 0, no opinion at the midpoint, bullish at 1.
    #
    # Integer classes (0/1/2) would need a 3-output head and CrossEntropyLoss,
    # and every consumer -- predict(), vote(), prediction_from_vote(), the
    # Council -- reads a single 0-1 scalar where 0.5 means neutral. BCELoss
    # accepts soft targets, so 0.5 trains the model toward neutral directly and
    # the existing head stays as it is.
    #
    # What matters is that direction is now IN the target. It was not before:
    # a profitable BUY setup and a profitable SELL setup both got 1, so the
    # label said only whether a setup paid off, never which way it pointed.
    SELL = 0.0
    NO_TRADE = 0.5
    BUY = 1.0
    CLASS_NAMES = {SELL: "SELL", NO_TRADE: "NO_TRADE", BUY: "BUY"}

    def __init__(self, lookback=60, future_horizon=30, threshold=0.001,
                 tp_pct=0.003, sl_pct=0.002):
        """
        Args:
            lookback: Number of past candles per sample (default: 60)
            future_horizon: How many candles ahead to predict (default: 5)
            threshold: Minimum price change for bullish label (default: 0.1%)
        """
        self.tp_pct = tp_pct
        self.sl_pct = sl_pct
        self.lookback = lookback
        self.future_horizon = future_horizon
        self.threshold = threshold
        self.scaler_path = 'models/scaler_v2.pkl'

    def build_sequences(self, df, features, scaler=None, fit_scaler=False):
        """
        Convert a DataFrame with indicator columns into (X, y) arrays.

        Args:
            df: DataFrame with 'close' column and indicator features
            features: List of column names to use as input features
            scaler: Optional pre-fitted scaler. If None, loads or creates one.
            fit_scaler: If True, fits the scaler on this data

        Returns:
            X: np.ndarray (N, lookback, num_features)
            y: np.ndarray (N,)
            scaler: The fitted scaler
        """
        # Filter available features
        available = [f for f in features if f in df.columns]
        if len(available) < len(features):
            missing = set(features) - set(available)
            print(f"[DataLoader] ⚠️ Missing features: {missing}")

        if len(available) == 0:
            return np.array([]), np.array([]), scaler

        raw_data = df[available].values

        # Scaling
        if scaler is None:
            scaler = self._load_or_create_scaler()

        if fit_scaler:
            # Use RobustScaler (handles outliers better than MinMaxScaler)
            scaler.fit(raw_data)
            self._save_scaler(scaler)
            print(f"[DataLoader] ✅ Scaler fitted on {len(raw_data)} samples, {len(available)} features")

        try:
            scaled_data = scaler.transform(raw_data)
        except Exception as e:
            print(f"[DataLoader] ⚠️ Scaler transform failed: {e}. Re-fitting...")
            scaler.fit(raw_data)
            scaled_data = scaler.transform(raw_data)
            self._save_scaler(scaler)

        # Replace NaN/Inf with 0
        scaled_data = np.nan_to_num(scaled_data, nan=0.0, posinf=1.0, neginf=-1.0)

        # Build sequences with SMART LABELS
        #
        # Three classes, because the previous single label could not express a
        # direction. It was `1 if profitable else 0` for buy_conditions and
        # sell_conditions alike, so the target said whether a profitable setup
        # existed and never which way it pointed -- while inference reads the
        # model's output as direction (>= 0.55 BUY, <= 0.45 SELL). Two
        # different questions sharing one number.
        #
        # Measured over 8000 BTC-USD candles under the old scheme: 17
        # positives in 1482 samples, and not one of them a BUY. A model fitted
        # on that learns to answer zero, which downstream reads as SELL on
        # everything -- exactly what the live bot did.
        X, y = [], []

        # Swept against real BTC/ETH/EURUSD candles. The old 0.6%/0.4% over a
        # 10-bar horizon produced almost nothing to learn from -- 0.4% of
        # samples carried a signal, and only 4 of 5300 were BUY:
        #
        #   horizon  TP     SL    SELL  NO_TRADE  BUY   signal
        #      10   0.6%  0.4%     18      5278     4     0.4%
        #      30   0.6%  0.4%     32      5165    43     1.4%
        #      30   0.3%  0.2%     89      5063    88     3.4%   <- this
        #      60   0.4%  0.3%     76      4982    92     3.3%
        #
        # R:R stays 1.5, and BUY and SELL come out balanced (88/89) instead of
        # 4 against 18.
        #
        # Note these are gross moves. Intraday costs run roughly 0.03-0.05%
        # round trip, so a 0.3% target keeps less headroom than 0.6% did --
        # worth revisiting against live fills before the gate is opened.
        sl_pct = self.sl_pct
        tp_pct = self.tp_pct

        for i in range(self.lookback, len(scaled_data) - self.future_horizon):
            X.append(scaled_data[i - self.lookback: i])

            current_close = df['close'].iloc[i]

            if current_close <= 0:
                y.append(self.NO_TRADE)
                continue

            # Check TA conditions at this candle
            row = df.iloc[i]
            ema50 = row.get('EMA_50', 0) or 0
            sma20 = row.get('SMA_20', 0) or 0
            adx_val = row.get('ADX', 0) or 0
            # RSI_25 is what the indicators emit. This asked for RSI_14 and
            # then RSI, neither of which exists, so it fell through to the
            # literal 50 on every row ever labelled -- the RSI term in both
            # conditions below has been a constant.
            rsi_val = row.get('RSI_25', None)
            if rsi_val is None:
                rsi_val = row.get('RSI_14', None)
            if rsi_val is None or rsi_val != rsi_val:  # missing or NaN
                rsi_val = 50
            macd_val = row.get('MACD', 0) or 0
            macd_sig = row.get('MACD_Signal', 0) or 0
            plus_di = row.get('plus_di', 0) or 0
            minus_di = row.get('minus_di', 0) or 0

            if not ema50 or not sma20 or not adx_val:
                y.append(self.NO_TRADE)
                continue

            # Check for BUY setup
            buy_trend = current_close > ema50 and sma20 > ema50
            buy_momentum = macd_val > macd_sig and plus_di > minus_di
            buy_rsi = 30 < rsi_val < 65
            buy_conditions = buy_trend and buy_momentum and buy_rsi and adx_val > 22

            # Check for SELL setup
            sell_trend = current_close < ema50 and sma20 < ema50
            sell_momentum = macd_val < macd_sig and minus_di > plus_di
            sell_rsi = 35 < rsi_val < 70
            sell_conditions = sell_trend and sell_momentum and sell_rsi and adx_val > 22

            if not buy_conditions and not sell_conditions:
                y.append(self.NO_TRADE)
                continue

            # Walk forward and see which of TP or SL the price reaches first.
            # A setup that was right about direction but got stopped out is a
            # NO_TRADE, not a signal to go the other way -- the opposite label
            # would teach the model to fade its own correct reads.
            profitable = False
            for j in range(1, min(self.future_horizon + 1, len(df) - i)):
                future_row = df.iloc[i + j]
                future_high = future_row.get('high', future_row['close'])
                future_low = future_row.get('low', future_row['close'])

                if buy_conditions:
                    if future_high >= current_close * (1 + tp_pct):
                        profitable = True
                        break
                    if future_low <= current_close * (1 - sl_pct):
                        break  # SL hit first = not profitable
                elif sell_conditions:
                    if future_low <= current_close * (1 - tp_pct):
                        profitable = True
                        break
                    if future_high >= current_close * (1 + sl_pct):
                        break  # SL hit first

            if not profitable:
                y.append(self.NO_TRADE)
            elif buy_conditions:
                y.append(self.BUY)
            else:
                y.append(self.SELL)

        return np.array(X), np.array(y), scaler

    def _load_or_create_scaler(self):
        """Load existing scaler or create new RobustScaler."""
        if os.path.exists(self.scaler_path):
            try:
                return joblib.load(self.scaler_path)
            except Exception:
                pass
        return RobustScaler()

    def _save_scaler(self, scaler):
        """Save scaler to disk."""
        os.makedirs(os.path.dirname(self.scaler_path) or 'models', exist_ok=True)
        joblib.dump(scaler, self.scaler_path)


class DataSplitter:
    """
    Time-series aware data splitting.
    
    IMPORTANT: Unlike standard ML, we NEVER shuffle time-series data.
    Train must always come BEFORE validation which comes BEFORE test.
    
    Split:  |---- Train (70%) ----|-- Val (15%) --|-- Test (15%) --|
    """

    @staticmethod
    def split(X, y, train_ratio=0.70, val_ratio=0.15):
        """
        Split data chronologically (no shuffling).

        Returns:
            (X_train, y_train), (X_val, y_val), (X_test, y_test)
        """
        n = len(X)
        train_end = int(n * train_ratio)
        val_end = int(n * (train_ratio + val_ratio))

        X_train, y_train = X[:train_end], y[:train_end]
        X_val, y_val = X[train_end:val_end], y[train_end:val_end]
        X_test, y_test = X[val_end:], y[val_end:]

        print(f"[DataSplitter] Train: {len(X_train)} | Val: {len(X_val)} | Test: {len(X_test)}")
        return (X_train, y_train), (X_val, y_val), (X_test, y_test)


def create_data_loaders(X_train, y_train, X_val, y_val,
                        batch_size=256, augment_train=True, balance_classes=True):
    """
    Create PyTorch DataLoaders with optional class balancing.

    Args:
        X_train, y_train: Training data
        X_val, y_val: Validation data
        batch_size: Batch size for training
        augment_train: Whether to augment training data
        balance_classes: Whether to use weighted sampling for class imbalance

    Returns:
        train_loader, val_loader
    """
    train_dataset = TradingDataset(X_train, y_train, augment=augment_train)
    val_dataset = TradingDataset(X_val, y_val, augment=False)

    sampler = None
    shuffle = True

    if balance_classes and len(y_train) > 0:
        # Calculate class weights
        class_counts = np.bincount(y_train.astype(int), minlength=2)
        if class_counts.min() > 0:
            weights = 1.0 / class_counts.astype(float)
            sample_weights = weights[y_train.astype(int)]
            sampler = WeightedRandomSampler(
                weights=torch.DoubleTensor(sample_weights),
                num_samples=len(sample_weights),
                replacement=True
            )
            shuffle = False  # Sampler handles ordering

            buy_pct = class_counts[1] / class_counts.sum() * 100
            print(f"[DataLoader] Class balance — BUY: {buy_pct:.1f}% | HOLD: {100-buy_pct:.1f}%")

    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=shuffle if sampler is None else False,
        sampler=sampler,
        num_workers=0,  # SQLite doesn't support multiprocess
        pin_memory=torch.cuda.is_available(),
        drop_last=True
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size * 2,  # Larger batch for validation (no grad)
        shuffle=False,
        num_workers=0,
        pin_memory=torch.cuda.is_available()
    )

    return train_loader, val_loader


# --- STANDARD FEATURE LIST (V2) ---
# This is the single source of truth for feature columns.
# All training scripts, live prediction, and learner must use this.

FEATURE_COLUMNS_V2 = [
    # Base Price + Trend
    'close', 'SMA_20', 'EMA_50', 'RSI_14', 'MACD', 'MACD_Signal', 'MACD_Hist',
    # Directional Movement
    'plus_di', 'minus_di', 'ADX',
    # Volatility
    'KC_Upper', 'KC_Lower', 'KC_Middle', 'volume_shock',
    # Multi-Timeframe (15m)
    '15m_EMA_50', '15m_SMA_20', '15m_RSI_14', '15m_MACD', '15m_ADX',
    # Multi-Timeframe (1H)
    '1H_EMA_50', '1H_RSI_14', '1H_ADX'
]
