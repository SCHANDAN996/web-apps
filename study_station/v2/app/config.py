import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_URL = os.environ.get('DATABASE_URL') or f"sqlite:///{BASE_DIR / 'studystation.db'}"
SITE_URL = os.environ.get('SITE_URL', '').rstrip('/')
COOKIE_SECURE = os.environ.get('COOKIE_SECURE', '1') != '0'
DEVICE_COOKIE = 'ss_device'

# Admin panel — locked until both are set (fails closed).
SECRET_KEY = os.environ.get('SECRET_KEY', '')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', '')

# AI features (tutor, question & current-affairs generation) — off until a key is set.
ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')
AI_MODEL = os.environ.get('AI_MODEL', 'claude-opus-5-5')
AI_DAILY_LIMIT_PER_DEVICE = int(os.environ.get('AI_DAILY_LIMIT_PER_DEVICE', '20'))
AI_DAILY_LIMIT_TOTAL = int(os.environ.get('AI_DAILY_LIMIT_TOTAL', '2000'))

LOG_DIR = Path(os.environ.get('LOG_DIR', BASE_DIR / 'logs'))
