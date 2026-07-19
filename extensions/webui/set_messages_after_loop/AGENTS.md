# Set Messages After Loop Extensions DOX

## Purpose

- Own frontend extensions that run after message DOM updates complete.

## Ownership

- Files in this folder own after-render message behavior.

## Local Contracts

- JavaScript modules must export a default function when present.
- Preserve message DOM stability and avoid duplicate controls on repeated renders.

## Work Guidance

- Use stable markers when injecting controls into message elements.

## Verification

- Smoke-test message rerendering and extension-injected controls after changes.

## Child DOX Index

No child DOX files.
