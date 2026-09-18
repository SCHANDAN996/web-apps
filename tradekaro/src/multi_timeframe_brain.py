"""
⏰ Brain voting on the one view the model was trained on.

The model is trained by learner.py on
TechnicalIndicators.apply_multi_timeframe_features(df_1m): 1-minute candles
turned into 5-minute bars, with 15m and 1H indicators joined on as extra
columns. That single frame already carries the multi-timeframe context
(15m_RSI_14, 1H_ADX, ...).

This used to ask the model for four separate "timeframe" opinions, and three
of them were not real (measured 2026-09-15):

  1m   apply_multi_timeframe_features turns any input into 5-minute bars, so
       this vote was the 5m vote copied -- identical on every sample.
  15m  15-minute bars fed into a function that assumes 1-minute input, which
       the model never saw in training.
  1H   needs 70 hourly bars; NSE symbols only hold about a week of 1m data, so
       it failed on every NSE sample and voted a neutral 0.5.

So "3 of 4 timeframes agree" usually meant the 5m vote agreeing with its own
copy and with an out-of-distribution guess.

Voting now asks the same in-distribution question on the latest four 5-minute
bars: now, 5, 10 and 15 minutes ago.

  4/4 agree  -> 100% size
  3/4 agree  ->  75% size   (MIN_AGREEMENT_TO_TRADE)
  2/4 agree  ->  50% size   (reported, not traded)
  otherwise  ->  HOLD

The latest bar must back the direction: a signal that has just faded is not
an entry.
"""

import numpy as np
import logging
from collections import OrderedDict

# How many of the recent bars must back the direction before anything is traded.
MIN_AGREEMENT_TO_TRADE = 3

# A vote above BUY_THRESHOLD backs BUY, below SELL_THRESHOLD backs SELL. The
# same band TheCouncil.review_trade uses to read direction.
BUY_THRESHOLD = 0.55
SELL_THRESHOLD = 0.45


def prediction_from_vote(mtf_result, min_agreement=MIN_AGREEMENT_TO_TRADE):
    """Collapse a vote() result into the single 0-1 number the Council reads.

    TheCouncil.review_trade takes direction straight off this number -- >= 0.55
    is BUY, <= 0.45 is SELL -- so the mapping has to preserve the sign of the
    brain's call. It lived inline in main.py, untested, and inverted every SELL
    for weeks. It is a function now so a test can hold it to that.

    Returns 0.5 (no opinion) unless the brain named a direction with enough
    bars behind it.
    """
    direction = mtf_result.get('direction', 'HOLD')
    agreement = mtf_result.get('agreement', 0)
    confidence = mtf_result.get('confidence', 0.5)

    if direction == 'HOLD' or agreement < min_agreement:
        return 0.5

    # confidence is the mean of the votes backing the direction, so it is
    # already directional and passes through unchanged. If the two ever
    # disagree the mapping is wrong somewhere upstream and the trade should
    # not go out on a coin flip.
    if (direction == 'BUY' and confidence < 0.5) or \
       (direction == 'SELL' and confidence > 0.5):
        logging.error(
            f"[MTF] direction {direction} contradicts confidence {confidence:.3f} "
            f"-- refusing to trade on it")
        return 0.5

    return confidence


class MultiTimeframeBrain:
    """
    Wraps a TradingBrain and turns its predictions into a trade decision.

    The name is historical: the multi-timeframe context lives in the features
    now (see the module docstring), and the votes are the model's reading of
    the latest few 5-minute bars.

    Usage:
        mtf = MultiTimeframeBrain(brain)  # pass TradingBrain instance
        result = mtf.vote(candles_1m_df)
        # result = {
        #   'direction': 'BUY',
        #   'confidence': 0.62,
        #   'position_size_pct': 75,
        #   'votes': {'t-15m': 0.51, 't-10m': 0.58, 't-5m': 0.61, 'now': 0.67},
        #   'agreement': 3,
        #   'aligned': False,
        #   'failed_views': [],
        # }
    """

    # Oldest first, so the dict reads left to right in time.
    VIEWS = OrderedDict([
        ('t-15m', 3),   # value: how many 5-minute bars back from the latest
        ('t-10m', 2),
        ('t-5m', 1),
        ('now', 0),
    ])

    LOOKBACK = 60

    # learner.py fits on the last 2000 1-minute bars. The 15m and 1H context
    # columns depend on how much history they are computed over (an EMA_50 on
    # 33 hourly bars is not the EMA_50 on 130), so inference uses the same
    # window rather than whatever main.py happened to fetch.
    TRAINING_WINDOW_1M = 2000

    # The trainer writes this after every fit. Inference has to read the same
    # file or the model is handed a distribution it was never fitted on.
    DEFAULT_SCALER_PATH = "models/scaler_v2.pkl"

    def __init__(self, brain, feature_columns=None, scaler="auto"):
        """
        Args:
            brain: TradingBrain instance
            feature_columns: list of column names to use as features
            scaler: a fitted scaler, None to skip scaling, or "auto" to load
                the one build_sequences saves
        """
        self.brain = brain
        self.feature_columns = feature_columns
        self.scaler = self._load_scaler() if scaler == "auto" else scaler

    def _load_scaler(self):
        """Load the scaler the trainer fits, or say so and go without."""
        import os
        try:
            import joblib
        except ImportError:
            return None

        if not os.path.exists(self.DEFAULT_SCALER_PATH):
            logging.error(
                f"[MTF] no scaler at {self.DEFAULT_SCALER_PATH} -- predicting on "
                f"unscaled features the model was never fitted on")
            return None

        try:
            scaler = joblib.load(self.DEFAULT_SCALER_PATH)
            logging.info(f"[MTF] scaler loaded "
                         f"({getattr(scaler, 'n_features_in_', '?')} features)")
            return scaler
        except Exception as e:
            logging.error(f"[MTF] could not load {self.DEFAULT_SCALER_PATH}: {e}")
            return None

    def predict(self, X):
        """Delegates single prediction call to underlying brain instance."""
        return self.brain.predict(X)

    def train_incremental(self, *args, **kwargs):
        """Delegates incremental training to underlying brain instance."""
        return self.brain.train_incremental(*args, **kwargs)

    def _get_input_size(self):
        """Delegates input size check to underlying brain instance."""
        return getattr(self.brain, '_get_input_size', lambda: 18)()

    def vote(self, candles_1m_df):
        """
        Vote on 1-minute candle data.

        Args:
            candles_1m_df: DataFrame with 1m OHLCV data, DatetimeIndex

        Returns:
            dict with direction, confidence, position size, votes, agreement
        """
        from src.indicators import TechnicalIndicators

        if candles_1m_df is None or len(candles_1m_df) < 120:
            return self._no_signal("Insufficient data")

        window = candles_1m_df.tail(self.TRAINING_WINDOW_1M)
        df_rich = TechnicalIndicators.apply_multi_timeframe_features(window)

        needed = self.LOOKBACK + max(self.VIEWS.values())
        if df_rich.empty or len(df_rich) < needed:
            return self._no_signal(
                f"only {len(df_rich)} 5-minute bars, need {needed}")

        votes = {}
        failed = []
        for name, bars_back in self.VIEWS.items():
            frame = df_rich if bars_back == 0 else df_rich.iloc[:-bars_back]
            try:
                votes[name] = round(float(self._predict_frame(frame, self.LOOKBACK)), 4)
            except Exception as e:
                logging.warning(f"[MTF] {name} failed: {e}")
                failed.append(f"{name}: {type(e).__name__}: {e}")

        if len(failed) == len(self.VIEWS):
            # Without this the result is a plain HOLD, which reads as
            # "flat market" instead of "the brain is broken".
            logging.error(f"[MTF] every view failed: {failed}")

        # Four bars fifteen minutes apart do not give the same prediction to
        # four decimals unless the model has stopped responding to its input.
        # Measured 2026-09-15: NIFTY and BTC-USD both returned 0.5549 on every
        # bar of every sample -- exactly what the model answers for an all-zero
        # scaled input. Their price columns sit tens to hundreds of scale units
        # out, because the one shared scaler was fitted on ~24,000 levels, and
        # the network saturates. 0.5549 also clears the 0.55 BUY line, so it
        # came out as a unanimous BUY. It is not an opinion; do not trade on it.
        if len(votes) == len(self.VIEWS) and len(set(votes.values())) == 1:
            stuck = next(iter(votes.values()))
            reason = (f"model output stuck at {stuck} on all {len(votes)} bars "
                      f"-- not responding to input")
            logging.warning(f"[MTF] {reason}")
            result = self._no_signal(reason)
            result['failed_views'] = [reason]
            return result

        return self._aggregate_votes(votes, failed)

    def _predict_frame(self, df_rich, lookback):
        """Brain prediction on the last `lookback` rows of a feature frame."""
        # Select feature columns
        if self.feature_columns:
            available = [c for c in self.feature_columns if c in df_rich.columns]

            # A partial match is a contract violation, not a degraded mode. It
            # is what broke this brain: the caller asked for lowercase names
            # ('sma_20', 'macd') while the indicators produce 'SMA_20', 'MACD',
            # so 6 of 18 silently vanished, the model got 12 where it wanted 13,
            # and predict() answered a neutral 0.5 every single time. That
            # cleared the `< 5` guard below without a word.
            #
            # Raising puts it in vote()'s failed_views and the log instead.
            if len(available) < len(self.feature_columns):
                missing = [c for c in self.feature_columns if c not in df_rich.columns]
                raise ValueError(
                    f"{len(missing)} of {len(self.feature_columns)} features missing "
                    f"from the indicator output: {missing[:6]}"
                    f"{'...' if len(missing) > 6 else ''}")
        else:
            # Auto-detect numeric columns
            available = [c for c in df_rich.select_dtypes(include=[np.number]).columns
                        if c not in ['volume'] and not c.startswith('_')]

        if len(available) < 5:
            raise ValueError(f"only {len(available)} usable feature columns")

        # Take last `lookback` rows
        data = df_rich[available].tail(lookback).values

        if len(data) < lookback:
            # Pad if needed
            pad = np.zeros((lookback - len(data), data.shape[1]))
            data = np.vstack([pad, data])

        # Clean before scaling -- RobustScaler propagates NaN.
        data = np.nan_to_num(data, nan=0.0, posinf=0.0, neginf=0.0)

        # The same transform the trainer applied. Nothing scaled here before:
        # build_sequences fits a RobustScaler and trains on its output, so the
        # model learnt weights for values around zero, while this path handed
        # it raw levels -- close and the moving averages sit near 63000 for
        # BTC. The model saturated, and the system read that as a settled
        # bearish view: 8468 SELL, 0 BUY, median confidence 0.09, all while
        # training loss sat at its theoretical floor of 0.693.
        if self.scaler is not None:
            expected = getattr(self.scaler, "n_features_in_", data.shape[1])
            if expected != data.shape[1]:
                raise ValueError(
                    f"scaler expects {expected} features, got {data.shape[1]} -- "
                    f"it was fitted against a different feature list")
            data = self.scaler.transform(data)

        # Reshape for brain: (1, lookback, features)
        X = data[np.newaxis, :, :]
        X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)

        return self.brain.predict(X)

    def _aggregate_votes(self, votes, failed=None):
        """Combine the per-bar votes into one decision."""

        if not votes:
            return self._no_signal("No view produced a vote")

        failed = failed or []

        buy_votes = sum(1 for v in votes.values() if v > BUY_THRESHOLD)
        sell_votes = sum(1 for v in votes.values() if v < SELL_THRESHOLD)

        # The side with more backing wins; a tie has no direction.
        if buy_votes > sell_votes:
            direction, agreement = 'BUY', buy_votes
        elif sell_votes > buy_votes:
            direction, agreement = 'SELL', sell_votes
        else:
            direction, agreement = 'HOLD', 0

        # The most recent bar decides whether this is still an entry. Three
        # bullish bars followed by a bearish one is a move that already ended.
        latest = votes.get('now')
        if direction == 'BUY' and latest is not None and not latest > BUY_THRESHOLD:
            direction = 'HOLD'
        elif direction == 'SELL' and latest is not None and not latest < SELL_THRESHOLD:
            direction = 'HOLD'

        # Position sizing based on agreement
        if direction != 'HOLD' and agreement >= 4:
            position_pct, strength = 100, 'STRONG'
        elif direction != 'HOLD' and agreement >= 3:
            position_pct, strength = 75, 'MODERATE'
        elif direction != 'HOLD' and agreement >= 2:
            position_pct, strength = 50, 'WEAK'
        else:
            position_pct, strength, direction = 0, 'NO_TRADE', 'HOLD'

        # Confidence is the mean of the votes behind the direction, so it keeps
        # the direction's side of 0.5 -- prediction_from_vote refuses a result
        # whose confidence contradicts its direction. With no direction it is
        # the plain mean, which is what the evening summary reports.
        if direction == 'BUY':
            backing = [v for v in votes.values() if v > BUY_THRESHOLD]
        elif direction == 'SELL':
            backing = [v for v in votes.values() if v < SELL_THRESHOLD]
        else:
            backing = list(votes.values())
        confidence = sum(backing) / len(backing)

        aligned = len(votes) == len(self.VIEWS) and (
            buy_votes == len(votes) or sell_votes == len(votes))

        return {
            'direction': direction,
            'confidence': round(confidence, 4),
            'position_size_pct': position_pct,
            'strength': strength,
            'votes': votes,
            'agreement': agreement,
            'aligned': aligned,
            # A view that raised casts no vote, so one broken view cannot swing
            # the decision -- but a broken brain must not look like a quiet
            # market either. Name them.
            'failed_views': failed,
        }

    def _no_signal(self, reason):
        return {
            'direction': 'HOLD',
            'confidence': 0.5,
            'position_size_pct': 0,
            'strength': 'NO_DATA',
            'votes': {},
            'agreement': 0,
            'aligned': False,
            'failed_views': [],
            'reason': reason
        }
