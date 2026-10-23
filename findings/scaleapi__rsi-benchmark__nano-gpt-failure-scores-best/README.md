# nano-gpt-data-curation: invalid or empty submission gets reward 0.0, the best value on a lower-is-better perplexity metric

- Issue: [scaleapi/rsi-benchmark#102](https://github.com/scaleapi/rsi-benchmark/issues/102)
- Commit: [`44a49f3`](https://github.com/scaleapi/rsi-benchmark/tree/44a49f33f6025c7fc4d9ac7440ec5da2ba8a7a14) (`44a49f33f6025c7fc4d9ac7440ec5da2ba8a7a14`)
- Environment: samples/nano-gpt-data-curation
- Pattern: failure scores best
- Severity: medium
- Status: open (as of 2026-10-23)

## Summary

The task's reward is held-out perplexity, where lower is better, but every failure path writes 0.0 to `reward.txt`. On this metric 0.0 beats every real run, including the reference. A missing, malformed or duplicate-id `selection.json` all give `status=invalid` with `reward.txt=0.0000`; only a consumer that reads `status` from `result.json` can tell them apart. The repro runs the real `test.sh` and scoring scripts with a stand-in data pool and a training stub that reports the task's own anchor perplexities.

## Files

- `repro.sh`: the reproduction script, exactly as posted in the issue.
- `output.txt`: the output, as posted in the issue.

## Run

Save `repro.sh` in the repository root and run `bash repro.sh` (needs numpy). The issue has the full context, the code links and the suggested fixes.
