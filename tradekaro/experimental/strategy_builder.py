"""
🔧 Strategy Builder — User-Defined Custom Strategy DSL

Define strategies without coding:
  rules = [
    {'indicator': 'RSI_14', 'condition': '<', 'value': 30, 'action': 'BUY'},
    {'indicator': 'RSI_14', 'condition': '>', 'value': 70, 'action': 'SELL'},
  ]
"""

import json, os


class StrategyBuilder:
    
    FILE = 'config/custom_strategies.json'
    
    def __init__(self):
        self.strategies = self._load()
    
    def create(self, name, rules, description=''):
        self.strategies[name] = {
            'rules': rules, 'description': description,
            'active': True, 'trades': 0, 'wins': 0
        }
        self._save()
    
    def evaluate(self, strategy_name, market_data):
        if strategy_name not in self.strategies:
            return {'signal': 'NONE', 'error': 'Unknown strategy'}
        
        rules = self.strategies[strategy_name]['rules']
        triggered = []
        
        for rule in rules:
            indicator = rule.get('indicator', '')
            condition = rule.get('condition', '>')
            value = rule.get('value', 0)
            action = rule.get('action', 'HOLD')
            
            actual = market_data.get(indicator)
            if actual is None: continue
            
            met = False
            if condition == '>' and actual > value: met = True
            elif condition == '<' and actual < value: met = True
            elif condition == '>=' and actual >= value: met = True
            elif condition == '<=' and actual <= value: met = True
            elif condition == '==' and actual == value: met = True
            elif condition == 'crosses_above' and actual > value: met = True
            elif condition == 'crosses_below' and actual < value: met = True
            
            if met:
                triggered.append({'rule': rule, 'actual_value': actual, 'action': action})
        
        if triggered:
            actions = [t['action'] for t in triggered]
            if 'BUY' in actions and 'SELL' not in actions:
                return {'signal': 'BUY', 'triggered_rules': triggered}
            elif 'SELL' in actions and 'BUY' not in actions:
                return {'signal': 'SELL', 'triggered_rules': triggered}
        
        return {'signal': 'NONE', 'triggered_rules': triggered}
    
    def list_strategies(self):
        return {n: {'description': s['description'], 'rules': len(s['rules']), 'active': s['active']}
                for n, s in self.strategies.items()}
    
    def _load(self):
        if os.path.exists(self.FILE):
            try:
                with open(self.FILE) as f: return json.load(f)
            except: pass
        return {}
    
    def _save(self):
        os.makedirs(os.path.dirname(self.FILE) or 'config', exist_ok=True)
        with open(self.FILE, 'w') as f: json.dump(self.strategies, f, indent=2)
