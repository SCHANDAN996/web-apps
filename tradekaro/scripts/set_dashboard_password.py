#!/usr/bin/env python3
"""
Set the dashboard login password.

    cd /var/www/tradekaro/Trading_AI_Project
    venv/bin/python scripts/set_dashboard_password.py

Writes DASH_PASSWORD_HASH into config/credentials.env, and generates
FLASK_SECRET_KEY there too if it is missing or still the shipped default.

The password itself is never stored or printed -- only the pbkdf2 hash goes to
disk. Nobody who reads credentials.env later can recover it.
"""
import os
import re
import secrets
import sys
from getpass import getpass

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from werkzeug.security import generate_password_hash

ENV_PATH = os.path.join(os.path.dirname(__file__), '..', 'config', 'credentials.env')
MIN_LENGTH = 10
SHIPPED_DEFAULT_SECRET = 'super_secret_key_123'


def upsert(text, key, value):
    """Replace KEY=... in place, or append it if absent."""
    pattern = re.compile(rf'^{re.escape(key)}=.*$', re.MULTILINE)
    line = f'{key}={value}'
    if pattern.search(text):
        return pattern.sub(line, text)
    if text and not text.endswith('\n'):
        text += '\n'
    return text + line + '\n'


def main():
    env_path = os.path.abspath(ENV_PATH)
    if not os.path.exists(env_path):
        print(f"Not found: {env_path}")
        return 1

    with open(env_path) as fh:
        content = fh.read()

    password = getpass('New dashboard password: ')
    if len(password) < MIN_LENGTH:
        print(f"Too short -- needs at least {MIN_LENGTH} characters.")
        return 1
    if password != getpass('Repeat: '):
        print("They do not match.")
        return 1

    content = upsert(content, 'DASH_PASSWORD_HASH', generate_password_hash(password))

    current_secret = ''
    match = re.search(r'^FLASK_SECRET_KEY=(.*)$', content, re.MULTILINE)
    if match:
        current_secret = match.group(1).strip()

    if not current_secret or current_secret == SHIPPED_DEFAULT_SECRET:
        # Session cookies are signed with this. The old app.py fell back to a
        # value committed in the source, so anyone with the repo could forge a
        # logged-in cookie.
        content = upsert(content, 'FLASK_SECRET_KEY', secrets.token_hex(32))
        print("Generated a new FLASK_SECRET_KEY.")

    with open(env_path, 'w') as fh:
        fh.write(content)
    os.chmod(env_path, 0o600)

    print(f"Saved to {env_path}")
    print("Now restart the dashboard:  systemctl restart tradekaro-web")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
