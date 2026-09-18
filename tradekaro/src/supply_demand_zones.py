"""
🏦 Supply/Demand Zone Mapper — Institutional Order Block Detection

Supply Zone: Where institutions SOLD heavily (price drops away fast)
Demand Zone: Where institutions BOUGHT heavily (price rockets up)

Price tends to RETURN to these zones and bounce again.
"""

import numpy as np


class SupplyDemandMapper:
    
    def detect_zones(self, df, lookback=100, min_move_pct=1.0):
        if df is None or len(df) < lookback:
            return {'demand': [], 'supply': []}
        
        recent = df.tail(lookback)
        demand_zones = []
        supply_zones = []
        
        o = recent['open'].values
        h = recent['high'].values
        l = recent['low'].values
        c = recent['close'].values
        v = recent['volume'].values
        avg_vol = np.mean(v)
        
        for i in range(2, len(c) - 3):
            future_move = (c[i+3] - c[i]) / c[i] * 100 if i + 3 < len(c) else 0
            vol_ratio = v[i] / max(avg_vol, 1)
            
            # Demand zone: consolidation then strong UP move
            if future_move > min_move_pct and vol_ratio > 1.2:
                demand_zones.append({
                    'zone_high': round(float(max(o[i], c[i])), 2),
                    'zone_low': round(float(min(o[i], c[i])), 2),
                    'strength': round(abs(future_move) * vol_ratio, 1),
                    'volume_ratio': round(vol_ratio, 2),
                    'move_after': round(future_move, 2)
                })
            
            # Supply zone: consolidation then strong DOWN move
            elif future_move < -min_move_pct and vol_ratio > 1.2:
                supply_zones.append({
                    'zone_high': round(float(max(o[i], c[i])), 2),
                    'zone_low': round(float(min(o[i], c[i])), 2),
                    'strength': round(abs(future_move) * vol_ratio, 1),
                    'volume_ratio': round(vol_ratio, 2),
                    'move_after': round(future_move, 2)
                })
        
        # Sort by strength, keep top 5
        demand_zones.sort(key=lambda x: x['strength'], reverse=True)
        supply_zones.sort(key=lambda x: x['strength'], reverse=True)
        
        current = float(c[-1])
        
        return {
            'demand': demand_zones[:5],
            'supply': supply_zones[:5],
            'nearest_demand': self._nearest_below(demand_zones, current),
            'nearest_supply': self._nearest_above(supply_zones, current),
            'current_price': round(current, 2)
        }
    
    def is_at_zone(self, df):
        zones = self.detect_zones(df)
        current = zones['current_price']
        
        for d in zones['demand']:
            if d['zone_low'] <= current <= d['zone_high'] * 1.005:
                return {'at_zone': True, 'type': 'DEMAND', 'action': 'BUY', 'zone': d}
        
        for s in zones['supply']:
            if s['zone_low'] * 0.995 <= current <= s['zone_high']:
                return {'at_zone': True, 'type': 'SUPPLY', 'action': 'SELL', 'zone': s}
        
        return {'at_zone': False}
    
    def _nearest_below(self, zones, price):
        below = [z for z in zones if z['zone_high'] < price]
        return max(below, key=lambda x: x['zone_high']) if below else None
    
    def _nearest_above(self, zones, price):
        above = [z for z in zones if z['zone_low'] > price]
        return min(above, key=lambda x: x['zone_low']) if above else None
