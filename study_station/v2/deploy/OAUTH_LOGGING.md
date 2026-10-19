# OAuth-safe operational logging

Uvicorn uses `deploy/logging.json`: access records retain client address, method,
path, protocol and status, but omit **all** URL queries. Errors retain tracebacks;
callback URLs have their complete query removed, including upstream URL copies.
Do not add request-body, token, cookie or Authorization-header logging.

Nginx's `ss_safe` access format uses `$uri`, not `$request` or `$request_uri`, and
excludes Referer. Status, client address, bytes, upstream status and timings remain.
**Nginx error logs cannot be redacted by `log_format`.** A dedicated Unix socket
passes errors directly to an isolated rsyslog ruleset, bypassing journald and
other collectors. Native rsyslog regex detects query-bearing callback errors and
writes a constant diagnostic with timestamp, hostname, tag and callback path.
Their full error detail is intentionally suppressed; access logs retain the
request method/status/client/path needed to correlate failures. Other nginx errors
remain intact. There is no external subprocess or sanitizer service, no writable
app code executed as root, and no AppArmor profile expansion.

## Deployment gate (before browser OAuth)

The sample unit uses `/var/www/study_station/v2`; adapt to the existing production
directory and preserve live domain/TLS/security settings. Do not copy example host
names from the sample nginx site over the live site.

1. Install `app/logging_security.py` and `deploy/logging.json` in the app. Add
   `--log-config deploy/logging.json` to the existing Uvicorn ExecStart, preserving
   service hardening. Ensure LF line endings.
2. Verify rsyslog's imuxsock module is loaded. Install
   `deploy/rsyslog-studystation.conf` as
   `/etc/rsyslog.d/00-studystation-nginx.conf`. Run `rsyslogd -N1` before restart.
   Confirm `/var/spool/rsyslog/studystation-nginx-log.sock` exists, nginx workers
   (normally www-data) can access it, and permissions persist after restart.
   The spool directory is already allowed by the standard Ubuntu rsyslog AppArmor
   profile; verify this host's profile instead of adding broad permissions.
3. Before switching nginx, inject synthetic noncredential events using
   `logger --socket /var/spool/rsyslog/studystation-nginx-log.sock -t studystation_nginx 'probe GET /api/v1/classroom/google/callback?code=SS_SYNTHETIC_CODE&state=SS_SYNTHETIC_STATE HTTP/1.1 upstream failure'`.
   Repeat with `%3Fcode=...` and inject an ordinary upstream failure. The callback
   events must produce only the constant callback diagnostic in
   `/var/log/nginx/studystation-error.log`; ordinary failure detail must survive.
   Neither synthetic value may reach that file, generic syslog, journal or any
   forwarded collector. If this fails, keep browser OAuth disabled.
4. Put `log_format ss_safe ...` in nginx's http context. Add supplied access_log
   and error_log directives to the existing Study Station server blocks only.
   Audit `nginx -T` for extra inherited/raw log destinations and location
   overrides (except static access_log off). Run `nginx -t` before reloading.
5. Reload service definitions, restart Study Station and reload nginx. Request the
   callback with synthetic code/state and verify both proxy/app access logs retain
   path/outcome without either value. Test an upstream failure on staging, without
   causing a production outage. Inspect local/global/journal/forwarded sinks.
6. Only after these checks, configure OAuth readiness. Include the two log files
   in existing logrotate/access/retention policies and keep them private.

No existing logs are modified. Handle any previously logged real credentials
according to the operator's incident/retention policy. Remove any obsolete
mmexternal launcher/module copies installed during earlier preparation; the final
configuration uses none.

Focused tests: `python -m pytest tests/test_logging_security.py -q`. They verify
real Uvicorn formatting and config safety, but do not replace `rsyslogd -N1`,
`nginx -t` or live synthetic probes.
