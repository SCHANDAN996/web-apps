"""Allowlisted same-origin study destinations; never forward provider URLs."""
import re
from urllib.parse import urlsplit, parse_qsl, urlencode, unquote

def study_target(value):
    if not isinstance(value,str) or len(value)>1024 or any(ord(c)<32 for c in value): return '/'
    try: parts=urlsplit(value)
    except ValueError: return '/'
    path=unquote(parts.path)
    if parts.scheme or parts.netloc or parts.fragment or '\\' in path or '//' in path or any(x in ('.','..') for x in path.split('/')): return '/'
    if not re.fullmatch(r'/(?:|books(?:/[A-Za-z0-9_-]+){0,2}|offline-study|practice|topic/[A-Za-z0-9_-]+/[A-Za-z0-9_-]+|mock(?:/[A-Za-z0-9_-]+)?|attempt/\d+|result/\d+|questions(?:/\d+)?|q/[A-Za-z0-9_-]+|w/[A-Za-z0-9_-]{16,128}|revise|progress|current-affairs|jobs(?:/[A-Za-z0-9_-]+)?|settings|classroom|membership|account)',path): return '/'
    keys={'lang','s','view','join','invite','workspace','qualification','category','status','q','page','topic','subject','difficulty'}
    query=[(k,v) for k,v in parse_qsl(parts.query) if k in keys and len(v)<=160 and not any(ord(c)<32 for c in v)]
    return path+('?' + urlencode(query) if query else '')
