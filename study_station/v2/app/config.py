import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_URL = os.environ.get('DATABASE_URL') or f"sqlite:///{BASE_DIR / 'studystation.db'}"
SITE_URL = os.environ.get('SITE_URL', '').rstrip('/')
COOKIE_SECURE = os.environ.get('COOKIE_SECURE', '1') != '0'
DEVICE_COOKIE = 'ss_device'
