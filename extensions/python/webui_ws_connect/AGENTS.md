# WebUI WebSocket Connect Extensions DOX

## Purpose

- Own backend behavior when a WebUI WebSocket client connects.

## Ownership

- Ordered Python files own state-sync behavior for new WebSocket connections.

## Local Contracts

- Preserve WebSocket auth/session assumptions.
- Send only state the connected client is allowed to receive.

## Work Guidance

- Coordinate connect behavior with frontend WebSocket client and sync store.

## Verification

- Smoke-test WebUI connection and initial state sync after changes.

## Child DOX Index

No child DOX files.
