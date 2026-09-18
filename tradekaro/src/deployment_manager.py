"""
🚀 Deployment Manager — Systemd Service + Auto-Restart

Production deployment utilities:
  - Generate systemd service file
  - Health check endpoint
  - Auto-restart on crash
  - Environment setup validation
"""

import os, subprocess


class DeploymentManager:
    
    SERVICE_TEMPLATE = '''[Unit]
Description=TradeKaro AI Trading System
After=network.target

[Service]
Type=simple
User={user}
WorkingDirectory={workdir}
Environment=ENVIRONMENT=PAPER_TRADING
ExecStart={python} {main_script}
Restart=always
RestartSec=10
StandardOutput=append:{log_dir}/tradekaro.log
StandardError=append:{log_dir}/tradekaro_error.log

[Install]
WantedBy=multi-user.target
'''
    
    def __init__(self, project_dir='/var/www/tradekaro/Trading_AI_Project'):
        self.project_dir = project_dir
    
    def generate_service(self, user='root'):
        return self.SERVICE_TEMPLATE.format(
            user=user, workdir=self.project_dir,
            python=os.path.join(self.project_dir, 'venv/bin/python'),
            main_script=os.path.join(self.project_dir, 'main.py'),
            log_dir=os.path.join(self.project_dir, 'data')
        )
    
    def check_environment(self):
        checks = {}
        checks['python'] = os.path.exists(os.path.join(self.project_dir, 'venv/bin/python'))
        checks['main.py'] = os.path.exists(os.path.join(self.project_dir, 'main.py'))
        checks['models_dir'] = os.path.exists(os.path.join(self.project_dir, 'models'))
        checks['data_dir'] = os.path.exists(os.path.join(self.project_dir, 'data'))
        checks['config'] = os.path.exists(os.path.join(self.project_dir, 'config'))
        
        src_files = len([f for f in os.listdir(os.path.join(self.project_dir, 'src'))
                        if f.endswith('.py')]) if os.path.exists(os.path.join(self.project_dir, 'src')) else 0
        checks['modules'] = src_files
        checks['ready'] = all(v for k, v in checks.items() if k != 'modules')
        return checks
    
    def save_service_file(self, path='/etc/systemd/system/tradekaro.service'):
        content = self.generate_service()
        with open(path, 'w') as f:
            f.write(content)
        return path
