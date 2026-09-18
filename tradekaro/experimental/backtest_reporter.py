"""
📋 Backtest Report Generator — Auto-Generate HTML Performance Reports

After running a backtest, generates a professional report:
  - Equity curve
  - Monthly returns table
  - Trade distribution
  - Key metrics (Sharpe, Sortino, Calmar, Win Rate)
  - Drawdown analysis
  - Risk-adjusted metrics
"""

import os
import json
import numpy as np
from datetime import datetime


class BacktestReportGenerator:
    """
    Generates professional backtest reports.
    
    Usage:
        report = BacktestReportGenerator()
        html = report.generate(trades, equity_curve, config)
        report.save('reports/backtest_2026.html')
    """
    
    def __init__(self):
        self.data = {}
    
    def generate(self, trades, equity_curve=None, config=None):
        """Generate complete backtest report data."""
        if not trades:
            return {'error': 'No trades'}
        
        self.data = {
            'summary': self._calculate_summary(trades, equity_curve),
            'monthly': self._monthly_breakdown(trades),
            'distribution': self._trade_distribution(trades),
            'streaks': self._win_loss_streaks(trades),
            'risk_metrics': self._risk_metrics(equity_curve),
            'config': config or {},
            'generated': datetime.now().isoformat()
        }
        
        return self.data
    
    def save_html(self, filepath='reports/backtest_report.html'):
        """Save report as HTML file."""
        os.makedirs(os.path.dirname(filepath) or 'reports', exist_ok=True)
        
        html = self._render_html()
        with open(filepath, 'w') as f:
            f.write(html)
        
        return filepath
    
    def save_json(self, filepath='reports/backtest_report.json'):
        """Save raw data as JSON."""
        os.makedirs(os.path.dirname(filepath) or 'reports', exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(self.data, f, indent=2, default=str)
        return filepath
    
    def _calculate_summary(self, trades, equity):
        wins = [t for t in trades if t.get('pnl', 0) > 0]
        losses = [t for t in trades if t.get('pnl', 0) < 0]
        
        total_pnl = sum(t.get('pnl', 0) for t in trades)
        gross_profit = sum(t['pnl'] for t in wins) if wins else 0
        gross_loss = abs(sum(t['pnl'] for t in losses)) if losses else 1
        
        avg_win = np.mean([t['pnl'] for t in wins]) if wins else 0
        avg_loss = abs(np.mean([t['pnl'] for t in losses])) if losses else 1
        
        # Drawdown from equity curve
        max_dd = 0
        if equity and len(equity) > 0:
            eq = np.array(equity)
            peak = np.maximum.accumulate(eq)
            dd = (peak - eq) / peak * 100
            max_dd = float(np.max(dd))
        
        # Sharpe
        if equity and len(equity) > 10:
            returns = np.diff(equity) / np.array(equity[:-1])
            sharpe = float(np.mean(returns) / max(np.std(returns), 1e-8) * np.sqrt(252))
        else:
            sharpe = 0
        
        return {
            'total_trades': len(trades),
            'winners': len(wins),
            'losers': len(losses),
            'win_rate': round(len(wins) / max(len(trades), 1) * 100, 1),
            'total_pnl': round(total_pnl, 0),
            'gross_profit': round(gross_profit, 0),
            'gross_loss': round(gross_loss, 0),
            'profit_factor': round(gross_profit / max(gross_loss, 1), 2),
            'avg_win': round(avg_win, 0),
            'avg_loss': round(avg_loss, 0),
            'expectancy': round(avg_win * len(wins)/max(len(trades),1) - avg_loss * len(losses)/max(len(trades),1), 0),
            'max_drawdown': round(max_dd, 2),
            'sharpe_ratio': round(sharpe, 2),
            'calmar': round(total_pnl / max(max_dd, 1), 2) if max_dd > 0 else 0,
            'payoff_ratio': round(avg_win / max(avg_loss, 1), 2),
        }
    
    def _monthly_breakdown(self, trades):
        monthly = {}
        for t in trades:
            dt = t.get('exit_time', t.get('time', ''))
            if dt:
                month = dt[:7]  # YYYY-MM
                if month not in monthly:
                    monthly[month] = {'trades': 0, 'pnl': 0, 'wins': 0}
                monthly[month]['trades'] += 1
                monthly[month]['pnl'] += t.get('pnl', 0)
                if t.get('pnl', 0) > 0:
                    monthly[month]['wins'] += 1
        
        for m in monthly:
            monthly[m]['pnl'] = round(monthly[m]['pnl'], 0)
            monthly[m]['win_rate'] = round(
                monthly[m]['wins'] / max(monthly[m]['trades'], 1) * 100, 1)
        
        return monthly
    
    def _trade_distribution(self, trades):
        pnls = [t.get('pnl', 0) for t in trades]
        if not pnls:
            return {}
        
        return {
            'mean': round(np.mean(pnls), 0),
            'median': round(np.median(pnls), 0),
            'std': round(np.std(pnls), 0),
            'best_trade': round(max(pnls), 0),
            'worst_trade': round(min(pnls), 0),
            'pct_profitable': round(sum(1 for p in pnls if p > 0) / len(pnls) * 100, 1)
        }
    
    def _win_loss_streaks(self, trades):
        max_win_streak = 0
        max_loss_streak = 0
        win_streak = 0
        loss_streak = 0
        
        for t in trades:
            if t.get('pnl', 0) > 0:
                win_streak += 1
                loss_streak = 0
                max_win_streak = max(max_win_streak, win_streak)
            else:
                loss_streak += 1
                win_streak = 0
                max_loss_streak = max(max_loss_streak, loss_streak)
        
        return {'max_win_streak': max_win_streak, 'max_loss_streak': max_loss_streak}
    
    def _risk_metrics(self, equity):
        if not equity or len(equity) < 10:
            return {}
        
        returns = np.diff(equity) / np.array(equity[:-1])
        downside = returns[returns < 0]
        
        sortino = float(np.mean(returns) / max(np.std(downside), 1e-8) * np.sqrt(252)) if len(downside) > 0 else 0
        
        return {
            'sortino_ratio': round(sortino, 2),
            'daily_vol': round(float(np.std(returns) * 100), 3),
            'annualized_vol': round(float(np.std(returns) * np.sqrt(252) * 100), 2),
            'best_day': round(float(max(returns) * 100), 3),
            'worst_day': round(float(min(returns) * 100), 3),
            'positive_days_pct': round(sum(1 for r in returns if r > 0) / len(returns) * 100, 1)
        }
    
    def _render_html(self):
        s = self.data.get('summary', {})
        d = self.data.get('distribution', {})
        r = self.data.get('risk_metrics', {})
        
        return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Backtest Report</title>
<style>
body{{font-family:'Segoe UI',sans-serif;background:#0d1117;color:#c9d1d9;padding:30px;max-width:900px;margin:auto}}
h1{{color:#58a6ff;border-bottom:2px solid #30363d;padding-bottom:10px}}
h2{{color:#79c0ff;margin-top:30px}}
.card{{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:20px;margin:15px 0}}
.grid{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:15px}}
.metric{{text-align:center}}.metric .value{{font-size:28px;font-weight:bold;color:#58a6ff}}
.metric .label{{font-size:12px;color:#8b949e;margin-top:4px}}
.green{{color:#3fb950!important}}.red{{color:#f85149!important}}
table{{width:100%;border-collapse:collapse;margin:10px 0}}
th,td{{padding:8px 12px;border:1px solid #30363d;text-align:right}}
th{{background:#21262d;color:#79c0ff}}
</style></head><body>
<h1>📊 TradeKaro AI — Backtest Report</h1>
<p>Generated: {self.data.get('generated','')}</p>
<div class="card"><div class="grid">
<div class="metric"><div class="value {'green' if s.get('total_pnl',0)>0 else 'red'}">₹{s.get('total_pnl',0):,.0f}</div><div class="label">Total P&L</div></div>
<div class="metric"><div class="value">{s.get('win_rate',0)}%</div><div class="label">Win Rate</div></div>
<div class="metric"><div class="value">{s.get('sharpe_ratio',0)}</div><div class="label">Sharpe Ratio</div></div>
<div class="metric"><div class="value">{s.get('profit_factor',0)}</div><div class="label">Profit Factor</div></div>
<div class="metric"><div class="value red">{s.get('max_drawdown',0)}%</div><div class="label">Max Drawdown</div></div>
<div class="metric"><div class="value">{s.get('total_trades',0)}</div><div class="label">Total Trades</div></div>
</div></div>
<h2>📈 Trade Stats</h2>
<div class="card">
<table><tr><th>Metric</th><th>Value</th></tr>
<tr><td>Avg Win</td><td class="green">₹{s.get('avg_win',0):,.0f}</td></tr>
<tr><td>Avg Loss</td><td class="red">₹{s.get('avg_loss',0):,.0f}</td></tr>
<tr><td>Best Trade</td><td class="green">₹{d.get('best_trade',0):,.0f}</td></tr>
<tr><td>Worst Trade</td><td class="red">₹{d.get('worst_trade',0):,.0f}</td></tr>
<tr><td>Payoff Ratio</td><td>{s.get('payoff_ratio',0)}</td></tr>
<tr><td>Expectancy</td><td>₹{s.get('expectancy',0):,.0f}</td></tr>
</table></div>
<h2>📉 Risk Metrics</h2>
<div class="card">
<table><tr><th>Metric</th><th>Value</th></tr>
<tr><td>Sortino Ratio</td><td>{r.get('sortino_ratio',0)}</td></tr>
<tr><td>Annualized Vol</td><td>{r.get('annualized_vol',0)}%</td></tr>
<tr><td>Calmar Ratio</td><td>{s.get('calmar',0)}</td></tr>
<tr><td>Positive Days</td><td>{r.get('positive_days_pct',0)}%</td></tr>
</table></div>
</body></html>"""
