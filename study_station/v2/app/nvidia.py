"""
NVIDIA API (build.nvidia.com, OpenAI-compatible chat completions) — a second AI provider, used by bookgen for
bulk book drafts. Standard library only; streams the answer so long sections never hit a gateway timeout.

Needs NVIDIA_API_KEY (server .env or the session environment — never in code or git). Model: NVIDIA_MODEL.
"""
import json
import hashlib
import itertools
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


LOCAL_KEY_ROTATION = itertools.count()
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


def _rate_deadline(path):
    try:
        return float(json.loads(path.read_text())['next_start'])
    except (OSError, ValueError, KeyError, TypeError):
        return 0


def _save_rate_state(path, data):
    output = os.open(path, os.O_CREAT | os.O_WRONLY | os.O_TRUNC, 0o600)
    with os.fdopen(output, 'w') as stream:
        json.dump(data, stream)
        stream.flush()
        os.fsync(stream.fileno())


def _save_rate_deadline(path, deadline):
    _save_rate_state(path, {'next_start': deadline})


def _open_rate_lock(path, nonblocking=False):
    import fcntl
    fd = os.open(path, os.O_CREAT | os.O_RDWR, 0o600)
    handle = os.fdopen(fd, 'a+')
    try:
        fcntl.flock(handle, fcntl.LOCK_EX | (fcntl.LOCK_NB if nonblocking else 0))
    except BlockingIOError:
        handle.close()
        return None
    return handle


def _close_rate_lock(handle):
    import fcntl
    fcntl.flock(handle, fcntl.LOCK_UN)
    handle.close()


@contextmanager
def _schedule_lock(directory):
    """Selection and start reservations are atomic across the whole supplied key pool."""
    handle = _open_rate_lock(directory / 'account.lock')
    try:
        yield
    finally:
        _close_rate_lock(handle)


def _try_inflight_slot(directory, digest, limit):
    """Return a free crash-safe key slot, without waiting while another key could be free."""
    for offset in range(limit):
        slot = (os.getpid() + offset) % limit
        handle = _open_rate_lock(directory / f'{digest}.slot{slot}.lock', nonblocking=True)
        if handle is not None:
            return handle
    return None


def _configured_keys():
    return list(dict.fromkeys(key.strip() for key in config.NVIDIA_API_KEY.split(',') if key.strip()))


@contextmanager
def _request_slot():
    """Choose an eligible key, bound its response concurrency and reserve a shared start time.

    Requests use free keys dynamically instead of binding a chapter to one key. Shared round-robin
    selection alternates keys when both are ready; busy keys do not strand a caller. These local
    safety settings are not the account's NVIDIA quota and are not shared across separate runners.
    Defaults remain one in-flight response per key with independent key spacing.
    """
    keys = _configured_keys()
    if not keys:
        raise AIUnavailable('not_configured')
    root = os.environ.get('BOOKGEN_RATE_STATE_DIR')
    if not root:
        yield keys[next(LOCAL_KEY_ROTATION) % len(keys)]
        return
    directory = Path(root)
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    digests = [hashlib.sha256(key.encode()).hexdigest() for key in keys]
    account_state = directory / 'account.json'
    rotation_state = directory / 'pool.json'
    interval = max(0, min(300, float(os.environ.get('NVIDIA_MIN_INTERVAL_SECONDS', '15'))))
    account_interval = max(0, min(300, float(os.environ.get('NVIDIA_ACCOUNT_MIN_INTERVAL_SECONDS', '0'))))
    shared_account = bool(account_interval or len(keys) > 1)
    limit = max(1, min(8, int(os.environ.get('NVIDIA_MAX_INFLIGHT_PER_KEY', '1'))))
    handle, selected = None, None
    while handle is None:
        delay, busy = None, False
        with _schedule_lock(directory):
            now = time.time()
            account_deadline = _rate_deadline(account_state) if shared_account else 0
            if account_deadline > now:
                delay = account_deadline - now
            else:
                try:
                    rotation = json.loads(rotation_state.read_text())
                    last = int(rotation['last_index'])
                except (OSError, ValueError, KeyError, TypeError):
                    rotation, last = {}, -1
                for offset in range(len(keys)):
                    index = (last + offset + 1) % len(keys)
                    digest = digests[index]
                    key_lock = _open_rate_lock(directory / (digest + '.lock'), nonblocking=True)
                    if key_lock is None:
                        busy = True
                        continue
                    try:
                        state = directory / (digest + '.json')
                        wait = _rate_deadline(state) - now
                        if wait > 0:
                            delay = min(delay, wait) if delay is not None else wait
                            continue
                        handle = _try_inflight_slot(directory, digest, limit)
                        if handle is None:
                            busy = True
                            continue
                        selected = index
                        try:
                            _save_rate_deadline(state, now + interval)
                            if account_interval:
                                _save_rate_deadline(account_state, now + account_interval)
                            if len(keys) > 1:
                                counts = rotation.get('starts_by_index')
                                if (not isinstance(counts, list) or len(counts) != len(keys)
                                        or any(type(count) is not int or count < 0 for count in counts)):
                                    counts = [0] * len(keys)
                                counts[index] += 1
                                _save_rate_state(rotation_state, {'last_index': index, 'starts_by_index': counts})
                        except BaseException:
                            _close_rate_lock(handle)
                            handle = None
                            raise
                        break
                    finally:
                        _close_rate_lock(key_lock)
        if handle is None:
            # No slot is held while waiting. Re-check shared cooldown after every wait because an
            # in-flight response can return 429, or a busy key can become free before another deadline.
            time.sleep(min(0.05 if busy else 60, delay if delay is not None else 0.05))
    try:
        yield keys[selected]
    except AIUnavailable as error:
        if str(error) == 'rate_limited':
            cooldown = max(interval, getattr(error, 'retry_after', 0), 60 if shared_account else 0)
            with _schedule_lock(directory):
                state = directory / (digests[selected] + '.json')
                key_lock = _open_rate_lock(directory / (digests[selected] + '.lock'))
                try:
                    deadline = time.time() + cooldown
                    _save_rate_deadline(state, max(_rate_deadline(state), deadline))
                    if shared_account:
                        _save_rate_deadline(account_state, max(_rate_deadline(account_state), deadline))
                finally:
                    _close_rate_lock(key_lock)
        raise
    finally:
        _close_rate_lock(handle)


def call(system, user, *, max_tokens=16000, temperature=0.3, model=None):
    """One chat completion, retried on rate limits and temporary failures."""
    for wait in RETRY_WAITS + (None,):
        try:
            with _request_slot() as api_key:
                return _call_once(system, user, max_tokens, temperature, model, api_key)
        except AIUnavailable as e:
            if wait is None or str(e) not in ('rate_limited', 'api_error', 'network', 'empty'):
                raise
            delay = max(wait, getattr(e, 'retry_after', 0))
            log.warning('NVIDIA %s — retrying in %ss', e, delay)
            time.sleep(delay)


def _call_once(system, user, max_tokens, temperature, model, api_key=None):
    api_key = api_key if api_key is not None else next(iter(_configured_keys()), '')
    if not api_key:
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
        {'Authorization': 'Bearer ' + api_key, 'Content-Type': 'application/json',
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
