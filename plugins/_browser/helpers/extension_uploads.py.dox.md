# Context-owned Browser upload sources

The user_message_ui hook records at most32 actual uploaded-file references for
its exact context, with an immutable byte count, SHA-256, MIME and filesystem
identity. No bytes or server path enter the extension/UI projection. Registry
records live in context data, never inherited from another chat. No tool call
may register a source, choose arbitrary server files, or use an unrecorded path.
Earlier attachments without evidence must be attached again. Ordinary chat
delivery is independent of optional Browser source capture.

Read only beneath Core's configured usr/uploads root, opening each child from
retained directory descriptors with no-follow flags. Reject symlink/hardlink
aliases, non-regular/group-writable/foreign-owned files, traversal, changes,
empty or over25MiB input. Recheck filesystem identity around bounded reads and
compare the original hash before transport. PreparedUpload is server-owned,
non-persistent and hides paths from repr. Each call gets a new opaque artifactID.

The runtime sends only descriptor fields and the current semantic ref, waits
for exact browser.perform dispatch before ordered input frames, and cancels
failed transfers conservatively. Services retain a bounded exact-binding source
permit only during transfer. Native keeps verified bytes private until the
extension's separate once-only external-side-effect approval and file-field
validation. Staging on the companion is not consent to send bytes to a site.

Verification: tests/test_browser_extension_uploads.py (synthetic owned files)
plus runtime/broker/artifact integration fixtures. No live uploads or approvals.
