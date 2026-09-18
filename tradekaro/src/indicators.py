"""
📊 Technical Indicators V2 — Expanded Feature Engineering

Original (V1): 12 base indicators + 8 MTF indicators = 20 features
New (V2): 22 base indicators + 8 MTF indicators = 30 features

New additions:
- VWAP (Volume Weighted Average Price) — institutional level
- Bollinger Bands (Width + %B) — volatility measurement
- Candlestick Patterns (Doji, Hammer, Engulfing) — price action
- Time-of-Day encoding (sin/cos cyclical) — intraday patterns
- Z-Score — statistical deviation from mean
- Volatility Ratio — current vs average volatility
"""

import pandas as pd
import numpy as np
import config.settings as settings


class TechnicalIndicators:

    # =================================================================== #
    #                       ORIGINAL V1 INDICATORS                         #
    # =================================================================== #

    @staticmethod
    def add_sma(df, period=20):
        """Simple Moving Average"""
        df[f'SMA_{period}'] = df['close'].rolling(window=period).mean()
        return df

    @staticmethod
    def add_ema(df, period=20):
        """Exponential Moving Average"""
        df[f'EMA_{period}'] = df['close'].ewm(span=period, adjust=False).mean()
        return df

    @staticmethod
    def add_rsi(df, period=14):
        """Relative Strength Index"""
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        df[f'RSI_{period}'] = 100 - (100 / (1 + rs))
        return df

    @staticmethod
    def add_macd(df, slow=26, fast=12, smooth=9):
        """Moving Average Convergence Divergence"""
        exp1 = df['close'].ewm(span=fast, adjust=False).mean()
        exp2 = df['close'].ewm(span=slow, adjust=False).mean()
        df['MACD'] = exp1 - exp2
        df['MACD_Signal'] = df['MACD'].ewm(span=smooth, adjust=False).mean()
        df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']
        return df

    @staticmethod
    def add_adx(df, period=14):
        """Average Directional Index"""
        if 'high' not in df.columns:
            df['high'] = df['close']
        if 'low' not in df.columns:
            df['low'] = df['close']

        high, low, close = df['high'], df['low'], df['close']

        plus_dm = high.diff()
        minus_dm = -low.diff()
        plus_dm[plus_dm < 0] = 0
        plus_dm[(plus_dm > minus_dm) == False] = 0
        minus_dm[minus_dm < 0] = 0
        minus_dm[(minus_dm > plus_dm) == False] = 0

        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean().replace(0, 1)

        plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)

        df['plus_di'] = plus_di
        df['minus_di'] = minus_di
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di + 1e-9)
        df['ADX'] = dx.rolling(window=period).mean().fillna(0)
        return df

    @staticmethod
    def add_atr(df, period=14):
        """Average True Range"""
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        df[f'ATR_{period}'] = true_range.rolling(window=period).mean()
        return df

    @staticmethod
    def add_keltner_channels(df, period=20, multiplier=2, atr_period=10):
        """Keltner Channels"""
        df['KC_Middle'] = df['close'].ewm(span=period, adjust=False).mean()
        df = TechnicalIndicators.add_atr(df, period=atr_period)
        atr_col = f'ATR_{atr_period}'
        df['KC_Upper'] = df['KC_Middle'] + (multiplier * df[atr_col])
        df['KC_Lower'] = df['KC_Middle'] - (multiplier * df[atr_col])
        return df

    @staticmethod
    def add_volume_shock(df, period=20):
        """Volume Shock: Current Vol vs Avg Vol"""
        avg_vol = df['volume'].rolling(window=period).mean().replace(0, 1)
        df['volume_shock'] = df['volume'] / avg_vol
        return df

    # =================================================================== #
    #                        NEW V2 INDICATORS                             #
    # =================================================================== #

    @staticmethod
    def add_vwap(df):
        """Volume Weighted Average Price — Institutional Reference Level"""
        if 'volume' not in df.columns or df['volume'].sum() == 0:
            df['VWAP'] = df['close']
            df['VWAP_dist'] = 0
            return df

        typical_price = (df['high'] + df['low'] + df['close']) / 3
        cum_tp_vol = (typical_price * df['volume']).cumsum()
        cum_vol = df['volume'].cumsum().replace(0, 1)
        df['VWAP'] = cum_tp_vol / cum_vol
        # Distance from VWAP (normalized)
        df['VWAP_dist'] = (df['close'] - df['VWAP']) / (df['VWAP'] + 1e-9)
        return df

    @staticmethod
    def add_bollinger_bands(df, period=20, std_dev=2):
        """Bollinger Bands — Volatility Envelope"""
        sma = df['close'].rolling(window=period).mean()
        std = df['close'].rolling(window=period).std()

        df['BB_Upper'] = sma + (std_dev * std)
        df['BB_Lower'] = sma - (std_dev * std)
        # Band Width (normalized volatility)
        df['BB_Width'] = (df['BB_Upper'] - df['BB_Lower']) / (sma + 1e-9)
        # %B (position within bands: 0=lower, 1=upper)
        df['BB_pctB'] = (df['close'] - df['BB_Lower']) / (df['BB_Upper'] - df['BB_Lower'] + 1e-9)
        return df

    @staticmethod
    def add_candlestick_patterns(df):
        """Basic Candlestick Pattern Detection (numerical encoding)"""
        if 'open' not in df.columns:
            df['candle_body'] = 0
            df['candle_shadow'] = 0
            return df

        body = abs(df['close'] - df['open'])
        total_range = (df['high'] - df['low']).replace(0, 1)

        # Body ratio (small body = indecision)
        df['candle_body'] = body / total_range

        # Upper shadow ratio (selling pressure)
        upper_shadow = df['high'] - df[['close', 'open']].max(axis=1)
        df['candle_shadow'] = upper_shadow / total_range

        return df

    @staticmethod
    def add_time_encoding(df):
        """Cyclical Time-of-Day Encoding using sin/cos"""
        if not isinstance(df.index, pd.DatetimeIndex):
            df['time_sin'] = 0
            df['time_cos'] = 0
            return df

        # Hour + minute as fraction of day (0-1)
        time_frac = (df.index.hour * 60 + df.index.minute) / (24 * 60)
        df['time_sin'] = np.sin(2 * np.pi * time_frac)
        df['time_cos'] = np.cos(2 * np.pi * time_frac)
        return df

    @staticmethod
    def add_zscore(df, period=20):
        """Z-Score — How far price deviates from its recent mean (in std devs)"""
        rolling_mean = df['close'].rolling(window=period).mean()
        rolling_std = df['close'].rolling(window=period).std().replace(0, 1)
        df['zscore'] = (df['close'] - rolling_mean) / rolling_std
        return df

    @staticmethod
    def add_volatility_ratio(df, short_period=5, long_period=50):
        """Volatility Ratio — Short-term vs Long-term volatility"""
        if f'ATR_{short_period}' not in df.columns:
            df = TechnicalIndicators.add_atr(df, period=short_period)

        short_atr = df[f'ATR_{short_period}']
        long_atr = df['close'].rolling(window=long_period).std().replace(0, 1)
        df['vol_ratio'] = short_atr / long_atr
        return df

    # =================================================================== #
    #                     V4 ENGINEERED FEATURES (Brain Smart Inputs)       #
    # =================================================================== #

    @staticmethod
    def add_engineered_features(df):
        """
        Derived trading signals that make brain learning MUCH easier.
        Instead of raw EMA values, give brain the SIGNAL (up/down/zone).
        """
        # Trend direction: 1=uptrend, -1=downtrend
        if 'SMA_20' in df.columns and 'EMA_50' in df.columns:
            df['ema_trend'] = np.where(df['SMA_20'] > df['EMA_50'], 1, -1).astype(float)
        
        # Price vs EMA50: how far above/below trend (normalized)
        if 'EMA_50' in df.columns:
            df['price_vs_ema'] = (df['close'] - df['EMA_50']) / (df['EMA_50'] + 1e-9)
        
        # MACD crossover state: 1=bullish, -1=bearish
        if 'MACD' in df.columns and 'MACD_Signal' in df.columns:
            df['macd_cross'] = np.where(df['MACD'] > df['MACD_Signal'], 1, -1).astype(float)
        
        # RSI zone: 0=oversold(<30), 1=normal(30-70), 2=overbought(>70)
        rsi_col = 'RSI_14' if 'RSI_14' in df.columns else ('RSI' if 'RSI' in df.columns else None)
        if rsi_col:
            df['rsi_zone'] = np.where(df[rsi_col] < 30, 0, np.where(df[rsi_col] > 70, 2, 1)).astype(float)
        
        # ADX strength (normalized 0-1)
        if 'ADX' in df.columns:
            df['adx_strength'] = (df['ADX'] / 50).clip(0, 2)
        
        # DI crossover: 1=bullish (+DI > -DI), -1=bearish
        if 'plus_di' in df.columns and 'minus_di' in df.columns:
            df['di_cross'] = np.where(df['plus_di'] > df['minus_di'], 1, -1).astype(float)
        
        # Candle momentum (close-open)/close (normalized)
        if 'open' in df.columns:
            df['candle_momentum'] = (df['close'] - df['open']) / (df['close'] + 1e-9)
        
        # Relative volatility (ATR/close)
        atr_col = 'ATR_14' if 'ATR_14' in df.columns else ('ATR_10' if 'ATR_10' in df.columns else None)
        if atr_col:
            df['rel_volatility'] = df[atr_col] / (df['close'] + 1e-9)
        
        # Price velocity (5-candle ROC)
        df['price_velocity'] = df['close'].pct_change(5).fillna(0)
        
        return df

    # =================================================================== #
    #                      APPLY ALL INDICATORS                            #
    # =================================================================== #

    @staticmethod
    def apply_all(df):
        """Apply all V1 + V2 + V4 indicators."""
        # Ensure standard column names
        if 'close' not in df.columns and 'intc' in df.columns:
            df['close'] = df['intc']
        if 'high' not in df.columns and 'inth' in df.columns:
            df['high'] = df['inth']
        if 'low' not in df.columns and 'intl' in df.columns:
            df['low'] = df['intl']
        if 'volume' not in df.columns and 'intv' in df.columns:
            df['volume'] = df['intv']
        if 'open' not in df.columns and 'into' in df.columns:
            df['open'] = df['into']

        rsi_period = getattr(settings, 'RSI_PERIOD', 14)

        # --- V1 Indicators ---
        df = TechnicalIndicators.add_sma(df)
        df = TechnicalIndicators.add_ema(df, period=50)
        df = TechnicalIndicators.add_rsi(df, period=rsi_period)
        df = TechnicalIndicators.add_macd(df)
        df = TechnicalIndicators.add_adx(df)
        df = TechnicalIndicators.add_atr(df)
        df = TechnicalIndicators.add_keltner_channels(df)
        df = TechnicalIndicators.add_volume_shock(df)

        # --- V2 New Indicators ---
        df = TechnicalIndicators.add_vwap(df)
        df = TechnicalIndicators.add_bollinger_bands(df)
        df = TechnicalIndicators.add_candlestick_patterns(df)
        df = TechnicalIndicators.add_time_encoding(df)
        df = TechnicalIndicators.add_zscore(df)
        df = TechnicalIndicators.add_volatility_ratio(df)

        # --- V4 Engineered Features (for Brain V3) ---
        df = TechnicalIndicators.add_engineered_features(df)

        return df.dropna()

    # =================================================================== #
    #                    MULTI-TIMEFRAME RESAMPLING                        #
    # =================================================================== #

    @staticmethod
    def resample_timeframe(df_1m, timeframe):
        """Resamples 1m DataFrame into a higher timeframe."""
        if df_1m.empty:
            return df_1m

        if not isinstance(df_1m.index, pd.DatetimeIndex):
            if 'timestamp' in df_1m.columns:
                df_1m['timestamp'] = pd.to_datetime(df_1m['timestamp'], utc=True)
                df_1m.set_index('timestamp', inplace=True)
            else:
                return df_1m

        pd_freq = timeframe
        if pd_freq.endswith('m') and pd_freq not in ['1m', '1h', '4h', '1d']:
            pd_freq = pd_freq.replace('m', 'min')

        agg_dict = {
            'open': 'first', 'high': 'max', 'low': 'min',
            'close': 'last', 'volume': 'sum'
        }
        # Only aggregate columns that exist
        agg_dict = {k: v for k, v in agg_dict.items() if k in df_1m.columns}

        resampled_df = df_1m.resample(pd_freq).agg(agg_dict).dropna()
        return resampled_df

    @staticmethod
    def apply_multi_timeframe_features(df_1m):
        """
        Takes raw 1m data → resamples into 5m, 15m, 1h.
        Calculates all indicators for each timeframe.
        Merges 15m and 1h indicators onto 5m base (forward filled).
        """
        if df_1m.empty or len(df_1m) < 60:
            return pd.DataFrame()

        df_5m = TechnicalIndicators.resample_timeframe(df_1m, '5min')
        df_15m = TechnicalIndicators.resample_timeframe(df_1m, '15min')
        df_1h = TechnicalIndicators.resample_timeframe(df_1m, '1h')

        if len(df_5m) < 60:
            return pd.DataFrame()

        # Apply ALL indicators (V1 + V2)
        df_5m = TechnicalIndicators.apply_all(df_5m)
        df_15m = TechnicalIndicators.apply_all(df_15m)
        df_1h = TechnicalIndicators.apply_all(df_1h)

        # Prefix and merge higher timeframes
        cols_15m = ['EMA_50', 'SMA_20', 'RSI_14', 'MACD', 'ADX']
        cols_1h = ['EMA_50', 'RSI_14', 'ADX']

        df_15m_f = df_15m[[c for c in cols_15m if c in df_15m.columns]].copy()
        df_15m_f.columns = [f"15m_{c}" for c in df_15m_f.columns]

        df_1h_f = df_1h[[c for c in cols_1h if c in df_1h.columns]].copy()
        df_1h_f.columns = [f"1H_{c}" for c in df_1h_f.columns]

        merged = df_5m.join(df_15m_f, how='left')
        merged = merged.join(df_1h_f, how='left')

        merged.ffill(inplace=True)
        merged.bfill(inplace=True)

        return merged
