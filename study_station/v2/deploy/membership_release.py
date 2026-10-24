"""Install an already-tested Study Station archive; run as root on its VPS.

Merchant credentials stay on the server. This does not create any payment order.
Enable only after payment terms and checkout integration have been verified.
"""
import argparse
import grp
import os
from pathlib import Path
import re
import shutil
import sqlite3
import subprocess
import tarfile
from datetime import datetime, timezone

ROOT = Path('/var/www/web-apps/study_station/v2')


def run():
    p = argparse.ArgumentParser()
    p.add_argument('--archive', required=True)
    p.add_argument('--lease-key', required=True)
    p.add_argument('--enable-website', action='store_true')
    args = p.parse_args()
    if os.geteuid() != 0 or ROOT.resolve() != ROOT or not (ROOT / '.env').is_file():
        raise SystemExit('Unexpected deployment target or privileges')
    os.umask(0o077)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')
    backup = Path('/root/ss-backups') / ('membership-' + stamp)
    backup.mkdir(mode=0o700)
    with sqlite3.connect('/var/lib/studystation/studystation.db') as source:
        with sqlite3.connect(str(backup / 'studystation.db')) as target:
            source.backup(target)
    shutil.copy2(ROOT / '.env', backup / 'environment')
    with tarfile.open(backup / 'source.tar.gz', 'w:gz') as tar:
        tar.add(ROOT / 'app', arcname='app', filter=lambda x: None if '__pycache__' in x.name else x)
        tar.add(ROOT / 'requirements.txt', arcname='requirements.txt')
    with tarfile.open(args.archive, 'r:gz') as tar:
        for m in tar.getmembers():
            parts = Path(m.name).parts
            if not parts or parts[0] not in ('app', 'deploy', 'requirements.txt') or '..' in parts or m.issym() or m.islnk():
                raise SystemExit('Invalid archive member')
        tar.extractall(ROOT, filter='data')
    # App code must not be writable by its service account.
    for directory in (ROOT / 'app', ROOT / 'deploy'):
        for item in (directory, *directory.rglob('*')):
            if item.is_symlink(): raise SystemExit('Unexpected source symlink')
            os.chown(item, 0, 0)
            os.chmod(item, 0o755 if item.is_dir() else 0o644)
    subprocess.run([str(ROOT / 'venv/bin/pip'), 'install', '-q', '-r', str(ROOT / 'requirements.txt')], check=True)
    from dotenv import dotenv_values
    merchant = dotenv_values('/var/www/ebookcart/config/.env')
    key, salt = merchant.get('PAYU_MERCHANT_KEY'), merchant.get('PAYU_MERCHANT_SALT')
    if not key or not salt: raise SystemExit('Merchant configuration missing')
    private = Path('/etc/studystation')
    private.mkdir(mode=0o750, exist_ok=True)
    group = grp.getgrnam('studystation').gr_gid
    os.chown(private, 0, group)
    os.chmod(private, 0o750)
    lease = private / 'membership-private.pem'
    shutil.copyfile(args.lease_key, lease)
    os.chown(lease, 0, group)
    os.chmod(lease, 0o640)
    enabled = '1' if args.enable_website else '0'
    values = {
        'MEMBERSHIP_ENABLED': enabled,
        'MEMBERSHIP_LEASE_PRIVATE_KEY_FILE': str(lease),
        'SS_PAYU_WEB_ENABLED': enabled,
        'SS_PAYMENT_CHANNEL': 'website',
        'SS_PAYU_WEB_ORIGIN': 'https://studystation.ebookcart.in',
        'SS_PAYU_ENV': 'production',
        'SS_PAYU_MERCHANT_KEY': key,
        'SS_PAYU_MERCHANT_SALT': salt,
        'PLAY_BILLING_ENABLED': '0',
    }
    env = ROOT / '.env'
    if (dotenv_values(env).get('SITE_URL') or '').rstrip('/') != values['SS_PAYU_WEB_ORIGIN']:
        raise SystemExit('SITE_URL must match the website payment origin')
    text = env.read_text()
    for name, value in values.items():
        # Single-quoted dotenv values; reject multiline config rather than interpolate.
        if any(c in value for c in ('\n', '\r', "'")):
            raise SystemExit('Unsupported configuration value')
        text = re.sub(r'(?m)^' + re.escape(name) + r'=.*\n?', '', text)
        text += '\n' + name + "='" + value + "'\n"
    tmp = env.with_name('.env.membership-new')
    tmp.write_text(text)
    os.chown(tmp, 0, group)
    os.chmod(tmp, 0o640)
    os.replace(tmp, env)
    effective = {**os.environ, **{k: v for k, v in dotenv_values(env).items() if v is not None}}
    if effective.get('SITE_URL', '').rstrip('/') != values['SS_PAYU_WEB_ORIGIN']:
        raise SystemExit('SITE_URL must match the website payment origin')
    # Apply additive schema once before two web workers start simultaneously.
    subprocess.run([str(ROOT / 'venv/bin/python'), '-c', 'import app.main; from app.db import ensure_schema; ensure_schema()'],
                   cwd=ROOT, env=effective, user='studystation', group='studystation', check=True)
    for name in ('studystation-payu-reconcile.service', 'studystation-payu-reconcile.timer'):
        shutil.copyfile(ROOT / 'deploy' / name, Path('/etc/systemd/system') / name)
    subprocess.run(['systemctl', 'daemon-reload'], check=True)
    subprocess.run(['systemctl', 'restart', 'studystation'], check=True)
    if args.enable_website:
        subprocess.run(['systemctl', 'enable', '--now', 'studystation-payu-reconcile.timer'], check=True)
    print('Deployment complete; backup=' + str(backup) + '; website_enabled=' + enabled)


if __name__ == '__main__':
    run()
