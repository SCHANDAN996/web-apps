"""
🔔 Alert & Notification Engine — Multi-Channel Trading Alerts

Sends alerts via multiple channels:
  - Console logging
  - File logging
  - Webhook (Discord, Slack, custom)
  - Sound alerts (terminal bell)
  - Telegram (via existing bot)

Alert types: TRADE, RISK, ANOMALY, SYSTEM, INFO
Priority: CRITICAL, HIGH, MEDIUM, LOW
"""

import json
import os
import logging
import threading
from datetime import datetime
from collections import deque

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


class AlertEngine:
    """
    Multi-channel alert and notification system.
    
    Usage:
        alerts = AlertEngine()
        alerts.add_channel('file', path='data/alerts.log')
        alerts.add_channel('webhook', url='https://discord.com/api/webhooks/...')
        
        alerts.send('BUY signal on NIFTY @ 22500', 
                    alert_type='TRADE', priority='HIGH')
    """
    
    PRIORITY_EMOJI = {
        'CRITICAL': '🚨', 'HIGH': '🔴', 'MEDIUM': '🟡', 'LOW': '🟢'
    }
    
    TYPE_EMOJI = {
        'TRADE': '💹', 'RISK': '⚠️', 'ANOMALY': '⚡',
        'SYSTEM': '🔧', 'INFO': 'ℹ️', 'PROFIT': '💰', 'LOSS': '📉'
    }
    
    def __init__(self):
        self.channels = {}
        self.history = deque(maxlen=500)
        self.suppression = {}
        self.alert_count = 0
        
        # Always add console
        self.add_channel('console')
    
    def add_channel(self, channel_type, **config):
        """Register an alert channel."""
        self.channels[channel_type] = config
    
    def send(self, message, alert_type='INFO', priority='MEDIUM',
             symbol=None, suppress_seconds=0):
        """
        Send alert to all registered channels.
        
        Args:
            suppress_seconds: Don't repeat same alert within this window
        """
        # Suppression check
        key = f"{alert_type}_{message[:50]}"
        now = datetime.now()
        if key in self.suppression:
            elapsed = (now - self.suppression[key]).total_seconds()
            if elapsed < suppress_seconds:
                return
        self.suppression[key] = now
        
        p_emoji = self.PRIORITY_EMOJI.get(priority, '')
        t_emoji = self.TYPE_EMOJI.get(alert_type, '')
        
        formatted = f"{p_emoji}{t_emoji} [{priority}] [{alert_type}] {message}"
        if symbol:
            formatted = f"{p_emoji}{t_emoji} [{symbol}] {message}"
        
        alert = {
            'id': self.alert_count,
            'message': message,
            'formatted': formatted,
            'type': alert_type,
            'priority': priority,
            'symbol': symbol,
            'timestamp': now.isoformat()
        }
        
        self.alert_count += 1
        self.history.append(alert)
        
        # Send to all channels
        for ch_type, config in self.channels.items():
            try:
                if ch_type == 'console':
                    self._send_console(formatted, priority)
                elif ch_type == 'file':
                    self._send_file(formatted, config)
                elif ch_type == 'webhook':
                    self._send_webhook(formatted, config)
            except Exception as e:
                logging.debug(f"Alert channel {ch_type} failed: {e}")
    
    def get_recent(self, n=20, priority=None, alert_type=None):
        """Get recent alerts with optional filters."""
        alerts = list(self.history)
        if priority:
            alerts = [a for a in alerts if a['priority'] == priority]
        if alert_type:
            alerts = [a for a in alerts if a['type'] == alert_type]
        return alerts[-n:]
    
    def _send_console(self, msg, priority):
        if priority == 'CRITICAL':
            print(f"\033[91m{msg}\033[0m")  # Red
        elif priority == 'HIGH':
            print(f"\033[93m{msg}\033[0m")  # Yellow
        else:
            print(msg)
    
    def _send_file(self, msg, config):
        path = config.get('path', 'data/alerts.log')
        os.makedirs(os.path.dirname(path) or 'data', exist_ok=True)
        with open(path, 'a') as f:
            f.write(f"[{datetime.now().isoformat()}] {msg}\n")
    
    def _send_webhook(self, msg, config):
        if not HAS_REQUESTS:
            return
        url = config.get('url', '')
        if url:
            threading.Thread(
                target=lambda: requests.post(url, json={'content': msg}, timeout=5),
                daemon=True
            ).start()
