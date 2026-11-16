"""
NVIDIA API (build.nvidia.com, OpenAI-compatible chat completions) — a second AI provider, used by bookgen for
bulk book drafts. Standard library only; streams the answer so long sections never hit a gateway timeout.

Needs NVIDIA_API_KEY (server .env or the session environment — never in code or git). Model: NVIDIA_MODEL.
"""
import json
import hashlib
import os
from contextlib import contextmanager
from datetime import timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
import logging
import re
import socket
import time
import urllib.error
import urllib.request

from . import config
from .ai import AIUnavailable

log = logging.getLogger('nvidia')
THINK = re.compile(r'<think>.*?</think>\s*', re.S)     # some models print their reasoning inline


RETRY_WAITS = (20, 60, 120, 240, 300)   # seconds between tries on rate limits / server or network errors (the free API is flaky)



def _retry_after(headers):
    """Read the server's bounded cooldown; never log response headers or credentials."""
    value = headers.get('Retry-After') if headers else None
    if not value:
        return 0
    try:
        seconds = float(value)
    except (TypeError, ValueError):
        try:
            deadline = parsedate_to_datetime(value)
            if deadline.tzinfo is None:
                deadline = deadline.replace(tzinfo=timezone.utc)
            seconds = deadline.timestamp() - time.time()
        except (TypeError, ValueError, OverflowError):
            return 0
    return max(0, min(300, seconds))


@contextmanager
def _request_slot():
    """Serialize each key across chapter subprocesses, when CI supplies a shared state directory.

    This is a local safety throttle, not a claim about the account's actual NVIDIA quota.
    Separate machines/runners cannot share this file lock.
    """
    root = os.environ.get('BOOKGEN_RATE_STATE_DIR')
    if not root:
        yield
        return
    import fcntl                         # the autopilot runs on Linux
    directory = Path(root)
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    digest = hashlib.sha256(config.NVIDIA_API_KEY.encode()).hexdigest()
    state = directory / (digest + '.json')
    lock = directory / (digest + '.lock')
    interval = max(0, min(300, float(os.environ.get('NVIDIA_MIN_INTERVAL_SECONDS', '15'))))
    fd = os.open(lock, os.O_CREAT | os.O_RDWR, 0o600)
    with os.fdopen(fd, 'a+') as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        try:
            try:
                next_start = float(json.loads(state.read_text())['next_start'])
            except (OSError, ValueError, KeyError, TypeError):
                next_start = 0
            delay = max(0, min(300, next_start - time.time()))
            if delay:
                time.sleep(delay)
            def save(deadline):
                output = os.open(state, os.O_CREAT | os.O_WRONLY | os.O_TRUNC, 0o600)
                with os.fdopen(output, 'w') as stream:
                    json.dump({'next_start': deadline}, stream)
                    stream.flush()
                    os.fsync(stream.fileno())
            save(time.time() + interval)
            try:
                yield
            except AIUnavailable as error:
                if str(error) == 'rate_limited':
                    save(time.time() + max(interval, getattr(error, 'retry_after', 0)))
                raise
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)

def call(system, user, *, max_tokens=16000, temperature=0.3, model=None):
    """One chat completion, retried on rate limits and temporary failures."""
    for wait in RETRY_WAITS + (None,):
        try:
            with _request_slot():
                return _call_once(system, user, max_tokens, temperature, model)
        except AIUnavailable as e:
            if wait is None or str(e) not in ('rate_limited', 'api_error', 'network', 'empty'):
                raise
            delay = max(wait, getattr(e, 'retry_after', 0))
            log.warning('NVIDIA %s — retrying in %ss', e, delay)
            time.sleep(delay)


def _call_once(system, user, max_tokens, temperature, model):
    if not config.NVIDIA_API_KEY:
        raise AIUnavailable('not_configured')
    body = json.dumps({
        'model': model or config.NVIDIA_MODEL,
        'messages': [{'role': 'system', 'content': system}, {'role': 'user', 'content': user}],
        'max_tokens': max_tokens,
        'temperature': temperature,
        'stream': True,
    }).encode()
    req = urllib.request.Request(
        config.NVIDIA_BASE_URL.rstrip('/') + '/chat/completions', body,
        {'Authorization': 'Bearer ' + config.NVIDIA_API_KEY, 'Content-Type': 'application/json',
         'Accept': 'text/event-stream'})
    parts, finish = [], None
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:     # timeout per read, not for the whole answer
            for raw in resp:
                line = raw.decode('utf-8', 'replace').strip()
                if not line.startswith('data:'):
                    continue
                data = line[5:].strip()
                if data == '[DONE]':
                    break
                try:
                    choice = json.loads(data)['choices'][0]
                except (ValueError, KeyError, IndexError):
                    continue
                parts.append((choice.get('delta') or {}).get('content') or '')
                finish = choice.get('finish_reason') or finish
    except urllib.error.HTTPError as e:
        if e.code in (401, 403):
            log.error('NVIDIA auth failed — check NVIDIA_API_KEY')
            raise AIUnavailable('auth')
        if e.code == 429:
            error = AIUnavailable('rate_limited')
            error.retry_after = _retry_after(e.headers)
            raise error
        log.warning('NVIDIA API error %s', e.code)
        raise AIUnavailable('bad_request' if e.code in (400, 404, 422) else 'api_error')
    except (urllib.error.URLError, socket.timeout, ConnectionError, TimeoutError):
        raise AIUnavailable('network')
    if finish == 'length':
        raise AIUnavailable('too_long')
    text = THINK.sub('', ''.join(parts)).strip()
    if not text or finish is None:                # stream cut off or an empty answer: retry
        log.warning('NVIDIA empty or unfinished answer (%s chars, finish=%s)', len(text), finish)
        raise AIUnavailable('empty')
    return text
