# Process Step Types Extensions DOX

## Purpose

- Register custom log types that render inside process groups.

## Ownership

- Plugin-specific registrations live in each plugin's `extensions/webui/get_process_step_types/` directory.

## Local Contracts

- Export a default function receiving `{ processStepTypes }`, a `Set` seeded with core types. Add custom process types with `processStepTypes.add(type)`; omit standalone types and preserve other registrations.
- `messages.js` awaits this hook before merging each message batch. The dispatcher also adds types that resolve to the generic tool renderer. The resulting set controls raw-log grouping, utility lookahead, and paging; unhandled types retain tool-step fallback rendering.
- Keep registration repeatable and independent of individual records. Each batch starts with a fresh set; the ordinary extension loader owns caching and plugin activation.

## Work Guidance

- Keep registrations consistent with the corresponding `get_message_handler` renderer. Pass its original argument to `drawProcessStep` as `log`.

## Verification

- Test live/replayed records, hidden utilities, oversized groups, and disabled-plugin history.

## Child DOX Index

No child DOX files.
