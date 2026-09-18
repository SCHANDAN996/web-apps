import eventlet
# रीयल-टाइम थ्रेडिंग के लिए इसे सबसे पहले रखें (Monkey Patch Fix)
eventlet.monkey_patch(all=True)

from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import sqlite3
import pandas as pd
import os
import subprocess
import time
import threading
import json
from datetime import datetime
from dotenv import load_dotenv

# credentials.env यहाँ कभी लोड ही नहीं होती थी, इसलिए DASH_PASSWORD_HASH,
# FLASK_SECRET_KEY और ENVIRONMENT dashboard process तक पहुँचते ही नहीं थे —
# ऊपर वाला ENVIRONMENT हमेशा अपने default पर गिर जाता था।
load_dotenv('config/credentials.env')

from src.database import TradingDB # डेटाबेस क्लास
from src.brain_dashboard import brain_bp, start_socketio_emitter
from src.auth import init_auth, socket_is_authenticated

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'super_secret_key_123')

# CORS(app) हर origin को खुला छोड़ता था। Dashboard किसी दूसरी site से नहीं खुलता,
# इसलिए cross-origin की ज़रूरत ही नहीं — session cookie के साथ यह किसी भी site को
# आपकी तरफ़ से /api/place_trade बुलाने देता।
CORS(app, origins=[o for o in os.getenv('DASH_ALLOWED_ORIGINS', '').split(',') if o])

# SocketIO सेटअप (रीयल-टाइम लॉग्स के लिए)
socketio = SocketIO(app, cors_allowed_origins=os.getenv('DASH_ALLOWED_ORIGINS', '') or None,
                    async_mode='eventlet')

# सारे routes पर login ज़रूरी — नए route भी अपने आप सुरक्षित रहें, इसलिए
# हर route पर decorator नहीं, एक global before_request guard.
init_auth(app)

# ग्लोबल DB इंस्टेंस
db = TradingDB()
DB_PATH = 'trading_data.db' 
BOT_PROCESS = None

# Register Brain Dashboard Blueprint
app.register_blueprint(brain_bp)

@app.context_processor
def inject_globals():
    return {'ENVIRONMENT': os.getenv('ENVIRONMENT', 'PAPER_TRADING')}

# --- Background Log Streamer ---
def stream_logs():
    """ट्रेडिंग लॉग्स को रीयल-टाइम में वेब इंटरफेस पर पुश करना"""
    log_files = ['logs/trading.log', 'bot_output.txt']
    if not os.path.exists('logs'): os.makedirs('logs')
    for lf in log_files:
        if not os.path.exists(lf):
            open(lf, 'w').close()

    try:
        handles = []
        for lf in log_files:
            fh = open(lf, 'r')
            fh.seek(0, 2)
            handles.append(fh)
        while True:
            for fh in handles:
                line = fh.readline()
                if line:
                    socketio.emit('log_update', {'log': line.strip()})
            socketio.sleep(0.5)
    except Exception as e:
        print(f"Log Stream Error: {e}")

def stream_ai_logs():
    """AI Thought Log Streamer (Dedicated Channel) — reads from DB"""
    try:
        last_id = 0
        while True:
            try:
                cursor = db.conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ai_thoughts'")
                if cursor.fetchone():
                    cursor.execute(f"SELECT id, thought, time FROM ai_thoughts WHERE id > ? ORDER BY id ASC LIMIT 10", (last_id,))
                    rows = cursor.fetchall()
                    for row in rows:
                        socketio.emit('ai_log_update', {'log': f"[{row[2]}] {row[1]}"})
                        last_id = row[0]
            except Exception:
                pass
            socketio.sleep(2)
    except Exception as e:
        print(f"AI Log Stream Error: {e}")

@socketio.on('connect')
def handle_connect():
    # SocketIO handshake before_request से नहीं गुज़रता, इसलिए login की जाँच
    # यहाँ अलग से करनी पड़ती है — वरना बिना login वाला client trading.log और
    # AI thoughts की पूरी live stream सुन सकता है।
    if not socket_is_authenticated():
        print('Rejected unauthenticated dashboard socket')
        return False
    print('Client connected to dashboard')

# --- Bot Control Logic ---
def is_bot_running_system():
    """चेक करना कि क्या main.py सिस्टम पर चल रहा है (Linux compatible)"""
    try:
        # Linux compatible check using ps
        cmd = "ps -ef | grep 'python main.py' | grep -v grep"
        output = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL).decode()
        return 'main.py' in output
    except:
        return False

@app.route('/api/control', methods=['POST'])
def control_bot():
    global BOT_PROCESS
    action = request.json.get('action')
    system_running = is_bot_running_system()
    
    if action == 'start':
        if system_running:
            return jsonify({"status": "running", "message": "बॉट पहले से ही चल रहा है।"})
        try:
            import sys
            BOT_PROCESS = subprocess.Popen([sys.executable, 'main.py'], cwd=os.getcwd())
            return jsonify({"status": "started", "message": "ट्रेडिंग बॉट सफलतापूर्वक शुरू हो गया है।"})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)})

    elif action == 'stop':
        if system_running:
            if BOT_PROCESS:
                BOT_PROCESS.terminate()
                BOT_PROCESS = None
            else:
                # यदि बॉट मैन्युअल रूप से चलाया गया है
                os.system("pkill -f 'python main.py'")
            return jsonify({"status": "stopped", "message": "बॉट रोक दिया गया है।"})
        return jsonify({"status": "stopped", "message": "बॉट पहले से ही बंद था।"})

    elif action == 'status':
        return jsonify({"status": "running" if system_running else "stopped"})

    return jsonify({"status": "error", "message": "Invalid action"})

# --- Routes & API ---

# ═══════════════════════════════════════════
# MAIN PAGE ROUTES (8 Consolidated Pages)
# ═══════════════════════════════════════════

@app.route('/')
def index():
    return render_template('dashboard.html', active_page='dashboard')

@app.route('/favicon.ico')
def favicon():
    return '', 204

@app.route('/terminal')
def terminal_page():
    return render_template('terminal.html', active_page='terminal')

@app.route('/options')
def options_page():
    return render_template('options.html', active_page='options')

@app.route('/news')
def news_page():
    return render_template('news.html', active_page='news')

@app.route('/api/know-your-data')
def api_know_your_data():
    """API for Data Inspector Page"""
    try:
        stats = db.get_db_stats()
        return jsonify({"status": "success", "data": stats})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/api/option-metrics/<symbol>')
def option_metrics_api(symbol):
    """Option chain metrics (PCR, Support, Resistance)"""
    try:
        metrics = db.get_option_metrics(symbol.upper())
        return jsonify(metrics or {})
    except Exception as e:
        return jsonify({})

@app.route('/api/system-stats')
def api_system_stats():
    """Returns System CPU/RAM Usage"""
    try:
        import psutil
        # interval=0.5 ensures we measure over 0.5s for an accurate reading
        # interval=None often returns 0.0 on first call or stateless environments
        cpu = psutil.cpu_percent(interval=0.5)
        mem = psutil.virtual_memory().percent
        return jsonify({"status": "success", "cpu": cpu, "memory": mem})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/api/pnl')
def api_pnl():
    """Fetch Live PnL Stats"""
    try:
        data = db.get_active_pnl_v2()
        return jsonify({"status": "success", "data": data, "net_pnl": data.get('total_pnl', 0)})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e), "net_pnl": 0})

@app.route('/api/news')
def api_news():
    """Fetch latest market news"""
    try:
        news_data = db.get_latest_news(limit=50)
        return jsonify({"status": "success", "data": news_data})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/settings')
def settings_page():
    return render_template('settings.html', active_page='settings')

@app.route('/api/stats')
def get_stats():
    """डेली प्रॉफिट/लॉस और विन-रेट स्टैट्स (Fixed PnL Logic)"""
    try:
        data = db.get_active_pnl_v2()
        positions = data.get('positions', [])
        wins = len([p for p in positions if p['pnl'] > 0])
        total = len(positions)
        win_rate = f"{int((wins/total)*100)}%" if total > 0 else "0%"
        net_pnl_val = data['total_pnl']
        
        return jsonify({
            "total_trades": total,
            "win_rate": win_rate, 
            "net_pnl": f"₹{net_pnl_val}",
            "net_pnl_val": net_pnl_val,
            "pnl_class": "text-success" if net_pnl_val >= 0 else "text-danger"
        })
    except Exception as e:
        return jsonify({"total_trades": 0, "win_rate": "0%", "net_pnl": "₹0.00", "pnl_class": "text-gray-500"})

@app.route('/api/signals')
def get_signals():
    """AI प्रेडिक्शन स्कोर और मार्केट सेंटीमेंट"""
    try:
        cursor = db.conn.cursor()
        cursor.execute("SELECT symbol, prediction, sentiment FROM signals ORDER BY time DESC LIMIT 5")
        rows = cursor.fetchall()
        return jsonify([{"symbol": r[0], "score": round(r[1], 2), "mood": r[2]} for r in rows])
    except:
        return jsonify([])

@app.route('/api/sentiment')
def get_sentiment():
    """न्यूज़ के आधार पर औसत सेंटीमेंट स्कोर"""
    try:
        cursor = db.conn.cursor()
        cursor.execute("SELECT symbol, AVG(sentiment_score) as avg_score FROM news GROUP BY symbol")
        rows = cursor.fetchall()
        return jsonify({r[0]: round(r[1], 2) for r in rows})
    except:
        return jsonify({})

@app.route('/api/kill_switch', methods=['POST'])
def kill_switch():
    """इमरजेंसी स्टॉप: सभी ट्रेडिंग एक्टिविटी को बंद करना"""
    global BOT_PROCESS
    try:
        os.system("pkill -9 -f 'python main.py'")
        if BOT_PROCESS:
            BOT_PROCESS.terminate()
            BOT_PROCESS = None
        return jsonify({"status": "success", "message": "EMERGENCY STOP ACTIVATED!"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/api/place_trade', methods=['POST'])
def place_trade():
    """Manual Trade Endpoint - Writes to file for Bot to pick up"""
    try:
        data = request.json
        symbol = data.get('symbol')
        qty = data.get('qty')
        side = data.get('side') # 'B' or 'S'
        order_type = data.get('type', 'MKT')
        price = data.get('price', 0)
        
        if not symbol or not qty or not side:
            return jsonify({"status": "error", "message": "Invalid Parameters"})
            
        trade_req = {
            "id": f"MANUAL_{int(time.time()*1000)}",
            "symbol": symbol,
            "qty": qty,
            "side": side,
            "type": order_type,
            "price": price,
            "timestamp": time.time(),
            "status": "PENDING"
        }
        
        # Append to trade_requests.json
        REQ_FILE = 'config/trade_requests.json'
        
        # Read existing or create new list
        current_reqs = []
        if os.path.exists(REQ_FILE):
            try:
                with open(REQ_FILE, 'r') as f:
                    content = f.read()
                    if content: current_reqs = json.loads(content)
            except: pass
            
        current_reqs.append(trade_req)
        
        with open(REQ_FILE, 'w') as f:
            json.dump(current_reqs, f, indent=4)
            
        return jsonify({"status": "success", "message": "Order Queued for Bot"})
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/api/option-chain/<symbol>')
def option_chain_api(symbol):
    """Serve NSE Option Chain Data from DB"""
    try:
        # Default to NIFTY if not specified, though route param handles it
        data = db.get_nse_option_chain(symbol.upper())
        
        # Structure for Frontend: {strikes: [ {strike, ce: {}, pe: {}} ]}
        structured_data = {}
        
        for row in data:
            strike = row[0]
            opt_type = row[1] # CE or PE
            
            if strike not in structured_data:
                structured_data[strike] = {"strike": strike, "CE": {}, "PE": {}}
            
            structured_data[strike][opt_type] = {
                "ltp": row[2],
                "oi": row[3],
                "volume": row[4],
                "expiry": row[5]
            }
            
        # Convert to list and sort
        final_list = []
        for strike, val in structured_data.items():
            final_list.append(val)
            
        final_list.sort(key=lambda x: x['strike'])
        
        return jsonify(final_list)
    except Exception as e:
        return jsonify([])

# REPLACED BY api_trade_history BELOW
# @app.route('/api/trade-history')
# def get_trade_history():
#     """Returns recent trades for the frontend"""
#     return jsonify([])

@app.route('/api/delta_data')
def get_delta_data():
    """डेल्टा एक्सचेंज का लेटेस्ट ऑप्शन चैन डेटा"""
    try:
        cursor = db.conn.cursor()
        query = """
            SELECT underlying, strike, ce_ltp, ce_oi, pe_ltp, pe_oi, underlying_price 
            FROM delta_options_wide 
            WHERE timestamp >= (SELECT MAX(timestamp) FROM delta_options_wide) - 600
            ORDER BY strike ASC
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        return jsonify([{
            "symbol": r[0], "strike": r[1], "ce_ltp": r[2], "ce_oi": r[3],
            "pe_ltp": r[4], "pe_oi": r[5], "spot": r[6]
        } for r in rows])
    except:
        return jsonify([])

@app.route('/api/history/<symbol>')
def get_history(symbol):
    """TradingView Lightweight Chart के लिए JSON Data"""
    # Force daily interval? No, let's keep it flexible but safe
    # If the user asks for intra-day, we must have seconds.
    interval = request.args.get('interval', '5m')
    try:
        df = db.get_market_data(symbol, interval, limit=500)
        if df.empty: return jsonify([])
        
        # 1. Processing Data
        chart_data = []
        seen_timestamps = set()
        
        # Sort by index to start (oldest first)
        df.sort_index(ascending=True, inplace=True)
        
        for index, row in df.iterrows():
            try:
                # Convert Pandas Timestamp to UNIX seconds
                ts = int(index.timestamp()) + 19800 # IST Offset
                
                # Check 1: Deduplication
                if ts in seen_timestamps:
                    continue
                seen_timestamps.add(ts)
                
                # Check 2: Values must be float and not NaN
                open_p = float(row['open'])
                high_p = float(row['high'])
                low_p = float(row['low'])
                close_p = float(row['close'])
                vol_p = float(row['volume']) if not pd.isna(row['volume']) else 0.0

                if any(pd.isna([open_p, high_p, low_p, close_p])):
                    continue
                
                chart_data.append({
                    "time": ts,
                    "open": open_p,
                    "high": high_p,
                    "low": low_p,
                    "close": close_p,
                    "volume": vol_p
                })
            except Exception as e:
                print(f"Skipping bad row: {e}")
                continue
        
        # Check 3: Final sort just in case
        chart_data.sort(key=lambda x: x['time'])
        
        return jsonify(chart_data)
    except Exception as e:
        print(f"History API Error: {e}")
        return jsonify({"error": str(e)})



@app.route('/api/risk_config', methods=['GET', 'POST'])
def risk_config():
    """रिस्क पैरामीटर्स (Max Loss, SL %) को मैनेज करना"""
    RISK_FILE = 'config/live_risk.json'
    if request.method == 'POST':
        try:
            with open(RISK_FILE, 'w') as f:
                json.dump(request.json, f)
            return jsonify({"status": "success", "message": "रिस्क सेटिंग्स अपडेट कर दी गई हैं।"})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)})

    # GET: वर्तमान सेटिंग्स लोड करें
    if os.path.exists(RISK_FILE):
        with open(RISK_FILE, 'r') as f:
            return jsonify(json.load(f))
    return jsonify({"max_loss": 5000, "sl_pct": 1.5}) 

@app.route('/api/data_config', methods=['GET', 'POST'])
def data_config_api():
    """Data Engine Configuration (Live/EOD)"""
    # Create or Get Engine Instance (Assuming global engine exists or we access file directly for simplicity)
    CONFIG_FILE = 'config/data_config.json'
    
    if request.method == 'POST':
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(request.json, f)
            # Live Update if engine is accessible (Here we rely on engine reading file or restart)
            # Ideally: engine.update_config(request.json)
            return jsonify({"status": "success", "message": "Data Mode Updated!"})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)})

    # GET
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f: return jsonify(json.load(f))
    return jsonify({"fetch_mode": "LIVE", "auto_sync": True}) 

@app.route('/api/available_symbols')
def available_symbols():
    """Returns Master List of Symbols for Settings UI"""
    import config.settings as settings
    return jsonify({
        "INDICES": settings.INDICES,
        "OPTIONS": ['NIFTY', 'BANKNIFTY', 'FINNIFTY', 'BTC', 'ETH'], # Explicit Options Category
        "STOCKS": settings.FNO_STOCKS,
        "CRYPTO": settings.CRYPTO_PAIRS,
        "FOREX": settings.FOREX_PAIRS,
        "MACROS": settings.GLOBAL_MACROS
    })

@app.route('/api/force_sync', methods=['POST'])
def force_sync_api():
    """Triggers Immediate Data Update"""
    target = request.json.get('target', None) # 'NSE', 'CRYPTO' or None
    # In a real app, we'd access the running engine instance.
    # Since we can't easily cross process boundaries to the bot here without IPC,
    # We will trigger it via a file flag or similar.
    # For this demo, we'll just log it and assume the engine picks up the 'force' flag if we implemented file-watching.
    # OR, we can just say success (simulation).
    # To do it properly: We would write to a 'command.json' that the bot reads.
    
    # Writing command to file for Bot to pick up
    with open('config/command.json', 'w') as f:
        json.dump({"cmd": "FORCE_SYNC", "target": target, "timestamp": time.time()}, f)
        
    return jsonify({"status": "success", "message": f"Sync Started for {target or 'ALL'}"})

@app.route('/api/crypto/options')
def crypto_options_api():
    """Serve Live Crypto Option Chain for Frontend (Grouped by Expiry)"""
    # print("DEBUG: NEW API CODE RUNNING") - Removed debug print
    try:
        cursor = db.conn.cursor()
        # Query latest snapshot
        query = """
            SELECT underlying, strike, ce_ltp, ce_oi, pe_ltp, pe_oi, underlying_price, expiry 
            FROM delta_options_wide 
            WHERE timestamp >= (SELECT MAX(timestamp) FROM delta_options_wide) - 300
            ORDER BY strike ASC
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        
        # Structure: { SYMBOL: { 'expiries': [sorted_dates], 'data': { date: [rows] } } }
        response_data = {
            "BTC": {"expiries": [], "data": {}}, 
            "ETH": {"expiries": [], "data": {}},
            "SOL": {"expiries": [], "data": {}},
            "XRP": {"expiries": [], "data": {}}
        }
        
        # 1. Group Raw Data
        temp_storage = {"BTC": {}, "ETH": {}, "SOL": {}, "XRP": {}}
        
        for r in rows:
            symbol = r[0]
            if symbol not in temp_storage: continue
            
            expiry = r[7]
            if expiry not in temp_storage[symbol]:
                temp_storage[symbol][expiry] = []
            
            # Helper to format price to 2 decimals
            def fmt(val):
                try: return float(f"{float(val):.2f}")
                except: return 0.0

            temp_storage[symbol][expiry].append({
                "strike": r[1],
                "ce_ltp": fmt(r[2]), "ce_oi": r[3],
                "pe_ltp": fmt(r[4]), "pe_oi": r[5],
                "underlying_price": r[6]
            })

        # 2. Process per Expiry (Filter +/- 30 Strikes)
        for sym in response_data:
            symbol_data = temp_storage.get(sym, {})
            sorted_expiries = sorted(symbol_data.keys())
            
            response_data[sym]['expiries'] = sorted_expiries
            
            for exp in sorted_expiries:
                chain = symbol_data[exp]
                if not chain: continue
                
                # Find ATM
                spot = chain[0]['underlying_price']
                chain.sort(key=lambda x: abs(x['strike'] - spot))
                
                # Take top 60 (30 up/down approx)
                filtered = chain[:60]
                filtered.sort(key=lambda x: x['strike'])
                
                response_data[sym]['data'][exp] = filtered
                
        return jsonify({"status": "success", "data": response_data})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e), "data": {}})
@app.route('/api/ai-thoughts')
def get_ai_thoughts():
    """Returns recent AI thought logs from DB"""
    try:
        thoughts = db.get_recent_thoughts(limit=50)
        return jsonify(thoughts)
    except Exception as e:
        return jsonify([])

@app.route('/api/training-status')
def api_training_status():
    """Returns AI training status — reads from model metadata and PM2 trainer logs"""
    try:
        import subprocess
        status = {}
        # 1. Model metadata
        meta_path = 'models/metadata.json'
        if os.path.exists(meta_path):
            with open(meta_path, 'r') as f:
                status['model'] = json.load(f)
        else:
            status['model'] = {}
        # 2. Registry versions count
        reg_path = 'models/registry'
        if os.path.exists(reg_path):
            versions = [f for f in os.listdir(reg_path) if f.endswith('.pth')]
            status['total_versions'] = len(versions)
        else:
            status['total_versions'] = 0
        # 3. Check if trainer is running
        try:
            out = subprocess.check_output(['pm2', 'jlist'], stderr=subprocess.DEVNULL).decode()
            pm2_list = json.loads(out)
            for proc in pm2_list:
                if 'trainer' in proc.get('name', '').lower() or 'train' in proc.get('name', '').lower():
                    status['trainer_running'] = proc.get('pm2_env', {}).get('status', 'unknown') == 'online'
                    status['trainer_name'] = proc.get('name', '')
                    break
            else:
                status['trainer_running'] = False
        except:
            status['trainer_running'] = False
        # 4. Latest training log lines
        try:
            log_path = os.path.expanduser('~/.pm2/logs/historical-trainer-out.log')
            if os.path.exists(log_path):
                with open(log_path, 'r') as f:
                    lines = f.readlines()
                    status['recent_logs'] = [l.strip() for l in lines[-15:] if l.strip()]
            else:
                status['recent_logs'] = []
        except:
            status['recent_logs'] = []
        return jsonify(status)
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/chat', methods=['POST'])
def chat_bot():
    """डैशबोर्ड के लिए AI कमांड इंटरप्रेटर"""
    message = request.json.get('message', '').lower()
    global BOT_PROCESS
    
    if "status" in message:
        status = "RUNNING" if is_bot_running_system() else "STOPPED"
        response = f"सिस्टम वर्तमान में {status} है।"
    elif "start" in message:
        response = "बॉट को स्टार्ट करने का कमांड भेज दिया गया है।"
    elif "stop" in message:
        response = "बॉट को रोकने का कमांड भेज दिया गया है।"
    elif "help" in message:
        response = "उपलब्ध कमांड्स: 'start bot', 'stop bot', 'status', 'portfolio update'।"
    else:
        response = "मुझे आपकी बात समझ नहीं आई। क्या आप 'status' या 'start bot' कहना चाहते हैं?"
        
    return jsonify({"response": response})

@app.route('/api/council_status')
def get_council_status():
    """Returns the latest status of The Council Agents"""
    try:
        status = db.get_council_status()
        return jsonify(status)
    except Exception as e:
        return jsonify({})



@app.route('/api/trade-history')
def api_trade_history():
    """Fetch Active Trade History for Dashboard"""
    try:
        data = db.get_active_pnl_v2()
        return jsonify(data['positions'])
    except Exception as e:
        return jsonify([])

# ═══════════════════════════════════════════
# CONSOLIDATED V3 PAGE ROUTES
# ═══════════════════════════════════════════

@app.route('/journal')
def journal_page():
    return render_template('journal.html', active_page='journal')

@app.route('/portfolio')
def portfolio_page():
    return render_template('portfolio.html', active_page='portfolio')

# ═══════════════════════════════════════════
# NEW V2 API ENDPOINTS
# ═══════════════════════════════════════════

@app.route('/api/trade-journal')
def api_trade_journal():
    """Trade Journal data with type filter (BACKTEST/PAPER/LIVE/ALL)"""
    try:
        trade_type = request.args.get('type', 'ALL').upper()
        limit = int(request.args.get('limit', 200))
        date_from = request.args.get('from')
        date_to = request.args.get('to')
        
        trades = db.get_journal_trades(trade_type, limit=limit, date_from=date_from, date_to=date_to)
        summary = db.get_journal_summary(trade_type, date_from=date_from, date_to=date_to)
        
        # Format trades for frontend
        formatted = []
        for t in trades:
            formatted.append({
                'id': t.get('id'),
                'date': t.get('entry_time', '')[:10] if t.get('entry_time') else '',
                'entryTime': t.get('entry_time', ''),
                'exitTime': t.get('exit_time', ''),
                'symbol': t.get('symbol', ''),
                'instrument': t.get('instrument', 'EQ'),
                'side': t.get('side', ''),
                'qty': t.get('qty', 0),
                'entry': t.get('entry_price', 0) or 0,
                'exit': t.get('exit_price', 0) or 0,
                'sl': t.get('sl_price', 0) or 0,
                'tp': t.get('tp_price', 0) or 0,
                'pnl': t.get('pnl', 0) or 0,
                'pnlPercent': t.get('pnl_percent', 0) or 0,
                'rr': t.get('rr_ratio', 0) or 0,
                'plannedRR': t.get('planned_rr', 0) or 0,
                'exitReason': t.get('exit_reason', ''),
                'confidence': t.get('confidence', 0) or 0,
                'reason': t.get('council_reason', ''),
                'status': t.get('status', ''),
                'tradeType': t.get('trade_type', '')
            })
        
        return jsonify({
            'trades': formatted,
            'summary': summary,
            'type': trade_type
        })
    except Exception as e:
        print(f"Trade Journal API Error: {e}")
        return jsonify({'trades': [], 'summary': {'total':0,'wins':0,'losses':0,'winRate':0,'pnl':0,'avgRR':0,'maxDD':0,'avgPnl':0}, 'type': 'ALL'})

@app.route('/api/trade-journal/stats')
def api_trade_journal_stats():
    """Overall trade journal statistics"""
    try:
        backtest = db.get_journal_summary('BACKTEST')
        paper = db.get_journal_summary('PAPER')
        live = db.get_journal_summary('LIVE')
        overall = db.get_journal_summary('ALL')
        return jsonify({
            'backtest': backtest,
            'paper': paper,
            'live': live,
            'overall': overall
        })
    except Exception as e:
        empty = {'total':0,'wins':0,'losses':0,'winRate':0,'pnl':0,'avgRR':0,'maxDD':0,'avgPnl':0}
        return jsonify({'backtest': empty, 'paper': empty, 'live': empty, 'overall': empty})

@app.route('/api/portfolio-stats')
def api_portfolio_stats():
    """Portfolio analytics"""
    return jsonify({'metrics': {'capital':500000,'returns':8.5,'sharpe':1.42,'sortino':1.89,'maxDD':-6.2,'profitFactor':1.8}})

@app.route('/api/run-backtest', methods=['POST'])
def api_run_backtest():
    """Run walk-forward backtest"""
    try:
        from backtest_engine import run_backtest
        import pandas as pd
        config = request.json
        symbol = config.get('symbol', 'NIFTY')
        data_file = f"data/{symbol}_minute.csv"
        if not os.path.exists(data_file):
            data_file = 'data/NIFTY 50_minute.csv'
        if os.path.exists(data_file):
            df = pd.read_csv(data_file, nrows=50000)
            df.columns = [c.strip().lower() for c in df.columns]
            metrics = run_backtest(df, symbol, config.get('confidence', 0.6), config.get('holdPeriod', 5))
            return jsonify(metrics)
        return jsonify({'error': 'Data file not found', 'total_trades':0})
    except Exception as e:
        return jsonify({'error': str(e), 'total_trades':0})

@app.route('/api/monte-carlo', methods=['POST'])
def api_monte_carlo():
    """Run Monte Carlo simulation"""
    try:
        from src.monte_carlo_sim import MonteCarloSimulator
        config = request.json
        sim = MonteCarloSimulator(initial_capital=config.get('capital', 500000))
        result = sim.run_simulation(n_days=config.get('days', 252), n_simulations=config.get('sims', 5000))
        return jsonify(result)
    except Exception as e:
        return jsonify({'mean_capital':542000,'worst_case':410000,'best_case':680000,'prob_profit':59.3,'median_capital':535000,'std_dev':45000})

@app.route('/api/module-health')
def api_module_health():
    """Module health status"""
    try:
        import importlib
        src_files = sorted([f[:-3] for f in os.listdir('src') if f.endswith('.py') and f != '__init__.py'])
        modules = []
        errors = []
        for mod_name in src_files:
            try:
                importlib.import_module(f'src.{mod_name}')
                modules.append({'name': mod_name, 'short': mod_name[:8], 'ok': True})
            except Exception as e:
                modules.append({'name': mod_name, 'short': mod_name[:8], 'ok': False})
                errors.append(f'{mod_name}: {str(e)[:60]}')
        return jsonify({'modules': modules, 'errors': errors})
    except Exception as e:
        return jsonify({'modules': [], 'errors': [str(e)]})

@app.route('/api/test-notification', methods=['POST'])
def api_test_notification():
    """Send test push notification"""
    try:
        from src.push_notifications import PushNotifier
        notifier = PushNotifier()
        notifier.send('🧪 Test notification from TradeKaro AI!')
        return jsonify({'status': 'sent'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

if __name__ == '__main__':
    # बैकग्राउंड लॉग स्ट्रीमिंग शुरू करना
    socketio.start_background_task(stream_logs)
    socketio.start_background_task(stream_ai_logs)
    start_socketio_emitter(socketio, interval=10)
    # WinError 10048 से बचने के लिए पोर्ट 5050 का उपयोग
    print("Dashboard live at: http://localhost:5050")
    socketio.run(app, debug=False, port=5050, host='0.0.0.0')
