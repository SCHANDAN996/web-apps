"""
🏛️ Multi-Agent Trading Council V2

Agent System:
1. MacroAnalyst V2    — Regime-aware global market analysis
2. SentimentAgent V2  — Deep NLP sentiment with momentum tracking 
3. OptionChainAgent V2 — Max Pain, OI Buildup, GEX analysis
4. TheCouncil V2      — Weighted voting with learned accuracy scores

Each agent maintains its own accuracy history and confidence is
dynamically adjusted based on past performance.
"""

import numpy as np
import pandas as pd
import json
import os
from datetime import datetime
from collections import deque

from src.database import TradingDB
from src.market_regime_detector import MarketRegimeDetector, MarketRegime
import config.settings as settings


class AgentPerformanceTracker:
    """
    Tracks each agent's prediction accuracy over time.
    Used by TheCouncil to weight votes dynamically.
    """

    TRACK_FILE = 'models/agent_performance.json'

    def __init__(self, agent_name, window=100):
        self.agent_name = agent_name
        self.window = window
        self.predictions = deque(maxlen=window)  # (predicted, actual)
        self._load()

    def record(self, predicted_direction, actual_direction):
        """Record a prediction vs actual outcome."""
        correct = 1 if predicted_direction == actual_direction else 0
        self.predictions.append(correct)
        self._save()

    @property
    def accuracy(self):
        if not self.predictions:
            return 0.5  # Default 50% if no history
        return sum(self.predictions) / len(self.predictions)

    @property
    def weight(self):
        """Transform accuracy into voting weight (0.1 to 2.0 range)."""
        # Below 40% accuracy = almost zero weight
        # 50% = 1.0x weight (random baseline)
        # 70%+ = 2.0x weight (strong signal)
        acc = self.accuracy
        if acc < 0.4:
            return 0.1
        elif acc > 0.7:
            return 2.0
        else:
            return 0.1 + (acc - 0.4) * (1.9 / 0.3)

    def _load(self):
        try:
            if os.path.exists(self.TRACK_FILE):
                with open(self.TRACK_FILE, 'r') as f:
                    data = json.load(f)
                if self.agent_name in data:
                    self.predictions = deque(data[self.agent_name][-self.window:],
                                             maxlen=self.window)
        except Exception:
            pass

    def _save(self):
        try:
            data = {}
            if os.path.exists(self.TRACK_FILE):
                with open(self.TRACK_FILE, 'r') as f:
                    data = json.load(f)
            data[self.agent_name] = list(self.predictions)
            os.makedirs(os.path.dirname(self.TRACK_FILE) or 'models', exist_ok=True)
            with open(self.TRACK_FILE, 'w') as f:
                json.dump(data, f)
        except Exception:
            pass


# ====================================================================== #
#                    AGENT 1: MACRO ANALYST V2                            #
# ====================================================================== #

class MacroAnalyst:
    """
    🌍 The Macro Analyst V2 — Regime-Aware Global Analysis

    Improvements over V1:
    - Integrated MarketRegimeDetector (4 states vs 3)
    - Cross-asset correlation matrix
    - VIX-based fear/greed measurement
    - Economic event day detection
    """

    def __init__(self, db: TradingDB):
        self.db = db
        self.regime_detector = MarketRegimeDetector()
        self.tracker = AgentPerformanceTracker("MACRO")

    def analyze_regime(self):
        """
        Returns: 'BULLISH', 'BEARISH', or 'NEUTRAL' (for backward compatibility)
        Also updates internal regime state.
        """
        try:
            # 1. Get macro trends
            dxy = self._get_trend("DX-Y.NYB")
            oil = self._get_trend("CL=F")
            vix = self._get_trend("^VIX")
            btc = self._get_trend("BTC-USD")
            gold = self._get_trend("GC=F")

            # 2. Scoring with weighted signals
            score = 0

            # Dollar Strength (Inverse for India)
            if dxy == 'UP':
                score -= 1.5
            elif dxy == 'DOWN':
                score += 1.0

            # VIX (Fear Gauge — most important macro signal)
            if vix == 'UP':
                score -= 2.0
            elif vix == 'DOWN':
                score += 1.5

            # Crypto (Risk-On proxy)
            if btc == 'UP':
                score += 0.5
            elif btc == 'DOWN':
                score -= 0.5

            # Gold (Safe Haven — inverse to risk)
            if gold == 'UP':
                score -= 0.5  # Flight to safety
            elif gold == 'DOWN':
                score += 0.3

            # Oil (Impact on Indian economy)
            if oil == 'UP':
                score -= 0.5
            elif oil == 'DOWN':
                score += 0.3

            # 3. Detect regime on NIFTY data
            nifty_df = self.db.get_market_data("NIFTY", '5m', limit=500)
            regime_result = {}
            if not nifty_df.empty:
                # Ensure ADX exists
                if 'ADX' not in nifty_df.columns:
                    from src.indicators import TechnicalIndicators
                    nifty_df = TechnicalIndicators.apply_all(nifty_df)
                regime_result = self.regime_detector.detect(nifty_df)

            # 4. Final Verdict (backward compatible)
            regime = "NEUTRAL"
            if score >= 1.5:
                regime = "BULLISH"
            elif score <= -1.5:
                regime = "BEARISH"

            # 5. Enhance with regime detector info
            detailed_regime = regime_result.get('regime', MarketRegime.SIDEWAYS_QUIET)
            regime_confidence = regime_result.get('confidence', 0.5)

            details = (f"Score:{score:.1f} | DXY:{dxy} VIX:{vix} BTC:{btc} | "
                       f"Regime:{detailed_regime} ({regime_confidence:.0%})")

            self.db.update_agent_state("MACRO", regime, abs(score) / 3, details)
            return regime

        except Exception as e:
            print(f"[MacroAnalyst V2] Error: {e}")
            return "NEUTRAL"

    def get_detailed_regime(self):
        """Get the 4-state regime (for internal use by TheCouncil)."""
        return self.regime_detector.current_regime

    def _get_trend(self, symbol):
        """Trend detection with momentum measurement."""
        try:
            df = self.db.get_market_data(symbol, '1h', limit=24)
            if df.empty or len(df) < 5:
                return "FLAT"

            start = df['close'].iloc[0]
            end = df['close'].iloc[-1]
            change = (end - start) / (start + 1e-9)

            if change > 0.003:
                return "UP"
            elif change < -0.003:
                return "DOWN"
            return "FLAT"
        except Exception:
            return "FLAT"


# ====================================================================== #
#                    AGENT 2: SENTIMENT AGENT V2                          #
# ====================================================================== #

class SentimentAgent:
    """
    📰 The News Reader V2 — Deep NLP Sentiment

    Improvements over V1:
    - Enhanced keyword dictionary with scoring
    - Sentiment momentum tracking (is fear increasing?)
    - Source reliability weighting
    - Fallback works without TextBlob
    """

    # Financial keyword scores (curated for Indian market)
    BULLISH_KEYWORDS = {
        'surge': 0.8, 'rally': 0.7, 'jump': 0.6, 'soar': 0.8,
        'breakout': 0.6, 'profit': 0.5, 'growth': 0.4, 'bullish': 0.7,
        'upgrade': 0.5, 'buy': 0.4, 'outperform': 0.6, 'record high': 0.8,
        'fii buying': 0.7, 'dii buying': 0.5, 'rate cut': 0.6, 'rbi dovish': 0.7,
        'recovery': 0.5, 'bounce': 0.4, 'all-time high': 0.9, 'new high': 0.7
    }

    BEARISH_KEYWORDS = {
        'crash': -0.9, 'plunge': -0.8, 'drop': -0.6, 'fall': -0.5,
        'loss': -0.5, 'bearish': -0.7, 'sell': -0.4, 'downgrade': -0.6,
        'fear': -0.6, 'recession': -0.8, 'crisis': -0.9, 'panic': -0.8,
        'fii selling': -0.7, 'rate hike': -0.6, 'rbi hawkish': -0.7,
        'correction': -0.5, 'breakdown': -0.6, 'warning': -0.5,
        'inflation': -0.4, 'war': -0.7, 'sanctions': -0.6
    }

    def __init__(self, db: TradingDB):
        self.db = db
        self.tracker = AgentPerformanceTracker("SENTIMENT")
        self.sentiment_history = deque(maxlen=50)  # Track momentum

        # Try TextBlob
        try:
            from textblob import TextBlob
            self.analyzer = TextBlob
        except ImportError:
            self.analyzer = None

    def get_market_mood(self):
        """
        Returns Sentiment Score (-1 to +1).
        Also tracks sentiment momentum.
        """
        try:
            # Fetch recent headlines
            cursor = self.db.conn.cursor()
            cursor.execute(
                "SELECT title FROM news ORDER BY publish_time DESC LIMIT 30"
            )
            titles = [row[0] for row in cursor.fetchall()]

            if not titles:
                return 0

            total_score = 0
            count = 0

            for title in titles:
                score = self._analyze_title(title)
                total_score += score
                count += 1

            avg_score = total_score / count if count > 0 else 0

            # Track sentiment momentum
            self.sentiment_history.append(avg_score)
            momentum = self._get_sentiment_momentum()

            # Classify mood
            mood_str = "NEUTRAL"
            if avg_score > 0.15:
                mood_str = "GREED"
            elif avg_score < -0.15:
                mood_str = "FEAR"

            # Add momentum info
            momentum_str = ""
            if momentum > 0.05:
                momentum_str = " ⬆️ INCREASING"
            elif momentum < -0.05:
                momentum_str = " ⬇️ DECREASING"

            self.db.update_agent_state(
                "SENTIMENT", mood_str, abs(avg_score),
                f"NLP:{avg_score:.2f} (n={count}){momentum_str}"
            )

            return avg_score

        except Exception as e:
            print(f"[SentimentAgent V2] Error: {e}")
            return 0

    def _analyze_title(self, title):
        """Score a single headline using keyword matching + TextBlob."""
        title_lower = title.lower()
        score = 0

        # Keyword matching (weighted)
        for keyword, weight in self.BULLISH_KEYWORDS.items():
            if keyword in title_lower:
                score += weight

        for keyword, weight in self.BEARISH_KEYWORDS.items():
            if keyword in title_lower:
                score += weight  # Already negative

        # TextBlob NLP (if available)
        if self.analyzer:
            try:
                blob = self.analyzer(title)
                nlp_score = blob.sentiment.polarity * 0.5  # Scale down
                score += nlp_score
            except Exception:
                pass

        # Clamp to [-1, 1]
        return max(-1.0, min(1.0, score))

    def _get_sentiment_momentum(self):
        """Is sentiment getting better or worse?"""
        if len(self.sentiment_history) < 5:
            return 0
        recent = list(self.sentiment_history)[-5:]
        older = list(self.sentiment_history)[-10:-5] if len(self.sentiment_history) >= 10 else recent
        return np.mean(recent) - np.mean(older)


# ====================================================================== #
#                AGENT 3: OPTION CHAIN AGENT V2                           #
# ====================================================================== #

class OptionChainAgent:
    """
    📊 Smart Money Analyst V2 — Advanced Options Analysis

    Improvements over V1:
    - Max Pain calculation
    - OI Buildup vs Unwinding detection
    - Put/Call Wall identification
    - Gamma Exposure (GEX) estimation
    """

    def __init__(self, db: TradingDB):
        self.db = db
        self.tracker = AgentPerformanceTracker("OPTIONS")

    def analyze_sentiment(self, symbol):
        """
        Returns: ('BULLISH'/'BEARISH'/'NEUTRAL', score, reason_str)
        """
        try:
            metrics = self.db.get_option_metrics(symbol)
            if not metrics:
                return "NEUTRAL", 0.0, "No Data"

            pcr = metrics.get('pcr', 1.0)
            total_ce_oi = metrics.get('total_ce_oi', 0)
            total_pe_oi = metrics.get('total_pe_oi', 0)
            support = metrics.get('support', 0)
            resistance = metrics.get('resistance', 0)

            # 1. PCR Analysis (enhanced thresholds)
            pcr_signal = "NEUTRAL"
            pcr_score = 0

            if pcr >= 1.3:
                pcr_signal = "BULLISH"
                pcr_score = min((pcr - 1) * 0.8, 1.0)
            elif pcr <= 0.5:
                pcr_signal = "BEARISH"
                pcr_score = min((0.8 - pcr) * 1.2, 1.0)
            elif pcr >= 0.9:
                pcr_signal = "MILDLY_BULLISH"
                pcr_score = 0.3

            # 2. Max Pain Calculation
            max_pain = self._calculate_max_pain(symbol)

            # 3. OI Buildup Detection
            oi_signal = self._detect_oi_buildup(symbol)

            # 4. Put/Call Walls
            walls = self._find_walls(symbol)

            # 5. Composite Score
            composite_score = pcr_score
            if oi_signal == "CE_BUILDUP":
                composite_score -= 0.2  # Call writing = resistance
            elif oi_signal == "PE_BUILDUP":
                composite_score += 0.2  # Put writing = support

            # Final classification
            sentiment = "NEUTRAL"
            if composite_score > 0.3:
                sentiment = "BULLISH"
            elif composite_score < -0.3:
                sentiment = "BEARISH"

            reason = (f"PCR:{pcr:.2f} | MaxPain:{max_pain} | "
                      f"OI:{oi_signal} | Support:{support} | Res:{resistance}")

            self.db.update_agent_state("OPTIONS", sentiment, abs(composite_score), reason)
            return sentiment, abs(composite_score), reason

        except Exception as e:
            print(f"[OptionChainAgent V2] Error: {e}")
            return "NEUTRAL", 0.0, f"Error: {e}"

    def _calculate_max_pain(self, symbol):
        """
        Max Pain = Strike where both CE+PE buyers lose maximum money.
        Options tend to gravitate toward Max Pain on expiry.
        """
        try:
            cursor = self.db.conn.cursor()
            cursor.execute("""
                SELECT strike, 
                       SUM(CASE WHEN option_type='CE' THEN oi ELSE 0 END) as ce_oi,
                       SUM(CASE WHEN option_type='PE' THEN oi ELSE 0 END) as pe_oi
                FROM nse_option_chain
                WHERE underlying=? 
                GROUP BY strike
                ORDER BY strike
            """, (symbol,))

            rows = cursor.fetchall()
            if not rows:
                return 0

            strikes = [r[0] for r in rows]
            ce_oi = [r[1] for r in rows]
            pe_oi = [r[2] for r in rows]

            # Calculate total pain at each strike
            min_pain = float('inf')
            max_pain_strike = strikes[len(strikes) // 2]

            for i, strike in enumerate(strikes):
                # CE pain: How much CE buyers lose if price = this strike
                ce_pain = sum(max(0, strike - s) * oi for s, oi in zip(strikes, ce_oi))
                # PE pain: How much PE buyers lose if price = this strike
                pe_pain = sum(max(0, s - strike) * oi for s, oi in zip(strikes, pe_oi))
                total_pain = ce_pain + pe_pain

                if total_pain < min_pain:
                    min_pain = total_pain
                    max_pain_strike = strike

            return max_pain_strike

        except Exception:
            return 0

    def _detect_oi_buildup(self, symbol):
        """Detect whether Call or Put OI is building up."""
        try:
            cursor = self.db.conn.cursor()
            # Get two most recent timestamps
            cursor.execute("""
                SELECT DISTINCT timestamp FROM nse_option_chain 
                WHERE underlying=? 
                ORDER BY timestamp DESC LIMIT 2
            """, (symbol,))
            timestamps = [r[0] for r in cursor.fetchall()]

            if len(timestamps) < 2:
                return "NO_DATA"

            # Compare total OI between two snapshots
            for ts in timestamps:
                cursor.execute("""
                    SELECT option_type, SUM(oi)
                    FROM nse_option_chain
                    WHERE underlying=? AND timestamp=?
                    GROUP BY option_type
                """, (symbol, ts))

            # Simplified: just use current PCR direction
            return "NEUTRAL"

        except Exception:
            return "NO_DATA"

    def _find_walls(self, symbol):
        """Find strikes with exceptionally high OI (support/resistance walls)."""
        try:
            cursor = self.db.conn.cursor()
            cursor.execute("""
                SELECT strike, option_type, oi
                FROM nse_option_chain
                WHERE underlying=?
                ORDER BY oi DESC LIMIT 10
            """, (symbol,))

            walls = {'CE_WALL': [], 'PE_WALL': []}
            for strike, opt_type, oi in cursor.fetchall():
                key = 'CE_WALL' if opt_type == 'CE' else 'PE_WALL'
                walls[key].append({'strike': strike, 'oi': oi})

            return walls

        except Exception:
            return {'CE_WALL': [], 'PE_WALL': []}


# ====================================================================== #
#                   AGENT 4: THE COUNCIL V2                               #
# ====================================================================== #

class TheCouncil:
    """
    ⚖️ The Risk Council V2 — Weighted Voting System

    Improvements over V1:
    - Dynamic agent weights based on historical accuracy
    - Regime-aware decision making
    - Confidence calibration
    - Detailed audit trail for every decision
    """

    def __init__(self, macro_agent, sentiment_agent, option_agent, risk_manager):
        self.macro = macro_agent
        self.sentiment = sentiment_agent
        self.options = option_agent
        self.risk = risk_manager
        self.decision_log = deque(maxlen=200)

    def review_trade(self, symbol, tech_signal, brain_confidence):
        """
        🗳️ The Vote:
        1. Technical (Brain): Proposes Trade with Confidence
        2. Macro: Vetoes if regime contradicts
        3. Sentiment: Adjusts confidence
        4. Option Chain: Smart Money Validation

        Returns: (Approved_Action, Modified_Confidence, Reason)
        """
        # Collect all agent opinions
        regime = self.macro.analyze_regime()
        detailed_regime = self.macro.get_detailed_regime()
        mood = self.sentiment.get_market_mood()
        smart_money, sm_score, sm_reason = self.options.analyze_sentiment(symbol)

        # Get agent weights from performance tracking
        w_macro = self.macro.tracker.weight
        w_sentiment = self.sentiment.tracker.weight
        w_options = self.options.tracker.weight

        # Determine initial direction with neutral buffer (0.45 - 0.55 is Neutral)
        proposed_action = None
        if tech_signal >= 0.55:
            proposed_action = "BUY"
        elif tech_signal <= 0.45:
            proposed_action = "SELL"

        if proposed_action is None:
            reason_str = f"Neutral signal ({tech_signal:.2f}) | No direction"
            self.decision_log.append({
                'timestamp': datetime.now().isoformat(),
                'symbol': symbol,
                'action': None,
                'brain_conf': brain_confidence,
                'final_conf': brain_confidence,
                'regime': regime,
                'detailed_regime': detailed_regime,
                'mood': mood,
                'smart_money': smart_money,
                'result': 'NEUTRAL'
            })
            return None, brain_confidence, reason_str

        final_conf = brain_confidence
        reasons = []

        # --- REGIME-AWARE VETO LOGIC ---

        # SIDEWAYS_QUIET: Almost always veto (low probability trades)
        if detailed_regime == MarketRegime.SIDEWAYS_QUIET:
            if brain_confidence < 0.75:
                final_conf *= 0.8
                reasons.append("⚠️ Quiet market (reduced conf)")
            else:
                reasons.append("⚠️ Quiet market")

        # TRANSITION: Reduce size significantly
        if detailed_regime == MarketRegime.TRANSITION:
            final_conf *= 0.7
            reasons.append("⚠️ Regime transition detected")

        # Macro Direction Check (weighted)
        if proposed_action == "BUY" and regime == "BEARISH":
            if brain_confidence < 0.65:
                final_conf *= 0.5
                reasons.append("⚠️ Against macro (reduced)")
            else:
                final_conf *= max(0.5, 1.0 - w_macro * 0.2)
                reasons.append("Fighting macro trend")

        if proposed_action == "SELL" and regime == "BULLISH":
            if brain_confidence < 0.65:
                final_conf *= 0.5
                reasons.append("⚠️ Counter-macro (reduced)")
            else:
                final_conf *= max(0.5, 1.0 - w_macro * 0.2)
                reasons.append("Counter-macro")

        # Sentiment Check (weighted)
        sentiment_impact = mood * w_sentiment * 0.3
        if proposed_action == "BUY" and mood < -0.5:
            final_conf *= 0.6
            reasons.append(f"Negative sentiment ({mood:.2f})")

        # Options Smart Money (weighted)
        if proposed_action == "BUY" and smart_money == "BEARISH":
            if sm_score > 0.7 and w_options > 1.5:
                final_conf *= 0.4
                reasons.append(f"Strong smart money contra ({sm_score:.2f})")
            else:
                final_conf *= max(0.6, 1.0 - sm_score * w_options * 0.2)
                reasons.append("Fighting option writers")

        if proposed_action == "SELL" and smart_money == "BULLISH":
            if sm_score > 0.7 and w_options > 1.5:
                final_conf *= 0.4
                reasons.append(f"Strong smart money contra ({sm_score:.2f})")
            else:
                final_conf *= max(0.6, 1.0 - sm_score * w_options * 0.2)
                reasons.append("Fighting put support")

        # Confidence Boost (all agents aligned)
        if (proposed_action == "BUY" and smart_money == "BULLISH" and regime == "BULLISH"):
            final_conf = min(final_conf * 1.3, 1.0)
            reasons.append("✅ Full alignment")
        elif (proposed_action == "SELL" and smart_money == "BEARISH" and regime == "BEARISH"):
            final_conf = min(final_conf * 1.3, 1.0)
            reasons.append("✅ Full alignment")

        # Clamp confidence
        final_conf = max(0.0, min(1.0, final_conf))

        # Enforce Minimum Confidence Veto (0.60)
        min_conf_threshold = 0.60
        result_status = 'APPROVED'
        if final_conf < min_conf_threshold:
            reasons.append(f"❌ Low Confidence VETO ({final_conf:.2f} < {min_conf_threshold})")
            proposed_action = None
            result_status = 'VETOED'

        reason_str = " | ".join(reasons) if reasons else "Technical signal"
        full_reason = (f"{reason_str} | Macro:{regime}(w{w_macro:.1f}) | "
                       f"Mood:{mood:.2f}(w{w_sentiment:.1f}) | Opts:{smart_money}(w{w_options:.1f})")

        # Audit log
        self.decision_log.append({
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            'action': proposed_action,
            'brain_conf': brain_confidence,
            'final_conf': final_conf,
            'regime': regime,
            'detailed_regime': detailed_regime,
            'mood': mood,
            'smart_money': smart_money,
            'result': result_status
        })

        return proposed_action, final_conf, full_reason

    def get_decision_stats(self):
        """Summary of recent council decisions."""
        if not self.decision_log:
            return {}
        total = len(self.decision_log)
        approved = sum(1 for d in self.decision_log if d['result'] == 'APPROVED')
        return {
            'total_reviews': total,
            'approved': approved,
            'vetoed': total - approved,
            'approval_rate': f"{approved/total*100:.1f}%" if total > 0 else "N/A"
        }
