# Agent Editor

Agent Editor provides the deterministic Easy modal and Advanced workspace for
Agent Zero profiles. It reads the existing layered profile architecture and
writes only sparse user overrides under `usr/agents/<profile-id>`.

The editor never invokes a model. Tool and skill controls are backed by the
central runtime policy owners, and every save is previewed as exact file writes
and deletions before the same validated plan is applied.
