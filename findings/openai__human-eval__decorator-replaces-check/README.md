# A completion ending in a decorator replaces the test's check() with a no-op (100/164 tasks pass)

- Issue: [openai/human-eval#71](https://github.com/openai/human-eval/issues/71)
- Commit: [`b9453e8`](https://github.com/openai/human-eval/tree/b9453e8f1865df0a0057a1383767caa400acfbcf) (`b9453e8f1865df0a0057a1383767caa400acfbcf`)
- Environment: HumanEval execution harness
- Pattern: harness override
- Severity: high
- Status: open (as of 2026-10-23)

## Summary

The harness builds the test program by concatenating the prompt, the completion and the test code, then runs it with a single `exec`. If a completion ends in a decorator, Python attaches it to the test's `def check(candidate):`, and the decorator can replace `check` with a no-op. A fixed two-line completion that implements nothing passes the 100 tasks whose test starts with `def check` (pass@1 0.61), against 164/164 for the canonical solutions and 0/164 for `pass`. The repro runs the unmodified `evaluate_functional_correctness` on all 164 tasks.

## Files

- `repro.py`: the reproduction script, exactly as posted in the issue.
- `output.txt`: the output, as posted in the issue.

## Run

Run `python repro.py` with the repository importable (for example from the repository root). The issue has the full context, the code links and the suggested fixes.
