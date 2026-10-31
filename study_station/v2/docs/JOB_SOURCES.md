# Additional official job sources — 31 October 2026

The existing jobs schedule reads `app/jobs/sources.py`; no extra cron or Telegram sender is needed.

| Source ID | Official listing | Parser / bound |
|---|---|---|
| `sbi` | https://sbi.bank.in/web/careers/current-openings | Advertisement accordions, maximum 20; PDF notices only, not Apply/Biodata links |
| `railway-board` | https://rb.indianrailways.gov.in/show-irPersonnel/preview/20 | VC table, maximum 20; organisation, role, posts and closing date remain separate |
| `iim-kozhikode` | https://webapps.iimk.ac.in/jobportal/vacancy | Existing HTML listing parser, maximum 20 |
| `icar-iimr` | https://iimr.res.in/events/vacancy | Existing HTML listing parser, maximum 10 |

These four listings were fetched using the existing identifying, rate-limited, robots-aware Fetcher. Trimmed public HTML is retained in test fixtures. Listing redirects must remain on approved official domains. Unrelated application portals do not become trusted merely by being linked.

SBI is explicitly refreshable: its stable advertisement IDs are reprocessed within the existing per-source run limit, updating deadline extensions without duplicating SeenItem records or changing first-seen history. Other sources retain their existing new-URL behaviour. Explicit SBI header deadlines override an older PDF/application range. Relative Railway deadlines such as “30 days from issue” remain unknown instead of being guessed.

Run a bounded check before an initial import:

```
python -m app.jobs run --only sbi,railway-board,iim-kozhikode,icar-iimr --max-new 5
python -m app.jobs health
python -m app.jobs summary
```

The initial import is bounded separately from future scheduled runs. Multiple sources can overlap; compare verified jobs and merges, not just raw notice counts. Research/deputation posts are not automatically general-entry exam vacancies. Failed sites remain visible in source health; do not disable TLS, robots checks or private-network protections to make them pass.

DRDO timed out from the server; the probed IIM Lucknow and NABARD routes returned 404/error-page results. Those unverified routes were not registered. CWC and GRSE additional portal trust remains a separate task.
