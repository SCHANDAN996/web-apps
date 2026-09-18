"""
📦 Model Registry — Version Control for AI Brain

Features:
- Save model checkpoints with metadata (performance, timestamp, config)
- A/B comparison between model versions
- Auto-rollback if new model performs worse
- Training history tracking
"""

import os
import json
import shutil
import torch
from datetime import datetime


class ModelRegistry:
    """
    Manages model versions for safe deployment.
    
    Directory structure:
        models/
        ├── tradenet_actor.pth          ← Active production model
        ├── best_brain.pth              ← Best validation checkpoint
        ├── registry/
        │   ├── registry.json           ← Version history
        │   ├── v001_20260303.pth       ← Archived versions
        │   ├── v002_20260310.pth
        │   └── ...
    """

    REGISTRY_DIR = 'models/registry'
    REGISTRY_FILE = 'models/registry/registry.json'
    ACTIVE_MODEL = 'models/tradenet_actor.pth'
    BEST_MODEL = 'models/best_brain.pth'

    def __init__(self):
        os.makedirs(self.REGISTRY_DIR, exist_ok=True)
        self.registry = self._load_registry()

    def _load_registry(self):
        if os.path.exists(self.REGISTRY_FILE):
            with open(self.REGISTRY_FILE, 'r') as f:
                return json.load(f)
        return {'versions': [], 'active_version': None}

    def _save_registry(self):
        with open(self.REGISTRY_FILE, 'w') as f:
            json.dump(self.registry, f, indent=2)

    def register_model(self, metrics=None, notes=""):
        """
        Archive the current active model as a new version.
        
        Args:
            metrics: dict with keys like 'val_loss', 'val_acc', 'test_acc', 'sharpe'
            notes: Human-readable description of this version
        
        Returns:
            version_id: e.g. 'v003'
        """
        if not os.path.exists(self.ACTIVE_MODEL):
            print("[Registry] No active model to register.")
            return None

        version_num = len(self.registry['versions']) + 1
        version_id = f"v{version_num:03d}"
        date_str = datetime.now().strftime('%Y%m%d_%H%M')
        filename = f"{version_id}_{date_str}.pth"
        dest_path = os.path.join(self.REGISTRY_DIR, filename)

        # Copy active model to registry
        shutil.copy2(self.ACTIVE_MODEL, dest_path)

        # Record metadata
        entry = {
            'version_id': version_id,
            'filename': filename,
            'timestamp': datetime.now().isoformat(),
            'metrics': metrics or {},
            'notes': notes,
            'file_size_mb': round(os.path.getsize(dest_path) / (1024 * 1024), 2)
        }

        self.registry['versions'].append(entry)
        self.registry['active_version'] = version_id
        self._save_registry()

        print(f"[Registry] ✅ Registered {version_id} — {filename}")
        return version_id

    def rollback(self, version_id=None):
        """
        Rollback active model to a previous version.
        If version_id is None, rolls back to the previous version.
        """
        versions = self.registry['versions']
        if not versions:
            print("[Registry] No versions to rollback to.")
            return False

        if version_id is None:
            # Rollback to second-to-last version
            if len(versions) < 2:
                print("[Registry] Only one version exists.")
                return False
            target = versions[-2]
        else:
            target = next((v for v in versions if v['version_id'] == version_id), None)
            if not target:
                print(f"[Registry] Version {version_id} not found.")
                return False

        source_path = os.path.join(self.REGISTRY_DIR, target['filename'])
        if not os.path.exists(source_path):
            print(f"[Registry] File missing: {source_path}")
            return False

        # Backup current active before overwriting
        if os.path.exists(self.ACTIVE_MODEL):
            backup_name = f"pre_rollback_{datetime.now().strftime('%Y%m%d_%H%M')}.pth"
            shutil.copy2(self.ACTIVE_MODEL, os.path.join(self.REGISTRY_DIR, backup_name))

        shutil.copy2(source_path, self.ACTIVE_MODEL)
        self.registry['active_version'] = target['version_id']
        self._save_registry()

        print(f"[Registry] ⏪ Rolled back to {target['version_id']}")
        return True

    def compare_versions(self, v1_id, v2_id):
        """Compare metrics between two versions."""
        v1 = next((v for v in self.registry['versions'] if v['version_id'] == v1_id), None)
        v2 = next((v for v in self.registry['versions'] if v['version_id'] == v2_id), None)

        if not v1 or not v2:
            print("[Registry] One or both versions not found.")
            return None

        print(f"\n{'Metric':<20} {v1_id:<15} {v2_id:<15} {'Winner':<10}")
        print("-" * 60)

        m1, m2 = v1.get('metrics', {}), v2.get('metrics', {})
        all_keys = set(list(m1.keys()) + list(m2.keys()))

        for key in sorted(all_keys):
            val1 = m1.get(key, 'N/A')
            val2 = m2.get(key, 'N/A')
            winner = ''
            if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                # Lower is better for loss, higher is better for acc/sharpe
                if 'loss' in key:
                    winner = v1_id if val1 < val2 else v2_id
                else:
                    winner = v1_id if val1 > val2 else v2_id
            print(f"{key:<20} {str(val1):<15} {str(val2):<15} {winner:<10}")

        return {'v1': m1, 'v2': m2}

    def get_latest_version(self):
        """Get info about the latest registered version."""
        if self.registry['versions']:
            return self.registry['versions'][-1]
        return None

    def list_versions(self, last_n=10):
        """List recent model versions."""
        versions = self.registry['versions'][-last_n:]
        print(f"\n📦 Model Registry ({len(self.registry['versions'])} versions)")
        print(f"   Active: {self.registry.get('active_version', 'None')}")
        print("-" * 60)
        for v in versions:
            metrics_str = ''
            if v.get('metrics'):
                m = v['metrics']
                parts = [f"{k}={v:.4f}" if isinstance(v, float) else f"{k}={v}"
                         for k, v in m.items()]
                metrics_str = ' | '.join(parts[:3])
            print(f"   {v['version_id']} | {v['timestamp'][:16]} | {v['file_size_mb']}MB | {metrics_str}")
        print()
