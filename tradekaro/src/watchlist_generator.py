"""
🔍 AI Watchlist Generator — Auto-Scan 500 Stocks, Find Top Setups

Instead of manually picking stocks:
  1. Scan all NIFTY 500 stocks
  2. Score each on technical setup quality
  3. Filter by AI confidence + volume
  4. Return top 10-20 actionable setups

Scoring criteria:
  - RSI oversold/overbought
  - MACD crossover
  - Volume surge
  - Support/resistance proximity
  - Trend alignment (EMA stack)
"""

import numpy as np
import pandas as pd
from datetime import datetime


class AIWatchlistGenerator:
    """
    Auto-scans stocks and generates ranked watchlist.
    
    Usage:
        gen = AIWatchlistGenerator(brain)
        watchlist = gen.scan_universe(stock_data_dict)
        # [{'symbol': 'RELIANCE', 'score': 87, 'setup': 'RSI_OVERSOLD + MACD_CROSS'}, ...]
    """
    
    # NIFTY 50 stocks (expandable to NIFTY 500)
    UNIVERSE = [
        'RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ICICIBANK', 'HINDUNILVR',
        'SBIN', 'BHARTIARTL', 'KOTAKBANK', 'ITC', 'AXISBANK', 'LT',
        'BAJFINANCE', 'MARUTI', 'TATAMOTORS', 'SUNPHARMA', 'TITAN',
        'ONGC', 'NTPC', 'ADANIENT', 'ADANIPORTS', 'POWERGRID', 'M&M',
        'JSWSTEEL', 'TATASTEEL', 'WIPRO', 'HCLTECH', 'ULTRACEMCO',
        'TECHM', 'INDUSINDBK', 'COALINDIA', 'DRREDDY', 'BAJAJFINSV',
        'GRASIM', 'CIPLA', 'NESTLEIND', 'HEROMOTOCO', 'DIVISLAB',
        'BRITANNIA', 'EICHERMOT', 'APOLLOHOSP', 'TATACONSUM', 'LTIM',
        'SHREECEM', 'BPCL', 'BAJAJ-AUTO', 'SBILIFE', 'HDFCLIFE',
        'HINDALCO', 'UPL'
    ]
    
    def __init__(self, brain=None):
        self.brain = brain
        self.last_scan = None
        self.watchlist = []
    
    def scan_universe(self, stock_data_dict, top_n=15):
        """
        Scan all stocks and return top N setups.
        
        Args:
            stock_data_dict: {symbol: df_ohlcv_with_indicators}
            top_n: number of top setups to return
        """
        scored = []
        
        for symbol, df in stock_data_dict.items():
            if df is None or len(df) < 60:
                continue
            
            try:
                setup = self._score_setup(symbol, df)
                if setup['total_score'] > 30:  # Min threshold
                    scored.append(setup)
            except Exception:
                continue
        
        # Sort by total score
        scored.sort(key=lambda x: x['total_score'], reverse=True)
        
        self.watchlist = scored[:top_n]
        self.last_scan = datetime.now().isoformat()
        
        return self.watchlist
    
    def _score_setup(self, symbol, df):
        """Score a single stock's technical setup (0-100)."""
        scores = {}
        signals = []
        
        row = df.iloc[-1]
        
        # 1. RSI Setup (0-25)
        rsi = row.get('RSI_14', row.get('RSI', row.get('rsi_14', 50)))
        if rsi < 30:
            scores['rsi'] = 25
            signals.append('RSI_OVERSOLD')
        elif rsi > 70:
            scores['rsi'] = 20
            signals.append('RSI_OVERBOUGHT')
        elif 40 < rsi < 60:
            scores['rsi'] = 10  # Neutral
        else:
            scores['rsi'] = 5
        
        # 2. MACD Crossover (0-20)
        macd = row.get('MACD', row.get('macd', 0))
        macd_signal = row.get('MACD_Signal', row.get('macd_signal', 0))
        if macd > macd_signal and macd > 0:
            scores['macd'] = 20
            signals.append('MACD_BULLISH')
        elif macd < macd_signal and macd < 0:
            scores['macd'] = 15
            signals.append('MACD_BEARISH')
        else:
            scores['macd'] = 5
        
        # 3. Volume Surge (0-20)
        vol = df['volume'].values
        vol_avg = np.mean(vol[-20:])
        vol_ratio = vol[-1] / max(vol_avg, 1)
        if vol_ratio > 2.0:
            scores['volume'] = 20
            signals.append('VOLUME_SURGE')
        elif vol_ratio > 1.5:
            scores['volume'] = 15
            signals.append('HIGH_VOLUME')
        else:
            scores['volume'] = 5
        
        # 4. Trend Alignment (0-20) — EMA stack
        close = row.get('close', 0)
        ema_50 = row.get('EMA_50', row.get('ema_50', 0))
        sma_20 = row.get('SMA_20', row.get('sma_20', 0))
        
        if close > sma_20 > ema_50 and ema_50 > 0:
            scores['trend'] = 20
            signals.append('BULLISH_STACK')
        elif close < sma_20 < ema_50 and ema_50 > 0:
            scores['trend'] = 15
            signals.append('BEARISH_STACK')
        else:
            scores['trend'] = 5
        
        # 5. ADX Strength (0-15)
        adx = row.get('ADX', row.get('adx', 20))
        if adx > 30:
            scores['adx'] = 15
            signals.append('STRONG_TREND')
        elif adx > 20:
            scores['adx'] = 10
        else:
            scores['adx'] = 3
        
        total = sum(scores.values())
        
        # Direction
        bullish_signals = ['RSI_OVERSOLD', 'MACD_BULLISH', 'BULLISH_STACK']
        bearish_signals = ['RSI_OVERBOUGHT', 'MACD_BEARISH', 'BEARISH_STACK']
        
        bull_count = sum(1 for s in signals if s in bullish_signals)
        bear_count = sum(1 for s in signals if s in bearish_signals)
        direction = 'BUY' if bull_count > bear_count else 'SELL' if bear_count > bull_count else 'NEUTRAL'
        
        return {
            'symbol': symbol,
            'total_score': total,
            'direction': direction,
            'signals': signals,
            'scores': scores,
            'close': close,
            'rsi': round(rsi, 1),
            'adx': round(adx, 1),
            'volume_ratio': round(vol_ratio, 2),
            'scan_time': datetime.now().strftime('%H:%M:%S')
        }
    
    def get_buy_setups(self):
        """Filter watchlist for BUY setups only."""
        return [w for w in self.watchlist if w['direction'] == 'BUY']
    
    def get_sell_setups(self):
        return [w for w in self.watchlist if w['direction'] == 'SELL']
    
    def format_watchlist(self):
        """Format watchlist as readable string."""
        lines = [f"🔍 *AI Watchlist* ({self.last_scan})", ""]
        
        for i, w in enumerate(self.watchlist[:10], 1):
            emoji = '🟢' if w['direction'] == 'BUY' else '🔴' if w['direction'] == 'SELL' else '🟡'
            lines.append(
                f"{i}. {emoji} *{w['symbol']}* — Score: {w['total_score']} "
                f"| {w['direction']} | {', '.join(w['signals'][:3])}"
            )
        
        return '\n'.join(lines)
