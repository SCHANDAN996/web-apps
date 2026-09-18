"""
🧠 AI Brain Dashboard — Real-Time Neural Activity Monitor

Flask Blueprint that adds:
- /brain route with stunning live dashboard
- /api/brain-state JSON API for live AI state
- /api/brain-history for prediction history
- SocketIO brain_update events pushed every 30 seconds
"""

import json
import os
import threading
import time
from datetime import datetime, timedelta
from flask import Blueprint, render_template, jsonify

brain_bp = Blueprint('brain', __name__)

# Global state (populated by main.py's bot loop)
_brain_state = {
    'stocks': {},         # {symbol: {score, signal, confidence, regime}}
    'regime': 'UNKNOWN',
    'regime_confidence': 0,
    'sentiment': 0,
    'model_version': 'v1',
    'model_params': 0,
    'training_active': False,
    'total_predictions': 0,
    'accuracy': 0,
    'win_rate': 0,
    'day_pnl': 0,
    'equity': 100000,
    'max_drawdown': 0,
    'sharpe': 0,
    'last_update': None,
    'uptime_seconds': 0,
    'evolution_status': 'idle'
}

_prediction_history = []  # [{time, symbol, score, signal}]
_start_time = datetime.now()


def update_brain_state(symbol, score, signal, confidence, regime='UNKNOWN'):
    """Called from main.py's monitoring loop to push live data."""
    _brain_state['stocks'][symbol] = {
        'score': round(score, 4),
        'signal': signal,
        'confidence': round(confidence, 3),
        'regime': regime,
        'updated': datetime.now().strftime('%H:%M:%S')
    }
    _brain_state['last_update'] = datetime.now().isoformat()
    _brain_state['uptime_seconds'] = int((datetime.now() - _start_time).total_seconds())
    
    # Store prediction history (keep last 500)
    _prediction_history.append({
        'time': datetime.now().strftime('%H:%M:%S'),
        'symbol': symbol,
        'score': round(score, 4),
        'signal': signal
    })
    if len(_prediction_history) > 500:
        _prediction_history.pop(0)


def update_performance_metrics(metrics_dict):
    """Update from PerformanceTracker."""
    for key in ['accuracy', 'win_rate', 'day_pnl', 'total_predictions',
                'sharpe', 'max_drawdown']:
        if key in metrics_dict:
            _brain_state[key] = metrics_dict[key]


def update_model_info(version, params, training_active=False):
    """Update model metadata."""
    _brain_state['model_version'] = version
    _brain_state['model_params'] = params
    _brain_state['training_active'] = training_active


def update_regime(regime, confidence):
    """Update current market regime."""
    _brain_state['regime'] = regime
    _brain_state['regime_confidence'] = round(confidence, 3)


# --- Routes ---

@brain_bp.route('/brain')
def brain_page():
    return render_template('brain.html', active_page='brain')


@brain_bp.route('/api/brain-state')
def api_brain_state():
    """Full brain state JSON — populated from real model + DB data."""
    import torch, os, sqlite3
    
    # Load real model info
    model_path = 'models/tradenet_actor.pth'
    if os.path.exists(model_path):
        try:
            checkpoint = torch.load(model_path, map_location='cpu', weights_only=False)
            _brain_state['model_version'] = str(checkpoint.get('model_version', 'v3'))
            _brain_state['model_params'] = int(sum(p.numel() for p in checkpoint['model_state'].values()))
            _brain_state['accuracy'] = float(round(float(checkpoint.get('val_acc', 0)) * 100, 1))
            _brain_state['pred_std'] = float(round(float(checkpoint.get('pred_std', 0)), 3))
            _brain_state['val_loss'] = float(round(float(checkpoint.get('val_loss', 0)), 4))
            _brain_state['trained_at'] = str(checkpoint.get('timestamp', ''))
            _brain_state['input_features'] = int(checkpoint.get('input_size', 0))
        except:
            pass
    
    # Load real backtest stats from DB
    db_path = 'trading_data.db'
    if os.path.exists(db_path):
        try:
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            c.execute('''SELECT COUNT(*), 
                SUM(CASE WHEN pnl>0 THEN 1 ELSE 0 END),
                ROUND(SUM(pnl),0),
                ROUND(AVG(pnl),2),
                ROUND(AVG(rr_ratio),2),
                ROUND(SUM(CASE WHEN pnl>0 THEN pnl ELSE 0 END) / 
                  NULLIF(ABS(SUM(CASE WHEN pnl<0 THEN pnl ELSE 0 END)),0), 2)
            FROM trade_journal WHERE status='CLOSED' ''')
            row = c.fetchone()
            if row and row[0]:
                total, wins, pnl, avg_pnl, avg_rr, pf = row
                _brain_state['win_rate'] = round(wins/total*100, 1) if total else 0
                _brain_state['total_trades'] = total
                _brain_state['total_pnl'] = pnl or 0
                _brain_state['avg_pnl'] = avg_pnl or 0
                _brain_state['avg_rr'] = avg_rr or 0
                _brain_state['profit_factor'] = pf or 0
                _brain_state['total_predictions'] = total
                
                # Per symbol
                c.execute('''SELECT symbol, COUNT(*), 
                    ROUND(SUM(CASE WHEN pnl>0 THEN 1.0 ELSE 0 END)/COUNT(*)*100,1),
                    ROUND(SUM(pnl),0)
                FROM trade_journal WHERE status='CLOSED' GROUP BY symbol''')
                symbol_stats = {}
                for r in c.fetchall():
                    symbol_stats[r[0]] = {'trades': r[1], 'winRate': r[2], 'pnl': r[3]}
                _brain_state['symbol_stats'] = symbol_stats
            conn.close()
        except:
            pass
    
    _brain_state['uptime_seconds'] = int((datetime.now() - _start_time).total_seconds())
    return jsonify(_brain_state)


@brain_bp.route('/api/brain-history')
def api_brain_history():
    """Recent prediction history."""
    return jsonify(_prediction_history[-100:])


@brain_bp.route('/api/brain-stocks')
def api_brain_stocks():
    """Just the stock confidence map."""
    return jsonify(_brain_state.get('stocks', {}))


def start_socketio_emitter(socketio, interval=30):
    """Background task that pushes brain state to all connected clients."""
    def _emit_loop():
        while True:
            socketio.sleep(interval)
            try:
                socketio.emit('brain_update', _brain_state)
            except:
                pass
    
    socketio.start_background_task(_emit_loop)
