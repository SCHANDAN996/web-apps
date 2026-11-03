# Study Station — Play release handover

Prepared 2026-10-19. This folder is preparation, not evidence of upload, review approval or publication. Recheck against the exact signed artifact and deployed server before submitting declarations.

## App identity

| Field | Prepared value |
|---|---|
| App name | Study Station |
| Production package | `com.studystation.app` |
| Debug package, never upload | `com.studystation.app.debug` |
| Intended next version | 1.2.0 / code 3; verify bundle manifest |
| Category | Education (proposed) |
| Support | all.chandansingh@gmail.com |
| Website | https://studystation.ebookcart.in |
| Privacy URL | https://studystation.ebookcart.in/privacy |
| Deletion URL | https://studystation.ebookcart.in/delete-account |
| Console account observed by main agent | Tube algo, organization account, ID 7384073571952451725 |

The operator must verify its legal identity, support address, target audience, countries and pricing. An existing organization account does not by itself establish app eligibility or policy compliance. Do not apply new-personal-account testing rules automatically to this account.

## Release gates

- [ ] Create the Study Station app record. Review legal declarations with the account owner; this document does not authorize accepting agreements.
- [ ] Verify public privacy and deletion pages work without an account and match deployed behavior, including a concrete retention schedule and responsible operator identity.
- [ ] Audit production backup/log retention: repository `deploy/backup.sh` removes daily backups older than 14 days when run, but deployment snapshots, additional copies and actual cron execution are not verified here. Do not promise all copies expire in 14 days.
- [ ] Review final merged manifest, resolved SDK inventory and real network traffic. Source manifest currently requests only INTERNET; local documents use Android's user-selected document picker.
- [ ] Complete [data-safety.md](data-safety.md) against all shipped features and server behavior.
- [ ] Confirm intended ages and complete the IARC questionnaire accurately. Public/group workspaces and discussions require review of user-generated-content reporting, blocking, moderation and applicable child-safety obligations before broad release. Do not select Families compliance without evidence.
- [ ] Confirm rights to bundled books, questions, images and branding; keep official sources for recruitment notices. Do not imply government affiliation, guaranteed selection, or that all questions are reviewed/PYQs.
- [ ] Audit the enabled AI feature path and provider disclosures. Do not advertise AI availability if the production key/budget/features are disabled.
- [ ] Use the correct public Web OAuth client ID in server and native config; secret stays server-side. Verify Android OAuth clients for production package and the actual signing certificates.
- [ ] Create and securely back up the upload key outside Git; verify signed AAB, target/min SDK, version and certificate. Follow `../../android/PLAY_RELEASE.md`.
- [ ] Configure Play App Signing; register its SHA-1 for Google sign-in and SHA-256 for domain App Links. Upload certificate and Play signing certificate are distinct.
- [ ] Rebuild offline pack/shell after final assets, then run required backend, native and browser checks. Phone unavailable at preparation time: native Google chooser, cancel, sign-out, re-open, links and real Play-delivered installation remain acceptance gates.
- [ ] Test account deletion only on an isolated disposable account. Verify owned-class cascading deletion disclosure and that unrelated users' independent work survives.
- [ ] Capture real app screenshots with fresh test content; no private learner records, fake ranks or fabricated outcomes. Supply 512×512 store icon and 1024×500 feature graphic using the selected logo. Check current Console asset validation before upload.
- [ ] Provide reviewer access instructions and any test-only credentials through Console's private App access field, never this repository. Verify access without the developer's personal Google account or OTP.
- [ ] Prepare internal-test release first; review any Console warnings. Complete all dashboard tasks before production submission. Public rollout requires the owner's final review.

## Reviewer navigation draft

Open Home → books/practice/mock sections for independent study. Open Workspace for drawing and saved notebooks. Open Classroom to create/sign in to an account and access groups, shared work and assignments. Account features need internet; bundled study content has offline paths. Settings and Classroom link to Privacy and Delete account. A new account has no pre-existing shared content; provide a safe invitation or disposable review group if needed.

Do not provide real teacher/student accounts. Never ask a reviewer to delete a real account; a disposable review account may be recreated after destructive testing. Account deletion leaves local files/Drive backups separate and can make account-scoped local notebooks inaccessible: export first.

## Official references checked for this preparation

- [Create and set up your app](https://support.google.com/googleplay/android-developer/answer/9859152?hl=en)
- [Data safety declarations](https://support.google.com/googleplay/android-developer/answer/10787469?hl=en)
- [Account deletion requirements](https://support.google.com/googleplay/android-developer/answer/13327111?hl=en)

Console requirements can change; these are review sources, not a statement that this app already meets every requirement.
