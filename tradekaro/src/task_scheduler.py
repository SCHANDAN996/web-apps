"""
⏰ Task Scheduler — Cron-Like Job Scheduler

Schedule recurring tasks:
  - Daily model retraining at 4 PM
  - Hourly data quality check
  - Weekly performance report
  - Pre-market watchlist scan at 9:00 AM
"""

import threading, time, logging
from datetime import datetime, timedelta


class TaskScheduler:
    
    def __init__(self):
        self.tasks = {}
        self.running = False
        self.thread = None
    
    def add_task(self, name, func, interval_minutes=60, run_at_time=None):
        self.tasks[name] = {
            'func': func, 'interval': interval_minutes * 60,
            'run_at': run_at_time, 'last_run': None,
            'runs': 0, 'errors': 0
        }
    
    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()
    
    def stop(self):
        self.running = False
    
    def _loop(self):
        while self.running:
            now = datetime.now()
            for name, task in self.tasks.items():
                should_run = False
                if task['run_at']:
                    h, m = map(int, task['run_at'].split(':'))
                    if now.hour == h and now.minute == m and (
                        not task['last_run'] or (now - task['last_run']).seconds > 120):
                        should_run = True
                elif task['last_run'] is None or (now - task['last_run']).seconds >= task['interval']:
                    should_run = True
                
                if should_run:
                    try:
                        task['func']()
                        task['runs'] += 1
                    except Exception as e:
                        task['errors'] += 1
                        logging.warning(f"Scheduler [{name}]: {e}")
                    task['last_run'] = now
            time.sleep(30)
    
    def get_status(self):
        return {name: {'runs': t['runs'], 'errors': t['errors'],
                       'last_run': t['last_run'].isoformat() if t['last_run'] else None}
                for name, t in self.tasks.items()}
