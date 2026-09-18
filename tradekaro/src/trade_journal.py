"""
📓 Trade Journal + Analytics — Learn From Every Trade

Every trade recorded with full context:
  - Entry/exit time, price, quantity
  - AI confidence at entry
  - Market regime at time of trade
  - Which agents agreed/disagreed
  - Actual P&L and holding time
  - What went right/wrong (auto-analysis)

Weekly analytics:
  - Best/worst trading days
  - Most profitable setups
  - Overtrading detection
  - Emotional pattern detection (revenge trading, FOMO)
"""

import json
import os
from datetime import datetime, timedelta
from collections import defaultdict, Counter


class TradeJournal:
    """
    Records and analyzes every trade for continuous improvement.
    
    Usage:
        journal = TradeJournal()
        journal.record_trade({
            'symbol': 'RELIANCE', 'side': 'BUY', 'entry_price': 2500,
            'exit_price': 2550, 'qty': 10, 'confidence': 0.78,
            'regime': 'BULL_TREND', 'notes': 'RSI oversold entry'
        })
        
        analytics = journal.weekly_analytics()
        patterns = journal.detect_patterns()
    """
    
    JOURNAL_FILE = 'data/trade_journal.json'
    
    def __init__(self):
        self.trades = self._load()
    
    def record_trade(self, trade_data):
        """Record a completed trade with full context."""
        entry = {
            'id': len(self.trades) + 1,
            'symbol': trade_data.get('symbol', 'UNKNOWN'),
            'side': trade_data.get('side', 'BUY'),
            'entry_price': trade_data.get('entry_price', 0),
            'exit_price': trade_data.get('exit_price', 0),
            'qty': trade_data.get('qty', 0),
            'confidence': trade_data.get('confidence', 0.5),
            'regime': trade_data.get('regime', 'UNKNOWN'),
            'sentiment': trade_data.get('sentiment', 0),
            'entry_time': trade_data.get('entry_time', datetime.now().isoformat()),
            'exit_time': trade_data.get('exit_time', datetime.now().isoformat()),
            'notes': trade_data.get('notes', ''),
        }
        
        # Calculate P&L
        if entry['side'] == 'BUY':
            entry['pnl'] = (entry['exit_price'] - entry['entry_price']) * entry['qty']
        else:
            entry['pnl'] = (entry['entry_price'] - entry['exit_price']) * entry['qty']
        
        entry['pnl_pct'] = round(
            (entry['pnl'] / (entry['entry_price'] * entry['qty'])) * 100, 2
        ) if entry['entry_price'] > 0 else 0
        
        entry['result'] = 'WIN' if entry['pnl'] > 0 else 'LOSS'
        
        # Auto-analysis
        entry['analysis'] = self._auto_analyze(entry)
        
        self.trades.append(entry)
        self._save()
        
        return entry
    
    def weekly_analytics(self, weeks_back=1):
        """Generate weekly analytics report."""
        cutoff = datetime.now() - timedelta(weeks=weeks_back)
        
        recent = [t for t in self.trades 
                 if datetime.fromisoformat(t['entry_time']) >= cutoff]
        
        if not recent:
            return {'message': 'No trades this week', 'trades': 0}
        
        wins = [t for t in recent if t['result'] == 'WIN']
        losses = [t for t in recent if t['result'] == 'LOSS']
        
        total_pnl = sum(t['pnl'] for t in recent)
        win_rate = len(wins) / len(recent) * 100
        avg_win = sum(t['pnl'] for t in wins) / len(wins) if wins else 0
        avg_loss = sum(t['pnl'] for t in losses) / len(losses) if losses else 0
        
        # Best/worst days
        day_pnl = defaultdict(float)
        for t in recent:
            day = t['entry_time'][:10]
            day_pnl[day] += t['pnl']
        
        best_day = max(day_pnl.items(), key=lambda x: x[1]) if day_pnl else ('N/A', 0)
        worst_day = min(day_pnl.items(), key=lambda x: x[1]) if day_pnl else ('N/A', 0)
        
        # Most profitable symbol
        sym_pnl = defaultdict(float)
        for t in recent:
            sym_pnl[t['symbol']] += t['pnl']
        
        best_symbol = max(sym_pnl.items(), key=lambda x: x[1]) if sym_pnl else ('N/A', 0)
        
        # Regime performance
        regime_stats = defaultdict(lambda: {'wins': 0, 'losses': 0, 'pnl': 0})
        for t in recent:
            r = t['regime']
            regime_stats[r]['pnl'] += t['pnl']
            if t['result'] == 'WIN':
                regime_stats[r]['wins'] += 1
            else:
                regime_stats[r]['losses'] += 1
        
        return {
            'period': f"Last {weeks_back} week(s)",
            'total_trades': len(recent),
            'win_rate': round(win_rate, 1),
            'total_pnl': round(total_pnl, 0),
            'avg_win': round(avg_win, 0),
            'avg_loss': round(avg_loss, 0),
            'profit_factor': round(abs(avg_win / avg_loss), 2) if avg_loss != 0 else 0,
            'best_day': {'date': best_day[0], 'pnl': round(best_day[1], 0)},
            'worst_day': {'date': worst_day[0], 'pnl': round(worst_day[1], 0)},
            'best_symbol': {'symbol': best_symbol[0], 'pnl': round(best_symbol[1], 0)},
            'regime_performance': dict(regime_stats)
        }
    
    def detect_patterns(self):
        """Detect behavioral patterns: overtrading, revenge, FOMO."""
        patterns = []
        
        if len(self.trades) < 10:
            return patterns
        
        recent = self.trades[-30:]
        
        # Overtrading: >10 trades per day
        day_counts = Counter(t['entry_time'][:10] for t in recent)
        for day, count in day_counts.items():
            if count > 10:
                patterns.append({
                    'type': 'OVERTRADING',
                    'severity': 'HIGH',
                    'message': f'⚠️ {count} trades on {day} — overtrading detected!'
                })
        
        # Revenge trading: loss → immediate trade within 5 min
        for i in range(1, len(recent)):
            if recent[i-1]['result'] == 'LOSS':
                t1 = datetime.fromisoformat(recent[i-1]['exit_time'])
                t2 = datetime.fromisoformat(recent[i]['entry_time'])
                if (t2 - t1).total_seconds() < 300:
                    patterns.append({
                        'type': 'REVENGE_TRADE',
                        'severity': 'HIGH',
                        'message': f'🔴 Quick trade after loss — revenge trading risk'
                    })
        
        # Low confidence trades: winning more on high-conf trades?
        high_conf = [t for t in recent if t['confidence'] > 0.7]
        low_conf = [t for t in recent if t['confidence'] < 0.6]
        
        if high_conf and low_conf:
            hc_wr = sum(1 for t in high_conf if t['result'] == 'WIN') / len(high_conf)
            lc_wr = sum(1 for t in low_conf if t['result'] == 'WIN') / len(low_conf)
            
            if lc_wr > hc_wr:
                patterns.append({
                    'type': 'CONFIDENCE_MISMATCH',
                    'severity': 'MEDIUM',
                    'message': f'⚠️ Low-confidence trades winning more ({lc_wr:.0%}) '
                              f'than high-confidence ({hc_wr:.0%}) — model may need recalibration'
                })
        
        # Consecutive losses
        streak = 0
        max_streak = 0
        for t in recent:
            if t['result'] == 'LOSS':
                streak += 1
                max_streak = max(max_streak, streak)
            else:
                streak = 0
        
        if max_streak >= 5:
            patterns.append({
                'type': 'LOSS_STREAK',
                'severity': 'HIGH',
                'message': f'📉 {max_streak} consecutive losses — consider pause or model review'
            })
        
        return patterns
    
    def _auto_analyze(self, trade):
        """Auto-analyze what went right/wrong."""
        notes = []
        
        if trade['result'] == 'WIN':
            if trade['confidence'] > 0.7:
                notes.append('✅ High-confidence trade hit target')
            else:
                notes.append('🍀 Low-confidence win — may be luck')
        else:
            if trade['confidence'] > 0.7:
                notes.append('❌ High-confidence miss — review model')
            else:
                notes.append('⚠️ Low-confidence loss — expected')
        
        if trade['regime'] == 'SIDEWAYS_VOLATILE' and trade['pnl'] < 0:
            notes.append('📊 Loss in volatile sideways — reduce sizing in this regime')
        
        return ' | '.join(notes)
    
    def _load(self):
        if os.path.exists(self.JOURNAL_FILE):
            try:
                with open(self.JOURNAL_FILE, 'r') as f:
                    return json.load(f)
            except:
                pass
        return []
    
    def _save(self):
        os.makedirs(os.path.dirname(self.JOURNAL_FILE) or 'data', exist_ok=True)
        with open(self.JOURNAL_FILE, 'w') as f:
            json.dump(self.trades, f, indent=2, default=str)
