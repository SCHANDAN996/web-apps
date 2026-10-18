# Rough Work workspace — 18 October 2026

Status: owner-requested plan only. Full-screen mode is an explicit requirement.

## Current implementation

The existing per-question board is a240px canvas with pen/eraser, three colors,
undo, clear confirmation and local saving. It has no redo, stroke-size control,
pages, zoom or full-screen workspace. Existing storage uses localStorage and
bounded stroke lists; trim() can evict old boards. Advanced storage must replace
silent eviction with visible capacity handling before it promises durable notebooks.

## Learner flow

- Keep a small inline Rough Work preview and a clear Expand/full-screen action.
- Full-screen uses the whole app content viewport. Collapse the ordinary header
  and bottom app navigation while working; retain a compact workspace toolbar.
- Workspace header: question number, saved/saving/error status and Close/minimize.
  Closing returns to the same question, selected answer and drawing position.
- Question reference is expandable. Portrait favors canvas with a compact question
  strip; landscape supports a question/canvas split. Neither requires leaving the
  workspace to read the question. Start with simple responsive proportions; add
  an adjustable divider only if its touch behavior tests well on small phones.
- Android Back first closes tool menus, then the workspace safely; it must not
  discard work, submit the question or leave the test unexpectedly.

## Tools, in priority order

1. Large canvas; pen and eraser; stroke thickness; existing colors; Undo and Redo.
2. Blank, ruled and square-grid paper; clear current page with confirmation.
3. Multiple rough pages for the same question, add/rename/switch, page thumbnails.
4. Zoom/pan with separate hand tool and two-finger navigation; a visible Reset view.
   Separate writing and page gestures so scrolling never accidentally draws.
5. Straight line, rectangle and circle tools plus selection/move when warranted.
6. PNG/PDF export of selected pages and a local rough-work library by question.

Stylus pressure and palm rejection are best-effort improvements on supported
devices, with a usable finger mode; do not promise unsupported hardware behavior.
OCR, AI solving and cloud rendering are later optional work, not required for a
fast offline writing surface. No answer assistance or extra calculator is added
to exam-mode mocks through the workspace.

## Data and performance

Use IndexedDB with versioned per-question/per-page vector strokes, stable page
coordinates, pen width and viewport state. Preserve page aspect rather than
stretching writing on rotation. Migrate existing boards transactionally, keep the
old data until verified, and support importing existing portable backups.

Autosave after strokes with small buffered writes; show a saved state only after
the write completes. Navigation/export waits for pending writes. Storage failures
offer retry/export and do not erase older notes silently. Page deletion should
be recoverable where practical; a full clear/reset remains explicit and scoped.

Drawing runs locally: batch input, simplify redundant points without visibly
changing writing, render only the active page/visible region, and bound canvas
pixel density/undo memory on inexpensive phones. Increasing canvas size alone
must not allocate an unbounded bitmap. No new font download or drawing framework
is required merely to achieve full-screen mode.

Rough work stays on the phone by default and joins portable backups. Optional
Google Drive backup uses the existing authorized app-file approach only after
its remaining restore flow is verified. No routine server upload is introduced.

The question Share action remains question/options/link only. Rough-work export
is a separate explicit action because handwriting can contain the answer and
personal notes; never attach the current solved/rough-work screen automatically.

## Mock behavior

Timer continues accurately while the workspace is open and remains visible.
Opening, minimizing, rotating or drawing never checks/submits an answer. Time-up
uses the normal mock completion path and preserves the board. Switching question
keeps each question's rough pages separate and restores them on return.

## Delivery stages and acceptance

First deliver a large/full-screen workspace, safe close/Back, question reference,
width control and Undo/Redo with a clear local-save status. Address current silent
storage eviction before expanding retained work. Then deliver IndexedDB migration,
multiple pages, pan/zoom and export. Shapes and optional advanced inputs come last.

Verify real finger/stylus input where available; portrait/landscape; English/Hindi;
light/dark/paper; keyboard and large-text access; writing versus page-scroll
gestures; reload/app restart; interrupted save; low storage; old backup migration;
undo/redo/clear cancellation; mock time-up; and correct question restoration.
Test on separate learner fixtures without resetting the owner's progress.
