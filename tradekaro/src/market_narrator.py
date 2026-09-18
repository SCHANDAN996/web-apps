"""
🧠 Market Narrator — AI Explains Its Decisions in Plain Language

Converts raw predictions → human-readable explanations.
No external LLM API needed — uses template-based narration.

Example Output:
  "NIFTY mein BUY signal kyunki:
   📊 RSI oversold (28) → reversal expected
   📈 Regime: BULL_TREND (conf: 0.87)
   ⏰ 3/4 timeframes bullish
   📰 Sentiment: Positive (0.72)
   🎯 Brain confidence: 0.78"
"""

from datetime import datetime


class MarketNarrator:
    """
    Template-based trade decision narrator.
    
    Usage:
        narrator = MarketNarrator()
        explanation = narrator.explain_prediction(
            symbol='NIFTY', score=0.78, signal='BUY',
            features={'RSI_14': 28, 'ADX': 32, 'MACD': 45},
            regime='BULL_TREND', regime_conf=0.87,
            sentiment=0.72, timeframe_votes={'1m': 0.75, '5m': 0.8, '15m': 0.82, '1H': 0.7}
        )
    """
    
    def explain_prediction(self, symbol, score, signal, features=None,
                          regime=None, regime_conf=0, sentiment=0,
                          timeframe_votes=None, council_votes=None):
        """Generate human-readable explanation of a prediction."""
        
        lines = []
        
        # Header
        emoji = '🟢' if signal == 'BUY' else '🔴' if signal == 'SELL' else '🟡'
        lines.append(f"{emoji} *{symbol} — {signal}* (Score: {score:.2f})")
        lines.append("")
        
        # Reasons
        reasons = self._get_reasons(score, signal, features, regime, 
                                    regime_conf, sentiment, timeframe_votes)
        
        for i, reason in enumerate(reasons, 1):
            lines.append(f"{i}. {reason}")
        
        # Confidence bar
        lines.append("")
        bar = self._confidence_bar(score)
        lines.append(f"Confidence: {bar} {score:.0%}")
        
        # Timestamp
        lines.append(f"\n_📅 {datetime.now().strftime('%d %b %Y, %H:%M:%S IST')}_")
        
        return '\n'.join(lines)
    
    def daily_summary(self, trades, total_pnl, win_rate, regime):
        """Generate daily trading summary."""
        
        lines = []
        lines.append("📊 *Daily Trading Summary*")
        lines.append(f"📅 {datetime.now().strftime('%d %B %Y')}")
        lines.append("")
        
        pnl_emoji = '🟢' if total_pnl >= 0 else '🔴'
        lines.append(f"💰 *P&L:* {pnl_emoji} ₹{total_pnl:,.0f}")
        lines.append(f"📈 *Win Rate:* {win_rate:.0f}%")
        lines.append(f"📊 *Regime:* {regime}")
        lines.append(f"🔢 *Total Trades:* {len(trades)}")
        
        if trades:
            lines.append("\n*Top Trades:*")
            sorted_trades = sorted(trades, key=lambda t: t.get('pnl', 0), reverse=True)
            for t in sorted_trades[:5]:
                pnl = t.get('pnl', 0)
                e = '🟢' if pnl >= 0 else '🔴'
                lines.append(f"  {e} {t.get('symbol', '?')}: ₹{pnl:,.0f}")
        
        return '\n'.join(lines)
    
    def explain_no_trade(self, symbol, reasons):
        """Explain why AI decided NOT to trade."""
        lines = [f"⏸️ *{symbol} — NO TRADE*", ""]
        for r in reasons:
            lines.append(f"  ❌ {r}")
        return '\n'.join(lines)
    
    def _get_reasons(self, score, signal, features, regime, regime_conf,
                     sentiment, tf_votes):
        """Extract key reasons for the decision."""
        reasons = []
        
        # Regime
        if regime and regime != 'UNKNOWN':
            regime_emoji = {'BULL_TREND': '📈', 'BEAR_TREND': '📉', 
                          'SIDEWAYS_QUIET': '➡️', 'SIDEWAYS_VOLATILE': '⚡',
                          'TRANSITION': '🔄'}.get(regime, '❓')
            reasons.append(f"{regime_emoji} Regime: *{regime}* (conf: {regime_conf:.2f})")
        
        # RSI
        if features:
            rsi = features.get('RSI_14', features.get('RSI', None))
            if rsi is not None:
                if rsi < 30:
                    reasons.append(f"📊 RSI oversold ({rsi:.0f}) → reversal expected")
                elif rsi > 70:
                    reasons.append(f"📊 RSI overbought ({rsi:.0f}) → pullback likely")
                else:
                    reasons.append(f"📊 RSI neutral ({rsi:.0f})")
            
            adx = features.get('ADX', None)
            if adx is not None:
                if adx > 25:
                    reasons.append(f"💪 Strong trend (ADX: {adx:.0f})")
                else:
                    reasons.append(f"😐 Weak trend (ADX: {adx:.0f})")
            
            macd = features.get('MACD', None)
            if macd is not None:
                if macd > 0:
                    reasons.append(f"📈 MACD bullish ({macd:.2f})")
                else:
                    reasons.append(f"📉 MACD bearish ({macd:.2f})")
        
        # Sentiment
        if sentiment != 0:
            if sentiment > 0.2:
                reasons.append(f"📰 Sentiment: *Bullish* ({sentiment:.2f})")
            elif sentiment < -0.2:
                reasons.append(f"📰 Sentiment: *Bearish* ({sentiment:.2f})")
            else:
                reasons.append(f"📰 Sentiment: Neutral ({sentiment:.2f})")
        
        # Timeframe alignment
        if tf_votes:
            bullish = sum(1 for v in tf_votes.values() if v > 0.55)
            total = len(tf_votes)
            reasons.append(f"⏰ {bullish}/{total} timeframes aligned")
        
        if not reasons:
            reasons.append(f"🧠 Brain score: {score:.2f}")
        
        return reasons
    
    def _confidence_bar(self, score, length=10):
        """Generate visual confidence bar."""
        filled = int(score * length)
        empty = length - filled
        return '█' * filled + '░' * empty
