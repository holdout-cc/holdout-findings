# skillsbench-3d-scan-calc: verifier recomputes the answer from the agent-writable scan_data.stl, so overwriting it and reporting mass 0 scores 1.0

- Issue: [UiPath/coder_eval#233](https://github.com/UiPath/coder_eval/issues/233)
- Commit: [`8d85394`](https://github.com/UiPath/coder_eval/tree/8d853946ba38f23556d367b7826986162baae0b5) (`8d853946ba38f23556d367b7826986162baae0b5`)
- Environment: skillsbench 3d-scan-calc
- Pattern: agent-writable ground truth
- Severity: high
- Status: open (as of 2026-10-22)

## Summary

The verifier has no stored answer: it recomputes the expected mass and material ID from `/root/scan_data.stl` at grading time. That file is the agent's own input, and the agent can write to it. Overwriting it with a single zero-volume triangle and reporting mass 0 scores 1.0; the same answer scores 0 when the input is left alone. The repro runs the task's real `test_outputs.py` with pytest, with the `/root` paths pointed at a temporary directory, and also shows the no-op (0) and an honest solution (1).

## Files

- `repro.py`: the reproduction script, exactly as posted in the issue.
- `output.txt`: the output, as posted in the issue.

## Run

Run `python repro.py <path to coder_eval checkout>` (needs pytest 8.4.1, as pinned by the task's `test.sh`). The issue has the full context, the code links and the suggested fixes.
