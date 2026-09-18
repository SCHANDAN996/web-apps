"""
📊 Forex Feature Engineering — Council of Models Feature Store
25 features organized by model specialization.

Model 1 (XGBoost): ALL 25 features (tabular snapshot)
Model 2 (GRU):     12 sequential features (60-bar window)
Model 3 (Regime):  8 regime features (market state)
Model 4 (Risk):    6 risk features (volatility estimation)
"""

import numpy as np
import pandas as pd

# ═══════════════════════════════════════════════════════════
# FEATURE SETS PER MODEL
# ═══════════════════════════════════════════════════════════

# Model 1: XGBoost Direction — uses ALL features (it selects what matters)
XGB_FEATURES = [
    'close_pctchange', 'candle_body_ratio', 'candle_upper_shadow',
    'candle_lower_shadow', 'candle_momentum',
    'ema_trend', 'ema_trend_slow', 'price_vs_ema50', 'sma20_slope',
    'price_velocity', 'higher_highs', 'candle_consistency_5',
    'rsi_14_norm', 'rsi_slope', 'macd_hist_norm', 'macd_cross',
    'stoch_rsi', 'momentum_divergence',
    'atr_norm', 'bb_width', 'bb_pctB', 'vol_ratio', 'atr_expansion',
    'adx_norm', 'di_cross', 'di_spread',
    'session_code', 'regime_code',
    # MTF Features
    'h1_ema_trend', 'h1_rsi', 'h4_ema_trend', 'h4_rsi', 'h4_atr_norm',
    'd1_ema_trend', 'd1_rsi', 'd1_candle_body', 'mtf_agreement',
    'price_vs_h4_ema50', 'price_vs_d1_high'
]

# Model 2: GRU Sequence — only sequential features (order matters)
GRU_FEATURES = [
    'close_pctchange', 'candle_momentum', 'candle_body_ratio',
    'rsi_14_norm', 'rsi_slope', 'macd_hist_norm', 'stoch_rsi',
    'atr_norm', 'bb_pctB', 'vol_ratio',
    'ema_trend', 'ema_trend_slow', 'di_cross', 'price_velocity',
    # MTF Sequential Context
    'h1_ema_trend', 'h4_ema_trend', 'mtf_agreement'
]

# Model 3: Regime — market state features
REGIME_FEATURES = [
    'adx_norm', 'atr_norm', 'bb_width', 'vol_ratio',
    'di_spread', 'price_range_20', 'trend_consistency', 'volume_trend'
]

# Model 4: Risk — volatility estimation
RISK_FEATURES = [
    'atr_14_raw', 'atr_5_raw', 'bb_width',
    'session_vol_avg', 'regime_code', 'hour_sin'
]

# All unique features needed
ALL_FEATURES = list(set(
    XGB_FEATURES + GRU_FEATURES + REGIME_FEATURES + RISK_FEATURES
))


# ═══════════════════════════════════════════════════════════
# SESSION CLASSIFICATION
# ═══════════════════════════════════════════════════════════

def classify_session(hour_utc):
    """Classify forex session by UTC hour.
    0 = dead (Asian, NY close) — skip
    1 = active (London, NY)
    2 = peak (London-NY overlap)
    """
    if 7 <= hour_utc < 10:
        return 1   # London open
    elif 10 <= hour_utc < 13:
        return 1   # London active
    elif 13 <= hour_utc < 16:
        return 2   # London-NY overlap (BEST)
    elif 16 <= hour_utc < 20:
        return 1   # NY active
    else:
        return 0   # Dead (Asian / NY close)


def is_active_session(hour_utc):
    """Returns True if this is a tradeable session."""
    return classify_session(hour_utc) >= 1


# ═══════════════════════════════════════════════════════════
# FEATURE COMPUTATION
# ═══════════════════════════════════════════════════════════

def compute_all_features(df):
    """
    Compute all 25+ features from a 5min OHLCV DataFrame.
    Expects columns: open, high, low, close, volume (optional)
    Index should be DatetimeIndex.

    Returns DataFrame with all features added (NaN rows dropped).
    """
    df = df.copy()
    c = df['close']
    o = df['open']
    h = df['high']
    l = df['low']

    # ── PRICE ACTION (5) ──
    df['close_pctchange'] = c.pct_change().fillna(0)

    body = (c - o).abs()
    total_range = (h - l).replace(0, 1e-10)
    df['candle_body_ratio'] = body / total_range
    df['candle_upper_shadow'] = (h - pd.concat([c, o], axis=1).max(axis=1)) / total_range
    df['candle_lower_shadow'] = (pd.concat([c, o], axis=1).min(axis=1) - l) / total_range
    df['candle_momentum'] = (c - o) / (c + 1e-10)

    # ── TREND (5) ──
    ema9 = c.ewm(span=9).mean()
    ema21 = c.ewm(span=21).mean()
    ema50 = c.ewm(span=50).mean()
    sma20 = c.rolling(20).mean()

    # Continuous trend strength (not binary!) — normalized by ATR
    # This prevents XGBoost from treating it as a simple 1/-1 switch
    hl_range = (h - l).rolling(14).mean()  # Avg range for normalization
    df['ema_trend'] = (ema9 - ema21) / (hl_range + 1e-10)
    df['ema_trend_slow'] = (ema9 - ema50) / (hl_range + 1e-10)  # Longer-term trend
    df['price_vs_ema50'] = (c - ema50) / (ema50 + 1e-10)
    df['sma20_slope'] = (sma20 - sma20.shift(5)) / (sma20.shift(5) + 1e-10)
    df['price_velocity'] = c.pct_change(5).fillna(0)
    # Higher highs: 1 if current high > previous high AND current low > previous low
    df['higher_highs'] = np.where(
        (h > h.shift(1)) & (l > l.shift(1)), 1.0,
        np.where((h < h.shift(1)) & (l < l.shift(1)), -1.0, 0.0)
    )
    # Candle consistency: % of last 5 candles closing in same direction as EMA trend
    ema_dir = np.sign(ema9 - ema21)
    candle_dir = np.where(c > o, 1.0, -1.0)
    agreement = pd.Series(
        np.where(ema_dir == candle_dir, 1.0, 0.0), index=df.index
    )
    df['candle_consistency_5'] = agreement.rolling(5).mean().fillna(0.5)

    # ── MOMENTUM (5) ──
    delta = c.diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss_v = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / (loss_v + 1e-10)
    rsi = 100 - (100 / (1 + rs))
    df['rsi_14_norm'] = rsi / 100.0  # Normalize 0-1
    df['rsi_slope'] = (rsi - rsi.shift(5)) / 100.0  # RSI rate of change (momentum acceleration)

    e12 = c.ewm(span=12).mean()
    e26 = c.ewm(span=26).mean()
    macd = e12 - e26
    macd_signal = macd.ewm(span=9).mean()
    macd_hist = macd - macd_signal

    # ATR for normalization (compute early)
    hl = h - l
    hc = (h - c.shift()).abs()
    lc = (l - c.shift()).abs()
    tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
    atr14 = tr.rolling(14).mean()
    atr5 = tr.rolling(5).mean()

    df['macd_hist_norm'] = macd_hist / (atr14 + 1e-10)  # Normalize by ATR
    df['macd_cross'] = np.where(macd > macd_signal, 1.0, -1.0)

    # Stochastic RSI
    rsi_min = rsi.rolling(14).min()
    rsi_max = rsi.rolling(14).max()
    df['stoch_rsi'] = (rsi - rsi_min) / (rsi_max - rsi_min + 1e-10)

    # Momentum divergence: price makes new high but RSI doesn't (bearish)
    price_hh = (c.rolling(20).max() == c)
    rsi_hh = (rsi.rolling(20).max() == rsi)
    df['momentum_divergence'] = np.where(
        price_hh & ~rsi_hh, -1.0,  # Bearish divergence
        np.where(~price_hh & rsi_hh, 1.0, 0.0)  # Bullish divergence
    ).astype(float)

    # ── VOLATILITY (5) ──
    df['atr_norm'] = atr14 / (c + 1e-10)
    df['atr_14_raw'] = atr14
    df['atr_5_raw'] = atr5

    bb_sma = c.rolling(20).mean()
    bb_std = c.rolling(20).std()
    bb_upper = bb_sma + 2 * bb_std
    bb_lower = bb_sma - 2 * bb_std
    df['bb_width'] = (bb_upper - bb_lower) / (bb_sma + 1e-10)
    df['bb_pctB'] = (c - bb_lower) / (bb_upper - bb_lower + 1e-10)

    atr_avg50 = atr14.rolling(50).mean()
    df['vol_ratio'] = atr14 / (atr_avg50 + 1e-10)
    df['atr_expansion'] = atr5 / (atr14 + 1e-10)

    # ── MARKET STRUCTURE (5+) ──
    plus_dm = h.diff()
    minus_dm = -l.diff()
    plus_dm = plus_dm.where(plus_dm > 0, 0)
    plus_dm = plus_dm.where(plus_dm > minus_dm, 0)
    minus_dm = minus_dm.where(minus_dm > 0, 0)
    minus_dm = minus_dm.where(minus_dm > plus_dm, 0)

    atr_for_di = tr.rolling(14).mean().replace(0, 1)
    plus_di = 100 * (plus_dm.rolling(14).mean() / atr_for_di)
    minus_di = 100 * (minus_dm.rolling(14).mean() / atr_for_di)
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di + 1e-10)
    adx = dx.rolling(14).mean()

    df['adx_norm'] = adx / 50.0  # Normalize (ADX rarely > 50)
    df['di_cross'] = np.where(plus_di > minus_di, 1.0, -1.0)
    df['di_spread'] = (plus_di - minus_di).abs() / 50.0  # Normalized

    # Price range (20-bar normalized)
    df['price_range_20'] = (h.rolling(20).max() - l.rolling(20).min()) / (c + 1e-10)

    # Trend consistency: % of last 20 candles that closed in current trend direction
    trend_dir = np.where(c > ema50, 1, -1)
    candle_dir = np.where(c > o, 1, -1)
    agreement = pd.Series(
        np.where(trend_dir == candle_dir, 1.0, 0.0), index=df.index
    )
    df['trend_consistency'] = agreement.rolling(20).mean()

    # Volume trend (if volume exists)
    if 'volume' in df.columns and df['volume'].sum() > 0:
        vol_sma = df['volume'].rolling(20).mean()
        df['volume_trend'] = df['volume'] / (vol_sma + 1e-10)
    else:
        df['volume_trend'] = 1.0

    # ── SESSION & TIME ──
    if isinstance(df.index, pd.DatetimeIndex):
        hours = df.index.hour
        df['session_code'] = [classify_session(h) for h in hours]
        df['hour_sin'] = np.sin(2 * np.pi * hours / 24)
        df['hour_cos'] = np.cos(2 * np.pi * hours / 24)

        # Session avg volatility (historical pattern)
        df['session_vol_avg'] = df.groupby(
            df.index.hour
        )['atr_norm'].transform('mean')
    else:
        df['session_code'] = 1
        df['hour_sin'] = 0.0
        df['hour_cos'] = 0.0
        df['session_vol_avg'] = df['atr_norm'].mean()

    # ── REGIME CODE (simple rule-based, Model 3 will learn better) ──
    df['regime_code'] = np.where(
        df['vol_ratio'] > 2.0, 2,  # VOLATILE
        np.where(adx > 25, 1, 0)   # TRENDING vs RANGING
    ).astype(float)

    # ── MULTI-TIMEFRAME (MTF) FEATURES ──
    if isinstance(df.index, pd.DatetimeIndex):
        import ta
        # H1 Features
        df_h1 = df.resample('1h').agg({'open':'first', 'high':'max', 'low':'min', 'close':'last'}).dropna()
        df_h1['h1_ema9'] = ta.trend.ema_indicator(df_h1['close'], window=9)
        df_h1['h1_ema21'] = ta.trend.ema_indicator(df_h1['close'], window=21)
        df_h1['h1_ema_trend'] = np.where(df_h1['h1_ema9'] > df_h1['h1_ema21'], 1, -1)
        df_h1['h1_rsi'] = ta.momentum.rsi(df_h1['close'], window=14)
        
        # H4 Features
        df_h4 = df.resample('4h').agg({'open':'first', 'high':'max', 'low':'min', 'close':'last'}).dropna()
        df_h4['h4_ema9'] = ta.trend.ema_indicator(df_h4['close'], window=9)
        df_h4['h4_ema21'] = ta.trend.ema_indicator(df_h4['close'], window=21)
        df_h4['h4_ema50'] = ta.trend.ema_indicator(df_h4['close'], window=50)
        df_h4['h4_ema_trend'] = np.where(df_h4['h4_ema9'] > df_h4['h4_ema21'], 1, -1)
        df_h4['h4_rsi'] = ta.momentum.rsi(df_h4['close'], window=14)
        df_h4['h4_atr_norm'] = ta.volatility.average_true_range(df_h4['high'], df_h4['low'], df_h4['close']) / (df_h4['close'] + 1e-10) * 100

        # D1 Features
        df_d1 = df.resample('1D').agg({'open':'first', 'high':'max', 'low':'min', 'close':'last'}).dropna()
        df_d1['d1_ema9'] = ta.trend.ema_indicator(df_d1['close'], window=9)
        df_d1['d1_ema21'] = ta.trend.ema_indicator(df_d1['close'], window=21)
        df_d1['d1_ema_trend'] = np.where(df_d1['d1_ema9'] > df_d1['d1_ema21'], 1, -1)
        df_d1['d1_rsi'] = ta.momentum.rsi(df_d1['close'], window=14)
        df_d1['d1_high'] = df_d1['high']
        df_d1['d1_candle_body'] = np.where(df_d1['close'] > df_d1['open'], 1, -1)

        # 🛑 CRITICAL FIX: Shift by 1 to prevent data leakage! 
        # A 1-hour bar ending at 00:55 should only be available to 5-min candles AFTER 01:00.
        df_h1 = df_h1.shift(1)
        df_h4 = df_h4.shift(1)
        df_d1 = df_d1.shift(1)

        # Merge back to 5-min DataFrame and forward fill
        df = df.join(df_h1[['h1_ema_trend', 'h1_rsi']])
        df[['h1_ema_trend', 'h1_rsi']] = df[['h1_ema_trend', 'h1_rsi']].ffill()

        df = df.join(df_h4[['h4_ema50', 'h4_ema_trend', 'h4_rsi', 'h4_atr_norm']])
        df[['h4_ema50', 'h4_ema_trend', 'h4_rsi', 'h4_atr_norm']] = df[['h4_ema50', 'h4_ema_trend', 'h4_rsi', 'h4_atr_norm']].ffill()

        df = df.join(df_d1[['d1_ema_trend', 'd1_rsi', 'd1_high', 'd1_candle_body']])
        df[['d1_ema_trend', 'd1_rsi', 'd1_high', 'd1_candle_body']] = df[['d1_ema_trend', 'd1_rsi', 'd1_high', 'd1_candle_body']].ffill()

        # MTF Agreement (1 if all agree UP, -1 if all agree DOWN, else 0)
        df['mtf_agreement'] = np.where((df['h1_ema_trend'] == 1) & (df['h4_ema_trend'] == 1) & (df['d1_ema_trend'] == 1), 1,
                              np.where((df['h1_ema_trend'] == -1) & (df['h4_ema_trend'] == -1) & (df['d1_ema_trend'] == -1), -1, 0))
        
        # Context features
        df['price_vs_h4_ema50'] = (df['close'] - df['h4_ema50']) / (df['close'] + 1e-10) * 100
        df['price_vs_d1_high'] = (df['d1_high'] - df['close']) / (df['close'] + 1e-10) * 100
        
        # Normalize RSI features
        df['h1_rsi'] = (df['h1_rsi'] - 50) / 50.0
        df['h4_rsi'] = (df['h4_rsi'] - 50) / 50.0
        df['d1_rsi'] = (df['d1_rsi'] - 50) / 50.0

        # Drop intermediate columns
        df.drop(columns=['h4_ema50', 'd1_high'], inplace=True, errors='ignore')
    else:
        # Fallback if no datetime index
        for c in ['h1_ema_trend', 'h1_rsi', 'h4_ema_trend', 'h4_rsi', 'h4_atr_norm', 
                  'd1_ema_trend', 'd1_rsi', 'd1_candle_body', 'mtf_agreement', 
                  'price_vs_h4_ema50', 'price_vs_d1_high']:
            df[c] = 0.0

    # ── CLEANUP ──
    df.replace([np.inf, -np.inf], 0, inplace=True)
    df.dropna(inplace=True)

    return df


def get_model_features(df, model_name):
    """Extract features for a specific model."""
    if model_name == 'xgb':
        cols = [c for c in XGB_FEATURES if c in df.columns]
    elif model_name == 'gru':
        cols = [c for c in GRU_FEATURES if c in df.columns]
    elif model_name == 'regime':
        cols = [c for c in REGIME_FEATURES if c in df.columns]
    elif model_name == 'risk':
        cols = [c for c in RISK_FEATURES if c in df.columns]
    else:
        cols = [c for c in ALL_FEATURES if c in df.columns]
    return df[cols]
