# Practice setup UI plan — 18 October 2026

Status: implemented, deployed and installed on 18 October 2026.

## Observed screen

Owner's connected phone is in landscape on offline Practice setup. The header and
heading have excessive vertical separation. Subject and topic are side by side,
but the question-count selector is a tiny native control. The fixed bottom
navigation obscures the Start button. The main task is choosing a topic and
starting practice; this action must be visible and reachable.

## Proposed hierarchy

1. Compact page heading: Practice / अभ्यास with a short purpose line only when
   space permits. Back remains a clear, accessible action.
2. One restrained glass-effect setup card. Label subject and topic clearly, show
   available question count as supporting text rather than unexplained parentheses.
3. Question quantity uses equally sized 10 / 20 / 50 choice chips with an explicit
   selected state and 44px minimum targets. Explain that this is session length;
   All Questions remains available for unrestricted browsing.
4. Primary Start practice action follows a concise selection summary. Disable it
   with a useful reason while no topic/content is available; show loading on tap
   and prevent duplicate session creation. Subject changes refresh topic/count
   without leaving a stale selection.
5. Secondary links: All Questions and Saved Questions. Keep these visually quieter
   than Start, and preserve selected topic when navigating where appropriate.
6. If an unfinished session exists, present Resume with its topic/progress. New
   session uses the existing safe replacement confirmation; no silent overwrite.

## Responsive behavior

Portrait: subject, topic, quantity, summary and Start in reading order. Landscape:
compact header/title and two-column subject/topic fields; quantity and Start share
a following row if there is room. Reduce decorative spacing, never shrink text
or tap targets to force a fit. All content remains scrollable with bottom padding
equal to the actual navigation/safe area so no control is covered. Avoid adding
another fixed toolbar. Keep enough scroll space when a keyboard or larger font
is active. Test rotation with selections intact and no accidental session start.

## Visual and related-screen consistency

Use existing light/dark/paper tokens, a subtle border/gradient and shallow shadow;
avoid expensive blur or decorative imagery that competes with the form. Hindi
labels need comfortable line height and wrapping; EN/HI indicates switch target
consistently. Focus and selected states must be visible without relying on color.
Use transform/opacity motion only, honoring reduced-motion preference.

Apply the same field/control language to Question Library and Saved Questions.
Keep practice question, feedback and result cards consistent with the structured
review already implemented. Preserve every learner's history and favorites.

## Acceptance and order

- First fix obscured Start and excessive landscape whitespace.
- Then implement setup card, quantity chips and selection summary.
- Then add secondary paths and unfinished-session entry using existing data.
- Verify Hindi/English, all three themes, portrait/landscape, larger text and
  narrow screens: no horizontal overflow, no covered action, complete scroll reach.
- Exercise subject/topic changes, empty content, loading/error/retry, 10/20/50,
  resume/replacement cancel, rotation and local/offline operation. No real learner
  answers or reset actions during phone visual QA.

Do not describe the quantity chips as removing the session-size choices; the
full question library is the separate path for any question.


## Acceptance completed

Custom subject/topic/difficulty/reset lists use searchable first-party dialogs,
selected checkmarks, 44px targets and keyboard/Escape/Android Back support.
Touch devices do not open the keyboard until search is requested. Header action
gaps reduced to4px while retaining44px targets. AI-generated/pending tags hidden
from learner views at owner's request; source/review metadata and admin review
remain unchanged. No question was automatically marked verified.

Resume now uses a short action, structured topic/progress and responsive grid.
Choice dialogs have a bottom gap, bounded internal scrolling and last-row
padding. On the phone at384x771, Resume is76px high and the last option is fully
inside the list with12px bottom spacing. Topic-list finger scrolling and page
scrolling after closing the dialog were verified. Current progress88answers,
4results and active10question session preserved. No answer/reset was submitted.
Original auto-rotate/user rotation settings restored.

Portrait/landscape, HI/EN, light/dark/paper, search/empty result, retry, active
resume/replacement cancellation and last-option visibility passed browser checks.
Full offline flow and targeted12 Python checks passed. Latest APK and production
assets updated; pre-change app backups retained. Public release/App Link external
launch acceptance remains tracked separately in the sharing plan.
