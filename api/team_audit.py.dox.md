# Team audit API

- Authorized, CSRF-protected access to allowlisted operation metadata and native user/response transcript lines.
- `options` returns audit projects and current grants. The platform administrator controls grants and can query event metadata across projects. Members need a current per-project audit grant.
- `events` accepts project, account, context, time, action and cursor filters. Event pages exclude message or file contents.
- `transcript` requires the separate project body permission and records the authorization decision before serving a page. Platform administrators also need this grant. Team members' ordinary shared chat remains available under project membership.
- Verify grant, downgrade and revocation from independent authenticated sessions. Test both successful and refused transcript reads and absence of body data in event responses.
