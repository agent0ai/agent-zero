# Security review ledger

## WA-001: WhatsApp document filenames escape the media cache

- Reviewed: 2026-09-09. Baseline: `884e514a0ca81412975316381e405e28736f3424`; reported introduction: `80518f22`.
- Disposition: confirmed arbitrary overwrite at the bridge callback; fixed in the working tree. High severity demonstrated locally; critical root-code-execution impact remains conditional on live transport preserving the crafted filename and a later executable-file load.
- Affected users: operators who enable and pair the WhatsApp integration. It is disabled by default. The attacker is a remote WhatsApp sender, including one excluded by the configured allowlist; no Agent Zero login is required to reach the bridge callback.
- Boundary: remote document metadata selected a filesystem destination outside `tmp/whatsapp/media`. Python sender/group filtering ran only after persistence. This exceeds a remote sender's intended authority even when sending messages is permitted.

### Evidence

The real `messages.upsert` callback, with transport/HTTP dependencies stubbed, overwrote a pre-existing temporary sentinel using `../../../../../extensions/python/job_loop/sentinel.py`. The normal filename control succeeded without changing the sentinel. Before the fix, `node --test tests/test_whatsapp_bridge.mjs` failed with actual `POC_CONFIRMED`, expected `ORIGINAL`. The callback and filesystem write were production code; no application file was overwritten.

Current source anchors:

- `plugins/_whatsapp_integration/whatsapp-bridge/bridge.js`: inbound callback, pre-download authorization, basename/containment checks, exclusive writes, and message queue.
- `plugins/_whatsapp_integration/helpers/handler.py:66`: Python polling and dispatch authorization remain in place.
- `plugins/_whatsapp_integration/helpers/bridge_manager.py`: startup policy normalization, CLI propagation, and restart when policy changes.
- `helpers/modules.py:12`: module loading executes Python top-level code. The real loader was separately exercised with a harmless temporary module inside the framework runtime.

### Remediation and review

Reduce document names to a basename after normalizing separators, check the resolved cache-relative destination, and use exclusive creation (`wx`) for media writes. Authorize senders and groups before downloading. Reuse existing LID resolution, Python number normalization, startup APIs, and policy-change restart behavior. Keep Python dispatch checks. No dependencies, new service, or core-module changes.

The supplied patch was adjusted because joining a comma-delimited string iterates characters, and its JavaScript normalization differed from Python's leading-zero and JID handling. Normalization now occurs in the shared bridge manager, with matching sender handling in JavaScript.

Frdel review: aligned, medium confidence. Inspected actual diffs from `80518f22` (plugin ownership, shared number normalization, bridge lifecycle), `89d4b891` (centralized module loading), and `e138e33c` (plugin ownership and authorization contracts). The integration squash records a prior LID mismatch and the move to fresh Python dispatch checks; those checks are retained and the bridge uses resolved sender numbers. Embedded individual commits were unavailable locally, so the squash establishes accepted repository behavior rather than sole authorship of every line.

### Verification and limits

```bash
node --test tests/test_whatsapp_bridge.mjs
PYTHONPATH=. conda run --no-capture-output -n a0 python -m pytest -q tests/test_whatsapp_bridge_manager.py tests/test_whatsapp_number_utils.py tests/test_whatsapp_storage_paths.py
```

- Results: Node regression passed; 13 Python tests passed. Controls cover normal and traversal names, wrapped documents, disallowed senders/groups, mentions/replies, self-chat/dedicated behavior, LID resolution, normalized settings, and authorization propagation/restart.
- Named runtime: `localhost:32081`, container `42eb67c9f635`, verified bind mount from this repository to `/a0`. Node regression also passed there. Framework process uses `/opt/venv-a0/bin/python` as UID 0; a fresh framework interpreter verified startup normalization with a mocked launch and independently exercised the real module loader. No dependencies were installed.
- Runtime WhatsApp configuration was disabled and no running bridge appeared in the process listing. No pairing, messages, configuration changes, or service restart was performed.
- Live WhatsApp transport preservation of slash-containing filenames and a full overwrite-to-automatic-extension-reload chain were not tested. Existing extension caches can defer execution until a later load/restart. Root impact is bounded by container-accessible files and mounts; it does not imply host-root escape.
- Tests use isolated temporary directories and remove them afterward.


## TG-001: Unauthenticated Telegram webhook accepts forged updates

- Reviewed: 2026-09-09. Baseline: `0e9ef3727399d66c0a236ca543ae30b1969568c2`; reported introduction: `fc787ea`.
- Disposition: confirmed authentication bypass; fixed in the working tree. High severity demonstrated; critical impact is conditional on agent capabilities and deployment exposure. No deterministic root execution or host escape is claimed.
- Affected users: operators with a running Telegram bot and an attacker-reachable Agent Zero HTTP service. Polling bots and webhook bots with empty secrets were affected. The bundled bots list is empty by default.
- Boundary: unauthenticated HTTP JSON supplies Telegram identity and prompt text. The sender allowlist trusts that identity only after transport authentication; schema validation alone cannot establish Telegram origin.
- Current source: `api/webhook.py:38` within the plugin owns authentication before aiogram dispatch; `helpers/bot_manager.py:193` owns webhook registration. `helpers/handler.py:153` checks the body-derived identity and later calls `context.communicate`. Shared `helpers/api.py` intentionally bypasses session authentication and CSRF for this webhook handler.

### Evidence and patch review

`tests/test_telegram_webhook_security.py` exercises the real dynamic Flask API route, bot registry, aiogram schema, dispatcher, and router with a synthetic bot and harmless `POC_CONFIRMED` message. Before the patch, polling instances (including one with a matching secret) and an active webhook with an empty secret returned HTTP 200 instead of the asserted 403. Wrong/missing nonempty-secret controls rejected requests, and the matching-secret control dispatched the marker with the selected sender ID. After the patch all controls pass.

The patch requires webhook-active state, a nonempty stored secret, and constant-time header comparison before dispatch. Setup validates 32–256 ASCII letters, digits, underscores or hyphens and always sends the secret to Telegram. Polling reuses webhook removal, which revokes local authorization before awaiting Telegram. Documentation and settings copy now make the secret mandatory. Existing invalid configurations must be updated before bot startup.

Adjustments to the supplied patch: compare encoded bytes so a non-ASCII attacker header is rejected instead of raising `TypeError`; validate format during setup; exercise real Flask and aiogram instead of stubbing their behavior. Secret length is not a randomness guarantee; the README gives a cryptographic generation command. The report's predictable `bot_N` default is stale: current new-bot names begin empty; names still are identifiers rather than credentials.

### Verification and limits

```bash
docker exec -w /a0 -e PYTHONPATH=. agent-zero /opt/venv-a0/bin/python tests/test_telegram_webhook_security.py
PYTHONPATH=. conda run --no-capture-output -n a0 python -m pytest -q tests/test_telegram_webhook_security.py tests/test_telegram_heartbeat.py tests/test_telegram_media_delivery.py tests/test_telegram_sessions_picker.py tests/test_telegram_intermediate_response.py tests/test_telegram_error_ui.py
```

- Framework runtime: both new tests pass; host focused suite: 13 tests and 11 subtests pass. The framework run emitted an unclosed-event-loop ResourceWarning from the existing async environment.
- Container `agent-zero` serves `localhost:32081`, verified with this repository bind-mounted at `/a0`. No dependencies were installed.
- The Flask test uses an isolated in-process bot registry and a callback sink; it does not create a production AgentContext or invoke a model. Telegram registration/deletion calls in the lifecycle check are mocked.
- A live HTTP request for an unregistered synthetic bot returned 404. This establishes endpoint reachability, not successful authorized Telegram delivery.
- No configured bot credentials, names, chats, or private content are recorded. No real Telegram messages, agent commands, configuration changes, or service restart were performed.
- Full Telegram delivery and model/tool execution were not exercised. Existing same-mode secret changes still require a bot restart; automatic secret rotation is outside this patch.
