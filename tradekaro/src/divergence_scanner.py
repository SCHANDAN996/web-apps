"""
🔍 Divergence Scanner — Auto-Detect RSI/MACD Divergences

Bullish Divergence: Price makes LOWER low, RSI makes HIGHER low → reversal UP
Bearish Divergence: Price makes HIGHER high, RSI makes LOWER high → reversal DOWN
Hidden divergences for continuation signals
"""

import numpy as np


class DivergenceScanner:
    
    def scan(self, df, lookback=30):
        if df is None or len(df) < lookback:
            return []
        
        recent = df.tail(lookback)
        divergences = []
        
        # RSI divergence
        if 'RSI_14' in recent.columns or 'RSI' in recent.columns:
            rsi_col = 'RSI_14' if 'RSI_14' in recent.columns else 'RSI'
            rsi_div = self._find_divergence(recent['close'].values, recent[rsi_col].values, 'RSI')
            divergences.extend(rsi_div)
        
        # MACD divergence
        if 'MACD' in recent.columns:
            macd_div = self._find_divergence(recent['close'].values, recent['MACD'].values, 'MACD')
            divergences.extend(macd_div)
        
        return divergences
    
    def get_signal(self, df):
        divs = self.scan(df)
        if not divs:
            return {'signal': 'NONE', 'divergences': []}
        
        bullish = [d for d in divs if 'BULLISH' in d['type']]
        bearish = [d for d in divs if 'BEARISH' in d['type']]
        
        if bullish and not bearish:
            return {'signal': 'BULLISH_REVERSAL', 'strength': len(bullish), 'divergences': divs}
        elif bearish and not bullish:
            return {'signal': 'BEARISH_REVERSAL', 'strength': len(bearish), 'divergences': divs}
        return {'signal': 'MIXED', 'divergences': divs}
    
    def _find_divergence(self, price, indicator, name):
        results = []
        n = len(price)
        window = min(10, n // 3)
        
        # Find swing lows in both
        p_lows = self._swing_lows(price, window)
        i_lows = self._swing_lows(indicator, window)
        
        # Find swing highs
        p_highs = self._swing_highs(price, window)
        i_highs = self._swing_highs(indicator, window)
        
        # Regular Bullish: price lower low, indicator higher low
        if len(p_lows) >= 2 and len(i_lows) >= 2:
            if p_lows[-1][1] < p_lows[-2][1] and i_lows[-1][1] > i_lows[-2][1]:
                results.append({
                    'type': 'REGULAR_BULLISH',
                    'indicator': name,
                    'description': f'{name} bullish divergence — price dropped but {name} rising',
                    'strength': 'STRONG'
                })
        
        # Regular Bearish: price higher high, indicator lower high
        if len(p_highs) >= 2 and len(i_highs) >= 2:
            if p_highs[-1][1] > p_highs[-2][1] and i_highs[-1][1] < i_highs[-2][1]:
                results.append({
                    'type': 'REGULAR_BEARISH',
                    'indicator': name,
                    'description': f'{name} bearish divergence — price rising but {name} falling',
                    'strength': 'STRONG'
                })
        
        # Hidden bullish: price higher low, indicator lower low (trend continuation)
        if len(p_lows) >= 2 and len(i_lows) >= 2:
            if p_lows[-1][1] > p_lows[-2][1] and i_lows[-1][1] < i_lows[-2][1]:
                results.append({
                    'type': 'HIDDEN_BULLISH',
                    'indicator': name,
                    'description': f'Hidden {name} bullish — uptrend continuation',
                    'strength': 'MEDIUM'
                })
        
        return results
    
    def _swing_lows(self, data, w=5):
        lows = []
        for i in range(w, len(data) - w):
            if data[i] == min(data[i-w:i+w+1]):
                lows.append((i, data[i]))
        return lows[-3:] if lows else []
    
    def _swing_highs(self, data, w=5):
        highs = []
        for i in range(w, len(data) - w):
            if data[i] == max(data[i-w:i+w+1]):
                highs.append((i, data[i]))
        return highs[-3:] if highs else []
