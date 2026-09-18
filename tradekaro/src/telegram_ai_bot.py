"""
📱 Telegram AI Bot — Natural Language Trading Assistant

Commands:
  /status    — AI brain state, regime, win rate
  /predict   — NIFTY/BANKNIFTY/stock prediction + confidence
  /portfolio — Current positions + P&L
  /explain   — Why AI took the last trade decision
  /risk      — Risk metrics + current drawdown
  /brain     — V2 model info + training status
  /help      — All commands list

Hindi Support:
  "NIFTY kaisa hai?"  → Same as /predict NIFTY
  "position dikhao"   → Same as /portfolio
  "risk kitna hai?"   → Same as /risk

Runs as background thread, polls Telegram every 2 seconds.
"""

import os
import json
import time
import threading
import logging
import requests
from datetime import datetime

# Load env
try:
    from dotenv import load_dotenv
    load_dotenv('config/credentials.env')
except:
    pass


class TelegramAIBot:
    """
    Lightweight Telegram bot using raw HTTP API.
    No external library needed — uses requests only.
    """
    
    API_BASE = "https://api.telegram.org/bot{token}"
    
    def __init__(self, brain=None, db=None):
        self.token = os.getenv('TELEGRAM_TOKEN', '')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID', '')
        self.brain = brain
        self.db = db
        self.last_update_id = 0
        self.running = False
        self._thread = None
        
        # State references (set by main.py)
        self.brain_state = {}
        self.last_predictions = {}
        self.last_trade_reason = "No trades yet"
        
        # Hindi keyword mapping
        self.hindi_commands = {
            'status': ['status', 'haalat', 'kya ho raha', 'kaisa hai bot', 'chalraha'],
            'predict': ['predict', 'prediction', 'kaisa hai', 'kaisa rahega', 'signal', 'kya lagta'],
            'portfolio': ['portfolio', 'position', 'dikhao', 'kitna profit', 'pnl', 'paisa'],
            'risk': ['risk', 'drawdown', 'kitna risk', 'safe', 'danger'],
            'brain': ['brain', 'model', 'dimag', 'training', 'accuracy'],
            'help': ['help', 'madad', 'kya kar sakta', 'commands'],
        }
        
        if self.token and self.token != 'REPLACE_WITH_BOT_TOKEN':
            print(f"[Telegram] 📱 AI Bot initialized")
        else:
            print(f"[Telegram] ⚠️ No token set — bot disabled")
    
    def start(self):
        """Start polling in background thread."""
        if not self.token or self.token == 'REPLACE_WITH_BOT_TOKEN':
            return
        
        self.running = True
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()
        print("[Telegram] 🟢 Bot started polling")
    
    def stop(self):
        self.running = False
    
    def send_message(self, text, chat_id=None, parse_mode='Markdown'):
        """Send message to Telegram."""
        cid = chat_id or self.chat_id
        if not cid or not self.token:
            return
        
        url = f"{self.API_BASE.format(token=self.token)}/sendMessage"
        try:
            requests.post(url, json={
                'chat_id': cid,
                'text': text,
                'parse_mode': parse_mode
            }, timeout=10)
        except Exception as e:
            logging.warning(f"[Telegram] Send failed: {e}")
    
    def send_alert(self, message):
        """Quick alert — used by main.py for trade notifications."""
        self.send_message(f"🚨 *ALERT*\n{message}")
    
    # --- Command Handlers ---
    
    def _handle_status(self, chat_id):
        regime = self.brain_state.get('regime', 'UNKNOWN')
        accuracy = self.brain_state.get('accuracy', 0)
        win_rate = self.brain_state.get('win_rate', 0)
        total_pred = self.brain_state.get('total_predictions', 0)
        sentiment = self.brain_state.get('sentiment', 0)
        uptime = self.brain_state.get('uptime_seconds', 0)
        
        hours = uptime // 3600
        mins = (uptime % 3600) // 60
        
        msg = f"""🧠 *AI Brain Status*

📊 *Market Regime:* `{regime}`
🎯 *Accuracy:* `{accuracy}%`
📈 *Win Rate:* `{win_rate}%`
🔮 *Total Predictions:* `{total_pred}`
📰 *Sentiment:* `{sentiment}`
🕐 *Uptime:* `{hours}h {mins}m`
⚡ *Status:* `RUNNING`"""
        
        self.send_message(msg, chat_id)
    
    def _handle_predict(self, chat_id, symbol=None):
        if not symbol:
            symbol = 'NIFTY'
        symbol = symbol.upper().strip()
        
        pred = self.last_predictions.get(symbol, {})
        score = pred.get('score', 0.5)
        signal = pred.get('signal', 'HOLD')
        
        if score > 0.65:
            emoji = '🟢'
            action = 'BUY'
        elif score < 0.35:
            emoji = '🔴'
            action = 'SELL'
        else:
            emoji = '🟡'
            action = 'HOLD'
        
        msg = f"""{emoji} *{symbol} Prediction*

🎯 *Score:* `{score:.2f}`
📊 *Signal:* `{action}`
🏛️ *Council:* `{signal}`

_Updated: {datetime.now().strftime('%H:%M:%S IST')}_"""
        
        self.send_message(msg, chat_id)
    
    def _handle_portfolio(self, chat_id):
        try:
            if self.db:
                data = self.db.get_active_pnl()
                positions = data.get('positions', [])
                total_pnl = data.get('total_pnl', 0)
                
                if not positions:
                    self.send_message("📭 *No open positions*", chat_id)
                    return
                
                lines = [f"📊 *Portfolio ({len(positions)} positions)*\n"]
                for p in positions[:10]:
                    pnl = p.get('pnl', 0)
                    emoji = '🟢' if pnl >= 0 else '🔴'
                    lines.append(f"{emoji} `{p.get('symbol', '?')}` → ₹{pnl:.0f}")
                
                lines.append(f"\n💰 *Total P&L:* `₹{total_pnl:.0f}`")
                self.send_message('\n'.join(lines), chat_id)
            else:
                self.send_message("⚠️ Database not connected", chat_id)
        except Exception as e:
            self.send_message(f"❌ Error: {e}", chat_id)
    
    def _handle_risk(self, chat_id):
        drawdown = self.brain_state.get('max_drawdown', 0)
        sharpe = self.brain_state.get('sharpe', 0)
        day_pnl = self.brain_state.get('day_pnl', 0)
        
        risk_level = '🟢 LOW' if drawdown < 3 else '🟡 MEDIUM' if drawdown < 7 else '🔴 HIGH'
        
        msg = f"""🛡️ *Risk Report*

📉 *Max Drawdown:* `{drawdown}%`
📊 *Sharpe Ratio:* `{sharpe}`
💰 *Day P&L:* `₹{day_pnl:.0f}`
⚠️ *Risk Level:* {risk_level}"""
        
        self.send_message(msg, chat_id)
    
    def _handle_brain(self, chat_id):
        version = self.brain_state.get('model_version', 'v2')
        params = self.brain_state.get('model_params', 1102466)
        training = self.brain_state.get('training_active', False)
        
        msg = f"""🧬 *Brain Info*

🏗️ *Architecture:* `TransformerLSTM V2`
🔢 *Parameters:* `{params:,}`
📏 *Features:* `29`
🎓 *Training:* `{'⚡ ACTIVE' if training else '✅ Complete'}`
📊 *Version:* `{version}`
🧠 *Attention Heads:* `4`
📐 *Hidden Dim:* `128`"""
        
        self.send_message(msg, chat_id)
    
    def _handle_explain(self, chat_id):
        msg = f"""📝 *Last Trade Decision*

{self.last_trade_reason}

_Ask /predict SYMBOL for specific analysis_"""
        self.send_message(msg, chat_id)
    
    def _handle_help(self, chat_id):
        msg = """🤖 *Trade Karo AI Bot Commands*

`/status` — Brain state, regime, accuracy
`/predict NIFTY` — Stock prediction + score
`/portfolio` — Open positions + P&L
`/risk` — Drawdown + risk metrics
`/brain` — Model architecture info
`/explain` — Why last trade was taken
`/help` — This message

💬 *Hindi bhi chalega:*
_"NIFTY kaisa hai?" "position dikhao" "risk kitna?"_"""
        self.send_message(msg, chat_id)
    
    # --- Polling ---
    
    def _poll_loop(self):
        """Long-poll Telegram for new messages."""
        while self.running:
            try:
                url = f"{self.API_BASE.format(token=self.token)}/getUpdates"
                resp = requests.get(url, params={
                    'offset': self.last_update_id + 1,
                    'timeout': 10
                }, timeout=15)
                
                if resp.status_code == 200:
                    data = resp.json()
                    for update in data.get('result', []):
                        self.last_update_id = update['update_id']
                        self._process_update(update)
            except Exception as e:
                logging.debug(f"[Telegram] Poll error: {e}")
            
            time.sleep(2)
    
    def _process_update(self, update):
        """Process a single Telegram update."""
        msg = update.get('message', {})
        text = msg.get('text', '').strip()
        chat_id = msg.get('chat', {}).get('id', self.chat_id)
        
        if not text:
            return
        
        # Command routing
        text_lower = text.lower()
        
        if text_lower.startswith('/status') or self._match_hindi(text_lower, 'status'):
            self._handle_status(chat_id)
        elif text_lower.startswith('/predict') or self._match_hindi(text_lower, 'predict'):
            symbol = text.split()[-1] if len(text.split()) > 1 else None
            self._handle_predict(chat_id, symbol)
        elif text_lower.startswith('/portfolio') or self._match_hindi(text_lower, 'portfolio'):
            self._handle_portfolio(chat_id)
        elif text_lower.startswith('/risk') or self._match_hindi(text_lower, 'risk'):
            self._handle_risk(chat_id)
        elif text_lower.startswith('/brain') or self._match_hindi(text_lower, 'brain'):
            self._handle_brain(chat_id)
        elif text_lower.startswith('/explain'):
            self._handle_explain(chat_id)
        elif text_lower.startswith('/help') or self._match_hindi(text_lower, 'help'):
            self._handle_help(chat_id)
        else:
            # Try to extract stock name from natural language
            for word in text.split():
                if word.upper() in ['NIFTY', 'BANKNIFTY', 'RELIANCE', 'TCS', 'INFY',
                                    'HDFCBANK', 'ICICIBANK', 'SBIN', 'TATAMOTORS']:
                    self._handle_predict(chat_id, word.upper())
                    return
            self._handle_help(chat_id)
    
    def _match_hindi(self, text, command):
        """Check if text matches Hindi keywords for a command."""
        keywords = self.hindi_commands.get(command, [])
        return any(kw in text for kw in keywords)
    
    def update_predictions(self, symbol, score, signal):
        """Called from main.py to push live predictions."""
        self.last_predictions[symbol] = {
            'score': round(score, 4),
            'signal': signal,
            'time': datetime.now().strftime('%H:%M:%S')
        }
    
    def update_brain_state(self, state_dict):
        """Called from main.py to push brain state."""
        self.brain_state.update(state_dict)
    
    def set_trade_reason(self, reason):
        """Called after a trade decision to store explanation."""
        self.last_trade_reason = reason
