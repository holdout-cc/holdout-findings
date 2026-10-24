# proposer_solver: the proposer's contract answer is never verified, so false or ambiguous problems earn max learnability

- Issue: [PrimeIntellect-ai/verifiers#2947](https://github.com/PrimeIntellect-ai/verifiers/issues/2947)
- Commit: [`8859385`](https://github.com/PrimeIntellect-ai/verifiers/tree/885938574b10969f9ea55c79b0f486faf0de6819) (`885938574b10969f9ea55c79b0f486faf0de6819`)
- Environment: proposer_solver
- Pattern: unverified label
- Severity: high
- Status: open (as of 2026-10-24)

## Summary

In the self-play `proposer_solver` environment, the proposer's contract answer becomes the solvers' ground truth without any check. The proposer is rewarded on solve rate alone (`4p(1-p)`), so a wrong or ambiguous label that splits the solvers earns the same maximum learnability as a genuinely hard problem. The repro uses the environment's own `from_trace`, `correct` and `finalize`: a false label ("1+1" -> 3) and an ambiguous one ("x^2 = 9" -> -3) both score learnability 1.0 when the solvers split 2/2, while a true easy problem scores 0.0. With `train_solver=True` (the default), solvers that answered correctly are scored 0 in those episodes.

## Files

- `repro.py`: the reproduction script, exactly as posted in the issue.
- `output.txt`: the output, as posted in the issue.
- `output-linux.txt`: Re-run on Ubuntu 24.04 LTS (Linux 6.8), Python 3.12.3, network disabled, at `8859385`.

## Run

The issue has the full context, the code links and the suggested fixes.
