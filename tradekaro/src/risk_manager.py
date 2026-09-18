# src/risk_manager.py
import logging
import os
import json
from dotenv import load_dotenv
from src.config_manager import AIConfigManager

# Load credentials env if needed
load_dotenv('config/credentials.env')

class RiskManager:
    def __init__(self, api_client, config=None):
        """
        RiskManager initialized with AIConfigManager dependency injection and fallback security.
        Args:
            api_client: Shoonya API instance
            config: AIConfigManager instance (instantiates default if None)
        """
        self.api = api_client
        self.config = config if config is not None else AIConfigManager()
        self.config.load()
        
        # Load parameters directly from AIConfigManager with fallback protection
        self.total_capital = self.config.get('trading.capital', 500000)
        # ai_config.json spells this "risk_per_trade_pct". Looking it up only under
        # the older "..._percent" name meant edits to the config were silently
        # ignored, so try the real key first and keep the old one as a fallback.
        self.risk_per_trade_pct = self.config.get(
            'trading.risk_per_trade_pct',
            self.config.get('trading.risk_per_trade_percent', 2.0))
        self.max_trades = self.config.get('trading.max_trades_per_day', 3)
        self.risk_reward_ratio = self.config.get('trading.risk_reward_ratio', 1.5)
        self.stop_loss_pct = self.config.get('trading.stop_loss_pct', 1.5)
        self.max_daily_loss = self.total_capital * (self.config.get('risk.max_daily_loss_pct', 3.0) / 100)
        
        # Live risk overrides (from UI dashboard).
        # -1 is a sentinel meaning "never checked"; None means "file absent".
        self._live_risk_stamp = -1
        self.load_live_settings()
        
        # Daily trade tracking state
        import datetime
        self.current_date = datetime.date.today()
        self.trade_count = 0
        self.stop_trading = False

    def load_live_settings(self):
        """Load fresh risk overrides from config/live_risk.json.

        The trading loop calls this on every iteration, so re-read and re-log
        only when the file has actually changed since the last check.
        """
        risk_file = 'config/live_risk.json'
        try:
            stamp = os.path.getmtime(risk_file) if os.path.exists(risk_file) else None
            if stamp == self._live_risk_stamp:
                return
            self._live_risk_stamp = stamp

            if stamp is None:
                logging.info("[RiskManager] No live_risk.json found. Using default config values.")
                return

            with open(risk_file, 'r') as f:
                live_config = json.load(f)
                self.max_daily_loss = float(live_config.get('max_loss', self.max_daily_loss))
                self.stop_loss_pct = float(live_config.get('sl_pct', self.stop_loss_pct))
                logging.info(f"[RiskManager] Live settings loaded: Max Loss={self.max_daily_loss}, SL={self.stop_loss_pct}%")

        except Exception as e:
            logging.error(f"Error loading live risk settings: {e}")

    def check_new_day(self):
        """Reset trade counters and stop flags on new date"""
        import datetime
        today = datetime.date.today()
        if today != self.current_date:
            logging.info(f"New day detected ({today}). Resetting trade count and stop flag.")
            self.trade_count = 0
            self.stop_trading = False
            self.current_date = today
            self.load_live_settings()

    def can_place_trade(self):
        """Verify if a new trade order can be placed"""
        self.check_new_day()
        
        # 1. 3:15 PM IST Cut-off
        import datetime
        ist_now = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=5, minutes=30)
        if ist_now.time() >= datetime.time(15, 15):
            logging.warning("Trading blocked: past 3:15 PM IST.")
            return False
            
        # 2. Emergency Kill-Switch
        if self.stop_trading:
            return False
            
        # 3. Max Daily Trade Limit
        if self.trade_count >= self.max_trades:
            logging.warning(f"Max daily trades ({self.max_trades}) reached. Stopping for the day.")
            return False
            
        return True

    def increment_trade_count(self):
        """Increment trade counter on successful order"""
        self.trade_count += 1
        
    def calculate_stop_loss(self, entry_price, side):
        """Calculate SL and TP prices based on entry_price and side"""
        sl_amount = entry_price * (self.stop_loss_pct / 100)
        
        if side == 'B':  # Buy
            sl = entry_price - sl_amount
            tp = entry_price + (sl_amount * self.risk_reward_ratio)
        else:  # Sell
            sl = entry_price + sl_amount
            tp = entry_price - (sl_amount * self.risk_reward_ratio)
            
        return round(sl, 2), round(tp, 2)

    def check_emergency_exit(self, current_pnl):
        """Halt trading if total daily loss exceeds max_daily_loss"""
        self.check_new_day()
        if current_pnl <= -self.max_daily_loss:
            self.stop_trading = True
            logging.critical(f"Daily loss limit hit: {current_pnl}. Halting trading!")
            return True
        return False

    def calculate_position_size(self, symbol, current_price, confidence, atr_value=0):
        """
        💰 Dynamic Position Sizing (Volatility & Risk-Adjusted)
        Calculates position Qty based on:
        1. Config Capital
        2. Config Risk Per Trade Percent
        3. Confidence Threshold (>= 0.60)
        4. Volatility (ATR)
        """
        try:
            total_capital = self.config.get('trading.capital', 500000)
            risk_per_trade_pct = self.risk_per_trade_pct
            
            risk_amount = total_capital * (risk_per_trade_pct / 100)
            
            # Reject trade if confidence < 0.60 threshold
            if confidence < 0.60:
                print(f"[RiskManager] Trade rejected: Confidence ({confidence:.2f}) < 0.60 threshold.")
                return 0
            
            # Calculate SL Distance (ATR vs Fixed Percentage)
            if atr_value and atr_value > 0:
                sl_distance = 2 * atr_value
            else:
                sl_distance = current_price * (self.stop_loss_pct / 100)
            
            if sl_distance == 0: 
                return 0

            # Calculate Quantity
            raw_qty = risk_amount / sl_distance
            
            # Capital Constraint Check
            max_qty_capital = total_capital / current_price
            final_qty = int(min(raw_qty, max_qty_capital))
            
            # Index / Derivative Lot Size Adjustments
            if symbol == "NIFTY":
                lot_size = 25 
                lots = max(1, final_qty // lot_size)
                final_qty = lots * lot_size
            elif symbol == "BANKNIFTY":
                lot_size = 15 
                lots = max(1, final_qty // lot_size)
                final_qty = lots * lot_size
            elif symbol == "FINNIFTY":
                lot_size = 25
                lots = max(1, final_qty // lot_size)
                final_qty = lots * lot_size
            elif symbol in self.config.get('trading.derivative_symbols', []):
                lot_size = 25
                lots = max(1, final_qty // lot_size)
                final_qty = lots * lot_size
            
            return max(0, final_qty)

        except Exception as e:
            print(f"[RiskManager] Sizing Error: {e}")
            return 0