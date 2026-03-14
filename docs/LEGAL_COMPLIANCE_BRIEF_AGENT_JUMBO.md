# Legal and Compliance Brief: Agent Jumbo

This document is an operations/legal review checklist for productization.
It is not legal advice.

## Product position

Agent Jumbo is a specialized AI Architect platform derived from Agent Zero code.

## Required controls before wider distribution

1. Preserve upstream license text and attribution requirements (Apache 2.0).
2. Preserve and review all required copyright headers/notices.
3. Add and maintain a root `NOTICE` file if derivative attribution is needed.
4. Ensure branding avoids implied endorsement by Agent Zero maintainers.
5. Keep a clear fork statement in README/docs.

## Trademark and naming controls

1. Use "Agent Jumbo" as primary product name in UX/docs.
2. Use "derived from Agent Zero" language only as attribution, not endorsement.
3. Remove or replace upstream links/icons that imply official ownership.

## Data and security controls

1. No secrets in code, commits, logs, screenshots, or demo recordings.
2. PAT/API key handling only through secrets settings and secure storage.
3. Define retention policy for chats, logs, tool traces, and uploaded files.
4. Define user deletion/export capabilities for local data handling.

## Commercial readiness controls

1. Publish Terms of Use and Privacy Policy matching actual data behavior.
2. Define support/SLA boundaries for free vs paid tiers.
3. Create incident response process for security/data exposure events.
4. Define third-party dependency review cadence.

## Upstream sharing controls

1. Share only generic technical improvements unless explicitly agreed.
2. Do not share customer data, internal prompts, or private runbooks.
3. Keep upstream PRs narrow, test-backed, and license-clean.

## Counsel review packet (recommended)

1. Architecture and data flow diagram
2. License and NOTICE inventory
3. Branding and trademark usage examples
4. Security + retention policy drafts
5. Planned commercial packaging and distribution model
