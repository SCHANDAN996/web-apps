"""
🕯️ Candlestick Pattern Recognizer — Detect 15+ Classic Patterns

Patterns detected:
  Reversal: Doji, Hammer, Inverted Hammer, Engulfing, Morning/Evening Star
  Continuation: Three White Soldiers, Three Black Crows, Marubozu
  Indecision: Spinning Top, Harami

Each pattern → signal strength (STRONG/MEDIUM/WEAK) + direction (BULL/BEAR)
"""

import numpy as np


class CandlePatternRecognizer:
    """
    Detects Japanese candlestick patterns from OHLCV data.
    
    Usage:
        recognizer = CandlePatternRecognizer()
        patterns = recognizer.scan(df_ohlcv)
        # [{'pattern': 'BULLISH_ENGULFING', 'strength': 'STRONG', 'direction': 'BULL'}]
    """
    
    def scan(self, df, lookback=5):
        """Scan last N candles for all known patterns."""
        if df is None or len(df) < lookback:
            return []
        
        patterns = []
        recent = df.tail(lookback)
        o = recent['open'].values
        h = recent['high'].values
        l = recent['low'].values
        c = recent['close'].values
        
        # Single candle patterns (last candle)
        patterns.extend(self._check_doji(o, h, l, c))
        patterns.extend(self._check_hammer(o, h, l, c))
        patterns.extend(self._check_marubozu(o, h, l, c))
        patterns.extend(self._check_spinning_top(o, h, l, c))
        
        # Two candle patterns
        if len(o) >= 2:
            patterns.extend(self._check_engulfing(o, h, l, c))
            patterns.extend(self._check_harami(o, h, l, c))
        
        # Three candle patterns
        if len(o) >= 3:
            patterns.extend(self._check_morning_evening_star(o, h, l, c))
            patterns.extend(self._check_three_soldiers_crows(o, h, l, c))
        
        return patterns
    
    def get_signal(self, df):
        """Get aggregate signal from all detected patterns."""
        patterns = self.scan(df)
        if not patterns:
            return {'signal': 'NEUTRAL', 'strength': 0, 'patterns': []}
        
        bull = sum(1 for p in patterns if p['direction'] == 'BULL')
        bear = sum(1 for p in patterns if p['direction'] == 'BEAR')
        
        strong = sum(1 for p in patterns if p['strength'] == 'STRONG')
        
        if bull > bear:
            signal = 'BULLISH'
        elif bear > bull:
            signal = 'BEARISH'
        else:
            signal = 'NEUTRAL'
        
        return {
            'signal': signal,
            'strength': strong,
            'patterns': [p['pattern'] for p in patterns],
            'details': patterns
        }
    
    def _body(self, o, c, i=-1):
        return abs(c[i] - o[i])
    
    def _upper_shadow(self, o, h, c, i=-1):
        return h[i] - max(o[i], c[i])
    
    def _lower_shadow(self, o, l, c, i=-1):
        return min(o[i], c[i]) - l[i]
    
    def _range(self, h, l, i=-1):
        return h[i] - l[i]
    
    def _is_bullish(self, o, c, i=-1):
        return c[i] > o[i]
    
    def _check_doji(self, o, h, l, c):
        body = self._body(o, c)
        rng = self._range(h, l)
        if rng > 0 and body / rng < 0.1:
            return [{'pattern': 'DOJI', 'strength': 'MEDIUM', 'direction': 'NEUTRAL',
                     'description': 'Indecision — trend reversal possible'}]
        return []
    
    def _check_hammer(self, o, h, l, c):
        patterns = []
        body = self._body(o, c)
        lower = self._lower_shadow(o, l, c)
        upper = self._upper_shadow(o, h, c)
        rng = self._range(h, l)
        
        if rng > 0 and body > 0:
            # Hammer: small body at top, long lower shadow
            if lower > body * 2 and upper < body * 0.5:
                patterns.append({'pattern': 'HAMMER', 'strength': 'STRONG', 
                               'direction': 'BULL',
                               'description': 'Bullish reversal — buyers rejected lower prices'})
            
            # Inverted Hammer: small body at bottom, long upper shadow
            if upper > body * 2 and lower < body * 0.5:
                patterns.append({'pattern': 'INVERTED_HAMMER', 'strength': 'MEDIUM',
                               'direction': 'BULL',
                               'description': 'Potential bullish reversal'})
            
            # Shooting Star (bearish hammer at top of uptrend)
            if upper > body * 2 and lower < body * 0.3 and c[-1] < o[-1]:
                patterns.append({'pattern': 'SHOOTING_STAR', 'strength': 'STRONG',
                               'direction': 'BEAR',
                               'description': 'Bearish reversal — sellers rejected higher prices'})
        return patterns
    
    def _check_engulfing(self, o, h, l, c):
        patterns = []
        # Bullish engulfing: prev bearish, current bullish, current body covers prev
        if c[-2] < o[-2] and c[-1] > o[-1]:  # prev bear, curr bull
            if o[-1] <= c[-2] and c[-1] >= o[-2]:
                patterns.append({'pattern': 'BULLISH_ENGULFING', 'strength': 'STRONG',
                               'direction': 'BULL',
                               'description': 'Strong bullish reversal — buyers overwhelmed sellers'})
        
        # Bearish engulfing
        if c[-2] > o[-2] and c[-1] < o[-1]:  # prev bull, curr bear
            if o[-1] >= c[-2] and c[-1] <= o[-2]:
                patterns.append({'pattern': 'BEARISH_ENGULFING', 'strength': 'STRONG',
                               'direction': 'BEAR',
                               'description': 'Strong bearish reversal — sellers overwhelmed buyers'})
        return patterns
    
    def _check_harami(self, o, h, l, c):
        patterns = []
        prev_body = abs(c[-2] - o[-2])
        curr_body = abs(c[-1] - o[-1])
        
        if curr_body < prev_body * 0.5:
            if c[-2] < o[-2] and c[-1] > o[-1]:  # prev bear, curr small bull
                patterns.append({'pattern': 'BULLISH_HARAMI', 'strength': 'MEDIUM',
                               'direction': 'BULL', 'description': 'Selling pressure weakening'})
            elif c[-2] > o[-2] and c[-1] < o[-1]:
                patterns.append({'pattern': 'BEARISH_HARAMI', 'strength': 'MEDIUM',
                               'direction': 'BEAR', 'description': 'Buying pressure weakening'})
        return patterns
    
    def _check_morning_evening_star(self, o, h, l, c):
        patterns = []
        body1 = abs(c[-3] - o[-3])
        body2 = abs(c[-2] - o[-2])
        body3 = abs(c[-1] - o[-1])
        
        # Morning Star: big bear + small body + big bull
        if (c[-3] < o[-3] and body2 < body1 * 0.3 and 
            c[-1] > o[-1] and body3 > body1 * 0.5):
            patterns.append({'pattern': 'MORNING_STAR', 'strength': 'STRONG',
                           'direction': 'BULL', 'description': 'Strong 3-candle bullish reversal'})
        
        # Evening Star: big bull + small body + big bear
        if (c[-3] > o[-3] and body2 < body1 * 0.3 and 
            c[-1] < o[-1] and body3 > body1 * 0.5):
            patterns.append({'pattern': 'EVENING_STAR', 'strength': 'STRONG',
                           'direction': 'BEAR', 'description': 'Strong 3-candle bearish reversal'})
        return patterns
    
    def _check_three_soldiers_crows(self, o, h, l, c):
        patterns = []
        # Three White Soldiers: 3 consecutive bullish with higher closes
        if (c[-3]>o[-3] and c[-2]>o[-2] and c[-1]>o[-1] and 
            c[-1]>c[-2]>c[-3]):
            patterns.append({'pattern': 'THREE_WHITE_SOLDIERS', 'strength': 'STRONG',
                           'direction': 'BULL', 'description': 'Strong bullish continuation'})
        
        # Three Black Crows
        if (c[-3]<o[-3] and c[-2]<o[-2] and c[-1]<o[-1] and 
            c[-1]<c[-2]<c[-3]):
            patterns.append({'pattern': 'THREE_BLACK_CROWS', 'strength': 'STRONG',
                           'direction': 'BEAR', 'description': 'Strong bearish continuation'})
        return patterns
    
    def _check_marubozu(self, o, h, l, c):
        body = self._body(o, c)
        rng = self._range(h, l)
        if rng > 0 and body / rng > 0.9:
            if c[-1] > o[-1]:
                return [{'pattern': 'BULLISH_MARUBOZU', 'strength': 'STRONG',
                        'direction': 'BULL', 'description': 'Full-body bullish — extreme conviction'}]
            else:
                return [{'pattern': 'BEARISH_MARUBOZU', 'strength': 'STRONG',
                        'direction': 'BEAR', 'description': 'Full-body bearish — extreme selling'}]
        return []
    
    def _check_spinning_top(self, o, h, l, c):
        body = self._body(o, c)
        upper = self._upper_shadow(o, h, c)
        lower = self._lower_shadow(o, l, c)
        if body > 0 and upper > body and lower > body:
            return [{'pattern': 'SPINNING_TOP', 'strength': 'WEAK',
                    'direction': 'NEUTRAL', 'description': 'Indecision — equal buying and selling'}]
        return []
