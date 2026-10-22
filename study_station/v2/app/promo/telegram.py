"""Telegram Bot API client for the channel: quiz polls and HTML messages.

Env: TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID (e.g. @studystation_hindi). The token is part of the request URL,
so errors never include the URL or the exception text — only the type and Telegram's own description.
"""
import html
import os
import re
import time

import httpx

SEND_GAP = 1.5          # seconds between messages (channel limit is ~20/minute)
MAX_TEXT = 3900         # Telegram allows 4096 per message


class TelegramError(Exception):
    pass


def _config():
    token, chat = os.environ.get('TELEGRAM_BOT_TOKEN'), os.environ.get('TELEGRAM_CHANNEL_ID')
    if not token or not chat:
        raise TelegramError('TELEGRAM_BOT_TOKEN / TELEGRAM_CHANNEL_ID not set')
    return token, chat


def _call(method, payload, retries=3):
    token, chat = _config()
    payload = {'chat_id': chat, **payload}
    for attempt in range(retries + 1):
        try:
            r = httpx.post(f'https://api.telegram.org/bot{token}/{method}', json=payload, timeout=30)
        except httpx.HTTPError as e:
            raise TelegramError(f'network error ({type(e).__name__})') from None
        try:
            body = r.json()
        except ValueError:
            body = {}
        if r.status_code == 429 and attempt < retries:
            time.sleep(min(int(body.get('parameters', {}).get('retry_after', 5)), 60) + 1)
            continue
        if r.status_code != 200 or not body.get('ok'):
            raise TelegramError(f'Telegram HTTP {r.status_code}: {str(body.get("description", ""))[:120]}')
        time.sleep(SEND_GAP)
        return body['result'].get('message_id')
    raise TelegramError('Telegram: still rate-limited')


def poll_payload(question, options, correct, explanation):
    return {'question': question[:300], 'options': [{'text': o[:100]} for o in options], 'type': 'quiz',
            'is_anonymous': True, 'correct_option_ids': [correct], 'explanation': explanation[:200]}


def send_poll(question, options, correct, explanation):
    return _call('sendPoll', poll_payload(question, options, correct, explanation))


def chunks(text, limit=MAX_TEXT):
    """Split at line ends so no HTML tag is cut (every tag we write opens and closes on one line)."""
    out, cur = [], ''
    for line in text.split('\n'):
        if cur and len(cur) + len(line) + 1 > limit:
            out.append(cur)
            cur = ''
        cur = f'{cur}\n{line}' if cur else line
    if cur:
        out.append(cur)
    return [c[:limit] for c in out]


def send_html(text):
    ids = []
    for part in chunks(text):
        ids.append(_call('sendMessage', {'text': part, 'parse_mode': 'HTML',
                                         'link_preview_options': {'is_disabled': True}}))
    return ids


def md_to_html(text):
    """The small Markdown subset the books use → Telegram HTML (escaped first)."""
    out = []
    for line in text.splitlines():
        s = html.escape(line.rstrip(), quote=False)
        s = re.sub(r'^\s*&gt;\s?', '', s)
        if (m := re.match(r'^\s*#{1,6}\s+(.*)', s)):
            s = f'<b>{m.group(1).strip()}</b>'
        s = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', s)
        s = re.sub(r'(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])', r'<i>\1</i>', s)
        out.append(s.replace('**', ''))
    return re.sub(r'\n{3,}', '\n\n', '\n'.join(out)).strip()


def message_link(msg_id):
    """t.me link to a channel post (public @channels only)."""
    chat = os.environ.get('TELEGRAM_CHANNEL_ID', '')
    if chat.startswith('@') and msg_id:
        return f'https://t.me/{chat[1:]}/{msg_id}'
    return ''
