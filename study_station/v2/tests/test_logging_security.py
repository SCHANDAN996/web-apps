import json
import logging
import sys
from pathlib import Path

import pytest
from app.logging_security import OAuthQueryFilter, redact_oauth_queries

ROOT = Path(__file__).resolve().parents[1]
CALLBACK = '/api/v1/classroom/google/callback'


@pytest.mark.parametrize('target', [CALLBACK + '?code=private-code&state=private-state',
                                   CALLBACK + '%3Fcode=private-code%26state=private-state'])
def test_callback_in_error_and_upstream_uri_is_redacted(target):
    text = f'upstream failed, request: "GET {target} HTTP/1.1", upstream: "http://127.0.0.1:8001{target}", client: 192.0.2.1'
    cleaned = redact_oauth_queries(text)
    assert 'private-code' not in cleaned
    assert 'private-state' not in cleaned
    assert 'upstream failed' in cleaned and '192.0.2.1' in cleaned
    assert CALLBACK in cleaned


def test_logging_config_covers_access_and_exception_and_preserves_metadata():
    config = json.loads((ROOT/'deploy/logging.json').read_text())
    from uvicorn.logging import AccessFormatter, DefaultFormatter
    assert config['handlers']['access']['filters'] == ['oauth_query']
    assert config['handlers']['default']['filters'] == ['oauth_query']
    access = logging.LogRecord('uvicorn.access', logging.INFO, '', 1,
        '%s - "%s %s HTTP/%s" %d',
        ('192.0.2.1:1234', 'GET', CALLBACK+'?code=private-code&state=private-state', '1.1', 302), None)
    OAuthQueryFilter().filter(access)
    text = AccessFormatter(**{k:v for k,v in config['formatters']['access'].items() if k != '()'}).format(access)
    assert 'private-code' not in text and 'private-state' not in text
    assert '192.0.2.1:1234' in text and CALLBACK in text and '302' in text
    target = 'GET '+CALLBACK+'?code=private-code&state=private-state'
    try:
        raise ValueError(target)
    except ValueError:
        error = logging.LogRecord('uvicorn.error', logging.ERROR, '', 1, 'OAuth callback failed', (), sys.exc_info())
    OAuthQueryFilter().filter(error)
    text = DefaultFormatter(**{k:v for k,v in config['formatters']['default'].items() if k != '()'}).format(error)
    assert 'OAuth callback failed' in text and 'ValueError' in text
    assert 'private-code' not in text and 'private-state' not in text


def test_regular_access_omits_query_but_error_message_is_unchanged():
    record = logging.LogRecord('uvicorn.access', logging.INFO, '', 1, '%s %s %s %s %s',
                              ('127.0.0.1', 'GET', '/jobs?q=railway', '1.1', 200), None)
    OAuthQueryFilter().filter(record)
    assert record.args == ('127.0.0.1', 'GET', '/jobs', '1.1', 200)
    assert redact_oauth_queries('GET /jobs?q=railway upstream timeout') == 'GET /jobs?q=railway upstream timeout'



def test_nginx_safe_format_and_error_pipeline_are_explicit():
    conf = (ROOT/'deploy/nginx.conf').read_text()
    safe_format = conf.split('log_format ss_safe ',1)[1].split(';',1)[0]
    assert '$uri' in safe_format and '$request_method' in safe_format
    assert '$request_uri' not in safe_format and '$http_referer' not in safe_format
    assert '$request"' not in safe_format
    assert 'tag=studystation_nginx' in conf
    pipeline = (ROOT/'deploy/rsyslog-studystation.conf').read_text()
    assert 'mmexternal' not in pipeline and 'stop' in pipeline
    assert '/var/spool/rsyslog/studystation-nginx-log.sock' in pipeline


def test_syslog_failure_branch_never_writes_the_raw_message():
    pipeline = (ROOT/'deploy/rsyslog-studystation.conf').read_text()
    assert 'set $msg' not in pipeline  # rsyslog's system msg property is read-only.
    unsafe_template = pipeline.split('template(name="ss_nginx_unsafe"', 1)[1].split('ruleset(', 1)[0]
    assert '%msg%' not in unsafe_template and 'suppressed' in unsafe_template
    branch = pipeline.split('if re_match', 1)[1].split('} else {', 1)[0]
    assert 'template="ss_nginx_unsafe"' in branch
    assert 'RSYSLOG_TraditionalFileFormat' not in branch
