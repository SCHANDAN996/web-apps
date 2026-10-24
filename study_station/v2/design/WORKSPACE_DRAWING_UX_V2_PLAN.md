# Drawing Workspace v2 — plan, 18 October 2026

Status: drawing editor, compact icon controls, Help, pinch/pan and marker/highlighter/selection implemented, deployed and installed on18October2026. Image/PDF annotation remains a later extension. See implementation/verification notes below.
This supersedes drawing UI/gesture parts of ROUGH_WORK_WORKSPACE_PLAN.md. Existing named workspaces, account isolation, classroom permissions and local-first storage remain requirements.

## Goal and reference
Make rough work feel immediate: most of the screen is usable paper, common tools need one tap, navigation never adds accidental ink, and help is available without leaving the notebook.
Google Keep reference: https://support.google.com/keep/answer/6395656?co=GENIE.Platform%3DAndroid&hl=en
Its documented drawing tools include pen, marker, highlighter, eraser and selection, with tool color/size controls. Two-finger pan/zoom below is our requested interaction specification, not a claim about Keep's gesture implementation.

## Findings in current source and reproduction
- workspace.js tracks a single pointer and ignores a second pointer; pinch is absent. pointercancel currently calls finish and can save unfinished ink.
- The wrapping text toolbar occupies up to150px, has its own vertical scroll, and competes with header, reference and page tabs.
- workspace-stage min-height100px combined with nonshrinking controls exceeds a short viewport. Isolated Chromium with actual Hindi copy and animations settled:390x844 has no stage overflow;844x330 has stage bottom361.59px, exceeding viewport by31.59px. This reproduces short landscape clipping; it does not prove every portrait phone clips.
- Canvas is900x1200; only its on-screen size changes. Pan/zoom must not rewrite saved coordinates or change exports.
- Current paper ruling/grid is CSS-only and absent from canvas export. Rendering should be consistent across the editor, shared snapshots and exported pages.

## Screen and controls
Portrait layout:
1. Compact top bar: Back, short notebook title, save-state indicator, Undo, Redo, ? Help, More. Adapt by moving Redo into secondary tools on narrow screens; never wrap the top bar into several lines.
2. Collapsed question/reference chip and compact page counter, e.g.2/5. Open full question or page picker only on request.
3. Canvas takes all remaining space. It is a viewport on the saved page, not a vertically oversized dialog.
4. Compact primary tool dock: pen, eraser, selection, hand/pan, current color, More. Initial release may hide selection until its complete behavior is implemented. Tool options open in a small popover/sheet; they do not permanently consume drawing space.

Use local SVG icons, matching app styling; avoid emoji as control icons. Common controls can be icons alone with localized accessible names, tooltips/long-press labels and clear selected state. Keep notebook title, save status and page count readable. Touch targets at least44px, preferably48px; icon artwork20–24px.
Move paper style, shapes, add/rename page, clear page, attach question, import/export and sharing into labeled menus. Confirmation for destructive clear/delete. No hidden destructive long-press action.
Landscape uses a compact side tool rail or one-line dock so paper stays usable. No nested vertically scrolling toolbar. Help and Close/Back always reachable.

## Gesture rules
- One finger draws with the chosen drawing tool. Hand mode makes one finger pan instead.
- Two fingers always pan/zoom, regardless of selected drawing tool. Pinch apart enlarges; pinch together reduces; moving both fingers translates the view.
- Zoom range proposed50–400%, with a visible percentage and Fit page / Reset view. Buttons provide an accessible alternative to gestures.
- Pinch is anchored to the point under the fingers: content must not jump to the canvas origin.
- When the second finger arrives, discard only the first finger's uncommitted preview stroke. Do not Undo an existing saved stroke.
- After a gesture, drawing stays paused until every gesture finger lifts. A remaining finger must not suddenly draw.
- Third finger, pointercancel, app backgrounding and lost pointer capture end/cancel the transient gesture safely; no phantom dot, connecting line or edge streak.
- Stylus writes when supported; touch fingers navigate. Offer a clear finger-drawing setting. Do not claim hardware palm rejection on devices that cannot provide it.
- View movement is not a document edit: no autosave churn or Undo entry for pinch/pan. Per-page viewport state is separate from stroke data.
- Rotation retains the content center and scale where possible; Fit page remains one tap away. Panning is bounded with useful page margins so the paper cannot be lost off-screen.

Implementation approach: gesture state machine(idle/drawing/panning/pinching/await-all-up), Map of pointer IDs, uniform view transform and inverse transform for page-space points. Use requestAnimationFrame to combine visual updates; avoid repainting all old strokes on each pointer sample. Keep pen width in document units while zooming. Handle off-page movement by clipping segments, not clamping every outside sample to the page edge.

## Drawing tool improvements
First milestone: existing pen/eraser/shapes with smoother stroke sampling, dependable Undo/Redo, presets for colors/width, compact controls, two-finger gestures and help.
Second milestone: marker, translucent highlighter, stroke selection and move/resize/delete/copy. Selection changes are one undoable action; cancelled selection must not modify data. Eraser behavior must be explicit: point eraser vs whole-stroke eraser; clearing a page remains separate.
Image/PDF annotation can be a later extension with explicit import, page count/file-size limits and offline rendering. No image upload by default.

New tools require a versioned schema: stable stroke IDs, tool type, width/color/opacity and selection transforms. Update store validation, legacy migration, backend snapshot/live validation, classroom renderer and every backup/export reader together. Preserve unknown/new-format backups safely; do not silently remove unsupported strokes. Existing notebooks remain reopenable; retain a recoverable migration source.

## ? How to use
Help opens a scrollable in-app sheet/dialog with short illustrations and Hindi/English instructions:
1. Write with one finger or pen; tap a tool to select it.
2. Tap the selected pen/color control for thickness and colors.
3. Move with two fingers; spread/pinch them to zoom.
4. Use Hand mode for one-finger movement; Fit page restores the page view.
5. Undo/Redo changes writing; pan/zoom does not erase anything.
6. Add a page or switch pages from the page counter.
7. Work is saved on this device; Saving/Saved/Failed have distinct states. Never tell users to close before an outstanding save completes.
8. Sharing/submitting is explicit; private writing is not automatically sent to a group/teacher.
9. Back closes the editor safely; clear/delete asks first. Export backup is the recovery path for a storage failure.
Only show rules for features actually implemented in that release. Include a small first-use hint, dismissible and reopenable via ?. Never block writing with a repeated tutorial.

## Bottom clipping fix
- Editor height follows the actual available viewport, including keyboard and rotation; stage flexes with min-height0.
- Avoid fixed min-height requirements that force content outside the editor. Anchor the tool dock inside the editor layout, not below it.
- Check visualViewport changes for sheets/keyboards. Name/rename/help sheets scroll internally and keep action buttons visible above the keyboard.
- Android already consumes system bar/cutout/IME insets in MainActivity.padForSystemBars. Apply safe-area padding only where not already consumed; do not subtract/add it twice.
- Fullscreen editor should not inherit app tabbar/body-bottom padding or generic dialog scaling that moves controls outside the viewport. Preserve keyboard focus and Android Back behavior.
- The bottom of a long page must remain reachable by pan; there must be no dead strip that cannot receive drawing input.

## Verification and release order
A. Layout/icons/help and clipping fix; verify360x640,390x844,412x915 and844x330, all three themes, HI/EN, keyboard and rotation.
B. Gesture engine; actual two-touch sequences on the connected phone, including second finger during a stroke, one finger lifting early, interruptions and repeated zoom/pan. Compare saved strokes byte-for-byte before/after view-only gestures.
C. Tool/schema improvements; migration, round-trip backup, shared snapshots, exported paper/opacity/shapes and classroom permission checks.
D. Build, install, final phone acceptance, then server/package update with backups. Existing authorization covers these actions when implementation is requested; this document does not claim they are implemented now.

Acceptance:
- Main drawing controls, ? and Back remain inside the usable viewport; last help/menu action reachable.
- Two-finger gestures never add ink; one-finger writing resumes only after all gesture fingers lift.
- A mark remains under the expected finger position after zoom; repeated zoom cycles do not distort strokes.
- Bottom edge remains reachable in both orientations; operating-system navigation gestures remain usable.
- Saved notebook, selected question, account ownership and learner progress survive reopen/rotation; failed saves do not display Saved.
- Drawing remains responsive on the target phone with a representative large existing notebook; report observed performance rather than inventing a target benchmark result.


## Implementation and verification
Implemented workspace-editor.js, workspace-gestures.js and shared workspace-renderer.js. Local/server validation and classroom rendering support additive opacity, marker/highlighter and stroke IDs; existing version1 notebooks remain accepted. Paper is rendered into PNG/SVG exports, and erasing clears only ink. Selection supports box selection, move, resize, duplicate and delete with page-specific Undo/Redo.

Full Python suite:249 passed on Windows; two existing symlink tests require Windows privileges and both pass in isolated Linux with this source. Browser acceptance covers HI/EN, three themes,360x640/390x844/412x915/844x330, real two-touch sequences, no phantom ink, autosave, selection actions, Help/menu reachability and actual PNG/SVG output pixels. Offline regression retains zero API requests during ordinary study. Android build and unit tests passed.

Connected Android acceptance: actual two-touch zoom reached180%, gesture-only saved strokes unchanged; eight-rule Help opened; portrait and landscape controls stayed inside available viewport; last More export option reachable. Temporary test notebook removed, original learner progress unchanged, original rotation settings restored. Source and live service backed up before deployment.

Limits: no hardware palm-rejection claim; stylus behavior conservatively separates inputs. SVG embeds a raster image. PDF still uses the platform print path and native print acceptance is not established here. Image/PDF imports and very large notebook performance/load tests remain later work. Private notebooks remain local unless explicitly shared or backed up.
