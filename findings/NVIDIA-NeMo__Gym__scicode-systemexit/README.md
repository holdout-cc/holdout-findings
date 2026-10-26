# scicode: `raise SystemExit(0)` in the generated code passes every sub-step (exit code 0 is the only pass signal)

- Issue: [NVIDIA-NeMo/Gym#4901](https://github.com/NVIDIA-NeMo/Gym/issues/4901)
- Commit: [`9240708`](https://github.com/NVIDIA-NeMo/Gym/tree/92407083ba1a8373b96ae660cbd4404cd874169c) (`92407083ba1a8373b96ae660cbd4404cd874169c`)
- Environment: scicode
- Pattern: early exit passes
- Severity: high
- Status (as of 2026-10-26): open; fix PR [#4946](https://github.com/NVIDIA-NeMo/Gym/pull/4946) (community, draft)

## Summary

A SciCode sub-step passes when its test program exits with code 0. Nothing confirms that the asserts ran, so a solution containing `raise SystemExit(0)` exits before reaching them and passes. Because each step's code is carried into later steps, one such line passes every later sub-step too: on the bundled example problems it passed 13/13 scored sub-steps, against 0/13 for a wrong-answer control. The posted repro is the minimal case: `run_substep` on a program whose only test is `assert False`.

## Files

- `repro.py`: the reproduction script, exactly as posted in the issue.
- `output.txt`: the output, as posted in the issue.
- `output-linux.txt`: Re-run on Ubuntu 24.04 LTS (Linux 6.8), Python 3.12.3, network disabled, at `9240708`.

## Run

Run from the repository root with `resources_servers/scicode` on `PYTHONPATH`. The issue has the full context, the code links and the suggested fixes.
