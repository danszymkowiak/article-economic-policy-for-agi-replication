# Project: LLM-panel sensitivity study

Re-implementation (not a replication) of the "Economic Policy for AGI" survey from its public description, plus a preregistered sensitivity analysis of how stable its rankings are. See README.md for the design.

## Ground rules
- Report the whole range of results; do not search for maximum variation. The adversarial arm is separate, in its own directory, and clearly labeled.
- Write `prereg/prereg.md` and keep it draft until the user tags it frozen. No paid API calls before that, except labeled non-inference runs (smoketest, pilot): each needs the user's explicit go-ahead, goes through the spend ceiling and `--confirm`, and its data never enters inference.
- Hard spend ceiling `max_spend_usd = 15`, enforced in code (`submit` needs `--confirm` and refuses anything that would exceed the ceiling). Confirm with the user before any paid call on a new provider.
- Run the tests and stop for user review after each task.
- Pin exact model snapshots, never aliases. Use single structured batch calls, not agentic subagents.
- Log every run, including failures, with seed and temperature. The raw store is append-only; analysis reads only from `results/raw`.
- Instability of scores shows they lack the claimed precision, not that the recommendations are wrong. Say so in write-ups.

## Architecture
Layers: domain (no I/O) -> ports (`ModelClient`, `ResultStore`) -> adapters (per-provider batch clients, JSONL/Parquet store) -> application (expand, build jobs, submit, collect, validate) -> bootstrap (config, cron-friendly CLI).
`job_id` = sha256(rendered prompt + model snapshot + temperature + seed), so reruns skip finished jobs. Responses are validated against a JSON schema (score 0-100 plus short rationale); malformed ones are retried once, then logged as failures.

## Credentials
Provider keys live in `.env` (gitignored) and are read from the environment at runtime, never opened by Claude. OpenCode Zen: `OPENCODE_API_KEY`. Zen auto-reload is off. Zen model ids are aliases, so log the model id each response reports.

## Local-only reference
`docs/private/` is gitignored and may hold the original design discussion (`design-chat.md`). Do not copy its contents verbatim into committed files.

<!-- BACKLOG.MD GUIDELINES START -->
<!-- backlog.md-instructions-version: 1.53.0 -->
<CRITICAL_INSTRUCTION>

## Backlog.md Workflow

This project uses Backlog.md for task and project management.

**At the beginning of each conversation in this project, run `backlog instructions overview` before answering or taking action. Re-read it only if you have not read it yet in the current conversation.**

Use the overview to decide whether to search, read, create, or update Backlog tasks.

Before task lifecycle actions, read the matching detailed guide:
- `backlog instructions task-creation` before creating or splitting tasks
- `backlog instructions task-execution` before planning, changing status or assignee, adding a plan or implementation notes, or implementing task work
- `backlog instructions task-finalization` before checking acceptance criteria, writing final summaries, or moving tasks to terminal statuses

Use `backlog <command> --help` before running unfamiliar commands. Help shows options, fields, and examples.

Do not edit Backlog task, draft, document, decision, or milestone markdown files directly. Use the `backlog` CLI so metadata, relationships, and history stay consistent.

</CRITICAL_INSTRUCTION>
<!-- BACKLOG.MD GUIDELINES END -->
