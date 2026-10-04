# CLAUDE SUBAGENT ARM (not pooled with the main analysis)

Prereg section 9a, TASK-35. The baseline B repeated on Claude Haiku 4.5 as Claude Code
subagents, to compare stability and the distribution of responses against the main model. No
variation battery. A user-approved exception to "single structured batch calls, not agentic
subagents"; its rows never enter the main inference. A difference between the models is a
difference between two model-and-harness bundles, not a clean model effect.

## Run (after the prereg is frozen and the user approves the agent count)

```
uv run python -m subagent_arm prepare            # one task file per job under work/tasks
uv run python -m subagent_arm next --limit 25    # JSON lines: job_id, attempt, agent prompt
# the session spawns one haiku subagent per line, then reports runs that used more than one Read
# and one Write (the agent result shows 3 tool uses: Read, Write and the harness hand-back):
uv run python -m subagent_arm discard JOB_ID:ATTEMPT ...
uv run python -m subagent_arm ingest             # answers -> results/rows.jsonl
uv run python -m subagent_arm status
```

An invalid or discarded run is retried once by a fresh agent; a second failure is terminal.
Analyse the store with the normal commands, e.g.
`uv run llm-panel --config subagent_arm/config.subagent.yaml analyze variance`.
