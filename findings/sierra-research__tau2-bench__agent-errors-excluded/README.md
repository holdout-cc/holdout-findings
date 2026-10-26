# Malformed tool-call JSON and empty replies can be excluded from the 2.0 score

- Issue: [sierra-research/tau2-bench#672](https://github.com/sierra-research/tau2-bench/issues/672)
- Commit: [`05736c2`](https://github.com/sierra-research/tau2-bench/tree/05736c27219b769d0be507574dd3135010916644) (`05736c27219b769d0be507574dd3135010916644`)
- Environment: 2.0 benchmark score (`metrics/benchmark.py`)
- Pattern: errors dropped from mean
- Severity: medium
- Status (as of 2026-10-26): open; fix PR [#674](https://github.com/sierra-research/tau2-bench/pull/674) (community, open)

## Summary

The 2.0 score drops `infrastructure_error` trials from the denominator as harness faults. Malformed tool-call JSON from the agent model and an empty agent reply both raise uncaught exceptions that end up recorded as `INFRASTRUCTURE_ERROR`. A task failed this way is excluded rather than scored 0: in the repro, a two-task cell scores 0.5 with an honest wrong answer and 1.0 with either failure, the same as solving the task. The repro runs the real orchestrator, agent and user simulator with the model calls replaced by scripted responses.

## Files

- `repro.py`: the reproduction script, exactly as posted in the issue.
- `output.txt`: the output, as posted in the issue.

## Run

Save `repro.py` in the repository root and run `uv run python repro.py`. The issue has the full context, the code links and the suggested fixes.
