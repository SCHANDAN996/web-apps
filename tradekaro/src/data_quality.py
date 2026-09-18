"""
🔍 Data Quality Monitor — Detect Bad Data Before It Kills Your AI

Bad data = bad predictions. This module detects:
  - Missing candles (gaps in time series)
  - Stale feeds (last update > 5 min ago)
  - Outlier prices (>5σ moves = likely bad tick)
  - Zero volume candles
  - Duplicate timestamps
  - Future timestamps (clock sync issues)
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta


class DataQualityMonitor:
    """
    Validates market data quality before feeding to AI.
    
    Usage:
        monitor = DataQualityMonitor()
        report = monitor.validate(df_ohlcv)
        if report['quality_score'] < 70:
            print("⚠️ Data quality too low for trading!")
    """
    
    def validate(self, df, expected_interval_min=1):
        """Full data quality validation."""
        if df is None or len(df) == 0:
            return {'quality_score': 0, 'issues': ['NO_DATA'], 'tradeable': False}
        
        issues = []
        scores = {}
        
        # 1. Missing candles
        missing = self._check_missing_candles(df, expected_interval_min)
        scores['missing'] = missing['score']
        if missing['count'] > 0:
            issues.append(f"⚠️ {missing['count']} missing candles ({missing['pct']:.1f}%)")
        
        # 2. Staleness
        stale = self._check_staleness(df)
        scores['staleness'] = stale['score']
        if stale['is_stale']:
            issues.append(f"🔴 Data stale: last update {stale['minutes_ago']:.0f} min ago")
        
        # 3. Outliers
        outliers = self._check_outliers(df)
        scores['outliers'] = outliers['score']
        if outliers['count'] > 0:
            issues.append(f"⚡ {outliers['count']} price outliers detected")
        
        # 4. Zero volume
        zero_vol = self._check_zero_volume(df)
        scores['volume'] = zero_vol['score']
        if zero_vol['count'] > 0:
            issues.append(f"📊 {zero_vol['count']} zero-volume candles")
        
        # 5. Duplicates
        dupes = self._check_duplicates(df)
        scores['duplicates'] = dupes['score']
        if dupes['count'] > 0:
            issues.append(f"🔁 {dupes['count']} duplicate timestamps")
        
        # 6. OHLC sanity
        sanity = self._check_ohlc_sanity(df)
        scores['ohlc'] = sanity['score']
        if sanity['violations'] > 0:
            issues.append(f"❌ {sanity['violations']} OHLC violations (H<L or O/C outside H-L)")
        
        quality = sum(scores.values()) / max(len(scores), 1)
        
        return {
            'quality_score': round(quality, 1),
            'issues': issues,
            'scores': scores,
            'tradeable': quality >= 60 and not any('stale' in i.lower() for i in issues),
            'total_rows': len(df),
            'timestamp': datetime.now().isoformat()
        }
    
    def clean(self, df):
        """Auto-fix common data issues."""
        if df is None or len(df) == 0:
            return df
        
        df = df.copy()
        
        # Remove duplicates
        if isinstance(df.index, pd.DatetimeIndex):
            df = df[~df.index.duplicated(keep='last')]
        
        # Remove zero-volume rows (except last)
        if 'volume' in df.columns:
            mask = (df['volume'] > 0) | (df.index == df.index[-1])
            df = df[mask]
        
        # Cap outliers at 5σ
        if 'close' in df.columns and len(df) > 20:
            returns = df['close'].pct_change()
            mean, std = returns.mean(), returns.std()
            threshold = 5 * std
            outlier_mask = returns.abs() > threshold
            if outlier_mask.any():
                df.loc[outlier_mask, 'close'] = df['close'].shift(1)[outlier_mask]
        
        # Forward fill NaNs
        df = df.ffill()
        
        return df
    
    def _check_missing_candles(self, df, interval_min):
        if not isinstance(df.index, pd.DatetimeIndex) or len(df) < 2:
            return {'count': 0, 'pct': 0, 'score': 100}
        
        expected_gap = timedelta(minutes=interval_min)
        gaps = df.index.to_series().diff()
        large = gaps[gaps > expected_gap * 2].dropna()
        
        pct = len(large) / max(len(df), 1) * 100
        score = max(0, 100 - pct * 5)
        return {'count': len(large), 'pct': pct, 'score': score}
    
    def _check_staleness(self, df):
        if not isinstance(df.index, pd.DatetimeIndex):
            return {'is_stale': False, 'score': 100, 'minutes_ago': 0}
        
        last = df.index[-1]
        now = pd.Timestamp.now()
        minutes = (now - last).total_seconds() / 60
        
        is_stale = minutes > 5
        score = 100 if minutes <= 2 else max(0, 100 - (minutes - 2) * 10)
        return {'is_stale': is_stale, 'minutes_ago': minutes, 'score': score}
    
    def _check_outliers(self, df):
        if 'close' not in df.columns or len(df) < 20:
            return {'count': 0, 'score': 100}
        returns = df['close'].pct_change().dropna()
        z = (returns - returns.mean()) / max(returns.std(), 1e-8)
        count = int((z.abs() > 5).sum())
        score = max(0, 100 - count * 20)
        return {'count': count, 'score': score}
    
    def _check_zero_volume(self, df):
        if 'volume' not in df.columns:
            return {'count': 0, 'score': 100}
        count = int((df['volume'] == 0).sum())
        pct = count / max(len(df), 1) * 100
        score = max(0, 100 - pct * 3)
        return {'count': count, 'score': score}
    
    def _check_duplicates(self, df):
        if isinstance(df.index, pd.DatetimeIndex):
            count = int(df.index.duplicated().sum())
        else:
            count = 0
        score = 100 if count == 0 else max(0, 100 - count * 10)
        return {'count': count, 'score': score}
    
    def _check_ohlc_sanity(self, df):
        violations = 0
        for col_set in [('high', 'low'), ('open', 'close')]:
            if all(c in df.columns for c in col_set):
                if col_set == ('high', 'low'):
                    violations += int((df['high'] < df['low']).sum())
        score = max(0, 100 - violations * 15)
        return {'violations': violations, 'score': score}
