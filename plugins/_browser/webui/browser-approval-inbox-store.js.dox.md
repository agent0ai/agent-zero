# Composer approval recovery

This presentation-only coordinator observes the two independently scoped
site and action inboxes. It has no API mutation, grant,
selection, credential, timer or persistent-state authority.

Empty inbox sections are hidden; pending requests and uncertain decisions are
not filtered using connection or browser-selection guesses. Each owning store
keeps unexpired current-chat prompts after failed polling and disables their
decision controls until a successful list response revalidates them.

Transport failures produce one frontend-only A0 notification-center entry per
chat/outage, with a stable ID bounding repeated entries. No recovery control,
inline outage row or toast is added to the composer. The mounted stores' existing
bounded polling automatically retries only their read-only list requests.
The coordinator never resends a decision or owns a retry loop.
