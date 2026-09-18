"""
🗺️ Sector Heatmap — Visual Sector Performance Matrix

Tracks sector-wise performance for rotation strategy
"""

import numpy as np
from collections import defaultdict


class SectorHeatmap:
    
    SECTORS = {
        'IT': ['TCS', 'INFY', 'WIPRO', 'HCLTECH', 'TECHM', 'LTIM'],
        'BANKING': ['HDFCBANK', 'ICICIBANK', 'SBIN', 'KOTAKBANK', 'AXISBANK', 'INDUSINDBK'],
        'AUTO': ['MARUTI', 'TATAMOTORS', 'M&M', 'BAJAJ-AUTO', 'HEROMOTOCO', 'EICHERMOT'],
        'PHARMA': ['SUNPHARMA', 'DRREDDY', 'CIPLA', 'DIVISLAB', 'APOLLOHOSP'],
        'METAL': ['TATASTEEL', 'JSWSTEEL', 'HINDALCO', 'COALINDIA'],
        'ENERGY': ['RELIANCE', 'ONGC', 'NTPC', 'POWERGRID', 'BPCL'],
        'FMCG': ['HINDUNILVR', 'ITC', 'NESTLEIND', 'BRITANNIA', 'TATACONSUM'],
        'INFRA': ['LT', 'ULTRACEMCO', 'GRASIM', 'SHREECEM', 'ADANIENT'],
        'FINANCE': ['BAJFINANCE', 'BAJAJFINSV', 'SBILIFE', 'HDFCLIFE'],
    }
    
    def __init__(self):
        self.sector_returns = defaultdict(list)
    
    def update(self, stock_returns):
        for sector, stocks in self.SECTORS.items():
            sector_rets = [stock_returns.get(s, 0) for s in stocks if s in stock_returns]
            if sector_rets:
                self.sector_returns[sector].append(np.mean(sector_rets))
    
    def get_heatmap(self, stock_returns=None):
        if stock_returns:
            self.update(stock_returns)
        
        heatmap = {}
        for sector, stocks in self.SECTORS.items():
            if stock_returns:
                rets = [stock_returns.get(s, 0) for s in stocks if s in stock_returns]
                avg_ret = np.mean(rets) if rets else 0
            elif self.sector_returns[sector]:
                avg_ret = self.sector_returns[sector][-1]
            else:
                avg_ret = 0
            
            color = 'GREEN' if avg_ret > 0.5 else 'RED' if avg_ret < -0.5 else 'GREY'
            heatmap[sector] = {
                'return_pct': round(avg_ret, 2), 'color': color,
                'stocks': len(self.SECTORS[sector])
            }
        
        ranked = sorted(heatmap.items(), key=lambda x: x[1]['return_pct'], reverse=True)
        return dict(ranked)
    
    def strongest_sector(self):
        hm = self.get_heatmap()
        return list(hm.items())[0] if hm else None
    
    def weakest_sector(self):
        hm = self.get_heatmap()
        return list(hm.items())[-1] if hm else None
