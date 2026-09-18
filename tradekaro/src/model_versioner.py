"""
📦 Model Versioner — Model Registry + A/B Testing

Track model versions, compare performance, auto-promote best:
  v1: Base LSTM, v2: TransformerLSTM, v3: Ensemble
"""

import os, json
from datetime import datetime


class ModelVersioner:
    REGISTRY_FILE = 'models/model_registry.json'
    
    def __init__(self):
        self.registry = self._load()
        self.active_model = self.registry.get('active', 'v2')
    
    def register(self, version, path, accuracy, params, notes=''):
        self.registry['models'][version] = {
            'path': path, 'accuracy': accuracy, 'params': params,
            'notes': notes, 'registered': datetime.now().isoformat()
        }
        self._save()
    
    def promote(self, version):
        if version in self.registry['models']:
            self.registry['active'] = version
            self.active_model = version
            self._save()
            return True
        return False
    
    def compare(self, v1, v2):
        m1 = self.registry['models'].get(v1, {})
        m2 = self.registry['models'].get(v2, {})
        return {
            v1: {'accuracy': m1.get('accuracy', 0), 'params': m1.get('params', 0)},
            v2: {'accuracy': m2.get('accuracy', 0), 'params': m2.get('params', 0)},
            'winner': v1 if m1.get('accuracy', 0) > m2.get('accuracy', 0) else v2
        }
    
    def auto_promote_best(self):
        models = self.registry.get('models', {})
        if not models: return
        best = max(models, key=lambda v: models[v].get('accuracy', 0))
        self.promote(best)
        return best
    
    def list_versions(self):
        return {v: {'accuracy': d.get('accuracy'), 'active': v == self.active_model}
                for v, d in self.registry.get('models', {}).items()}
    
    def _load(self):
        if os.path.exists(self.REGISTRY_FILE):
            try:
                with open(self.REGISTRY_FILE) as f: return json.load(f)
            except: pass
        return {'active': 'v2', 'models': {}}
    
    def _save(self):
        os.makedirs('models', exist_ok=True)
        with open(self.REGISTRY_FILE, 'w') as f: json.dump(self.registry, f, indent=2)
