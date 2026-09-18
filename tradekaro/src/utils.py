import datetime
import pytz

def get_ist_time():
    """Returns current time in Indian Standard Time (IST)."""
    return datetime.datetime.now(pytz.timezone('Asia/Kolkata'))

def is_market_open():
    """
    Checks if NSE Market is Open.
    Market Hours: Mon-Fri, 09:15 AM - 03:30 PM IST.
    Returns: bool
    """
    now = get_ist_time()
    
    # 1. Weekend Check (Saturday=5, Sunday=6)
    if now.weekday() >= 5:
        return False
        
    # 2. Time Check
    current_time = now.time()
    market_start = datetime.time(9, 15)
    market_end = datetime.time(15, 30)
    
    return market_start <= current_time <= market_end

def is_market_holiday(date_str=None):
    """
    Checks if today is a trading holiday.
    (Placeholder: Ideally fetch from a config file or API)
    """
    # TODO: Implement holiday list check
    return False
