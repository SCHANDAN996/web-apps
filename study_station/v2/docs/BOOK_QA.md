# Continuous book QA

Writing and QA share one autopilot, one chapter claim, the existing four-key pool and its account-wide rate limiter. Keys 1/2 remain disabled. Twelve total workers remain: three prefer QA and nine prefer writing; idle workers borrow the other queue. This is not twelve concurrent API requests. No additional model family is enabled.

## Queue and evidence

`--continuous-qa --qa-workers 3 --qa-checks 4` enables incremental QA for structurally complete, committed chapters in `books/QUEUE.txt`. The new Hindi and Computer books retain priority; older books are also covered. Explicit MANUAL entries and dynamic current-affairs chapters are excluded. A chapter claimed for writing cannot be claimed for QA at the same time.

`app.bookqa` keeps chapter-local `QA.json` receipts tied to the actual input hashes and policy version. Partial successes and blockers are committed after each bounded slice, even when other checks remain. A changed input invalidates only checks that depend on it. Existing bookcheck-OK status or a historical commit does not count as a current QA receipt. Existing chapters without receipts enter the QA queue; this may re-check previously approved answers once to establish a durable baseline.

The plan includes blind answer verification in each available language, full solution review, translation meaning/answer parity when applicable, non-practice editorial review, consistency and duplicate checks, source grounding and syllabus coverage. Missing official evidence remains `needs_reference`; it must never become an automatic pass. AI passes are not human publication approval. Inspect the ledger for exact current findings and the status page for aggregate progress.

## Operation

From study_station/v2:

```sh
python -m app.bookqa --chapter ../books/<level>/<subject>/<book>/Chapter_01_topic --max-checks 4
python tools/book_autopilot.py --workers 12 --continuous-qa --qa-workers 3 --qa-checks 4
```

The normal workflow stops starting new chapter slices after its time budget, saves unfinished work, and dispatches a successor. Failed API work has a cooldown and per-run failure cap; reference-blocked checks wait for changed evidence. Do not start a separate workflow with its own rate state for QA.

## Remaining evidence and publication work

Source validation requires actual retrieved official excerpts and claim-to-evidence comparison, not a model's memory or a Source label. Explicitly cited official HTML/text and small text-based PDFs are fetched with site-policy checks and bounded size/page limits. Site restrictions, scanned PDFs and unsupported formats remain explicit blockers. Syllabus coverage needs an official syllabus document. Unresolved contradictions must remain visible; repeated agreement from one model does not settle them.

UI/reader/DB integration, Devanagari font rendering, PDF pagination, export, download and authorization checks are separate local/browser tests. Final human proofreading and release approval remain separate from continuous AI QA. This workflow does not automatically publish a finished ebook or change chapter metadata to human-reviewed.
