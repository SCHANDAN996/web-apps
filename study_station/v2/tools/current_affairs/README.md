# Current-affairs book chapters

The four `Chapter_*_Current_Affairs_*` chapters in `study_station/books` are built from **All India Radio
News** (newsonair.gov.in) reports only. This folder holds the fact bank and the tool that turns it into a
chapter. Refresh every few months.

| Chapter | kind |
|---|---|
| `10th_Level/GK/Foundation_10th_GK_WorldClass/Chapter_20_Current_Affairs_6M` | `10` |
| `12th_Level/GK/Intermediate_12th_GK_WorldClass/Chapter_20_Current_Affairs_6M` | `12` |
| `Graduation_Level/GK/Advanced_Graduation_GK_WorldClass/Chapter_20_Current_Affairs_6M` | `G6` |
| `Graduation_Level/GK/Advanced_Graduation_GK_WorldClass/Chapter_30_Current_Affairs_12M` | `G12` |

## Files
- `facts.tsv`: the fact bank. There is one MCQ per row, with columns `date level question answer wrong_options
  explanation air_link air_title`.
  - `level` is E/M/H.
  - `wrong_options` holds exactly 3 options, separated by `;`.
  - Every row must point to the AIR report it came from.
- `cabook.py`: the CLI (run it from `study_station/v2`).
- `cache/`: crawled AIR feeds. It is git-ignored; set `CA_CACHE` to use another folder.

## Refresh runbook
1. **Crawl:** `python tools/current_affairs/cabook.py crawl --from 2026-10-01`.
   - It reads the AIR category feeds (national, international, business, sports, miscellaneous).
   - It uses an identifying User-Agent and waits 2 s between pages.
2. **Find events:**
   - `cabook.py find "appointed|sworn in|Nobel|medal" --from …` lists matching reports.
   - `cabook.py read <link>` prints the full text of a report.
3. **Write facts:** add rows to `facts.tsv` by hand, taken only from the article text. Rules:
   - No facts from memory. These events are newer than any model's training.
   - The answer must not appear among the wrong options.
   - The explanation must stand on its own.
4. **Verify:** `cabook.py verify --model z-ai/glm-5.3 --from <date>`, then again with
   `--model nvidia/nemotron-3-ultra-550b-a55b`.
   - Each MCQ is checked against its own article.
   - Fix or drop every row that either model flags, after reading the article yourself.
5. **Sets:** `cabook.py sets G6 <chapter>`.
   - Writes 6 English sets of 25 questions, with answers balanced.
   - Each question gets a `Source: All India Radio News, <date> (<link>)` line.
6. **Hindi sets:** translate each set with `bookgen.translate_set`.
   - For long sets use `NVIDIA_MODEL=nvidia/nemotron-3-ultra-550b-a55b`.
   - Check each set with `bookgen._set_problem(text, n)`.
7. **Prose:** `cabook.py prose G6 <chapter>`.
   - Writes `Content_en`, `Key_Facts_en`, `Flashcards_en`, `PYQ_en` and `Mind_Map`.
   - Update `Feynman_en` and `Memory_Hooks_en` by hand.
   - Translate the `_en` sections into `_hi`.
8. **Review:** `cabook.py review <chapter>` is report-only.
   - The reviewer is told not to flag facts from memory.
   - Accept only flags you can confirm against the AIR article.
9. **Check and commit:** `python -m app.bookcheck ../books/<Level>/GK/<Book>` must say OK.
   - Update `as_of` and the notes in `chapter.json`.
   - Commit each chapter on its own.

Wrong facts here cost students marks. When in doubt, leave the fact out.
