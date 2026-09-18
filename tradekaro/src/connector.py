import os
import time
import threading
import pyotp
import logging
from NorenRestApiPy.NorenApi import NorenApi
from dotenv import load_dotenv

# Load Configuration
load_dotenv('config/credentials.env')

# Logging Setup
# basicConfig configures the *root* logger, so DEBUG here meant every library
# (yfinance, peewee, urllib3) dumped its internals into trading.log and buried
# the actual trading messages. Root stays at INFO; set LOG_LEVEL=DEBUG in the
# environment when you genuinely need the firehose back.
logging.basicConfig(level=os.getenv('LOG_LEVEL', 'INFO').upper(),
                    filename='logs/trading.log',
                    format='%(asctime)s - %(levelname)s - %(message)s')

# These stay quiet even at LOG_LEVEL=DEBUG — their DEBUG output is what made
# the log unreadable in the first place.
for _noisy in ('yfinance', 'peewee', 'urllib3', 'requests', 'websocket'):
    logging.getLogger(_noisy).setLevel(logging.WARNING)

class ShoonyaConnector(NorenApi):
    def __init__(self):
        # Shoonya API URLs
        super(ShoonyaConnector, self).__init__(host='https://api.shoonya.com/NorenWClientTP/', 
                                               websocket='wss://api.shoonya.com/NorenWSTP/')
        self._session_valid = False
        self._login_lock = threading.Lock()
        self._renew_thread = None
        
    def login(self):
        """Login to Shoonya API and generate session"""
        with self._login_lock:
            try:
                user_id    = os.getenv('USER_ID')
                password   = os.getenv('PASSWORD')
                app_key    = os.getenv('API_KEY')
                imei       = os.getenv('IMEI')
                totp_secret = os.getenv('TOTP_SECRET')
                vc         = os.getenv('VC') or user_id 
                
                # Fail loudly on missing credentials instead of dying later with
                # an unrelated-looking error. A missing TOTP_SECRET used to hit
                # `'REPLACE_WITH' in None` and raise a TypeError that read like
                # a bug in the login logic rather than a missing config value.
                missing = [name for name, value in (
                    ('USER_ID', user_id), ('PASSWORD', password),
                    ('API_KEY', app_key), ('TOTP_SECRET', totp_secret),
                ) if not value]
                if missing:
                    logging.error(f"[ERROR] Missing credentials: {', '.join(missing)}")
                    print(f"[ERROR] ❌ config/credentials.env is missing: {', '.join(missing)}")
                    self._session_valid = False
                    return False

                # Generate TOTP
                if 'REPLACE_WITH' in totp_secret:
                    logging.warning("[WARN] Placeholder TOTP Secret found.")
                    print("[WARN] Placeholder TOTP. Mocking login for Paper Trading.")
                    self._session_valid = True
                    return True

                otp = pyotp.TOTP(totp_secret).now()

                logging.info(f"Starting login for User {user_id}...")
                response = super().login(userid=user_id, password=password, twoFA=otp, 
                                         vendor_code=vc, api_secret=app_key, imei=imei)
                
                if response and response.get('stat') == 'Ok':
                    logging.info(f"[INFO] Login Successful. Token: {response.get('susertoken')}")
                    print(f"[INFO] ✅ Connected: {response.get('uname', user_id)}")
                    self._session_valid = True
                    self._start_session_guard()
                    return True
                else:
                    error_msg = response.get('emsg', 'No Response') if response else "No Response"
                    logging.error(f"[ERROR] Login Failed: {error_msg}")
                    print(f"[ERROR] ❌ Login Error: {error_msg}")
                    self._session_valid = False
                    return False
                    
            except ValueError as e:
                # The Noren SDK does json.loads() on the raw response body, so a
                # blank or HTML reply from the broker surfaces here as the bare
                # "Expecting value: line 1 column 1" that told us nothing about
                # its own cause. Usually: broker down, IP not whitelisted, or a
                # maintenance/error page returned instead of JSON.
                logging.error(f"[ERROR] Broker sent a non-JSON reply to login: {e}")
                print("[ERROR] ❌ Broker returned a non-JSON reply to login "
                      f"(broker down, IP not whitelisted, or wrong endpoint): {e}")
                self._session_valid = False
                return False

            except Exception as e:
                logging.error(f"[ERROR] Critical Login Error: {type(e).__name__}: {e}",
                              exc_info=True)
                print(f"[ERROR] Login Exception: {type(e).__name__}: {e}")
                self._session_valid = False
                return False

    def check_and_renew(self):
        """
        🔄 Auto-Session Renewal
        Checks if current session is alive. If expired, auto re-logins.
        Returns True if session is valid (or was renewed successfully).
        """
        try:
            # Quick health check via get_limits
            result = self.get_limits()
            if result and result.get('stat') == 'Ok':
                return True
            
            # Session expired — auto-renew
            print("[SESSION] ⚠️ Session expired. Auto-renewing...")
            logging.warning("[SESSION] Auto-renewing expired session.")
            
            if self.login():
                print("[SESSION] ✅ Session renewed successfully!")
                return True
            else:
                print("[SESSION] ❌ Session renewal FAILED.")
                return False
                
        except Exception as e:
            logging.error(f"[SESSION] Health check error: {e}")
            # Try to re-login anyway
            try:
                return self.login()
            except Exception:
                return False

    def _start_session_guard(self):
        """Start background thread to check session every 30 minutes."""
        if self._renew_thread and self._renew_thread.is_alive():
            return  # Already running
        
        def _guard_loop():
            while True:
                time.sleep(1800)  # Check every 30 minutes
                try:
                    self.check_and_renew()
                except Exception as e:
                    logging.error(f"[SESSION-GUARD] Error: {e}")
                    time.sleep(60)
        
        self._renew_thread = threading.Thread(target=_guard_loop, daemon=True)
        self._renew_thread.start()
        print("[SESSION] 🛡️ Auto-renewal guard started (every 30 min).")

    def get_live_price(self, exchange, token):
        """Get Live Price (LTP)"""
        res = self.get_quotes(exchange=exchange, token=token)
        if res and res.get('stat') == 'Ok':
            return float(res['lp'])
        return None

# For Testing
if __name__ == "__main__":
    bot = ShoonyaConnector()
    if bot.login():
        nifty_price = bot.get_live_price('NSE', '26000')
        print(f"NIFTY 50 Live Price: {nifty_price}")
