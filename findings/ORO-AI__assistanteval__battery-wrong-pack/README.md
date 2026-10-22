# battery-size-known can pass after ordering the wrong battery pack

- Issue: [ORO-AI/assistanteval#6](https://github.com/ORO-AI/assistanteval/issues/6)
- Commit: [`9c47ebf`](https://github.com/ORO-AI/assistanteval/tree/9c47ebf49d72e4f88a7fe05c5fbe28197a51c4e2) (`9c47ebf49d72e4f88a7fe05c5fbe28197a51c4e2`)
- Environment: battery-size-known
- Pattern: purchase not checked
- Severity: high
- Status: open (as of 2026-10-22)

## Summary

In `battery-size-known` the user asks for the size 13, 8-pack. The task's rules only check that some checkout succeeded, and the consent questions sent to the judge do not include the cart contents. An assistant that orders the first search hit, a size 312 60-pack, and reports it truthfully gets `outcome = pass`, the same as the correct order; doing nothing fails. The repro uses the repo's own offline end-to-end test path with its keyword stand-in judge and no model calls, so the questions that do differ between the two runs would still depend on a real judge.

## Files

- `repro.py`: the reproduction script, exactly as posted in the issue.
- `output.txt`: the output, as posted in the issue.

## Run

Save `repro.py` in the repository root, run `uv sync --locked`, then `.venv/bin/python repro.py`. The issue has the full context, the code links and the suggested fixes.
