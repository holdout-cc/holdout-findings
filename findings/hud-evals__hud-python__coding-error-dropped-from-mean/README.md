# coding-task: an agent can drop a failed run from Job.reward by making the hidden tests exit before writing JUnit XML

- Issue: [hud-evals/hud-python#737](https://github.com/hud-evals/hud-python/issues/737)
- Commit: [`e95373f`](https://github.com/hud-evals/hud-python/tree/e95373f201dced7097d19c75e5a226907926b7f5) (`e95373f201dced7097d19c75e5a226907926b7f5`)
- Environment: coding environment / `Job.reward`
- Pattern: errors dropped from mean
- Severity: medium
- Status: open (as of 2026-10-22)

## Summary

In the coding environment, a hidden test run that writes no JUnit report is graded `isError=True`, and `Job.reward` leaves error runs out of the mean. The agent's code runs inside that test command, so two lines that call `os._exit(0)` once pytest is loaded make the report go missing. A failed task is then excluded instead of counted as 0: solving one of two tasks and breaking the tests on the other gives a job reward of 1.000, the same as solving both, against 0.500 for an honest failure. Per-run rewards are not affected.

## Files

- `repro.py`: the reproduction script, exactly as posted in the issue.
- `output.txt`: the output, as posted in the issue.

## Run

Save `repro.py` in the repository root and run `python repro.py` with the coding environment's dependencies installed. The issue has the full context, the code links and the suggested fixes.
