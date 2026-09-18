"""
📊 Volume Profile — VPOC + Value Area (Where Institutions Trade)

Volume Profile shows WHERE most volume traded at each price level:
  VPOC: Volume Point of Control (price with highest volume)
  VAH: Value Area High (70% volume above)
  VAL: Value Area Low (70% volume below)
  HVN: High Volume Nodes (institutional interest)
  LVN: Low Volume Nodes (price moves fast through these)
"""

import numpy as np
import pandas as pd


class VolumeProfile:
    
    def __init__(self, n_bins=50, value_area_pct=70):
        self.n_bins = n_bins
        self.value_area_pct = value_area_pct
    
    def calculate(self, df, lookback=None):
        if df is None or len(df) < 20:
            return None
        data = df.tail(lookback) if lookback else df
        prices = data['close'].values
        volumes = data['volume'].values
        
        price_min, price_max = prices.min(), prices.max()
        bins = np.linspace(price_min, price_max, self.n_bins + 1)
        bin_centers = (bins[:-1] + bins[1:]) / 2
        vol_at_price = np.zeros(self.n_bins)
        
        for p, v in zip(prices, volumes):
            idx = min(np.searchsorted(bins, p) - 1, self.n_bins - 1)
            idx = max(0, idx)
            vol_at_price[idx] += v
        
        vpoc_idx = np.argmax(vol_at_price)
        vpoc = round(float(bin_centers[vpoc_idx]), 2)
        
        vah, val = self._value_area(bin_centers, vol_at_price, vpoc_idx)
        hvn = self._high_volume_nodes(bin_centers, vol_at_price)
        lvn = self._low_volume_nodes(bin_centers, vol_at_price)
        
        current = float(prices[-1])
        if current > vah:
            position = 'ABOVE_VALUE'
            bias = 'BULLISH'
        elif current < val:
            position = 'BELOW_VALUE'
            bias = 'BEARISH'
        else:
            position = 'IN_VALUE'
            bias = 'NEUTRAL'
        
        return {
            'vpoc': vpoc, 'vah': round(vah, 2), 'val': round(val, 2),
            'current_price': round(current, 2),
            'position': position, 'bias': bias,
            'hvn': hvn[:5], 'lvn': lvn[:3],
            'range': round(float(price_max - price_min), 2)
        }
    
    def _value_area(self, centers, volumes, vpoc_idx):
        total = volumes.sum()
        target = total * self.value_area_pct / 100
        included = np.zeros(len(volumes), dtype=bool)
        included[vpoc_idx] = True
        current_vol = volumes[vpoc_idx]
        
        lo, hi = vpoc_idx, vpoc_idx
        while current_vol < target and (lo > 0 or hi < len(volumes) - 1):
            vol_above = volumes[hi + 1] if hi < len(volumes) - 1 else 0
            vol_below = volumes[lo - 1] if lo > 0 else 0
            if vol_above >= vol_below and hi < len(volumes) - 1:
                hi += 1
                current_vol += volumes[hi]
            elif lo > 0:
                lo -= 1
                current_vol += volumes[lo]
            else:
                break
        
        return float(centers[hi]), float(centers[lo])
    
    def _high_volume_nodes(self, centers, volumes):
        mean_vol = volumes.mean()
        return [{'price': round(float(centers[i]), 2), 'volume': int(volumes[i])}
                for i in range(len(volumes)) if volumes[i] > mean_vol * 1.5]
    
    def _low_volume_nodes(self, centers, volumes):
        mean_vol = volumes.mean()
        return [{'price': round(float(centers[i]), 2)}
                for i in range(len(volumes)) if 0 < volumes[i] < mean_vol * 0.3]
