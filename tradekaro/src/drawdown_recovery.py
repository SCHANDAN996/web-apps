"""
🔄 Drawdown Recovery Engine — Auto-Adjust After Losses

When losses pile up, most traders panic. This engine:
  1. Detects drawdown severity (minor/moderate/severe/critical)
  2. Auto-reduces position sizes
  3. Tightens stop-losses
  4. Shifts to defensive strategies
  5. Auto-recovers when performance improves
"""

from datetime import datetime
from collections import deque


class DrawdownRecoveryEngine:
    """
    Automatically adjusts trading parameters during drawdowns.
    
    Usage:
        recovery = DrawdownRecoveryEngine(capital=500000)
        adjustment = recovery.get_adjustment(current_capital=470000)
        # {'mode': 'DEFENSIVE', 'position_scale': 0.5, 'sl_multiplier': 0.8}
    """
    
    MODES = {
        'NORMAL':      {'dd_range': (0, 3),   'position_scale': 1.0, 'sl_mult': 1.0, 'strategies': 'ALL'},
        'CAUTIOUS':    {'dd_range': (3, 5),   'position_scale': 0.75, 'sl_mult': 0.85, 'strategies': 'ALL'},
        'DEFENSIVE':   {'dd_range': (5, 8),   'position_scale': 0.50, 'sl_mult': 0.75, 'strategies': 'LOW_RISK'},
        'SURVIVAL':    {'dd_range': (8, 12),  'position_scale': 0.25, 'sl_mult': 0.60, 'strategies': 'HEDGED_ONLY'},
        'CRITICAL':    {'dd_range': (12, 100),'position_scale': 0.0,  'sl_mult': 0.0,  'strategies': 'STOP_TRADING'},
    }
    
    def __init__(self, capital=500000, auto_pause_dd=15):
        self.initial_capital = capital
        self.peak_capital = capital
        self.auto_pause_dd = auto_pause_dd
        self.mode_history = deque(maxlen=100)
        self.recovery_streak = 0
    
    def get_adjustment(self, current_capital):
        """
        Get trading adjustments based on current drawdown.
        """
        # Update peak
        if current_capital > self.peak_capital:
            self.peak_capital = current_capital
        
        # Calculate drawdown
        dd_pct = (self.peak_capital - current_capital) / self.peak_capital * 100
        
        # Determine mode
        mode = 'NORMAL'
        for mode_name, config in self.MODES.items():
            low, high = config['dd_range']
            if low <= dd_pct < high:
                mode = mode_name
                break
        
        config = self.MODES[mode]
        
        # Recovery bonus: if recovering from drawdown, can slightly increase
        recovery_bonus = 0
        if len(self.mode_history) >= 3:
            recent = [h['dd_pct'] for h in list(self.mode_history)[-3:]]
            if all(recent[i] >= recent[i+1] for i in range(len(recent)-1)):
                self.recovery_streak += 1
                if self.recovery_streak > 3:
                    recovery_bonus = 0.10
            else:
                self.recovery_streak = 0
        
        adjustment = {
            'mode': mode,
            'drawdown_pct': round(dd_pct, 2),
            'position_scale': min(1.0, config['position_scale'] + recovery_bonus),
            'sl_multiplier': config['sl_mult'],
            'allowed_strategies': config['strategies'],
            'peak_capital': round(self.peak_capital, 0),
            'current_capital': round(current_capital, 0),
            'recovery_needed': round(self.peak_capital - current_capital, 0),
            'recovery_pct_needed': round(
                (self.peak_capital / max(current_capital, 1) - 1) * 100, 2
            ),
            'trading_paused': dd_pct >= self.auto_pause_dd,
            'timestamp': datetime.now().isoformat()
        }
        
        self.mode_history.append({
            'mode': mode, 'dd_pct': dd_pct,
            'time': datetime.now().isoformat()
        })
        
        return adjustment
    
    def should_trade(self, current_capital):
        """Quick check: should we trade at all?"""
        adj = self.get_adjustment(current_capital)
        return not adj['trading_paused'] and adj['position_scale'] > 0
    
    def get_recovery_plan(self, current_capital):
        """Generate recovery plan with milestones."""
        dd_pct = (self.peak_capital - current_capital) / self.peak_capital * 100
        recovery_needed = self.peak_capital - current_capital
        
        milestones = []
        for pct in [25, 50, 75, 100]:
            recovered = current_capital + (recovery_needed * pct / 100)
            milestones.append({
                'milestone': f'{pct}% Recovery',
                'target_capital': round(recovered, 0),
                'remaining': round(self.peak_capital - recovered, 0)
            })
        
        return {
            'drawdown': round(dd_pct, 2),
            'loss_amount': round(recovery_needed, 0),
            'milestones': milestones,
            'estimated_days': round(recovery_needed / max(current_capital * 0.005, 1), 0)
        }
