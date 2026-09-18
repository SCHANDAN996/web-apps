"""
🗄️ Feature Store — Centralized Feature Pipeline + Versioning

Single source for ALL features used across models:
  - Consistent feature computation
  - Feature versioning (v1, v2 features)
  - Missing feature detection
  - Feature statistics tracking
"""

import numpy as np
import pandas as pd
from datetime import datetime


# These both used to be lists of their own, and both disagreed with the list
# inference used and with what the indicators actually emit -- FEATURES_V2 asked
# for an RSI_14 that has never existed, so the trainer quietly built 13-column
# sequences and the model still carries input_size=13 because of it.
#
# There is one list now, in config/feature_config.py. The names here stay so
# existing imports (learner.py, live_train.py, chat_agent.py) keep working.
from config.feature_config import FEATURES

FEATURES_V2 = FEATURES
FEATURES_V4 = FEATURES


class FeatureStore:
    
    VERSION = 'v4'
    
    # Historical sets, kept for reading old artifacts. Note that v1/v2/v3 all
    # name RSI_14, which the indicators do not emit -- anything trained against
    # them was one column short of what it asked for and never said so.
    FEATURE_REGISTRY = {
        'v1': ['close', 'SMA_20', 'EMA_50', 'RSI_14', 'MACD', 'volume'],
        'v2': ['close', 'SMA_20', 'EMA_50', 'MACD', 'MACD_Signal', 'MACD_Hist',
               'plus_di', 'minus_di', 'ADX', 'KC_Upper', 'KC_Lower', 'KC_Middle',
               'volume_shock', 'RSI_14'],
        'v3': ['close', 'SMA_20', 'EMA_50', 'MACD', 'MACD_Signal', 'MACD_Hist',
               'plus_di', 'minus_di', 'ADX', 'KC_Upper', 'KC_Lower', 'KC_Middle',
               'volume_shock', 'RSI_14', '15m_EMA_50', '15m_SMA_20', '15m_MACD',
               '15m_ADX', '1H_EMA_50', '1H_ADX', '15m_RSI_14', '1H_RSI_14'],
        'v4': FEATURES,
        'v5': FEATURES,
    }
    
    def __init__(self, version='v3'):
        self.version = version
        self.stats = {}
    
    def get_features(self, df, version=None):
        v = version or self.version
        cols = self.FEATURE_REGISTRY.get(v, self.FEATURE_REGISTRY['v2'])
        available = [c for c in cols if c in df.columns]
        missing = [c for c in cols if c not in df.columns]
        return {'features': available, 'missing': missing, 'version': v,
                'data': df[available] if available else pd.DataFrame()}
    
    def compute_stats(self, df):
        stats = {}
        for col in df.select_dtypes(include=[np.number]).columns:
            stats[col] = {
                'mean': round(float(df[col].mean()), 4),
                'std': round(float(df[col].std()), 4),
                'min': round(float(df[col].min()), 4),
                'max': round(float(df[col].max()), 4),
                'nulls': int(df[col].isnull().sum())
            }
        self.stats = stats
        return stats
    
    def validate(self, df, version=None):
        result = self.get_features(df, version)
        completeness = len(result['features']) / max(len(result['features']) + len(result['missing']), 1)
        return {
            'completeness': round(completeness * 100, 1),
            'missing': result['missing'],
            'valid': completeness > 0.7,
            'version': result['version']
        }
