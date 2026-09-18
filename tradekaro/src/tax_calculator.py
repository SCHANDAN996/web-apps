"""
💰 Tax Calculator — Indian Trading Tax Computation

Calculates:
  STT (Securities Transaction Tax)
  Capital Gains (STCG 15%, LTCG 10%)
  GST on brokerage
  Stamp duty, SEBI fees, Exchange fees
  Net P&L after all taxes
"""


class TaxCalculator:
    
    STT_DELIVERY = 0.1      # 0.1% both sides
    STT_INTRADAY = 0.025    # 0.025% sell side
    STT_FNO = 0.0125        # 0.0125% sell side
    GST = 18                # 18% on brokerage
    STAMP_BUY = 0.015       # 0.015% buy side
    SEBI = 0.0001           # per crore
    EXCHANGE = 0.00345      # NSE
    STCG_RATE = 15          # Short term capital gains
    LTCG_RATE = 10          # Long term (>1yr)
    LTCG_EXEMPT = 100000    # ₹1L exemption
    
    def calculate_charges(self, turnover, trade_type='INTRADAY', brokerage_pct=0.03):
        brokerage = turnover * brokerage_pct / 100
        
        if trade_type == 'DELIVERY':
            stt = turnover * self.STT_DELIVERY / 100
        elif trade_type == 'FNO':
            stt = turnover / 2 * self.STT_FNO / 100
        else:
            stt = turnover / 2 * self.STT_INTRADAY / 100
        
        gst = brokerage * self.GST / 100
        stamp = turnover / 2 * self.STAMP_BUY / 100
        sebi = turnover * self.SEBI / 100
        exchange = turnover * self.EXCHANGE / 100
        total = brokerage + stt + gst + stamp + sebi + exchange
        
        return {k: round(v, 2) for k, v in {
            'brokerage': brokerage, 'stt': stt, 'gst': gst,
            'stamp': stamp, 'sebi': sebi, 'exchange': exchange, 'total': total
        }.items()}
    
    def capital_gains_tax(self, profit, holding_period_days):
        if profit <= 0:
            return {'tax': 0, 'type': 'NO_TAX', 'net_profit': profit}
        if holding_period_days > 365:
            taxable = max(0, profit - self.LTCG_EXEMPT)
            tax = taxable * self.LTCG_RATE / 100
            return {'tax': round(tax, 0), 'type': 'LTCG', 'exemption_used': min(profit, self.LTCG_EXEMPT),
                    'net_profit': round(profit - tax, 0)}
        else:
            tax = profit * self.STCG_RATE / 100
            return {'tax': round(tax, 0), 'type': 'STCG', 'net_profit': round(profit - tax, 0)}
    
    def annual_summary(self, trades):
        total_turnover = sum(abs(t.get('turnover', 0)) for t in trades)
        total_profit = sum(t.get('pnl', 0) for t in trades)
        total_charges = self.calculate_charges(total_turnover, 'INTRADAY')
        cg = self.capital_gains_tax(max(0, total_profit), 30)
        net = total_profit - total_charges['total'] - cg['tax']
        return {'turnover': round(total_turnover, 0), 'gross_profit': round(total_profit, 0),
                'charges': total_charges, 'tax': cg, 'net_after_tax': round(net, 0)}
