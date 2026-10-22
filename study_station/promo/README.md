# Promotion (Telegram channel + Shorts)

Plan and rules: `../PROMO_PLAN.md`. Code: `v2/app/promo/` (run from `study_station/v2`).

```
python -m app.promo telegram --slot quiz|trick|revision|weekly --dry-run   # what would be posted
python -m app.promo shorts --count 3 --out shorts_out                       # 3 videos + captions
```

- `posted.json` lists what has already gone out (Telegram ids, Shorts ids, today's polls for the evening
  answers). The workflows commit it back to the books branch. Do not edit it by hand.
- Only questions from bookcheck-OK chapters are used. Both the Hindi and English copies must pass the quality
  check and give the same answer, and the question must need no figure or passage.

## Fonts (`fonts/`)
- Noto Sans Devanagari and Noto Sans (Regular and Bold) from the Noto project.
- Both are under the SIL Open Font License 1.1; the licence texts are `fonts/OFL.txt` and `fonts/OFL-NotoSans.txt`.

## Audio
- The videos carry a silent AAC track, so there is no music licence to track.
- If music is added later, use only CC0 or royalty-free tracks and record each source and licence here.
