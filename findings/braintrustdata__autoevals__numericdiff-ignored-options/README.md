# NumericDiff ignores documented tolerance options and can score near misses highly

- Issue: [braintrustdata/autoevals#251](https://github.com/braintrustdata/autoevals/issues/251)
- Commit: [`2786296`](https://github.com/braintrustdata/autoevals/tree/2786296339f4b99c907a4dc8a9a867f0fe57ad7a) (`2786296339f4b99c907a4dc8a9a867f0fe57ad7a`)
- Environment: NumericDiff (Python and JS)
- Pattern: documented options ignored
- Severity: medium
- Status: open (as of 2026-10-22)

## Summary

`SCORERS.md` documents `max_diff` and `relative` options for `NumericDiff`, but neither the Python nor the JS implementation reads them. Python accepts the options silently, so a caller who sets a tight tolerance gets the default score: with `max_diff=0.01`, 2025 vs 2024 scores 0.9998 and 999 vs 1000 scores 0.9995. Both worked examples in the docs disagree with the code. The repro calls the real Python scorer; the JS version was not run.

A community pull request (#252) proposing a documentation fix is open.

## Files

- `repro.py`: the reproduction script, exactly as posted in the issue.
- `output.txt`: the output, as posted in the issue.

## Run

Save `repro.py` in the repository root and run `python repro.py` after `pip install -e .`. The issue has the full context, the code links and the suggested fixes.
