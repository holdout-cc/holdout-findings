# on-policy-self-distillation verifier can score a reused checkpoint without enforcing 100 training steps

- Issue: [scaleapi/rsi-benchmark#103](https://github.com/scaleapi/rsi-benchmark/issues/103)
- Commit: [`44a49f3`](https://github.com/scaleapi/rsi-benchmark/tree/44a49f33f6025c7fc4d9ac7440ec5da2ba8a7a14) (`44a49f33f6025c7fc4d9ac7440ec5da2ba8a7a14`)
- Environment: samples/on-policy-self-distillation
- Pattern: budget not enforced
- Severity: high
- Status: open (as of 2026-10-22)

## Summary

The verifier is meant to enforce a 100-step training budget by running the training itself, but it runs the solver's own `opsd_train.py` and then scores any directory named `checkpoint-100`. Nothing checks how many steps were trained, and a non-zero exit from training is ignored. A solver can stash a checkpoint trained outside the rules and have its script copy it into place; the verifier scores it in all five runs with `status: ok` and no flags. The repro runs the real `test.sh` and `train_capped.sh` with the GPU, model and evaluation stubbed; the cheat's score is a placeholder, not a measured result.

## Files

- `repro.sh`: the reproduction script, exactly as posted in the issue.
- `output.txt`: the output, as posted in the issue.

## Run

From an empty directory next to a checkout: `unshare -n bash repro.sh rsi-benchmark`. The issue has the full context, the code links and the suggested fixes.
