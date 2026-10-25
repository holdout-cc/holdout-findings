# bug: coding examples are graded by source-text substrings, so unfixed code with the expected snippet in a comment scores 1.0

- Issue: [Toloka/tolokaforge#1933](https://github.com/Toloka/tolokaforge/issues/1933)
- Commit: [`daac88e`](https://github.com/Toloka/tolokaforge/tree/daac88e3dec00e6712f2cbc111c4f73e70411466) (`daac88e3dec00e6712f2cbc111c4f73e70411466`)
- Environment: examples/native/coding
- Pattern: substring match
- Severity: high
- Status (as of 2026-10-25): open; no fix PR yet

## Summary

The two bundled coding tasks grade the source file by case-insensitive substring match and never run the code. Leaving the bug in place and adding the expected snippet as a comment scores 1.0 and passes, while the correct one-character fix scores 0.783 and fails, the same score as leaving the bug alone. The repro grades three versions of `buggy_math.py` with the real `GradingEngine` and prints what the patched function actually returns.

## Files

- `repro.py`: the reproduction script, exactly as posted in the issue.
- `output.txt`: the output, as posted in the issue.

## Run

Save `repro.py` in the repository root and run `uv run python repro.py`. The issue has the full context, the code links and the suggested fixes.
