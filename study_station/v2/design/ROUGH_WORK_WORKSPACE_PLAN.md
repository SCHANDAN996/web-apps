# Rough Work workspace — 18 October 2026

Status: owner-requested plan only. Full-screen mode is an explicit requirement.

Group study and one-teacher/many-students teaching are expanded in
GROUP_STUDY_CLASSROOM_PLAN.md, which builds on this workspace foundation.

## App-wide workspaces and linked teaching — owner extension

Confirmed sharing rule: anyone holding the link may view after app sign-up.
Viewing does not grant editing. This is a product plan, not an existing feature.

### Placement and workspace library

Add a Workspace entry to Home's secondary tools and Practice tools, and keep the
per-question Rough Work entry. The per-question entry can create a new workspace
or attach the question to an existing named workspace. The app-wide entry works
without choosing a bank question, including solving a question from a book or
elsewhere. Keep the main study navigation uncluttered; no sixth bottom tab by default.

The library has My workspaces, Shared with me and Linked workspaces. Each workspace
has an owner, stable ID, user-chosen name, thumbnail, optional subject, pages and
last-edited time. Support create/rename/search/duplicate/recoverable delete and
several separately named workspaces such as Algebra practice and Railway class.
One workspace can reference multiple question IDs; deleting a question reference
does not silently delete its written pages. Names need not be globally unique.

### Sharing and account flow

Private workspaces remain phone-local by default. Sharing explicitly publishes
only that workspace's selected content to the sync service. It never publishes
all local notebooks, progress, account details or unrelated rough work.

Opening a workspace link before installation shows only an install/sign-in route
and workspace code, not private canvas/thumbnail/page content. After installation
and sign-up, the learner reopens the original link or enters the code. Do not
promise automatic deferred post-install opening until tested. App Links for `/w/`
will need their own validated routing in addition to existing question links.

The current app uses device/recovery-code identity, not a complete account and
workspace membership system. Real sign-in, server-validated sessions and explicit
linking of local data to an account are prerequisites. Keep Google Drive backup
consent separate from sign-in. Do not reset or merge two learners silently.

A high-entropy, unlisted share link grants authenticated viewers access. Treat it
as forwardable: anyone who receives it can join under the owner's chosen rule.
The owner may revoke/rotate the link or stop sharing. Permissions are owner,
explicit editor and viewer, enforced on every API and live-room operation.
No content/answer is embedded in URL previews or pre-auth page responses. App
installation alone is not authentication or a guarantee against copying content.

### Linked Workspace and teaching

Offer two distinct actions:

- Make a copy: an independent workspace; later teacher edits do not alter it.
- Link workspace: follow the source workspace's updates while preserving the
  source owner's authority. Show source/connection status and last synchronized time.

For a class, the teacher owns a shared source board and students join from its
link after sign-up. The teacher's drawing/page changes can stream live to viewers.
Each student can maintain a private personal practice layer or linked child board;
it does not overwrite the teacher board. Owner-granted co-editors may write on a
shared board, with separate stroke ownership so one person's undo does not erase
another person's work. Learners can optionally send their own work for discussion.

Start with live drawing, page-following, text notes and a connection indicator.
Voice/video calls and recording are separate later work with explicit controls,
consent and cost planning; a live board alone is not presented as a full video class.
Source deletion, sharing revocation and loss of access produce clear unavailable
states; do not leave a linked board silently displaying itself as up to date.

### Server load and staged implementation

Local named notebooks and offline drawing use IndexedDB. Only explicitly shared
or linked/live workspaces require server state: account/membership, share tokens,
compact stroke/page snapshots and changes. Send incremental strokes, not continuous
screen images; batch/save changes, bound room/asset sizes and handle reconnects.
Do not promise zero server cost for live collaboration or silent Drive syncing.
Offline edits need a queued/retry/conflict policy and honest sync status.

Implementation order:

1. Full-screen drawing, named local workspace library, migration and reliable save.
2. Real sign-up/account ownership, shared snapshots and authenticated view links.
3. Linked source/child workspaces, live teacher updates and reconnect handling.
4. Explicit co-editing and advanced classroom features, then optional voice/video.

Acceptance includes multiple named boards, per-question attachment and reopening,
account switches, sign-up/install return, unauthenticated denial, viewer/edit
boundaries, forwarded/revoked links, independent copy versus linked updates,
offline/reconnect, concurrent strokes/undo and retained local work on sync failure.

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
