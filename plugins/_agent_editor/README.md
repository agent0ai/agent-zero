# Agent Editor

Agent Editor provides the deterministic Easy modal and Advanced workspace for
Agent Zero profiles. It reads the existing layered profile architecture and
writes only sparse overrides in the selected Global or project profile layer.

The editor never invokes a model. Tool and skill controls are backed by the
central runtime policy owners, and every save is previewed as exact file writes
and deletions before the same validated plan is applied.

Global agents and customizations live under `usr/agents/<profile-id>` and apply
across projects. Project-scoped agents and customizations live under
`usr/projects/<project>/.a0proj/agents/<profile-id>`, inherit the Global layer,
and can be removed without changing it.

Manage agents can duplicate the effective profile into the selected scope and
toggle whether each profile is available there. Project availability reuses
`.a0proj/agents.json`; Global availability is a sparse profile override.
The Default profile always remains available.
