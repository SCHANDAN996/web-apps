"""
📊 Portfolio Dashboard — Flask Analytics Page

Dedicated portfolio analytics endpoint:
  /dashboard — Full portfolio view with P&L, positions, charts
"""

from flask import Blueprint, render_template_string

dashboard_blueprint = Blueprint('dashboard', __name__)

_portfolio = {}

def init_dashboard(portfolio_tracker=None, journal=None):
    global _portfolio
    _portfolio = {'tracker': portfolio_tracker, 'journal': journal}

DASHBOARD_HTML = '''<!DOCTYPE html><html><head>
<meta charset="utf-8"><title>TradeKaro Portfolio</title>
<style>
body{font-family:'Segoe UI',sans-serif;background:#0d1117;color:#c9d1d9;margin:0;padding:20px}
h1{color:#58a6ff;text-align:center}.grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:15px;max-width:900px;margin:auto}
.card{background:#161b22;border:1px solid #30363d;border-radius:12px;padding:20px;text-align:center}
.card .value{font-size:32px;font-weight:bold;color:#58a6ff}.card .label{color:#8b949e;margin-top:5px}
.green{color:#3fb950!important}.red{color:#f85149!important}
table{width:100%;max-width:900px;margin:20px auto;border-collapse:collapse}
th,td{padding:10px;border:1px solid #30363d;text-align:center}th{background:#21262d;color:#79c0ff}
</style></head><body>
<h1>📊 TradeKaro AI — Portfolio Dashboard</h1>
<div class="grid">
<div class="card"><div class="value {{ 'green' if pnl > 0 else 'red' }}">₹{{ pnl|round(0)|int }}</div><div class="label">Net P&L</div></div>
<div class="card"><div class="value">{{ equity|round(0)|int }}</div><div class="label">Equity</div></div>
<div class="card"><div class="value">{{ trades }}</div><div class="label">Trades</div></div>
</div>
<h2 style="text-align:center;color:#79c0ff;margin-top:30px">Open Positions</h2>
<table><tr><th>Symbol</th><th>Side</th><th>Qty</th><th>Avg Price</th><th>P&L</th></tr>
{% for sym, pos in positions.items() %}
<tr><td>{{ sym }}</td><td>{{ pos.side }}</td><td>{{ pos.qty }}</td><td>{{ pos.avg }}</td>
<td class="{{ 'green' if pos.pnl > 0 else 'red' }}">₹{{ pos.pnl|round(0)|int }}</td></tr>
{% endfor %}
</table></body></html>'''

@dashboard_blueprint.route('/dashboard')
def portfolio_dashboard():
    tracker = _portfolio.get('tracker')
    if tracker:
        data = tracker.get_pnl()
        return render_template_string(DASHBOARD_HTML,
            pnl=data.get('net_pnl', 0), equity=data.get('gross_pnl', 0) + 500000,
            trades=data.get('closed_trades', 0), positions=data.get('positions', {}))
    return render_template_string(DASHBOARD_HTML, pnl=0, equity=500000, trades=0, positions={})
