# parse_log scores a failing withheld test as PASSED when its failure message contains "PASSED"

- Issue: [GeneralReasoning/env-r2e-gym#11](https://github.com/GeneralReasoning/env-r2e-gym/issues/11)
- Commit: [`2455cfa`](https://github.com/GeneralReasoning/env-r2e-gym/tree/2455cfac289a2287f6fa66701cdff423d37f6c9c) (`2455cfac289a2287f6fa66701cdff423d37f6c9c`)
- Environment: env-r2e-gym (`parse_log`)
- Pattern: stdout scraping
- Severity: high
- Status: open (as of 2026-10-24)

## Summary

`parse_log` decides each test's status by substring and checks `PASSED` before `FAILED`. pytest's summary line for a failed test ends with the failure message, so `FAILED ...::test_distance - PASSED` is recorded as passed. An agent can make the function under test raise an exception whose message is `PASSED` and get full reward without fixing the bug. The repro runs real pytest on a small task and scores the output with `R2EGym.answer()`: no fix 0.0, gold fix 1.0, and both exception variants 1.0 while pytest reports three failures.

## Files

- `repro.py`: the reproduction script, exactly as posted in the issue.
- `output.txt`: the output, as posted in the issue.

## Run

Save `repro.py` in the repository root and run `python repro.py` with `requirements.txt` and pytest installed. The issue has the full context, the code links and the suggested fixes.
