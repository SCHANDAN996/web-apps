"""
📅 Expiry Day Strategy — Theta Decay Tactics for Weekly/Monthly Expiry

Expiry day = rapid theta decay → options sellers' paradise:
  Sell OTM options in morning, buy back cheaper by afternoon
  Avoid deep ITM, manage gamma risk
"""

from datetime import datetime, time as dt_time


class ExpiryStrategy:
    
    WEEKLY_EXPIRY = 'THU'  # NIFTY/BANKNIFTY weekly on Thursday
    
    def is_expiry_day(self, date=None):
        d = date or datetime.now()
        return d.strftime('%a').upper()[:3] == self.WEEKLY_EXPIRY
    
    def get_strategy(self, spot_price, iv, time_to_expiry_hours, pcr=1.0):
        if time_to_expiry_hours > 24:
            return {'strategy': 'NOT_EXPIRY_DAY', 'action': 'Use normal strategy'}
        
        now = datetime.now().time()
        
        if now < dt_time(9, 30):
            phase = 'PRE_MARKET'
            strategy = 'WAIT — Let opening volatility settle'
        elif now < dt_time(11, 0):
            phase = 'MORNING_SELL'
            otm_distance = max(100, int(spot_price * 0.005))
            strategy = f'SELL OTM options ±{otm_distance} pts from spot'
        elif now < dt_time(14, 0):
            phase = 'HOLD_AND_MONITOR'
            strategy = 'Hold shorts, trail SL to cost'
        elif now < dt_time(15, 0):
            phase = 'THETA_CRUSH'
            strategy = 'Theta accelerating — hold winning shorts'
        else:
            phase = 'EXIT_ALL'
            strategy = 'Close all positions before 3:25 PM'
        
        risk_level = 'HIGH' if iv > 20 else 'MEDIUM' if iv > 12 else 'LOW'
        
        return {
            'is_expiry': True, 'phase': phase, 'strategy': strategy,
            'risk_level': risk_level, 'iv': iv,
            'hours_to_expiry': round(time_to_expiry_hours, 1),
            'sell_ce_strike': int(spot_price + spot_price * 0.005),
            'sell_pe_strike': int(spot_price - spot_price * 0.005),
            'max_position_size': '2 lots max on expiry'
        }
