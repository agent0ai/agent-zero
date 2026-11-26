# Project scheduler authorization

- Team tasks keep their stable project and creator in native scheduler storage. A user action uses the active member's identity. A due task uses its creator's current grant.
- Team tasks use dedicated native chat contexts. Dispatch shares the standard team run reservation, user attribution, cancellation and history persistence.
- Task API callers must scope each action to the current project. Team scheduler payloads carry text and use the approved project tool set.
- Verify list, create, run, edit and delete from separate project memberships, plus a project grant revoked before the scheduler dispatches.
