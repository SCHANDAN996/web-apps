---
description: Complete or repair Study Station books — ss-book-writer agents in parallel, one chapter each
argument-hint: "[book or chapter path, e.g. books/10th_Level/GK/Foundation_10th_GK_WorldClass]"
---
Run this as the **main agent** (sub-agents cannot start other agents).

Target: $ARGUMENTS (empty = the book with the highest priority in `study_station/v2/AGENTS.md` → "Books").

1. `cd study_station/v2 && python -m app.bookcheck <book dir>` — list chapters as OK / TODO / FIX.
2. Pick a finished, clean chapter of the same book (or the closest book) as GOLD for format.
3. Launch one **ss-book-writer** per TODO/FIX chapter **in parallel** (up to 7 at a time; chapters are separate
   folders, so they never collide). Brief each with: CHAPTER path, MODE (write/fix), GOLD path, and the list of
   todo/problems bookcheck printed for that chapter.
4. As each finishes: re-run bookcheck on its chapter yourself, read a sample (1 content section + 5 random MCQs
   in both languages) and check facts you doubt. Send it back with reasons if it is not OK.
5. Commit verified chapters (one commit per batch: `Books: <book> chapters NN–MM`), never DB files.
6. Chapters about current affairs come from the live AIR/PIB pipeline (`/ca`), not from the book writer.
7. Report in Hindi: chapters finished, still open, doubts that need a human.
