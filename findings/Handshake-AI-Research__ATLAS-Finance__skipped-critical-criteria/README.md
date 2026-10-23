# pass_at_k ignores critical criteria skipped by failed section gates

- Issue: [Handshake-AI-Research/ATLAS-Finance#12](https://github.com/Handshake-AI-Research/ATLAS-Finance/issues/12)
- Commit: [`cb7e574`](https://github.com/Handshake-AI-Research/ATLAS-Finance/tree/cb7e574a1420a62c8340dd76d5ea74e1ad95eacd) (`cb7e574a1420a62c8340dd76d5ea74e1ad95eacd`)
- Environment: pass@k (`scripts/pass_at_k.py`)
- Pattern: skipped criteria pass
- Severity: high
- Status: open (as of 2026-10-23)

## Summary

The README says a trial passes only when every critical criterion (weight >= 3) is met, but `judge_pass` drops criteria marked `skipped`, and the grader marks a whole section skipped when its gate is not met. Not attempting a gated section therefore passes, while attempting it and missing one critical criterion fails. Across the 100 tasks, a blank workbook passes 3 at reward 0.000. The repro runs the real grader and `pass_at_k.py` with the LLM judge replaced by fixed verdicts; the gate verdicts are assumed, not judged.

## Files

- `repro.py`: the reproduction script, exactly as posted in the issue.
- `output.txt`: the output, as posted in the issue.

## Run

Run `python -I repro.py <ATLAS-Finance checkout> <generated datasets/atlas dir>`. The setup steps (checkout, dataset download, grader install at its pinned commit) are in the issue. The issue has the full context, the code links and the suggested fixes.
