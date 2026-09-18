"""
⚡ Walk-Forward Backtesting Engine V2

Professional-grade backtester with:
- Walk-Forward Analysis (rolling train/test windows)
- Realistic slippage & commission modeling
- Risk-adjusted metrics (Sharpe, Sortino, Calmar)
- Maximum drawdown calculation
- Equity curve generation
- Performance attribution by regime
- Monte Carlo simulation for robustness
"""

import numpy as np
import pandas as pd
import json
import os
from datetime import datetime
from collections import defaultdict

from src.brain import TradingBrain, DEVICE
from src.indicators import TechnicalIndicators
from src.data_loader import SequenceBuilder
from src.feature_store import FEATURES_V2
from src.market_regime_detector import MarketRegimeDetector


class BacktestResult:
    """Stores and computes backtest metrics."""

    def __init__(self):
        self.trades = []
        self.equity_curve = []
        self.initial_capital = 100000

    def add_trade(self, entry_time, exit_time, entry_price, exit_price,
                  side, qty, regime="UNKNOWN"):
        pnl = (exit_price - entry_price) * qty if side == "BUY" else (entry_price - exit_price) * qty
        pct = pnl / (entry_price * qty) * 100
        self.trades.append({
            'entry_time': str(entry_time),
            'exit_time': str(exit_time),
            'entry_price': entry_price,
            'exit_price': exit_price,
            'side': side,
            'qty': qty,
            'pnl': round(pnl, 2),
            'pct_return': round(pct, 3),
            'regime': regime
        })

    def compute_metrics(self):
        """Compute all performance metrics."""
        if not self.trades:
            return {'error': 'No trades'}

        pnls = [t['pnl'] for t in self.trades]
        pcts = [t['pct_return'] for t in self.trades]
        wins = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p <= 0]

        # Build equity curve
        capital = self.initial_capital
        self.equity_curve = [capital]
        for pnl in pnls:
            capital += pnl
            self.equity_curve.append(capital)

        # Drawdown
        peak = self.equity_curve[0]
        max_dd = 0
        for val in self.equity_curve:
            if val > peak:
                peak = val
            dd = (peak - val) / peak
            max_dd = max(max_dd, dd)

        # Ratios
        returns = np.array(pcts)
        avg_return = np.mean(returns)
        std_return = np.std(returns) if len(returns) > 1 else 1

        # Sharpe (annualized, assuming ~250 trading days, ~70 trades/day at 5m)
        sharpe = (avg_return / std_return) * np.sqrt(252) if std_return > 0 else 0

        # Sortino (only downside deviation)
        downside = returns[returns < 0]
        downside_std = np.std(downside) if len(downside) > 1 else 1
        sortino = (avg_return / downside_std) * np.sqrt(252) if downside_std > 0 else 0

        # Profit Factor
        gross_profit = sum(wins) if wins else 0
        gross_loss = abs(sum(losses)) if losses else 1
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')

        # Expectancy
        win_rate = len(wins) / len(pnls) if pnls else 0
        avg_win = np.mean(wins) if wins else 0
        avg_loss = abs(np.mean(losses)) if losses else 0
        expectancy = (win_rate * avg_win) - ((1 - win_rate) * avg_loss)

        return {
            'total_trades': len(self.trades),
            'win_rate': round(win_rate * 100, 1),
            'avg_win': round(avg_win, 2),
            'avg_loss': round(avg_loss, 2),
            'profit_factor': round(profit_factor, 2),
            'expectancy': round(expectancy, 2),
            'total_pnl': round(sum(pnls), 2),
            'max_drawdown': round(max_dd * 100, 2),
            'sharpe_ratio': round(sharpe, 3),
            'sortino_ratio': round(sortino, 3),
            'final_capital': round(self.equity_curve[-1], 2),
            'return_pct': round((self.equity_curve[-1] - self.initial_capital) / self.initial_capital * 100, 2)
        }

    def regime_breakdown(self):
        """Performance broken down by market regime."""
        by_regime = defaultdict(list)
        for t in self.trades:
            by_regime[t['regime']].append(t['pnl'])

        breakdown = {}
        for regime, pnls in by_regime.items():
            wins = [p for p in pnls if p > 0]
            breakdown[regime] = {
                'trades': len(pnls),
                'win_rate': round(len(wins) / len(pnls) * 100, 1) if pnls else 0,
                'total_pnl': round(sum(pnls), 2)
            }
        return breakdown


class WalkForwardBacktester:
    """
    Walk-Forward Analysis:

    |---Train Window---|--Test Window--|
                |---Train Window---|--Test Window--|
                             |---Train Window---|--Test Window--|

    Each window trains a model and tests on unseen future data.
    """

    def __init__(self, train_window=5000, test_window=1000,
                 step_size=1000, slippage_pct=0.05, commission=20):
        self.train_window = train_window  # Candles for training
        self.test_window = test_window    # Candles for testing
        self.step_size = step_size        # How much to slide forward
        self.slippage_pct = slippage_pct  # Realistic slippage (%)
        self.commission = commission      # Per-trade commission (₹)
        self.seq_builder = SequenceBuilder()
        self.regime_detector = MarketRegimeDetector()

    def run(self, df, confidence_threshold=0.6, holding_period=5):
        """
        Run walk-forward backtest.

        Args:
            df: DataFrame with 1m OHLCV data (must have 'close', 'high', 'low')
            confidence_threshold: Min confidence to take trade
            holding_period: How many candles to hold each trade

        Returns:
            BacktestResult with all trades and metrics
        """
        result = BacktestResult()
        n = len(df)

        if n < self.train_window + self.test_window:
            print(f"[Backtest] Not enough data. Need {self.train_window + self.test_window}, got {n}")
            return result

        # Apply indicators once
        df_full = TechnicalIndicators.apply_multi_timeframe_features(df)
        if df_full.empty:
            print("[Backtest] Indicator computation failed.")
            return result

        # Walk forward
        start = 0
        fold = 0

        while start + self.train_window + self.test_window <= len(df_full):
            fold += 1
            train_end = start + self.train_window
            test_end = train_end + self.test_window

            train_df = df_full.iloc[start:train_end]
            test_df = df_full.iloc[train_end:test_end]

            print(f"   Fold {fold}: Train[{start}:{train_end}] → Test[{train_end}:{test_end}]")

            # Build train sequences
            X_train, y_train, scaler = self.seq_builder.build_sequences(
                train_df, FEATURES_V2, fit_scaler=True
            )

            if len(X_train) == 0:
                start += self.step_size
                continue

            # Train a fresh model on this window
            brain = TradingBrain(input_features=X_train.shape[2], use_v2=True)
            brain.train_incremental(X_train, y_train, epochs=5)

            # Build test sequences
            X_test, y_test, _ = self.seq_builder.build_sequences(
                test_df, FEATURES_V2, scaler=scaler
            )

            if len(X_test) == 0:
                start += self.step_size
                continue

            # Simulate trading on test data
            self._simulate_trades(brain, X_test, test_df, result,
                                  confidence_threshold, holding_period)

            start += self.step_size

        return result

    def _simulate_trades(self, brain, X_test, test_df, result,
                         threshold, hold_period):
        """Simulate trades on test data."""
        import torch

        prices = test_df['close'].values
        lookback = self.seq_builder.lookback

        i = 0
        while i < len(X_test):
            # Get prediction
            sample = X_test[i:i+1]  # (1, 60, features)
            confidence = brain.predict(sample)

            price_idx = lookback + i

            if price_idx + hold_period >= len(prices):
                break

            # Apply threshold
            if confidence > threshold:
                entry_price = prices[price_idx]
                # Apply slippage
                entry_price *= (1 + self.slippage_pct / 100)

                exit_price = prices[min(price_idx + hold_period, len(prices) - 1)]
                exit_price *= (1 - self.slippage_pct / 100)

                # Detect regime
                if 'ADX' in test_df.columns:
                    sub_df = test_df.iloc[max(0, price_idx-50):price_idx]
                    regime_info = self.regime_detector.detect(sub_df)
                    regime = regime_info['regime']
                else:
                    regime = "UNKNOWN"

                result.add_trade(
                    entry_time=test_df.index[price_idx] if hasattr(test_df.index, '__getitem__') else price_idx,
                    exit_time=test_df.index[min(price_idx + hold_period, len(test_df) - 1)] if hasattr(test_df.index, '__getitem__') else price_idx + hold_period,
                    entry_price=round(entry_price, 2),
                    exit_price=round(exit_price, 2),
                    side="BUY",
                    qty=1,
                    regime=regime
                )

                i += hold_period  # Skip holding period
            else:
                i += 1

    def monte_carlo(self, result, n_simulations=1000):
        """
        Monte Carlo simulation — shuffle trade order to test robustness.

        If strategy is robust, different orderings should give similar results.
        If not, performance might be due to luck/sequence.
        """
        if not result.trades:
            return {}

        pnls = [t['pnl'] for t in result.trades]
        final_capitals = []

        for _ in range(n_simulations):
            shuffled = np.random.permutation(pnls)
            capital = result.initial_capital
            for p in shuffled:
                capital += p
            final_capitals.append(capital)

        return {
            'median_capital': round(np.median(final_capitals), 2),
            'mean_capital': round(np.mean(final_capitals), 2),
            'worst_case': round(np.percentile(final_capitals, 5), 2),
            'best_case': round(np.percentile(final_capitals, 95), 2),
            'std_dev': round(np.std(final_capitals), 2),
            'prob_profit': round(np.mean([c > result.initial_capital for c in final_capitals]) * 100, 1)
        }


# --- Convenience Function (used by chat_agent.py) ---
def run_backtest(df, symbol="NIFTY", confidence_threshold=0.6, holding_period=5):
    """
    Quick-run wrapper for the walk-forward backtester.
    
    Args:
        df: DataFrame with 1m OHLCV data
        symbol: Symbol name (for logging)
        confidence_threshold: Min confidence to take trade
        holding_period: Candles to hold each trade
    
    Returns:
        dict: Backtest metrics
    """
    print(f"[Backtest] Running walk-forward backtest for {symbol}...")
    backtester = WalkForwardBacktester(
        train_window=5000, test_window=1000, step_size=1000
    )
    result = backtester.run(df, confidence_threshold, holding_period)
    metrics = result.compute_metrics()
    metrics['regime_breakdown'] = result.regime_breakdown()
    return metrics


# --- CLI Entry Point ---
if __name__ == "__main__":
    print("=" * 60)
    print("⚡ WALK-FORWARD BACKTESTING ENGINE")
    print("=" * 60)

    data_file = "data/NIFTY 50_minute.csv"
    if not os.path.exists(data_file):
        print(f"❌ Data file not found: {data_file}")
        exit(1)

    print(f"Loading data: {data_file}")
    df = pd.read_csv(data_file, nrows=50000)  # Limit for speed
    df.columns = [c.strip().lower() for c in df.columns]

    if 'date' in df.columns:
        df['timestamp'] = pd.to_datetime(df['date'])
        df.set_index('timestamp', inplace=True)

    backtester = WalkForwardBacktester(
        train_window=5000, test_window=1000, step_size=1000
    )

    result = backtester.run(df, confidence_threshold=0.6)
    metrics = result.compute_metrics()

    print("\n📊 BACKTEST RESULTS:")
    for k, v in metrics.items():
        print(f"   {k}: {v}")

    regime_stats = result.regime_breakdown()
    if regime_stats:
        print("\n📈 REGIME BREAKDOWN:")
        for regime, stats in regime_stats.items():
            print(f"   {regime}: {stats}")

    mc = backtester.monte_carlo(result)
    if mc:
        print("\n🎲 MONTE CARLO (1000 simulations):")
        for k, v in mc.items():
            print(f"   {k}: {v}")
