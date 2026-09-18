"""
🌐 API Gateway — REST API for External Access

Exposes trading system functionality via HTTP:
  GET /api/status, /api/portfolio, /api/signals
  POST /api/trade, /api/config
"""

from flask import Blueprint, jsonify, request

api_blueprint = Blueprint('trading_api', __name__)

_system = {}  # Injected system reference

def init_api(orchestrator=None, config=None):
    global _system
    _system = {'orchestrator': orchestrator, 'config': config}

@api_blueprint.route('/api/status')
def api_status():
    orch = _system.get('orchestrator')
    if orch:
        return jsonify(orch.get_status())
    return jsonify({'status': 'NO_ORCHESTRATOR'})

@api_blueprint.route('/api/portfolio')
def api_portfolio():
    orch = _system.get('orchestrator')
    if orch:
        paper = orch.get_module('paper_trade')
        if paper:
            return jsonify(paper.get_portfolio())
    return jsonify({'error': 'No portfolio data'})

@api_blueprint.route('/api/signals')
def api_signals():
    orch = _system.get('orchestrator')
    if orch:
        meta = orch.get_module('meta_learner')
        if meta and meta.history:
            return jsonify(meta.history[-10:])
    return jsonify([])

@api_blueprint.route('/api/health')
def api_health():
    orch = _system.get('orchestrator')
    if orch:
        prod = orch.get_module('production')
        if prod:
            return jsonify(prod.get_status())
    return jsonify({'health': 'UNKNOWN'})

@api_blueprint.route('/api/config', methods=['GET', 'POST'])
def api_config():
    config = _system.get('config')
    if not config:
        return jsonify({'error': 'No config manager'})
    if request.method == 'POST':
        data = request.get_json()
        for key, value in data.items():
            config.set(key, value)
        return jsonify({'status': 'updated'})
    return jsonify(config.config)

@api_blueprint.route('/api/watchlist')
def api_watchlist():
    orch = _system.get('orchestrator')
    if orch:
        wl = orch.get_module('watchlist')
        if wl and wl.watchlist:
            return jsonify(wl.watchlist)
    return jsonify([])
