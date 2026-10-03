import os

from app import app
from models import db, SystemSettings

# Loads .env automatically (see telegram_config.py)
import telegram_config  # noqa: F401

with app.app_context():
    # Remove old keys if any
    SystemSettings.query.filter_by(setting_key='gemini_api_keys').delete()
    SystemSettings.query.filter_by(setting_key='gemini_api_key').delete()

    # Insert new key (read from environment — never hardcode secrets)
    key = os.environ.get('GEMINI_API_KEY', '')
    if not key:
        raise SystemExit("GEMINI_API_KEY is not set. Add it to backend-server/.env first.")
    s = SystemSettings(setting_key='gemini_api_keys', setting_value=key)
    db.session.add(s)
    db.session.commit()
    print("API Key restored successfully!")
