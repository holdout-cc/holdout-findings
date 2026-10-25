# bug: terminal_bench 2.1 tasks mount /tests writable in the agent's container, so rewriting test.sh scores 1.0

- Issue: [Toloka/tolokaforge#1934](https://github.com/Toloka/tolokaforge/issues/1934)
- Commit: [`daac88e`](https://github.com/Toloka/tolokaforge/tree/daac88e3dec00e6712f2cbc111c4f73e70411466) (`daac88e3dec00e6712f2cbc111c4f73e70411466`)
- Environment: terminal_bench adapter (2.1-shape tasks)
- Pattern: agent-writable tests
- Severity: high
- Status (as of 2026-10-25): open; no fix PR yet

## Summary

For terminal_bench tasks in the 2.1 shape, the adapter mounts the task's `tests/` read-write into the agent's container, and grading later runs `/tests/test.sh` from that same mount. An agent can overwrite `test.sh` with one line that writes 1.0 to the reward file and score 1.0 without changing the code. The repro builds a small task in the same shape and grades a do-nothing turn (0.00), a correct fix (1.00) and the test rewrite (1.00) with the real adapter and grader. The agent container is emulated; Docker is not used.

## Files

- `repro.py`: the reproduction script, exactly as posted in the issue.
- `output.txt`: the output, as posted in the issue.

## Run

Save `repro.py` in the repository root and run `uv run python repro.py`. The issue has the full context, the code links and the suggested fixes.
