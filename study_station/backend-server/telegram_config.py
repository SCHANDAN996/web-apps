# telegram_config.py
# ==========================================
# Telegram Bot Configuration
# ==========================================
# Secrets are read from environment variables (or a .env file) so they are
# never committed to git. Copy .env.example to .env and fill in real values.

import os

# Lightweight .env loader (no external dependency needed)
_env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
if os.path.exists(_env_path):
    with open(_env_path, encoding='utf-8') as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith('#') and '=' in _line:
                _k, _, _v = _line.partition('=')
                os.environ.setdefault(_k.strip(), _v.strip())

# 1. Create a bot using @BotFather on Telegram and put the token in .env:
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")

# 2. Create a Telegram Channel (e.g. @StudyStationJobs). The bot MUST be an
#    admin of that channel to send messages.
TELEGRAM_CHANNEL_ID = os.environ.get("TELEGRAM_CHANNEL_ID", "")

# Broadcasting stays off until both values are configured.
IS_TELEGRAM_ENABLED = (
    os.environ.get("IS_TELEGRAM_ENABLED", "false").lower() in ("1", "true", "yes")
    and bool(TELEGRAM_BOT_TOKEN)
    and bool(TELEGRAM_CHANNEL_ID)
)
