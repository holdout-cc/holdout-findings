# prime_math reward gives full credit to wrong intervals and to 100x, 1/100x and off-by-one numbers, and gives 0 to many correct equation answers

- Issue: [verl-project/verl#8346](https://github.com/verl-project/verl/issues/8346)
- Commit: [`d430157`](https://github.com/verl-project/verl/tree/d430157d15516d89e0cc853fd10fcd21d9234c44) (`d430157d15516d89e0cc853fd10fcd21d9234c44`)
- Environment: `prime_math` reward (`default_compute_score` for `numina_*` data sources)
- Pattern: loose numeric and interval match
- Severity: medium
- Status (as of 2026-10-25): open; fix PR [#8347](https://github.com/verl-project/verl/pull/8347) (ours, open)

## Summary

`default_compute_score` sends every `numina_*` data source, which covers the math rows of Eurus-2-RL-Data, to `prime_math.compute_score`, and that grader has three errors. An interval with the wrong endpoint bracket gets full credit, because the fallback `math_equal` strips the brackets before comparing. For a numeric gold, 100x and 1/100x the gold both score 1 through the percentage check, and so does an off-by-one integer once the gold is 10,000 or more. Many correct equation answers score 0, because the boxed answer is cut after its last `=`. On the 1,024 `numina_*` validation rows, 100x and 1/100x score 1 on all 452 nonzero numeric golds, a wrong bracket scores 1 on 9 of the 29 interval golds, and 61 golds score 0 when given back unchanged. The repro calls `default_compute_score` on eleven cases, with nothing patched.

## Files

- `repro.py`: the reproduction script, exactly as posted in the issue (posted as an unnamed snippet).
- `output.txt`: the output, as posted in the issue (Ubuntu 24.04, Python 3.12.3, CPU only, at `d430157`).

## Run

Run `python repro.py` from the repository root, in an environment built from the repository lockfile with `uv sync --frozen --all-packages --extra cpu`. The issue has the full context, the per-row counts, the root causes and the proposed fix.
