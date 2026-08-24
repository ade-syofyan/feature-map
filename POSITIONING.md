# feature-map positioning notes

`feature-map` sits near codebase-understanding and AI-documentation tools, but
it should not claim to replace them.

## Adjacent Tools

Sourcegraph and Cody focus on code search, navigation, and broad codebase
context for humans and AI agents.

Swimm focuses on building a validated, traceable knowledge base and
documentation layer for AI tools and modernization work.

General legacy-modernization guidance consistently points to the same first
step: understand the existing system, preserve business behavior, and validate
changes before rewriting or splitting services.

## What To Copy

- speak to both humans and AI agents
- emphasize reliable context, not just generated prose
- show modernization as a staged workflow
- prove claims with repeatable checks
- make limitations explicit

## What To Avoid

- claiming no similar tools exist
- pretending static analysis proves all business logic
- competing on broad enterprise search
- promising automatic migration or refactoring

## Differentiation

`feature-map` is narrower and more local:

- Git-reviewable `FEATURE-MAP.yaml`
- business-flow touchpoints across UI, backend, docs, migrations, and services
- stale-flow reminders and audit vocabulary
- read-only app migration packs for route/UI/auth/data discovery
- no SaaS dependency for the core workflow
- designed to be consumed directly by Claude Code and Codex

The strongest claim:

> `feature-map` is a local-first business-flow and migration-discovery layer for
> AI coding agents. It gives agents reviewable maps of what must stay consistent
> before they edit, rewrite, or split an application.
