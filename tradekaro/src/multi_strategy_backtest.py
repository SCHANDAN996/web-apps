"""
🏆 Multi-Strategy Backtester — Compare Strategies Head-to-Head

Run multiple strategies on same data, compare:
  - Total return, Sharpe, max drawdown, win rate
  - Which strategy works best in which regime?
  - Optimal strategy blend

Built-in strategies:
  - MeanReversion: Buy oversold, sell overbought
  - Momentum: Follow the trend
  - BreakoutORB: Opening range breakout
  - AIBrain: Use V2 model predictions
"""

import numpy as np
from datetime import datetime
from collections import defaultdict


class Strategy:
    """Base class for strategies."""
    name = "Base"
    
    def signal(self, row, df_history):
        """Return 1 (BUY), -1 (SELL), 0 (HOLD)."""
        return 0


class MeanReversionStrategy(Strategy):
    name = "MeanReversion"
    
    def __init__(self, rsi_buy=30, rsi_sell=70):
        self.rsi_buy = rsi_buy
        self.rsi_sell = rsi_sell
    
    def signal(self, row, df_history):
        rsi = row.get('RSI_14', row.get('RSI', row.get('rsi_14', 50)))
        if rsi < self.rsi_buy:
            return 1
        elif rsi > self.rsi_sell:
            return -1
        return 0


class MomentumStrategy(Strategy):
    name = "Momentum"
    
    def signal(self, row, df_history):
        close = row.get('close', 0)
        ema = row.get('EMA_50', row.get('ema_50', 0))
        adx = row.get('ADX', row.get('adx', 0))
        
        if close > ema and adx > 25:
            return 1
        elif close < ema and adx > 25:
            return -1
        return 0


class MACDCrossStrategy(Strategy):
    name = "MACD_Cross"
    
    def signal(self, row, df_history):
        macd = row.get('MACD', row.get('macd', 0))
        signal = row.get('MACD_Signal', row.get('macd_signal', 0))
        
        if macd > signal and macd > 0:
            return 1
        elif macd < signal and macd < 0:
            return -1
        return 0


class MultiStrategyBacktester:
    """
    Compare multiple strategies on same data.
    
    Usage:
        bt = MultiStrategyBacktester(capital=500000)
        bt.add_strategy(MeanReversionStrategy())
        bt.add_strategy(MomentumStrategy())
        bt.add_strategy(MACDCrossStrategy())
        results = bt.run(df_ohlcv_with_indicators)
        comparison = bt.compare()
    """
    
    def __init__(self, capital=500000, sl_pct=1.5, tp_pct=2.0):
        self.capital = capital
        self.sl_pct = sl_pct
        self.tp_pct = tp_pct
        self.strategies = []
        self.results = {}
    
    def add_strategy(self, strategy):
        self.strategies.append(strategy)
    
    def run(self, df, position_size_pct=5.0):
        """Run all strategies on the same data."""
        if df is None or len(df) < 60:
            return {}
        
        for strat in self.strategies:
            self.results[strat.name] = self._backtest_single(
                strat, df, position_size_pct)
        
        return self.results
    
    def compare(self):
        """Compare all strategy results side by side."""
        if not self.results:
            return {}
        
        comparison = {}
        for name, result in self.results.items():
            comparison[name] = {
                'total_return': result['total_return'],
                'win_rate': result['win_rate'],
                'total_trades': result['total_trades'],
                'max_drawdown': result['max_drawdown'],
                'sharpe': result['sharpe'],
                'profit_factor': result['profit_factor'],
            }
        
        # Rank by Sharpe
        ranked = sorted(comparison.items(), 
                       key=lambda x: x[1]['sharpe'], reverse=True)
        
        for rank, (name, stats) in enumerate(ranked, 1):
            stats['rank'] = rank
        
        return dict(ranked)
    
    def get_best_strategy(self):
        """Return the best strategy by Sharpe ratio."""
        comparison = self.compare()
        if not comparison:
            return None
        return list(comparison.items())[0]
    
    def _backtest_single(self, strategy, df, pos_size_pct):
        """Backtest a single strategy."""
        capital = self.capital
        position = 0
        entry_price = 0
        trades = []
        equity_curve = [capital]
        
        for i in range(60, len(df)):
            row = df.iloc[i]
            history = df.iloc[max(0, i-60):i]
            sig = strategy.signal(row, history)
            price = row['close']
            
            # Entry
            if position == 0 and sig != 0:
                position = sig
                entry_price = price
                trade_capital = capital * pos_size_pct / 100
            
            # Exit check
            elif position != 0:
                if position == 1:  # Long
                    pnl_pct = (price - entry_price) / entry_price * 100
                else:  # Short
                    pnl_pct = (entry_price - price) / entry_price * 100
                
                if pnl_pct >= self.tp_pct or pnl_pct <= -self.sl_pct or sig == -position:
                    pnl = trade_capital * pnl_pct / 100
                    capital += pnl
                    trades.append({
                        'entry': entry_price, 'exit': price,
                        'pnl': pnl, 'pnl_pct': pnl_pct,
                        'result': 'WIN' if pnl > 0 else 'LOSS'
                    })
                    position = 0
            
            equity_curve.append(capital)
        
        # Calculate metrics
        wins = [t for t in trades if t['result'] == 'WIN']
        losses = [t for t in trades if t['result'] == 'LOSS']
        
        equity = np.array(equity_curve)
        returns = np.diff(equity) / equity[:-1]
        
        peak = np.maximum.accumulate(equity)
        drawdown = (peak - equity) / peak * 100
        
        avg_win = np.mean([t['pnl'] for t in wins]) if wins else 0
        avg_loss = abs(np.mean([t['pnl'] for t in losses])) if losses else 1
        
        return {
            'strategy': strategy.name,
            'final_capital': round(capital, 0),
            'total_return': round((capital - self.capital) / self.capital * 100, 2),
            'total_trades': len(trades),
            'win_rate': round(len(wins) / max(len(trades), 1) * 100, 1),
            'max_drawdown': round(np.max(drawdown), 2),
            'sharpe': round(np.mean(returns) / max(np.std(returns), 1e-6) * np.sqrt(252), 2),
            'profit_factor': round(avg_win / max(avg_loss, 1), 2),
            'avg_win': round(avg_win, 0),
            'avg_loss': round(avg_loss, 0),
        }
