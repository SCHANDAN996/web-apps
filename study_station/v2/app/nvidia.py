"""
NVIDIA API (build.nvidia.com, OpenAI-compatible chat completions) — a second AI provider, used by bookgen for
bulk book drafts. Standard library only; streams the answer so long sections never hit a gateway timeout.

Needs NVIDIA_API_KEY (server .env or the session environment — never in code or git). Model: NVIDIA_MODEL.
"""
import json
import logging
import re
import socket
import urllib.error
import urllib.request

from . import config
from .ai import AIUnavailable

log = logging.getLogger('nvidia')
THINK = re.compile(r'<think>.*?</think>\s*', re.S)     # some models print their reasoning inline


def call(system, user, *, max_tokens=16000, temperature=0.3, model=None):
    """One chat completion. Returns the answer text (reasoning, if any, is dropped)."""
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
            raise AIUnavailable('rate_limited')
        log.warning('NVIDIA API error %s', e.code)
        raise AIUnavailable('bad_request' if e.code in (400, 404, 422) else 'api_error')
    except (urllib.error.URLError, socket.timeout, ConnectionError, TimeoutError):
        raise AIUnavailable('network')
    if finish == 'length':
        raise AIUnavailable('too_long')
    return THINK.sub('', ''.join(parts)).strip()
