"""YouTube Data API uploads with a channel guard and a fail-closed upload journal.

No automatic retry of video mutations: a lost upload response may already have created a video.
Pending entries require checking YouTube Studio before an operator reconciles the journal.
"""
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import urlparse

import httpx


class YouTubeError(Exception):
    """Safe to show in logs; never include HTTP bodies, credentials or session URLs."""


def client():
    return httpx.Client(timeout=httpx.Timeout(300, connect=30), follow_redirects=False)


def checkpoint(path):
    """On Actions, publish the journal BEFORE starting a remote mutation; local use is opt-in."""
    if os.environ.get('PROMO_YOUTUBE_GIT_CHECKPOINT', '').lower() != 'true':
        return
    branch = os.environ.get('PROMO_YOUTUBE_BRANCH', '')
    if not branch or branch.startswith('-'):
        raise YouTubeError('YouTube journal checkpoint branch is missing or invalid')
    try:
        root = Path(subprocess.run(['git', 'rev-parse', '--show-toplevel'], check=True,
                                   capture_output=True, text=True).stdout.strip())
        rel = str(path.resolve().relative_to(root.resolve()))
        subprocess.run(['git', 'add', '--', rel], cwd=root, check=True, capture_output=True)
        changed = subprocess.run(['git', 'diff', '--cached', '--quiet', '--', rel], cwd=root,
                                 capture_output=True)
        if changed.returncode == 1:
            subprocess.run(['git', 'commit', '-q', '-m', 'Promo: checkpoint YouTube upload', '--', rel],
                           cwd=root, check=True, capture_output=True)
        elif changed.returncode != 0:
            raise YouTubeError('YouTube journal checkpoint diff failed')
        subprocess.run(['git', 'push', '-q', 'origin', f'HEAD:refs/heads/{branch}'], cwd=root,
                       check=True, capture_output=True)
    except (OSError, ValueError, subprocess.CalledProcessError):
        raise YouTubeError('YouTube journal checkpoint failed; upload stopped') from None


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(dir=path.parent, suffix='.tmp')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False)
            fh.write('\n')
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)
    checkpoint(path)


class Uploader:
    def __init__(self):
        names = ('YOUTUBE_CLIENT_ID', 'YOUTUBE_CLIENT_SECRET', 'YOUTUBE_REFRESH_TOKEN', 'YOUTUBE_CHANNEL_ID')
        values = {n: os.environ.get(n, '').strip() for n in names}
        if any(not v for v in values.values()):
            raise YouTubeError('Missing YouTube OAuth secrets or YOUTUBE_CHANNEL_ID')
        self.channel = values['YOUTUBE_CHANNEL_ID']
        self.privacy = os.environ.get('YOUTUBE_PRIVACY_STATUS', 'private').strip()
        if self.privacy not in ('private', 'unlisted', 'public'):
            raise YouTubeError('YOUTUBE_PRIVACY_STATUS must be private, unlisted or public')
        kids = os.environ.get('YOUTUBE_MADE_FOR_KIDS', '').lower()
        if kids not in ('true', 'false'):
            raise YouTubeError('Set YOUTUBE_MADE_FOR_KIDS explicitly to true or false')
        self.kids = kids == 'true'
        self.path = Path(os.environ.get('PROMO_YOUTUBE_POSTED',
                         Path(__file__).resolve().parents[3] / 'promo' / 'youtube_uploads.json'))
        try:
            self.data = json.loads(self.path.read_text(encoding='utf-8')) if self.path.exists() else {'uploads': {}}
            entries = self.data['uploads']
            if not isinstance(entries, dict) or any(not isinstance(v, dict) or v.get('status') not in
                                                    ('pending', 'uploaded', 'not_uploaded') for v in entries.values()):
                raise ValueError()
        except (OSError, ValueError, KeyError, TypeError):
            raise YouTubeError('Invalid YouTube upload journal; refusing to risk duplicate uploads') from None
        if any(v.get('status') == 'pending' for v in entries.values()):
            raise YouTubeError('YouTube journal has a pending upload; check YouTube Studio and reconcile before retrying')
        try:
            with client() as http:
                r = http.post('https://oauth2.googleapis.com/token', data={
                    'client_id': values['YOUTUBE_CLIENT_ID'], 'client_secret': values['YOUTUBE_CLIENT_SECRET'],
                    'refresh_token': values['YOUTUBE_REFRESH_TOKEN'], 'grant_type': 'refresh_token'})
                r.raise_for_status()
                self.token = r.json()['access_token']
                r = http.get('https://www.googleapis.com/youtube/v3/channels',
                             params={'part': 'id', 'mine': 'true'}, headers=self.headers)
                r.raise_for_status()
                channels = [item['id'] for item in r.json()['items']]
                if channels != [self.channel]:
                    raise YouTubeError('Authorized YouTube channel does not match YOUTUBE_CHANNEL_ID')
        except (httpx.HTTPError, ValueError, KeyError, TypeError):
            raise YouTubeError('YouTube authentication/channel check failed; check OAuth secrets and API access') from None

    @property
    def headers(self):
        return {'Authorization': f'Bearer {self.token}'}

    def upload(self, question_id, path, caption, day):
        key = f'{self.channel}:{question_id}'
        previous = self.data['uploads'].get(key, {})
        if previous.get('status') == 'uploaded':
            return previous['video_id']
        if previous.get('status') == 'pending':
            raise YouTubeError('YouTube upload is pending; manual reconciliation required')
        title, _, description = caption.partition('\n')
        # YouTube forbids ASCII angle brackets even in plain-text maths comparisons.
        title = title.strip().replace('<', '＜').replace('>', '＞')
        description = description.replace('<', '＜').replace('>', '＞')
        if not title or len(title) > 100 or len(description.encode('utf-8')) > 5000:
            raise YouTubeError('YouTube title/description exceeds API limits')
        path = Path(path)
        if not path.is_file() or not path.stat().st_size:
            raise YouTubeError('YouTube video file is missing or empty')
        entry = {'question_id': question_id, 'channel_id': self.channel, 'day': day.isoformat(),
                 'title': title, 'status': 'pending'}
        self.data['uploads'][key] = entry
        save(self.path, self.data)
        try:
            with client() as http:
                r = http.post('https://www.googleapis.com/upload/youtube/v3/videos',
                              params={'uploadType': 'resumable', 'part': 'snippet,status', 'notifySubscribers': 'false'},
                              headers={**self.headers, 'X-Upload-Content-Type': 'video/mp4',
                                       'X-Upload-Content-Length': str(path.stat().st_size)},
                              json={'snippet': {'title': title, 'description': description.strip(),
                                                'categoryId': '27', 'defaultLanguage': 'hi'},
                                    'status': {'privacyStatus': self.privacy,
                                               'selfDeclaredMadeForKids': self.kids}})
                r.raise_for_status()
                location = r.headers['Location']
                url = urlparse(location)
                if url.scheme != 'https' or url.hostname != 'www.googleapis.com' or url.username or url.password:
                    raise YouTubeError('YouTube returned an unexpected upload endpoint; upload stopped')
                with path.open('rb') as video:
                    r = http.put(location, headers={**self.headers, 'Content-Type': 'video/mp4',
                                                  'Content-Length': str(path.stat().st_size)}, content=video)
                r.raise_for_status()
                video_id = r.json()['id']
                if not isinstance(video_id, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,64}', video_id):
                    raise ValueError()
        except (httpx.HTTPError, ValueError, KeyError, TypeError, OSError):
            raise YouTubeError('YouTube upload failed or response was lost; pending journal retained. Check YouTube Studio before retrying') from None
        entry.update(status='uploaded', video_id=video_id, requested_privacy=self.privacy)
        save(self.path, self.data)
        return video_id
