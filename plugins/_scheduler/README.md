# Scheduler

Provides the `scheduler` agent tool for managing saved tasks and schedules: listing, finding by name, showing, running, updating, deleting, and creating scheduled, ad-hoc, and planned tasks.

The Scheduled Tasks modal, welcome card, sidebar navigation entry and tasks list, and scheduler CRUD API endpoints live in this plugin; the shared `TaskScheduler` scheduling engine stays in core (used by the job loop, tick API, chat lifecycle, and other plugins).

If Agent Zero is offline when a recurring task is due, the task runs once on the next scheduler tick after startup. Several missed occurrences produce one run, followed by the normal schedule. The same behavior covers delayed ticks and applies to both agent tasks and plugin maintenance. The scheduler ticks at startup and then every minute.

Disabled tasks stay disabled. Changing the cron/timezone or re-enabling a task starts its schedule from that moment; renaming it or editing its prompt preserves a pending run. Manual runs, cancellation and completion consume intervening occurrences, so they are not immediately replayed. Errored tasks and tasks interrupted while running require explicit recovery.

Saved recurring tasks include `schedule_anchor`. Older task files derive it from their saved creation, update and last-run timestamps. When changing a schedule directly in a task file, set its anchor to the time the new schedule takes effect. Existing overdue tasks can run once when upgrading.
