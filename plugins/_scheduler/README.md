# Scheduler

Provides the `scheduler` agent tool for managing saved tasks and schedules: listing, finding by name, showing, running, updating, deleting, and creating scheduled, ad-hoc, and planned tasks.

The Scheduled Tasks modal, welcome card, sidebar navigation entry and tasks list, and scheduler CRUD API endpoints live in this plugin; the shared `TaskScheduler` scheduling engine stays in core (used by the job loop, tick API, chat lifecycle, and other plugins).
