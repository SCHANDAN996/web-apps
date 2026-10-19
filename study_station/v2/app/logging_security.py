"""Remove OAuth callback parameters before records leave application logging.
"""
import logging
import re
import traceback

# Cover raw and percent-encoded separators. Keep the path, drop the entire query
# rather than guessing which providers' parameters may carry a credential.
_CALLBACK_QUERY = re.compile(
    r"(/api/v1/classroom/google/callback)(?:\?|%3[fF])[^\s\"'<>]*",
    re.IGNORECASE,
)


def redact_oauth_queries(value: str) -> str:
    return _CALLBACK_QUERY.sub(r"\1[query-redacted]", value)


class OAuthQueryFilter(logging.Filter):
    """Filter both access args and exception text before any formatter sees them."""

    def filter(self, record: logging.LogRecord) -> bool:
        def clean(value):
            if isinstance(value, str):
                return redact_oauth_queries(value)
            if isinstance(value, tuple):
                return tuple(clean(item) for item in value)
            if isinstance(value, dict):
                return {key: clean(item) for key, item in value.items()}
            return value

        record.msg = clean(record.msg)
        record.args = clean(record.args)
        if record.name == 'uvicorn.access' and isinstance(record.args, tuple) and len(record.args) == 5:
            client, method, target, protocol, status = record.args
            if isinstance(target, str):
                target = target.split('?', 1)[0]
            record.args = (client, method, target, protocol, status)
        if record.exc_info:
            record.exc_text = redact_oauth_queries(
                ''.join(traceback.format_exception(*record.exc_info))
            )
        elif record.exc_text:
            record.exc_text = redact_oauth_queries(record.exc_text)
        if record.stack_info:
            record.stack_info = redact_oauth_queries(record.stack_info)
        return True
