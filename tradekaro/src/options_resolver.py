"""
Options Resolver — Resolves NIFTY/BANKNIFTY signals to option symbols.
Handles ATM strike selection, CE/PE logic, expiry detection, and lot sizing.
"""
import datetime
import pytz


class OptionsResolver:
    """Resolve underlying signal to the correct options contract."""

    # Lot sizes (as of 2024-25, check for updates)
    LOT_SIZES = {
        'NIFTY': 25,
        'BANKNIFTY': 15,
        'FINNIFTY': 25,
    }

    # Strike intervals
    STRIKE_INTERVALS = {
        'NIFTY': 50,
        'BANKNIFTY': 100,
        'FINNIFTY': 50,
    }

    # Exchange for options
    EXCHANGE = 'NFO'

    def __init__(self, db=None):
        self.db = db
        self.ist = pytz.timezone('Asia/Kolkata')

    def get_atm_strike(self, underlying_price, symbol='NIFTY'):
        """Round to nearest strike interval to get ATM strike."""
        interval = self.STRIKE_INTERVALS.get(symbol, 50)
        return round(underlying_price / interval) * interval

    def get_option_type(self, signal):
        """
        BUY signal → Call (CE) — bullish
        SELL signal → Put (PE) — bearish
        """
        if signal in ('BUY', 'B', 'BULLISH'):
            return 'CE'
        elif signal in ('SELL', 'S', 'BEARISH'):
            return 'PE'
        return 'CE'  # Default

    def get_nearest_expiry(self, symbol='NIFTY'):
        """
        Get the nearest valid expiry based on real SEBI/NSE rules:
        - NIFTY has Weekly Expiry (Thursday)
        - BANKNIFTY has ONLY Monthly Expiry (Last Thursday of the month)
        - FINNIFTY has ONLY Monthly Expiry (Last Tuesday of the month)
        """
        now = datetime.datetime.now(self.ist)
        today = now.date()
        
        if symbol == 'NIFTY':
            # Weekly expiry (Thursday = weekday 3)
            days_until_expiry = (3 - today.weekday()) % 7
            if days_until_expiry == 0:
                if now.hour < 15 or (now.hour == 15 and now.minute < 30):
                    return today
                else:
                    return today + datetime.timedelta(days=7)
            return today + datetime.timedelta(days=days_until_expiry)
            
        elif symbol in ('BANKNIFTY', 'FINNIFTY'):
            # Monthly expiry
            # BANKNIFTY: Last Thursday of the month (weekday 3)
            # FINNIFTY: Last Tuesday of the month (weekday 1)
            target_weekday = 3 if symbol == 'BANKNIFTY' else 1
            
            import calendar
            def get_last_weekday_of_month(year, month, weekday):
                last_day = calendar.monthrange(year, month)[1]
                last_date = datetime.date(year, month, last_day)
                offset = (last_date.weekday() - weekday) % 7
                return last_date - datetime.timedelta(days=offset)
                
            curr_expiry = get_last_weekday_of_month(today.year, today.month, target_weekday)
            
            # If current month's expiry has passed (after 15:30 on expiry day)
            if today > curr_expiry or (today == curr_expiry and now.hour >= 15 and now.minute >= 30):
                if today.month == 12:
                    next_expiry = get_last_weekday_of_month(today.year + 1, 1, target_weekday)
                else:
                    next_expiry = get_last_weekday_of_month(today.year, today.month + 1, target_weekday)
                return next_expiry
            return curr_expiry
            
        else:
            # Fallback to weekly Thursday
            days_until_expiry = (3 - today.weekday()) % 7
            return today + datetime.timedelta(days=days_until_expiry)


    def format_expiry_shoonya(self, expiry_date, symbol='NIFTY'):
        """
        Format expiry for Shoonya API.
        Format: NIFTY27MAR25C22500 (symbol + DD + MMM + YY + CE/PE + strike)
        """
        month_map = {
            1: 'JAN', 2: 'FEB', 3: 'MAR', 4: 'APR', 5: 'MAY', 6: 'JUN',
            7: 'JUL', 8: 'AUG', 9: 'SEP', 10: 'OCT', 11: 'NOV', 12: 'DEC'
        }
        dd = expiry_date.strftime('%d')
        mmm = month_map[expiry_date.month]
        yy = expiry_date.strftime('%y')
        return f"{dd}{mmm}{yy}"

    def resolve_option_symbol(self, underlying_symbol, underlying_price, signal):
        """
        Main method: Convert an underlying signal to a full options symbol.
        
        Args:
            underlying_symbol: 'NIFTY' or 'BANKNIFTY'
            underlying_price: Current price of the underlying (e.g., 22500)
            signal: 'BUY' or 'SELL'
        
        Returns:
            dict with: symbol, option_type, strike, expiry, lot_size, exchange
        """
        atm_strike = self.get_atm_strike(underlying_price, underlying_symbol)
        option_type = self.get_option_type(signal)
        expiry = self.get_nearest_expiry(underlying_symbol)
        lot_size = self.LOT_SIZES.get(underlying_symbol, 25)
        
        # Shoonya format: NIFTY27MAR25C22500
        expiry_str = self.format_expiry_shoonya(expiry, underlying_symbol)
        opt_char = 'C' if option_type == 'CE' else 'P'
        trading_symbol = f"{underlying_symbol}{expiry_str}{opt_char}{int(atm_strike)}"
        
        result = {
            'trading_symbol': trading_symbol,
            'underlying': underlying_symbol,
            'strike': atm_strike,
            'option_type': option_type,
            'expiry': expiry.strftime('%Y-%m-%d'),
            'lot_size': lot_size,
            'exchange': self.EXCHANGE,
            'instrument': option_type,  # CE or PE
        }
        
        print(f"🎯 Options Resolved: {underlying_symbol} {signal} → {trading_symbol} (Strike: {atm_strike})")
        return result

    def calculate_option_sl_tp(self, option_premium, signal, sl_percent=30, rr_ratio=2.0):
        """
        Calculate SL and TP based on option premium.
        
        For options, SL is typically % of premium (e.g., 30% loss on premium).
        TP = SL * R:R ratio.
        
        Args:
            option_premium: Current option price (e.g., ₹250)
            signal: 'BUY' (we always buy options, direction via CE/PE)
            sl_percent: Max loss as % of premium
            rr_ratio: Target Reward:Risk
        """
        sl_amount = option_premium * (sl_percent / 100)
        tp_amount = sl_amount * rr_ratio
        
        # For option buying: SL = premium - sl_amount, TP = premium + tp_amount
        sl_price = round(option_premium - sl_amount, 2)
        tp_price = round(option_premium + tp_amount, 2)
        
        # SL can't go below 0
        sl_price = max(sl_price, 0.05)
        
        return {
            'sl_price': sl_price,
            'tp_price': tp_price,
            'risk_amount': round(sl_amount, 2),
            'reward_amount': round(tp_amount, 2),
            'rr_ratio': rr_ratio
        }
