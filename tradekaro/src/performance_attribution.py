"""
📊 Performance Attribution Engine — Attribute P&L to Each Component

Answers: "WHICH part of the AI made money and which lost?"
  - Brain prediction accuracy contribution
  - Sentiment agent contribution
  - Regime detection contribution
  - Risk manager contribution
  - Timing contribution (entry vs exit)

Critical for understanding WHERE to improve next.
"""

import json
import os
from datetime import datetime
from collections import defaultdict


class PerformanceAttribution:
    """
    Attributes P&L to individual AI components.
    
    Usage:
        attrib = PerformanceAttribution()
        attrib.record_decision('RELIANCE', {
            'brain_score': 0.78, 'sentiment': 0.6, 'regime': 'BULL',
            'brain_agreed': True, 'sentiment_agreed': True,
            'regime_agreed': True, 'outcome': 'WIN', 'pnl': 500
        })
        report = attrib.get_attribution_report()
    """
    
    REPORT_FILE = 'data/attribution_report.json'
    
    def __init__(self):
        self.decisions = self._load()
        self.component_stats = defaultdict(lambda: {
            'correct': 0, 'wrong': 0, 'total_pnl': 0, 'trades': 0
        })
        self._recalculate()
    
    def record_decision(self, symbol, decision):
        """
        Record a trading decision with component-level agreement.
        
        decision = {
            brain_score, sentiment, regime,
            brain_agreed, sentiment_agreed, regime_agreed,
            entry_timing_good, exit_timing_good,
            outcome, pnl
        }
        """
        entry = {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            **decision
        }
        self.decisions.append(entry)
        
        # Update component stats
        pnl = decision.get('pnl', 0)
        outcome = decision.get('outcome', 'HOLD')
        
        components = {
            'brain': decision.get('brain_agreed', False),
            'sentiment': decision.get('sentiment_agreed', False),
            'regime': decision.get('regime_agreed', False),
            'entry_timing': decision.get('entry_timing_good', False),
            'exit_timing': decision.get('exit_timing_good', False),
        }
        
        for comp, agreed in components.items():
            self.component_stats[comp]['trades'] += 1
            if agreed and outcome == 'WIN':
                self.component_stats[comp]['correct'] += 1
                self.component_stats[comp]['total_pnl'] += pnl
            elif not agreed and outcome == 'LOSS':
                self.component_stats[comp]['correct'] += 1  # Correctly disagreed
            elif agreed and outcome == 'LOSS':
                self.component_stats[comp]['wrong'] += 1
                self.component_stats[comp]['total_pnl'] += pnl
            else:
                self.component_stats[comp]['wrong'] += 1
        
        self._save()
    
    def get_attribution_report(self):
        """Get full attribution report."""
        report = {}
        
        for comp, stats in self.component_stats.items():
            total = stats['correct'] + stats['wrong']
            accuracy = stats['correct'] / max(total, 1) * 100
            
            report[comp] = {
                'accuracy': round(accuracy, 1),
                'total_trades': stats['trades'],
                'correct_calls': stats['correct'],
                'wrong_calls': stats['wrong'],
                'pnl_contribution': round(stats['total_pnl'], 0),
                'grade': self._grade(accuracy),
                'recommendation': self._recommend(comp, accuracy)
            }
        
        # Sort by accuracy
        report = dict(sorted(report.items(), 
                            key=lambda x: x[1]['accuracy'], reverse=True))
        
        return report
    
    def get_best_component(self):
        """Which component contributes most to wins?"""
        report = self.get_attribution_report()
        if not report:
            return None
        return max(report.items(), key=lambda x: x[1]['accuracy'])
    
    def get_worst_component(self):
        """Which component needs most improvement?"""
        report = self.get_attribution_report()
        if not report:
            return None
        return min(report.items(), key=lambda x: x[1]['accuracy'])
    
    def get_improvement_plan(self):
        """Auto-generate improvement plan based on attribution."""
        report = self.get_attribution_report()
        plan = []
        
        for comp, stats in report.items():
            if stats['accuracy'] < 50:
                plan.append({
                    'component': comp,
                    'accuracy': stats['accuracy'],
                    'action': 'CRITICAL — Retrain or recalibrate',
                    'priority': 'HIGH'
                })
            elif stats['accuracy'] < 60:
                plan.append({
                    'component': comp,
                    'accuracy': stats['accuracy'],
                    'action': 'Needs fine-tuning',
                    'priority': 'MEDIUM'
                })
        
        return plan
    
    def format_report(self):
        """Format attribution as readable string."""
        report = self.get_attribution_report()
        if not report:
            return "📊 No data yet"
        
        lines = ["📊 *Performance Attribution Report*", ""]
        
        for comp, stats in report.items():
            grade = stats['grade']
            acc = stats['accuracy']
            pnl = stats['pnl_contribution']
            emoji = '🟢' if acc > 60 else '🟡' if acc > 50 else '🔴'
            
            lines.append(
                f"{emoji} *{comp.upper()}*: {acc}% accuracy | "
                f"₹{pnl:,.0f} P&L | Grade: {grade}"
            )
        
        # Best/worst
        best = self.get_best_component()
        worst = self.get_worst_component()
        
        if best and worst:
            lines.append("")
            lines.append(f"🏆 Best: *{best[0]}* ({best[1]['accuracy']}%)")
            lines.append(f"⚠️ Needs work: *{worst[0]}* ({worst[1]['accuracy']}%)")
        
        return '\n'.join(lines)
    
    def _grade(self, accuracy):
        if accuracy >= 70: return 'A'
        if accuracy >= 60: return 'B'
        if accuracy >= 50: return 'C'
        if accuracy >= 40: return 'D'
        return 'F'
    
    def _recommend(self, component, accuracy):
        if accuracy >= 70:
            return f'{component} performing well — maintain'
        if accuracy >= 55:
            return f'{component} decent — minor tuning recommended'
        return f'{component} underperforming — retrain/recalibrate urgently'
    
    def _recalculate(self):
        """Recalculate stats from stored decisions."""
        for d in self.decisions:
            pnl = d.get('pnl', 0)
            outcome = d.get('outcome', 'HOLD')
            for comp in ['brain', 'sentiment', 'regime', 'entry_timing', 'exit_timing']:
                agreed = d.get(f'{comp}_agreed', False)
                self.component_stats[comp]['trades'] += 1
                if (agreed and outcome == 'WIN') or (not agreed and outcome == 'LOSS'):
                    self.component_stats[comp]['correct'] += 1
                else:
                    self.component_stats[comp]['wrong'] += 1
                if agreed:
                    self.component_stats[comp]['total_pnl'] += pnl
    
    def _load(self):
        if os.path.exists(self.REPORT_FILE):
            try:
                with open(self.REPORT_FILE, 'r') as f:
                    return json.load(f)
            except:
                pass
        return []
    
    def _save(self):
        os.makedirs(os.path.dirname(self.REPORT_FILE) or 'data', exist_ok=True)
        with open(self.REPORT_FILE, 'w') as f:
            json.dump(self.decisions[-1000:], f, indent=2, default=str)
