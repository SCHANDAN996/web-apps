"""
⚙️ AI Config Manager — Central Configuration with Hot-Reload

Single source of truth for ALL system parameters:
  - Trading config (capital, SL%, TP%, max positions)
  - Model config (brain version, features, thresholds)
  - API credentials (encrypted reference)
  - Module toggles (enable/disable any module)
  - Environment management (PAPER / LIVE)

Features:
  - Hot-reload without restart
  - Config validation
  - Config diff (what changed?)
  - Environment-specific overrides
"""

import os
import json
from datetime import datetime
from collections import ChainMap


class AIConfigManager:
    """
    Central configuration manager for the entire AI system.
    
    Usage:
        config = AIConfigManager()
        config.load()
        
        capital = config.get('trading.capital')
        sl = config.get('trading.stop_loss_pct')
        
        config.set('trading.capital', 600000)
        config.hot_reload()
    """
    
    CONFIG_FILE = 'config/ai_config.json'
    
    DEFAULT_CONFIG = {
        'system': {
            'version': '2.0.0',
            'mode': 'PAPER',        # PAPER or LIVE
            'log_level': 'INFO',
            'auto_start_scrapers': True,
        },
        'trading': {
            'capital': 500000,
            'max_positions': 5,
            'max_position_pct': 20,     # Max % per position
            'stop_loss_pct': 1.5,
            'take_profit_pct': 2.0,
            'confidence_threshold': 0.60,
            'trade_start_time': '09:20',
            'trade_end_time': '15:10',
            'avoid_expiry_day': True,
            'enable_options': False,
        },
        'model': {
            'brain_version': 'v2',
            'model_path': 'models/tradenet_actor.pth',
            'scaler_path': 'models/scaler_v2.pkl',
            'sequence_length': 60,
            'features': 'auto',          # auto-detect or list
            'ensemble_enabled': False,
            'multi_tf_enabled': False,
        },
        'risk': {
            'max_daily_loss_pct': 3.0,
            'max_drawdown_pct': 10.0,
            'var_confidence': 0.95,
            'auto_pause_on_loss_streak': 5,
            'position_scaling': True,
        },
        'modules': {
            'telegram_bot': False,
            'news_scraper': True,
            'social_scraper': False,
            'brain_dashboard': True,
            'trade_journal': True,
            'alert_engine': True,
            'anomaly_detector': True,
            'candle_patterns': True,
            'fibonacci': True,
            'order_flow': True,
            'pair_trading': False,
            'gamma_scalper': False,
        },
        'telegram': {
            'enabled': False,
            'token': '',
            'chat_id': '',
        },
        'alerts': {
            'console': True,
            'file': True,
            'webhook_url': '',
            'file_path': 'data/alerts.log',
        }
    }
    
    def __init__(self, config_file=None):
        self.config_file = config_file or self.CONFIG_FILE
        self.config = {}
        self.load_time = None
        self.change_log = []
    
    def load(self):
        """Load config from file, merge with defaults."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    file_config = json.load(f)
                self.config = self._deep_merge(self.DEFAULT_CONFIG, file_config)
            except Exception as e:
                print(f"⚠️ Config load failed: {e}, using defaults")
                self.config = self.DEFAULT_CONFIG.copy()
        else:
            self.config = self.DEFAULT_CONFIG.copy()
            self.save()  # Create default file
        
        self.load_time = datetime.now()
        return self.config
    
    def get(self, key_path, default=None):
        """
        Get config value using dot notation.
        Example: config.get('trading.capital') → 500000
        """
        keys = key_path.split('.')
        val = self.config
        for k in keys:
            if isinstance(val, dict) and k in val:
                val = val[k]
            else:
                return default
        return val
    
    def set(self, key_path, value):
        """Set config value using dot notation."""
        keys = key_path.split('.')
        obj = self.config
        for k in keys[:-1]:
            if k not in obj:
                obj[k] = {}
            obj = obj[k]
        
        old_value = obj.get(keys[-1])
        obj[keys[-1]] = value
        
        self.change_log.append({
            'key': key_path, 'old': old_value, 'new': value,
            'time': datetime.now().isoformat()
        })
        
        self.save()
    
    def hot_reload(self):
        """Reload config without restart."""
        old_config = json.dumps(self.config, sort_keys=True)
        self.load()
        new_config = json.dumps(self.config, sort_keys=True)
        
        changed = old_config != new_config
        if changed:
            print("🔄 Config hot-reloaded — changes detected")
        return changed
    
    def save(self):
        """Save current config to file."""
        os.makedirs(os.path.dirname(self.config_file) or 'config', exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2, default=str)
    
    def validate(self):
        """Validate config values."""
        errors = []
        
        cap = self.get('trading.capital', 0)
        if cap <= 0:
            errors.append('trading.capital must be > 0')
        
        sl = self.get('trading.stop_loss_pct', 0)
        if sl <= 0 or sl > 10:
            errors.append('trading.stop_loss_pct should be 0-10%')
        
        mode = self.get('system.mode', '')
        if mode not in ['PAPER', 'LIVE']:
            errors.append('system.mode must be PAPER or LIVE')
        
        conf = self.get('trading.confidence_threshold', 0)
        if conf < 0.5 or conf > 0.95:
            errors.append('confidence_threshold should be 0.5-0.95')
        
        return {'valid': len(errors) == 0, 'errors': errors}
    
    def get_enabled_modules(self):
        """Get list of enabled modules."""
        modules = self.get('modules', {})
        return [name for name, enabled in modules.items() if enabled]
    
    def get_diff(self):
        """Get recent config changes."""
        return self.change_log[-20:]
    
    def _deep_merge(self, base, override):
        """Deep merge override into base."""
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result
