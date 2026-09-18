"""
📋 Daily Report Generator — Auto Morning/Evening Summary

Pre-market: What to expect today
Post-market: What happened, P&L, lessons
"""

from datetime import datetime


class DailyReportGenerator:
    
    def pre_market_report(self, global_data=None, watchlist=None, earnings=None, macro_score=None):
        now = datetime.now()
        sections = [f"# 📊 Pre-Market Report — {now.strftime('%d %b %Y, %A')}\n"]
        
        if global_data:
            sections.append("## 🌍 Global Markets")
            for idx, data in global_data.items():
                emoji = '🟢' if data.get('change_pct', 0) > 0 else '🔴'
                sections.append(f"  {emoji} {idx}: {data.get('change_pct', 0):+.2f}%")
        
        if watchlist:
            sections.append("\n## 🎯 Today's Watchlist")
            for i, w in enumerate(watchlist[:5], 1):
                sections.append(f"  {i}. {w.get('symbol', '')} — {w.get('direction', '')} (Score: {w.get('score', 0):.0f})")
        
        if earnings:
            sections.append("\n## 📅 Earnings Today")
            for e in earnings: sections.append(f"  ⏰ {e.get('symbol', '')}")
        
        if macro_score:
            sections.append(f"\n## 📈 Macro: {macro_score.get('environment', 'N/A')} (Score: {macro_score.get('score', 50)})")
        
        return '\n'.join(sections)
    
    def post_market_report(self, pnl_data=None, trades=None, alerts=None):
        now = datetime.now()
        sections = [f"# 📊 Post-Market Report — {now.strftime('%d %b %Y')}\n"]
        
        if pnl_data:
            emoji = '💰' if pnl_data.get('net_pnl', 0) > 0 else '📉'
            sections.append(f"## {emoji} P&L: ₹{pnl_data.get('net_pnl', 0):,.0f}")
            sections.append(f"  Trades: {pnl_data.get('closed_trades', 0)}")
            sections.append(f"  Win Rate: {pnl_data.get('win_rate', 0):.0f}%")
        
        if trades:
            sections.append("\n## 📝 Trade Log")
            for t in trades[-5:]:
                emoji = '✅' if t.get('pnl', 0) > 0 else '❌'
                sections.append(f"  {emoji} {t.get('symbol', '')} — ₹{t.get('pnl', 0):,.0f}")
        
        return '\n'.join(sections)
    
    def save_report(self, report, filepath=None):
        if not filepath:
            filepath = f"data/reports/daily_{datetime.now().strftime('%Y%m%d')}.md"
        import os
        os.makedirs(os.path.dirname(filepath) or 'data/reports', exist_ok=True)
        with open(filepath, 'w') as f: f.write(report)
        return filepath
