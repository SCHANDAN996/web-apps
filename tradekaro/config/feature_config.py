"""
Central Feature Configuration & Versioning for TradeKaro AI
Single source of truth for all ML model feature sets and versioning.

Every name here is spelled exactly as TechnicalIndicators emits it. That is
the whole point of this file, and it was not true before: four lists disagreed
with each other and with the indicators, and every consumer dropped whatever
did not match without saying so.

    src/feature_store.py FEATURES_V2   14 names, 1 absent (RSI_14)  -> 13 used
    src/feature_store.py FEATURES_V4   20 names, 2 absent           -> 18 used
    config/feature_config.py           18 names, 6 absent (case)    -> 12 used
    a fourth copy inline at main.py:253 shadowing the import

The trainer built on the first list and got 13 columns, which is why the model
carries input_size=13 -- not a considered choice, just RSI_14 going missing in
silence. Inference asked for the third list, got 12, and the model refused to
predict on a short vector by returning a neutral 0.5. That is the whole story
of 22 July to 6 August with no trades.

Use select_features() rather than a list comprehension over df.columns. A
comprehension is what silently produced the short vectors; select_features
raises instead.
"""

# RSI_25 is the RSI the indicators actually compute. Both older lists asked for
# RSI_14 and neither noticed it was never there, so RSI has in practice never
# reached the model. It is included here because both lists clearly meant to.
FEATURES = [
    'close',

    # Trend
    'SMA_20', 'EMA_50',

    # MACD
    'MACD', 'MACD_Signal', 'MACD_Hist',

    # Directional movement
    'plus_di', 'minus_di', 'ADX',

    # Momentum
    'RSI_25',

    # Volume
    'volume_shock',

    # Derived signals -- relative rather than absolute, so they carry across
    # symbols priced decades apart (NIFTY at 24000, a midcap at 500)
    'ema_trend', 'price_vs_ema', 'macd_cross',
    'adx_strength', 'di_cross', 'candle_momentum',
    'rel_volatility', 'price_velocity',
]

FEATURE_VERSION = 'v5'
REQUIRED_FEATURE_COUNT = len(FEATURES)

# Older name, kept so existing imports keep working. Same list.
V4_FEATURES = FEATURES


def select_features(df, features=None):
    """Return df[features] in order, or raise saying exactly what is missing.

    The raise is the feature. Silently returning the intersection is what let
    a spelling mismatch masquerade as a quiet market for two weeks.
    """
    features = features or FEATURES
    missing = [c for c in features if c not in df.columns]
    if missing:
        raise KeyError(
            f"{len(missing)} of {len(features)} features missing from the "
            f"indicator output: {missing}. Either TechnicalIndicators stopped "
            f"emitting them or this list drifted from what it emits.")
    return df[features]


def describe_coverage(df, features=None):
    """Non-raising counterpart, for diagnostics and startup checks."""
    features = features or FEATURES
    present = [c for c in features if c in df.columns]
    missing = [c for c in features if c not in df.columns]
    return {
        'expected': len(features),
        'present': len(present),
        'missing': missing,
        'complete': not missing,
    }
