# Study Station — Design system (Material Design 3)

The UI follows **Google's Material Design 3 (Material You)** — the system Google's own Android apps use — adapted
for long study sessions on cheap Android phones. All values live as tokens in `app/static/css/app.css`; components
use only tokens. Any AI or developer changing the UI must follow this file and CLAUDE.md rule 5.

## Why these choices (research summary)
- **Material 3 colour system** — one seed colour → five tonal palettes → colour *roles* (primary, on-primary,
  primary-container, surface-container-lowest…highest, outline…). Roles guarantee readable pairs in light and
  dark, and surfaces separate by *tone* instead of heavy shadows. ([m3.material.io — how the colour system works](https://m3.material.io/styles/color/system/how-the-system-works))
- **Reading comfort** — off-white instead of pure white, near-black instead of pure black, body contrast ≥ 4.5:1;
  warm (cream/peach) backgrounds improved reading performance over cool ones in a CMU study → the book reader
  has a warm **"कागज़ / Paper"** page colour. ([CMU: Good background colors for readers](https://www.cs.cmu.edu/~jbigham/pubs/pdfs/2017/colors.pdf),
  [Harvard: use sufficient colour contrast](https://accessibility.huit.harvard.edu/use-sufficient-color-contrast))
- **Motion** — M3 emphasized easing and short durations (100–450 ms) make the app feel smooth without slowing
  it down. ([m3.material.io — motion](https://m3.material.io/styles/motion/overview/how-it-works))

## Colour
- Seed **#1A73E8 (Google Blue)** — blue = calm, focus, trust. Generated with Google's
  `@material/material-color-utilities` (v0.3.0): primary roles from `SchemeFidelity` (keeps the brand blue vivid),
  surfaces/secondary from `SchemeTonalSpot` (quiet neutrals), success (green) and warning (amber) harmonised to the
  seed; CBT "marked for review" stays purple because TCS iON uses purple.
- Light: page `surface #F9F9FF`, cards `surface-container-low #F3F3FA`, text `#1A1B20`. Dark: `#111318` / `#1A1B20` / `#E2E2E9`.
- Every text pair is ≥ 4.5:1 in both themes (checked when generated; outline is used only for borders, ≥ 3:1).
- Meaning: primary = main action/selection · secondary-container = selected chip/tab/option · success/error
  containers = right/wrong answer · warning = notices and streak. **Never** use colour alone — keep icons/text.
- Regenerate (if the seed ever changes): `tools/m3_palette.mjs` (SchemeFidelity + SchemeTonalSpot +
  Blend.harmonize, prints a contrast report) — never hand-pick hex values.

## Shape · type · space
- Corners: small 8 (chips, badges) · medium 12 (options, inputs) · large 16 (cards) · extra-large 28 (dialogs,
  hero) · full (buttons, nav indicator).
- Type: Noto Sans Devanagari (Android's system font — no download), M3 scale: body 16 · title 22 · headline 24/28;
  weights 400/500/600 (no 800). Hindi line-height 1.75; questions 18 px / 1.7.
- Space: 4-point scale (`--sp-*`); touch targets ≥ 44 px, buttons 48 px tall.

## Components (M3 equivalents)
| Ours | M3 component | Rule |
|---|---|---|
| `.btn-primary` | filled button | one per screen section, pill, 48 px |
| `.btn-secondary` | tonal button | secondary actions |
| `.btn-ghost` | text button | low-emphasis |
| `.chip` | filter chip | 8 px corners; selected = secondary-container |
| `.card` | filled card | tonal surface, no border/shadow |
| `.tabbar .tab` | navigation bar | 64×32 pill indicator behind the active icon |
| `.topbar` | small top app bar | surface; tints to surface-container when the page scrolls |
| `dialog` | dialog | 28 px corners, surface-container-high, level-2 shadow |
| `.toast` | snackbar | inverse surface |
| `.seg` | segmented button | reader page colour / text size, theme (System/Light/Dark) |
| `.search` | search bar | 56 px pill, surface-container-high, live filter |
| `.today-card` + `.ring` | — (home hero) | primary-container, goal ring 0–10, 7-day streak strip |
| `.plan .list-item` | list item with leading icon | today's plan: revise → 10 questions → continue chapter → current affairs |
| `.chips-scroll` | chip set (scrollable) | long filter lists stay one line with an edge fade |
| `.tile` | small filled card | entry points (books, current affairs) |
| `.cal`, `.bars`, `.spark` | — (data viz) | progress: 4-week activity, accuracy by subject, mock trend |

State layers: hover 8 %, pressed 10 % of the content colour (`color-mix`). Ripple on press (`static/js/app.js`).

## Motion
`--ease-emph (.2,0,0,1)` for most changes · `--ease-decel` for things entering · `--ease-accel` for leaving.
Durations `--dur-1..4` = 100/200/300/450 ms. Animate only `transform`/`opacity` (and colour). Everything respects
`prefers-reduced-motion` (ripple is skipped entirely).

## Navigation feel
- Page changes use the View Transitions API ("fade through": 90 ms out, 210 ms in); app bars keep their place.
- Haptics on answer: 12 ms tick for right, double buzz for wrong (Android only).
- Theme: System / Light / Dark in Settings, applied before paint by `static/js/theme.js`.

## Book reader
Page colour **सामान्य / कागज़ / रात** and text size **A− / A+** (85–150 %), remembered per device (localStorage).
Reading progress bar under the top bar; a chapter counts as read when its end is reached (✓ in the chapter list);
the home plan offers "Continue: <last chapter>".

## Checks before shipping a UI change
1. `pytest -q` and `node tests/e2e/flow.mjs` (no JS errors, no horizontal scroll).
2. Phone screenshots at 360 px in **light and dark**.
3. Long unbroken strings must wrap (`overflow-wrap: anywhere` on question/option/solution/book text) — otherwise
   phones zoom out and the fixed action bar moves off-screen.
