"""
📊 Margin Calculator — SPAN Margin Estimation for F&O

Estimates margin requirements for futures and options:
  Initial margin, exposure margin, total per lot
"""


class MarginCalculator:
    
    # Approximate margin % for Indian F&O
    MARGIN_RATES = {
        'NIFTY_FUT': 12, 'BANKNIFTY_FUT': 15, 'FINNIFTY_FUT': 14,
        'NIFTY_OPT_SELL': 15, 'BANKNIFTY_OPT_SELL': 18,
        'NIFTY_OPT_BUY': 0, 'BANKNIFTY_OPT_BUY': 0,  # Premium only
    }
    LOT_SIZES = {'NIFTY': 25, 'BANKNIFTY': 15, 'FINNIFTY': 25}
    
    def calculate(self, symbol, price, position_type='FUT', side='BUY', lots=1):
        lot_size = self.LOT_SIZES.get(symbol, 25)
        contract_value = price * lot_size * lots
        
        if position_type == 'OPT' and side == 'BUY':
            return {'initial_margin': 0, 'premium_required': round(contract_value, 0),
                    'total': round(contract_value, 0), 'type': 'PREMIUM_ONLY'}
        
        key = f"{symbol}_{position_type}{'_SELL' if side == 'SELL' and position_type == 'OPT' else ''}"
        rate = self.MARGIN_RATES.get(key, 15)
        initial = contract_value * rate / 100
        exposure = contract_value * 3.5 / 100
        
        return {
            'contract_value': round(contract_value, 0),
            'initial_margin': round(initial, 0),
            'exposure_margin': round(exposure, 0),
            'total_margin': round(initial + exposure, 0),
            'margin_per_lot': round((initial + exposure) / lots, 0),
            'lot_size': lot_size, 'lots': lots
        }
    
    def max_lots(self, symbol, price, available_capital, position_type='FUT'):
        single = self.calculate(symbol, price, position_type, lots=1)
        margin_per = single['total_margin']
        return {'max_lots': int(available_capital / max(margin_per, 1)),
                'margin_per_lot': margin_per, 'available': available_capital}
    
    def portfolio_margin(self, positions):
        total = 0
        details = {}
        for pos in positions:
            m = self.calculate(pos['symbol'], pos['price'], pos.get('type', 'FUT'),
                             pos.get('side', 'BUY'), pos.get('lots', 1))
            total += m['total_margin']
            details[pos['symbol']] = m
        return {'total_margin': round(total, 0), 'positions': details}
