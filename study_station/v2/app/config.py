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
# NVIDIA API (build.nvidia.com, OpenAI-compatible) — optional second provider, used by bookgen for book drafts.
NVIDIA_API_KEY = os.environ.get('NVIDIA_API_KEY', '')
NVIDIA_MODEL = os.environ.get('NVIDIA_MODEL', 'moonshotai/kimi-k3')
NVIDIA_CHECK_MODEL = os.environ.get('NVIDIA_CHECK_MODEL', 'nvidia/nemotron-3-ultra-550b-a55b')   # independent re-solve
NVIDIA_FALLBACK_MODELS = [m for m in os.environ.get('NVIDIA_FALLBACK_MODELS', 'deepseek-ai/deepseek-v4.1-flash,moonshotai/kimi-k3').split(',') if m]
NVIDIA_BASE_URL = os.environ.get('NVIDIA_BASE_URL', 'https://integrate.api.nvidia.com/v1')
# bookgen provider: 'nvidia' or 'anthropic'; empty = nvidia when NVIDIA_API_KEY is set, else anthropic
BOOKGEN_PROVIDER = os.environ.get('BOOKGEN_PROVIDER', '')

LOG_DIR = Path(os.environ.get('LOG_DIR', BASE_DIR / 'logs'))
AI_DAILY_BOOK_SECTIONS = int(os.environ.get('AI_DAILY_BOOK_SECTIONS', '60'))   # bookgen: AI calls per day, all chapters

# Books (study_station/books/<Level>/<Subject>/[<Book>/]Chapter_NN_Name/) — read-only for the app.
BOOKS_DIR = Path(os.environ.get('BOOKS_DIR') or BASE_DIR.parent / 'books')
BOOKS_RECHECK_SECONDS = float(os.environ.get('BOOKS_RECHECK_SECONDS', '30'))   # how often to look for new/changed files
