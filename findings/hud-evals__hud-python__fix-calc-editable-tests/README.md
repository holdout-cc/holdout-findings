# daytona-rl `fix_calc`: reward 1.0 while `calc.py` stays broken (test file is editable, pass count is read from stdout)

- Issue: [hud-evals/hud-python#736](https://github.com/hud-evals/hud-python/issues/736)
- Commit: [`e95373f`](https://github.com/hud-evals/hud-python/tree/e95373f201dced7097d19c75e5a226907926b7f5) (`e95373f201dced7097d19c75e5a226907926b7f5`)
- Environment: cookbooks/daytona-rl `fix_calc`
- Pattern: agent-writable tests, stdout scraping
- Severity: high
- Status: open (as of 2026-10-24)

## Summary

`fix_calc` gives reward 1.0 when the pass count parsed from pytest output equals the expected total. The test file sits in the agent's workspace and is not restored before grading, so replacing it with ten empty tests scores 1.0. Separately, the pass count is the first `(\d+) passed` match in the combined output, so a `print("10 passed")` in `calc.py` also scores 1.0 while pytest itself reports 4 failed. Both shortcuts work on all 24 variants; the repro also shows the no-op (0/24) and the correct fix (24/24).

## Files

- `repro_fix_calc.py`: the reproduction script, exactly as posted in the issue.
- `output.txt`: the output, as posted in the issue.

## Run

Save `repro_fix_calc.py` in the repository root and run it in the repository's environment (needs pytest). The issue has the full context, the code links and the suggested fixes.
