# Core input artifact sender

`BrowserBridgeArtifactSender.send` accepts only server-provided immutable bytes
and an exact typed input/upload_file binding, never a file path or a client
artifact claim. It bounds transfers to 25 MiB each, 16 concurrent transfers and
100 MiB aggregate. Ordered 192 KiB frames each require their exact ACK within
eight seconds; the whole process-owned transfer expires within two minutes.

ACK reception is installed in the restricted application dispatcher and matches
the exact principal object, SID, generation, context/session/turn/action/op/artifact,
phase, byte offset, chunk position and final digest descriptor. Forged, duplicate,
stale and cross-route ACKs cannot advance the transfer. Send and settlement
recheck the application authorizer. Caller cancellation does not cancel an
owned transfer; exact route retirement and owner shutdown do. No auto retry or
remote upload success is inferred from transport completion.

Application authorization requires the current broker upload operation, exact
live turn and the server-owned source/site preflight. The caller must await
`broker.wait_dispatched(ticket)` before staging: successful socket dispatch is
ordering evidence, not operation completion. Native retains the corresponding
operation until its exact artifact is complete; the extension independently
requires one-use site-sharing consent before its concrete file-input effect.
Transport completion alone never authorizes that effect. Full artifact readiness
requires this source registry and consumer composition, not output screenshots.
