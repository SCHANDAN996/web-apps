"""
⚖️ Forex Council — Ensemble Voting System
Combines all 4 models into a unified trading decision engine.
Trade only when: Regime ≠ Volatile + Models agree + Confidence > threshold.
"""

import numpy as np
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from forex_model_xgb import EVRegressor
from forex_model_gru import SequencePredictor
from forex_model_regime import RegimeDetector
from forex_model_risk import RiskEstimator
from forex_features import is_active_session

CLASSES = {0: 'HOLD', 1: 'BUY', 2: 'SELL'}
PIP = 0.0001


class ForexCouncil:
    """
    The Council of 4 Models — ensemble trading decision system.

    Voting Logic:
    1. Regime model gates: VOLATILE → NO TRADE
    2. Session check: Dead session → NO TRADE
    3. XGBoost + GRU must agree on direction
    4. Combined confidence > min_confidence
    5. Risk model calculates dynamic SL/TP
    """

    def __init__(self, min_ev_pips=2.5, cooldown_bars=25):
        self.ev_model = EVRegressor()
        self.sequence_model = SequencePredictor() # Kept loaded for future Hybrid Option B
        self.regime_model = RegimeDetector()
        self.risk_model = RiskEstimator()

        self.min_ev_pips = min_ev_pips
        self.cooldown_bars = cooldown_bars
        self.last_trade_bar = -999  # For cooldown tracking

        self.stats = {
            'total_candles': 0, 'trades_taken': 0,
            'blocked_regime': 0, 'blocked_session': 0,
            'blocked_disagree': 0, 'blocked_confidence': 0,
            'blocked_cooldown': 0, 'blocked_adx': 0
        }

    def load_all(self):
        """Load all 4 models from disk."""
        ok = True
        ok &= self.ev_model.load()
        ok &= self.sequence_model.load()
        ok &= self.regime_model.load()
        ok &= self.risk_model.load()
        if ok:
            print("  [Council] All 4 models loaded ✅")
        else:
            print("  [Council] ⚠️ Some models missing — train first!")
        return ok

    def decide(self, xgb_features, gru_sequence, regime_features,
               risk_features, hour_utc=12, current_price=1.0):
        """
        Make a trading decision using all 4 models.

        Args:
            xgb_features: (1, 25) array for Model 1
            gru_sequence: (1, 60, 12) array for Model 2
            regime_features: (1, 8) array for Model 3
            risk_features: (1, 6) array for Model 4
            hour_utc: Current hour in UTC
            current_price: Current close price

        Returns:
            dict with decision, direction, confidence, sl, tp, reason
        """
        self.stats['total_candles'] += 1

        # ── GATE 1: Session Check ──
        if not is_active_session(hour_utc):
            self.stats['blocked_session'] += 1
            return self._no_trade('Dead session — no volume')

        # ── GATE 2: Regime Check ──
        regime = self.regime_model.predict(regime_features)[0]
        if regime == 2:  # VOLATILE
            self.stats['blocked_regime'] += 1
            return self._no_trade('Volatile regime — sit out')

        # ── GATE 3: Direction Agreement ──
        xgb_dir, xgb_conf = self.direction_model.predict_with_confidence(xgb_features)
        gru_dir, gru_conf = self.sequence_model.predict_with_confidence(gru_sequence)

        xgb_dir = xgb_dir[0]
        xgb_conf = xgb_conf[0]
        gru_dir = gru_dir[0]
        gru_conf = gru_conf[0]

        # Both must predict BUY or SELL (not HOLD) and agree
        if xgb_dir == 0 or gru_dir == 0:
            self.stats['blocked_disagree'] += 1
            return self._no_trade(
                f'Model says HOLD (XGB={CLASSES[xgb_dir]}, GRU={CLASSES[gru_dir]})'
            )

        if xgb_dir != gru_dir:
            self.stats['blocked_disagree'] += 1
            return self._no_trade(
                f'Models disagree (XGB={CLASSES[xgb_dir]}, GRU={CLASSES[gru_dir]})'
            )

        direction = xgb_dir  # Both agree

        # ── GATE 4: Confidence Threshold ──
        combined_conf = (xgb_conf * self.xgb_weight + gru_conf * self.gru_weight)
        if combined_conf < self.min_confidence:
            self.stats['blocked_confidence'] += 1
            return self._no_trade(
                f'Low confidence: {combined_conf:.1%} < {self.min_confidence:.1%}'
            )

        # ── PASSED ALL GATES → Calculate Risk ──
        risk = self.risk_model.calculate_sl_tp(risk_features)
        sl_dist = risk['sl_dist'][0]
        tp_dist = risk['tp_dist'][0]

        if direction == 1:  # BUY
            sl_price = current_price - sl_dist
            tp_price = current_price + tp_dist
        else:  # SELL
            sl_price = current_price + sl_dist
            tp_price = current_price - tp_dist

        self.stats['trades_taken'] += 1

        regime_name = {0: 'RANGING', 1: 'TRENDING', 2: 'VOLATILE'}[regime]

        return {
            'action': 'TRADE',
            'direction': CLASSES[direction],
            'confidence': round(combined_conf, 3),
            'xgb_confidence': round(xgb_conf, 3),
            'gru_confidence': round(gru_conf, 3),
            'regime': regime_name,
            'entry_price': current_price,
            'sl_price': round(sl_price, 5),
            'tp_price': round(tp_price, 5),
            'sl_pips': round(risk['sl_pips'][0], 1),
            'tp_pips': round(risk['tp_pips'][0], 1),
            'rr_ratio': f"1:{risk['rr_ratio']:.1f}",
            'reason': (f'{regime_name} regime, both models agree '
                       f'{CLASSES[direction]} @ {combined_conf:.0%}')
        }

    def decide_batch(self, xgb_features, gru_sequences, regime_features,
                     risk_features, hours, prices):
        """
        Batch decision for backtesting.
        Returns list of decisions for each candle.
        """
        n = len(xgb_features)
        decisions = []

        # Option B: Augment XGBoost features with Transformer probabilities
        tf_probs = self.sequence_model.predict_proba(gru_sequences)
        tf_prob_buy = tf_probs[:, 1].reshape(-1, 1)
        tf_prob_sell = tf_probs[:, 2].reshape(-1, 1)
        xgb_features_aug = np.hstack((xgb_features, tf_prob_buy, tf_prob_sell))

        # Batch predictions for speed
        xgb_ev_pips, xgb_ev_conf = self.ev_model.predict_with_confidence(xgb_features_aug)
        regimes = self.regime_model.predict(regime_features)
        risks = self.risk_model.calculate_sl_tp(risk_features)

        for i in range(n):
            self.stats['total_candles'] += 1

            # Session check
            if not is_active_session(hours[i]):
                self.stats['blocked_session'] += 1
                decisions.append(self._no_trade('Dead session'))
                continue

            # Adaptive Cooldown check (no trade clustering)
            current_cooldown = 10 if regimes[i] == 1 else self.cooldown_bars
            if i - self.last_trade_bar < current_cooldown:
                self.stats['blocked_cooldown'] += 1
                decisions.append(self._no_trade('Cooldown'))
                continue

            # Soft Regime Filter — require higher EV if Volatile
            regime_penalty = 0.5 if regimes[i] == 2 else 0.0  # Require +0.5 pips EV in Volatile
            required_ev = self.min_ev_pips + regime_penalty

            # EV check
            expected_pips = xgb_ev_pips[i]
            if expected_pips > required_ev:
                direction = 1  # BUY
            elif expected_pips < -required_ev:
                direction = 2  # SELL
            else:
                self.stats['blocked_confidence'] += 1
                reason = f'Low EV ({expected_pips:.1f} < {required_ev:.1f})'
                decisions.append(self._no_trade(reason))
                continue

            self.stats['trades_taken'] += 1
            self.last_trade_bar = i  # Set cooldown
            sl_dist = risks['sl_dist'][i]
            tp_dist = risks['tp_dist'][i]
            price = prices[i]

            decisions.append({
                'action': 'TRADE',
                'direction': CLASSES[direction],
                'confidence': round(abs(expected_pips), 2),  # Use absolute expected pips as confidence proxy
                'sl_pips': round(risks['sl_pips'][i], 1),
                'tp_pips': round(risks['tp_pips'][i], 1),
                'sl_dist': sl_dist,
                'tp_dist': tp_dist,
                'entry_price': price,
                'tf_prob_buy': float(tf_prob_buy[i][0]),
                'tf_prob_sell': float(tf_prob_sell[i][0])
            })

        return decisions

    def _no_trade(self, reason):
        return {'action': 'NO_TRADE', 'reason': reason}

    def get_stats(self):
        """Return council decision statistics."""
        s = self.stats
        total = s['total_candles']
        if total == 0:
            return s
        s['trade_rate'] = f"{s['trades_taken']/total*100:.1f}%"
        s['selectivity'] = f"1 in {total/max(s['trades_taken'],1):.0f} candles"
        return s
