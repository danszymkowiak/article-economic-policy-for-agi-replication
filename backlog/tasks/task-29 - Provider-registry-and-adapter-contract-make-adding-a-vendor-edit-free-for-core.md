---
id: TASK-29
title: >-
  Provider registry and adapter contract (make adding a vendor edit-free for
  core)
status: In Progress
assignee:
  - '@claude'
created_date: '2026-10-03 11:30'
updated_date: '2026-10-03 11:33'
labels:
  - refactor
dependencies: []
ordinal: 29000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The repo will be shared, and others may want to connect a different vendor. ModelClient already abstracts providers, but default_client_factory in bootstrap/cli.py is a hardcoded if/elif over fake and opencode, main() catches the Zen-specific ZenConfigError by name, and domain/zen_protocol.py puts a vendor wire format in the domain layer. Adding a provider currently means editing core files. No Anthropic adapter is in scope (the user has no Anthropic account); the aim is only that a third party can add one without touching core. Wiring changes must not alter job_id inputs, which the preregistration relies on.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 A pinned-job_id regression test captures a known job_id before the refactor and still passes after it
- [x] #2 A reusable ModelClient contract test suite passes for both FakeModelClient and ZenClient
- [x] #3 Providers are looked up in a registry; default_client_factory contains no per-provider branches and adding a provider requires no edit to cli.py
- [x] #4 ports.py defines ProviderConfigError, ZenConfigError subclasses it, and the CLI catches only the port-level error
- [x] #5 zen_protocol.py moves out of domain/ into the Zen adapter package; domain/ stays I/O- and vendor-free (test_no_io passes)
- [x] #6 docs/adding-a-provider.md explains the ModelClient contract, registration, pricing and approved_providers config, and the key-in-.env convention
- [x] #7 Full test suite passes with no paid calls
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Pin job_id with a characterization test. 2. Write the ModelClient contract suite, registry tests, CLI refusal test and a domain no-vendor test (red). 3. Add ProviderConfigError to ports; move Zen client and wire format to adapters/zen/; add bootstrap/providers.py registry; slim cli.py. 4. Write docs/adding-a-provider.md.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Red phase confirmed (missing registry, ProviderConfigError, adapters.zen). After: 202 tests pass (was 176), ruff clean. Zen transport injection kept as ProviderContext.transports, a test seam.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Added a provider registry (bootstrap/providers.py), ProviderConfigError in ports, and a shared ModelClient contract suite run against Fake and Zen. Zen client and wire format now live in adapters/zen/; cli.py has no per-provider branches; docs/adding-a-provider.md written. job_id pinned by test. Verified: 202 tests pass, ruff clean, no paid calls.
<!-- SECTION:FINAL_SUMMARY:END -->
