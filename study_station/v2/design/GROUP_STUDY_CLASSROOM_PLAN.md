# Workspace, Group Study and Teacher Classroom

Date: 18 October 2026. Status: plan only; not implemented.
Extends ROUGH_WORK_WORKSPACE_PLAN.md, including full-screen mode.

## Product goal

Make the app the normal place for daily preparation through useful learning:
study a topic, solve questions, submit selected work, receive feedback, retry
mistakes and keep a notebook. Teacher and peer learning should complete this loop.
Use relevant, optional reminders; avoid artificial streak loss, forced invitations
or blocked personal exports as substitutes for educational value.

## Three clear objects

| Object | Purpose | What remains after class |
| --- | --- | --- |
| Workspace | Named notebook, pages, attached questions and drawings | Saved notebook |
| Group / class | Members, resources, assignments and discussion context | Ongoing study community |
| Session | A particular live teacher/peer meeting | Its saved material; live presence ends |

Prefer one group/class container with a type and scoped roles over duplicated
membership systems. A person may teach one class and study in another.

## App placement and screens

Home secondary tools: Workspace & Group Study. Practice/questions: Open in
workspace. Reading and personal practice remain the first Home actions.

The hub offers My Workspaces, Study Groups and My Classes. Workspaces can filter
private/shared/linked notebooks. Create and Join by link/code are clear actions;
avoid adding several new bottom-navigation tabs.

Screens: workspace library; full-screen editor; group/class overview; assignment;
student submission; teacher review; live room; access controls; account sign-up
and invitation return. Each workspace supports a name, multiple pages, thumbnail,
search, rename, copy and recoverable deletion.

## Daily learning cycle

Teacher/organizer chooses a topic and questions from the existing bank, attaches
an explanation when needed and publishes a focused assignment. Learner solves
privately, including offline rough work, then explicitly submits selected pages
and answers. Teacher returns per-question/page feedback. Learner retries mistakes
and keeps the notebook. The group overview shows the next useful task.

Do not automatically expose all personal practice or rough work. Personal mocks
remain separate from collaborative practice. Classroom practice is not advertised
as a proctored exam simply because answers are hidden in the normal interface.

## Peer Group Study

- Named group with a study goal/topic, members and optional scheduled sessions.
- Share chosen questions/resources and contribute to a common practice task.
- Each member has a private notebook; shared-board editing requires permission.
- Timed group practice can be followed by solution discussion; classmates' answers
  are not broadcast during an individual attempt.
- Doubts attach to a question/page instead of disappearing in a noisy global feed.
- Organizer can remove/mute disruption and revoke invitation links.

## One teacher, many students

Teacher creates a class and shares an invitation. Students sign up in the app,
explicitly join and open the session. The first live board is teacher-controlled;
students follow its pages/drawings while solving in private linked child boards.
Raise hand / Request help prevents everyone writing or speaking at once.

Teacher sees only work explicitly submitted or intentionally shared with the
class, gives annotations and returns feedback. Teacher can grant writing or
co-teacher permissions. Viewer access never implies editor/teacher access.

Live delivery starts with board/page updates, focused questions and connection
status. Teacher audio is a later separately tested option without requiring
everyone's camera. Voice/video/recording need their own network, permission,
cost and on/off controls. A silent shared board is not a full video classroom.

## Confirmed sharing rule and access

Anyone holding a shared-workspace link may view after app sign-up. No owner
approval is required for viewing that intentionally shared workspace. Editing is
granted separately. Forwarded links also work for signed-up viewers until revoked.

Opening a link does not silently join a group, reveal the student roster or grant
access to private submissions. Membership uses an explicit Join action. Student
sees own work; teacher/authorized reviewers see submitted work; ordinary viewers
see only resources intentionally shared with them.

Owner can revoke/rotate links. Server checks every content/live operation; there
is no private thumbnail/canvas in pre-sign-up previews. Installation alone is not
authentication. Do not promise to erase copies already exported by a viewer.

Without the app, show an install/sign-up path and return code. Preserve invitation
through sign-in and allow reopening the original link after installation. Automatic
post-install return is a separate test case, not assumed from ordinary App Links.

## Linked versus copied work

Link follows the teacher/source workspace with source ownership and sync status
visible. Student's private practice layer remains separate. Copy creates an
independent notebook without later source updates. Stable source/page/question
IDs survive renames. Source changes must not overwrite private student pages.

Revoked/deleted/disconnected sources display honest status. Later co-editing needs
stroke ownership and scoped Undo; never replace the entire board last-write-wins.

## Accounts, offline operation and server load

Current app has device identity/recovery sync, not complete accounts, class
membership or classrooms. Build real sign-in, server-validated sessions, ownership
and explicit linking of existing learner data first. Do not reset guest progress
or silently merge two learners. Drive consent stays separate from sign-in.

Private notebooks stay in IndexedDB. Only explicitly shared work, submissions,
assignments and live sessions require server state. Downloaded practice/local
writing works offline. Saved on phone, Waiting to send, Submitted and Disconnected
must be distinct statuses. Export/navigation waits for pending local writes.

Live sync sends compact incremental strokes/page events with snapshots, sequence
IDs, duplicate protection and reconnect recovery. Start with one teacher writing
and many viewers; do not continuously stream full-screen images. Collaboration
has real storage/fan-out costs. Measure pilot classes before defining supported
class size or paid plans; no invented cost, scale or release-date claims.

## Implementation stages

1. Reliable personal workspaces: full-screen, names/pages, Undo/Redo, safe migration,
   autosave/export and no silent deletion of old work.
2. Accounts/permissions: safe guest linking, sign-up return, shared view links,
   revocation and explicit group joining.
3. Useful group/class MVP: shared questions/resources, assignments, private
   submissions, teacher feedback and retry. This is the first complete learning loop.
4. Live teacher sessions: board/page following, linked personal work, raise hand,
   reconnects, then teacher audio after separate testing.
5. Advanced collaboration: co-teachers, student writing grants, simultaneous
   editing, optional voice/video/recording and further class reporting.

Each stage must be useful on its own before the next expands complexity.

## Pilot and release checks

Use a small real teacher/group pilot: can people create/join without help, finish
an assignment, submit work, get feedback and improve a retry? Observe purposeful
repeat study and teacher reuse rather than screen time alone. Class/task reminders
remain learner-controlled; personal work remains exportable.

Verify multiple named boards, full-screen Back, drawing/scroll gestures, account
switching, install/sign-in return, viewer/editor isolation, private submissions,
forwarded/revoked links, duplicate submissions, deadlines/late work during outages,
teacher/student reconnect, concurrent strokes/Undo when introduced, personal mock
separation, Hindi/English and low-end devices. Test measured fan-out before claiming
class sizes; test real audio/video/recording before marketing those features.
