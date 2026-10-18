# Workspace and classroom implementation — 2026-10-18

Implemented:
- Home: four primary illustrated cards above the existing study cards: Workspace, Group study, Teacher classroom, Shared workspaces. Two-column layout and existing themes.
- Local named notebooks, pages, fullscreen canvas, pen/eraser/shapes, width/color, undo/redo, pan/zoom, paper styles, recoverable deletion, references, JSON import/export, PNG and raster-in-SVG, system print-to-PDF.
- Existing rough drawings retained; guest-to-account copying is explicit. Private notebooks are isolated by account scope; shared work requires server authentication.
- Username/password signup and secure cookie sessions, persistent group/class membership and roles, expiring sessions and database rate limits.
- Explicit published notebook snapshots, signup-required high-entropy share links, revoke, independent copies, source-linked notebooks and separately granted editing.
- Assignments, selected notebook/answer submissions, private teacher feedback and repeat submissions; question-focused discussion.
- Teacher live board, durable sequenced events, replay, write permissions, raised hand, conflict retries and local pending event queue.
- Optional notebooks included in general backup exports/restores; older backups remain accepted, existing byte limits apply. A large notebook can also use its individual JSON export.

Verified:
- Browser: two separate accounts, invitation, assignment, private submission, feedback, teacher stroke received by student, raised hand received by teacher.
- Local notebook browser: legacy migration, pointer drawing, autosave, undo/redo, pages, isolation, trash/restore, backup restore and malformed import rejection.
- Offline study regression passed with zero server API requests during normal study, and all three themes.
- Android build and unit tests passed. Phone installation succeeded; fullscreen notebook and classroom sign-in screen passed before the final Home-card promotion; original study state unchanged.
- Final Home cards checked at mobile browser sizes. Final repeated phone navigation/test command rejected by automatic approval review with generic blocked-by-policy reason; do not claim this acceptance completed.
- Windows symlink tests require privileges; both passed against this source in isolated Linux tests. The fixed-date current-affairs fixture now sets its reference date explicitly.

Limits and later stages:
- No voice/video calling, recording, object selection/move or pinch gestures. SVG embeds raster canvas. PDF uses the platform print dialog.
- Large classroom capacity and extended offline/reconnect behavior need load/device testing; no claim of production scale acceptance.
- Google Drive OAuth/restore acceptance and production signing/distribution remain separate existing release tasks. Notebook backup support does not assert Drive setup is complete.
- No learner progress was reset. No production test accounts or notifications were created during deployment.
