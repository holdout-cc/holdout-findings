# Reward-mode container verifier scores a reward.txt the agent planted, even when test.sh exits non-zero

- Issue: [scaleapi/agentenv-framework#305](https://github.com/scaleapi/agentenv-framework/issues/305)
- Commit: [`35b6ae1`](https://github.com/scaleapi/agentenv-framework/tree/35b6ae1ac977ecedc33f6912d1deb34e80e4d484) (`35b6ae1ac977ecedc33f6912d1deb34e80e4d484`)
- Environment: container unit-test verifier (reward mode)
- Pattern: planted reward file
- Severity: medium
- Status: fixed (as of 2026-10-23)
- Fix: [scaleapi/agentenv-framework#310](https://github.com/scaleapi/agentenv-framework/pull/310), merged 2026-10-23. The verifier now deletes the reward file before running.

## Summary

In reward mode, the container verifier reads the reward file from the task container after the test command runs, without clearing it first and without checking the exit code. If the agent writes `1` to the reward path during its turn and the task's `test.sh` then fails without writing the file, the planted `1` is recorded as `score=1.0, result=True` with exit code 1. This needs a `test.sh` that can exit without writing the file; one that always writes 0 or 1 is not affected. The repro drives the real verifier step with the sandbox replaced by temporary directories.

## Files

- `repro.py`: the reproduction script, exactly as posted in the issue.
- `output.txt`: the output, as posted in the issue.

## Run

Run `uv run python repro.py` from the repository root. The issue has the full context, the code links and the suggested fixes.
