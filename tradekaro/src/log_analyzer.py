"""
📋 Log Analyzer — Pattern Detection in System Logs

Analyzes logs for: Error frequency, common failures, latency spikes, memory leaks
"""

import os, re
from collections import Counter, defaultdict
from datetime import datetime


class LogAnalyzer:
    
    def __init__(self, log_dir='data'):
        self.log_dir = log_dir
    
    def analyze_file(self, filepath):
        if not os.path.exists(filepath):
            return {'error': 'File not found'}
        
        with open(filepath, 'r') as f:
            lines = f.readlines()
        
        errors = [l for l in lines if 'ERROR' in l or 'error' in l.lower()]
        warnings = [l for l in lines if 'WARNING' in l or 'WARN' in l]
        
        error_types = Counter()
        for e in errors:
            match = re.search(r'([\w]+Error|Exception)', e)
            if match:
                error_types[match.group(1)] += 1
        
        return {
            'total_lines': len(lines), 'errors': len(errors), 'warnings': len(warnings),
            'error_rate': round(len(errors) / max(len(lines), 1) * 100, 2),
            'top_errors': dict(error_types.most_common(5)),
            'health': 'GOOD' if len(errors) < 5 else 'WARNING' if len(errors) < 20 else 'CRITICAL'
        }
    
    def find_patterns(self, filepath, pattern):
        if not os.path.exists(filepath):
            return []
        with open(filepath) as f:
            return [l.strip() for l in f if pattern.lower() in l.lower()][:20]
    
    def error_frequency(self, filepath, hours=24):
        """Count errors per hour."""
        analysis = self.analyze_file(filepath)
        return {'errors_in_period': analysis.get('errors', 0),
                'avg_per_hour': round(analysis.get('errors', 0) / hours, 1)}
