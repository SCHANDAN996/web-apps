# Book authoring rate policy — 17 November 2026

- Six chapter workers; only keys 3 and 4. Every worker receives the full active pool.
- Route every request to an eligible key with a free response slot. Alternate keys when both are
  ready; a busy key must not strand a request while the other has capacity.
- Nemotron-3 Ultra for authoring, both blind answer checks and editorial review.
- At most one in-flight request per key, two across the configured pool.
- One shared account start gate: at least twenty seconds between request starts (three starts/minute).
- Each key also waits at least fifteen seconds between starts.
- HTTP 429 delays future requests across the pool for at least sixty seconds or the larger bounded
  server Retry-After. Existing in-flight responses finish normally.
- These are conservative local settings, not a measurement or guarantee of NVIDIA's actual quota.
  Rate-limit retries appear in the autopilot log; do not log credentials or response headers.
- One GitHub run owns the queue and shared throttle files. Preserve the stable concurrency/cache names.
- Hindi books remain Hindi-only. Keep both blind answer checks and the editorial publishing gate.
